import os
from dotenv import load_dotenv

# --- 1. SET ENVIRONMENT VARIABLES FIRST ---
# Langfuse strictly checks the environment upon import! We must set these before importing langfuse.
load_dotenv(".env", override=True)

if "LANGFUSE_BASE_URL" in os.environ and "LANGFUSE_HOST" not in os.environ:
    os.environ["LANGFUSE_HOST"] = os.environ["LANGFUSE_BASE_URL"]

# Debug check to prevent confusing Langfuse errors
if not os.environ.get("LANGFUSE_PUBLIC_KEY"):
    print("\n" + "="*60)
    print("ERROR: Could not load LANGFUSE_PUBLIC_KEY from .env!")
    print("This often happens if the .env file has a hidden encoding issue (like UTF-16 from PowerShell).")
    print("To fix this: Open .env in your editor, copy the contents, delete the file, create a new .env file, paste, and save.")
    print("="*60 + "\n")
    exit(1)

from typing import TypedDict, List
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END

# --- 2. LANGFUSE IMPORT & INIT ---
from langfuse.langchain import CallbackHandler
langfuse_handler = CallbackHandler()

llm = ChatOllama(model="llama3", temperature=0)

# ==========================================
# Phase 3: Observability with Langfuse
# ==========================================
# (The Agent logic remains exactly the same as our practical customer bot)

class AgentState(TypedDict):
    messages: List[BaseMessage]
    category: str

def categorizer_node(state: AgentState):
    print("--- [Node] Categorizing Intent ---")
    last_message = state["messages"][-1].content
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a routing agent. Categorize the user's input into exactly one of these three categories: 'sales', 'support', or 'escalate'. Respond ONLY with the category name and nothing else."),
        ("user", "{input}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"input": last_message})
    
    category = response.content.strip().lower().replace(".", "")
    if category not in ["sales", "support", "escalate"]:
        category = "support"
        
    print(f"    -> Category determined: {category}")
    return {"category": category}

def support_agent_node(state: AgentState):
    print("--- [Node] Support Agent Answering ---")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful technical support agent. Keep your answer brief and polite."),
        MessagesPlaceholder(variable_name="messages")
    ])
    chain = prompt | llm
    response = chain.invoke({"messages": state["messages"]})
    return {"messages": state["messages"] + [AIMessage(content=response.content)]}

def sales_agent_node(state: AgentState):
    print("--- [Node] Sales Agent Answering ---")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an enthusiastic sales agent. You want to sell our Premium Widget. Keep it brief."),
        MessagesPlaceholder(variable_name="messages")
    ])
    chain = prompt | llm
    response = chain.invoke({"messages": state["messages"]})
    return {"messages": state["messages"] + [AIMessage(content=response.content)]}

def human_escalation_node(state: AgentState):
    print("--- [Node] Escalating to Human ---")
    response_msg = "I understand you're frustrated. I'm escalating your case to a human manager. Please hold on..."
    return {"messages": state["messages"] + [AIMessage(content=response_msg)]}

def route_by_category(state: AgentState):
    category = state.get("category", "support")
    if category == "sales":
        return "sales_agent"
    elif category == "escalate":
        return "human_escalation"
    else:
        return "support_agent"

builder = StateGraph(AgentState)
builder.add_node("categorizer", categorizer_node)
builder.add_node("support_agent", support_agent_node)
builder.add_node("sales_agent", sales_agent_node)
builder.add_node("human_escalation", human_escalation_node)

builder.add_edge(START, "categorizer")
builder.add_conditional_edges("categorizer", route_by_category)

builder.add_edge("support_agent", END)
builder.add_edge("sales_agent", END)
builder.add_edge("human_escalation", END)

app = builder.compile()


if __name__ == "__main__":
    test_input = "My app keeps crashing when I open the settings menu. How do I fix it?"
    
    print(f"\n\n{'='*60}\nSCENARIO: {test_input}\n{'='*60}")
    
    initial_state = {
        "messages": [HumanMessage(content=test_input)],
        "category": ""
    }
    
    # --- 3. INJECT THE LANGFUSE CALLBACK ---
    # We pass the langfuse_handler in the config under 'callbacks'.
    # LangGraph will automatically propagate this to every node and LLM call!
    final_state = app.invoke(
        initial_state,
        config={"callbacks": [langfuse_handler]}
    )
    
    print(f"\n[FINAL BOT RESPONSE]:\n{final_state['messages'][-1].content}")
    
    # --- 4. TRACE COMPLETE ---
    # Modern Langfuse SDK handles flushing automatically on script exit.
    try:
        print(f"\n[INFO] Trace sent to Langfuse! View it here: {langfuse_handler.get_trace_url()}")
    except Exception:
        print("\n[INFO] Trace sent! Check your Langfuse Cloud Dashboard.")
