import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

load_dotenv(override=True)
llm = ChatOllama(model="llama3.1", temperature=0)

# ==========================================
# Phase 8: Retrieval-Augmented Generation (RAG)
# ==========================================

# 1. Define the State
# Notice we added a "context" field to hold our retrieved documents!
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    context: str

# 2. Define the Nodes

def retrieve_node(state: AgentState):
    print("\n--- [Node: RETRIEVER] Fetching context from Vector Database ---")
    
    # In a real app, this would use ChromaDB, FAISS, or Pinecone to search vectors.
    # For this demo, we mock a very simple database lookup.
    mock_vector_db = {
        "company policy": "Company policy dictates a 30-day return window for all electronics. Must have original receipt.",
        "project apollo": "Project Apollo is our secret new software platform scheduled for launch in Q4 2026."
    }
    
    query = state["messages"][-1].content.lower()
    context = "No relevant context found in database."
    
    for key, doc in mock_vector_db.items():
        if key in query:
            context = doc
            break
            
    print(f"   -> Retrieved: '{context}'")
    
    # We update the state with the retrieved context!
    return {"context": context}

def generate_node(state: AgentState):
    print("\n--- [Node: GENERATOR] Crafting Response ---")
    
    # If we have context, we augment our prompt!
    context = state.get("context", "")
    
    if context and context != "No relevant context found in database.":
        system_prompt = f"Answer the user's question based ONLY on the following context:\n\n{context}"
    else:
        system_prompt = "You are a helpful assistant. Answer the user's question to the best of your ability."
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    response = (prompt | llm).invoke({"messages": state["messages"]})
    return {"messages": [response]}

# 3. Define the Router
def route_query(state: AgentState):
    """Dynamically route based on the user's query."""
    last_msg = state["messages"][-1].content.lower()
    
    # If they are asking about internal company data, we MUST route to the retriever.
    if "policy" in last_msg or "project apollo" in last_msg:
        print("\n   -> Router: Query requires internal context. Routing to Retriever.")
        return "retrieve"
    
    # Otherwise, just generate a normal response.
    print("\n   -> Router: General knowledge question. Routing directly to Generator.")
    return "generate"


# 4. Build the Graph
builder = StateGraph(AgentState)

builder.add_node("retrieve", retrieve_node)
builder.add_node("generate", generate_node)

builder.add_conditional_edges(START, route_query)

# After retrieving context, we MUST go to the generator to craft the final response
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)

app = builder.compile()

if __name__ == "__main__":
    print("====================================")
    print("SCENARIO 1: General Knowledge Query")
    print("====================================")
    
    user_input_1 = "Hi, what is the capital of France?"
    print(f"USER: {user_input_1}")
    
    # The router will send this directly to the generator
    final_state_1 = app.invoke({"messages": [HumanMessage(content=user_input_1)]})
    print(f"\n[FINAL BOT RESPONSE]: {final_state_1['messages'][-1].content}")
    
    
    print("\n\n====================================")
    print("SCENARIO 2: Internal RAG Query")
    print("====================================")
    
    user_input_2 = "Can you tell me the details of Project Apollo?"
    print(f"USER: {user_input_2}")
    
    # The router will send this to the retriever first, which will augment the generator!
    final_state_2 = app.invoke({"messages": [HumanMessage(content=user_input_2)]})
    print(f"\n[FINAL BOT RESPONSE]: {final_state_2['messages'][-1].content}")
