import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

load_dotenv(override=True)
llm = ChatOllama(model="llama3", temperature=0)

# ==========================================
# Phase 4: Agent Memory & Checkpointing
# ==========================================

# 1. Define the State
# We use `Annotated[list, add_messages]` to tell LangGraph NOT to overwrite the messages list.
# Instead, any new messages returned by nodes will be APPENDED to the existing list.
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# 2. Define the Node
def chatbot_node(state: AgentState):
    print("\n--- [Node] Chatbot Thinking ---")
    response = llm.invoke(state["messages"])
    
    # We only return the NEW message. `add_messages` handles appending it to the state.
    return {"messages": [response]}

# 3. Build the Graph
builder = StateGraph(AgentState)
builder.add_node("chatbot", chatbot_node)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

# --- 4. ADD MEMORY ---
# We instantiate an in-memory checkpointer. 
# For production, you would use PostgresSaver, SqliteSaver, or MongoDBSaver.
memory = MemorySaver()

# We pass the checkpointer to compile()
app = builder.compile(checkpointer=memory)

if __name__ == "__main__":
    # We define a configuration with a unique thread_id (like a Session ID)
    # Any invocations with this thread_id will load and share the same memory!
    config = {"configurable": {"thread_id": "user_session_123"}}
    
    print("====================================")
    print("CONVERSATION TURN 1")
    print("====================================")
    
    user_input_1 = "Hi, my name is John and I love Python."
    print(f"USER: {user_input_1}")
    
    # Pass the config to invoke
    app.invoke({"messages": [HumanMessage(content=user_input_1)]}, config=config)
    
    print("\n====================================")
    print("CONVERSATION TURN 2 (Testing Memory)")
    print("====================================")
    
    # In turn 2, we ONLY pass the new message!
    # The checkpointer automatically loads the history from TURN 1.
    user_input_2 = "What is my name and what programming language do I like?"
    print(f"USER: {user_input_2}")
    
    # Using the SAME config (same thread_id)
    final_state = app.invoke({"messages": [HumanMessage(content=user_input_2)]}, config=config)
    
    # The final state will contain the full conversation history
    print(f"\n[FINAL BOT RESPONSE]:\n{final_state['messages'][-1].content}")
