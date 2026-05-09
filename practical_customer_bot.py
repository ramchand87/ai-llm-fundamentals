import os
from typing import TypedDict, List
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END

# Load environment variables (if any)
load_dotenv()

# We use the local Ollama model (llama3)
# Setting temperature=0 ensures more deterministic/focused routing
llm = ChatOllama(model="llama3", temperature=0)

# ==========================================
# Practical LangGraph: Customer Service Bot
# ==========================================

# 1. Define the State
# We track the conversation history and the determined category of the user's issue.
# In a Java context, think of this as a DTO (Data Transfer Object) passed through a pipeline.
class AgentState(TypedDict):
    messages: List[BaseMessage]
    category: str

# 2. Define the Nodes

def categorizer_node(state: AgentState):
    """Analyzes the latest user message and categorizes the intent."""
    print("--- [Node] Categorizing Intent ---")
    
    # Get the latest user message from the state
    last_message = state["messages"][-1].content
    
    # Ask LLM to categorize
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a routing agent. Categorize the user's input into exactly one of these three categories: 'sales', 'support', or 'escalate'. Respond ONLY with the category name and nothing else."),
        ("user", "{input}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"input": last_message})
    
    # Clean up the output (LLMs sometimes add punctuation)
    category = response.content.strip().lower().replace(".", "")
    if category not in ["sales", "support", "escalate"]:
        category = "support" # default fallback
        
    print(f"    -> Category determined: {category}")
    
    # We return the updated fields of the state
    return {"category": category}

def support_agent_node(state: AgentState):
    """Handles technical support questions."""
    print("--- [Node] Support Agent Answering ---")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful technical support agent. Keep your answer brief and polite."),
        MessagesPlaceholder(variable_name="messages")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"messages": state["messages"]})
    
    # Append the new AI response to the existing messages list
    return {"messages": state["messages"] + [AIMessage(content=response.content)]}

def sales_agent_node(state: AgentState):
    """Handles sales inquiries."""
    print("--- [Node] Sales Agent Answering ---")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an enthusiastic sales agent. You want to sell our Premium Widget. Keep it brief."),
        MessagesPlaceholder(variable_name="messages")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"messages": state["messages"]})
    
    return {"messages": state["messages"] + [AIMessage(content=response.content)]}

def human_escalation_node(state: AgentState):
    """Hands off to a human."""
    print("--- [Node] Escalating to Human ---")
    response_msg = "I understand you're frustrated. I'm escalating your case to a human manager. Please hold on..."
    return {"messages": state["messages"] + [AIMessage(content=response_msg)]}

# 3. Define the Router (Conditional Edge)
def route_by_category(state: AgentState):
    """Routes to the appropriate agent based on the category."""
    category = state.get("category", "support")
    
    if category == "sales":
        print("    [Router] -> Routing to Sales")
        return "sales_agent"
    elif category == "escalate":
        print("    [Router] -> Routing to Human Escalation")
        return "human_escalation"
    else:
        print("    [Router] -> Routing to Tech Support")
        return "support_agent"

# 4. Build the Graph
builder = StateGraph(AgentState)

# Add our workflow nodes
builder.add_node("categorizer", categorizer_node)
builder.add_node("support_agent", support_agent_node)
builder.add_node("sales_agent", sales_agent_node)
builder.add_node("human_escalation", human_escalation_node)

# Define the flow
# 1. Start by categorizing the user's intent
builder.add_edge(START, "categorizer")

# 2. Use our routing function to decide where to go next
builder.add_conditional_edges("categorizer", route_by_category)

# 3. All paths eventually finish the transaction
builder.add_edge("support_agent", END)
builder.add_edge("sales_agent", END)
builder.add_edge("human_escalation", END)

# Compile into a runnable application
app = builder.compile()


if __name__ == "__main__":
    # We will test the graph with three distinct scenarios
    test_inputs = [
        "My app keeps crashing when I open the settings menu. How do I fix it?",
        "How much does the enterprise plan cost for 50 users? Do you offer discounts?",
        "This is unacceptable! Your service is terrible and I want to speak to a human manager immediately!"
    ]
    
    for idx, user_input in enumerate(test_inputs):
        print(f"\n\n{'='*60}\nSCENARIO {idx + 1}: {user_input}\n{'='*60}")
        
        # The initial state is just the user's first message
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "category": ""
        }
        
        # Invoke the graph
        final_state = app.invoke(initial_state)
        
        # The graph runs through its nodes and returns the final updated state
        print(f"\n[FINAL BOT RESPONSE]:\n{final_state['messages'][-1].content}")
