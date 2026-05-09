import os
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

load_dotenv(override=True)

# ==========================================
# Phase 7: Multi-Agent Systems (Supervisor)
# ==========================================

# 1. Define the Router Schema
# We use Pydantic to force the LLM to output ONLY one of these three exact strings.
class Router(BaseModel):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal["Researcher", "Coder", "FINISH"]

# 2. Setup our LLMs (We MUST use llama3.1 for structured output support)
llm = ChatOllama(model="llama3.1", temperature=0)

# We create a special version of the LLM for the Supervisor that guarantees JSON output matching our Router schema
supervisor_llm = llm.with_structured_output(Router)

# 3. Define the State
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next: str

# 4. Define the Nodes
def supervisor_node(state: AgentState):
    print("\n--- [Node: SUPERVISOR] Analyzing Request ---")
    system_prompt = (
        "You are a supervisor managing two specialized workers: 'Researcher' and 'Coder'. "
        "Based on the user's request and the conversation history, decide who should act next. "
        "If the user asks for explanations, history, or facts, route to 'Researcher'. "
        "If the user asks to write, debug, or generate code, route to 'Coder'. "
        "If the task is fully complete and both questions are answered, route to 'FINISH'."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | supervisor_llm
    
    try:
        # We get a strongly typed Python object back!
        response = chain.invoke({"messages": state["messages"]})
        next_agent = response.next
    except Exception as e:
        print(f"   [Warning] Supervisor failed strict parsing. Defaulting to FINISH. Error: {e}")
        next_agent = "FINISH"
        
    print(f"   -> Supervisor decided to route to: {next_agent}")
    return {"next": next_agent}

def researcher_node(state: AgentState):
    print("\n--- [Node: RESEARCHER] Gathering Information ---")
    system_prompt = "You are an expert researcher. Provide a brief, one-paragraph explanation of the topic requested."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    response = (prompt | llm).invoke({"messages": state["messages"]})
    return {"messages": [AIMessage(content=f"[Researcher]: {response.content}")]}

def coder_node(state: AgentState):
    print("\n--- [Node: CODER] Writing Code ---")
    system_prompt = "You are an expert software engineer. Write clean Python code to solve the request. Only output code, no markdown explanations."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    response = (prompt | llm).invoke({"messages": state["messages"]})
    return {"messages": [AIMessage(content=f"[Coder]: {response.content}")]}

# 5. Build the Graph
builder = StateGraph(AgentState)

builder.add_node("Supervisor", supervisor_node)
builder.add_node("Researcher", researcher_node)
builder.add_node("Coder", coder_node)

# Entry point is always the manager
builder.add_edge(START, "Supervisor")

# Workers ALWAYS report back to the supervisor when done!
builder.add_edge("Researcher", "Supervisor")
builder.add_edge("Coder", "Supervisor")

# The Supervisor conditionally routes to the workers or END
builder.add_conditional_edges(
    "Supervisor",
    lambda state: state["next"],
    {
        "Researcher": "Researcher",
        "Coder": "Coder",
        "FINISH": END
    }
)

app = builder.compile()

if __name__ == "__main__":
    print("====================================")
    print("SCENARIO: Multi-Agent Workflow")
    print("====================================")
    
    # We ask a complex prompt that requires BOTH research and coding.
    user_input = "Can you briefly explain what Quicksort is, and then write a Python function for it?"
    print(f"USER: {user_input}\n")
    
    # Run the multi-agent hive!
    final_state = app.invoke({"messages": [HumanMessage(content=user_input)]})
    
    print("\n\n====================================")
    print("FINAL CONVERSATION TRACE")
    print("====================================")
    for msg in final_state["messages"]:
        if isinstance(msg, AIMessage):
            print(f"\n{msg.content}")
