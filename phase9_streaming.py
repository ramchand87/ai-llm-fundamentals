import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, BaseMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

load_dotenv(override=True)
llm = ChatOllama(model="llama3.1", temperature=0)

# ==========================================
# Phase 9: Streaming & Production
# ==========================================

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def agent_node(state: AgentState):
    # We do NOT use print statements here because we want to see the streaming magic in the main execution block!
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)

app = builder.compile()

if __name__ == "__main__":
    print("====================================")
    print("SCENARIO 1: Streaming Node Updates")
    print("====================================")
    
    # stream_mode="updates" yields the state updates output by each node as they finish.
    # This is perfect for UI progress bars (e.g., "Agent is thinking...", "Tool is running...")
    user_input_1 = "Explain Quantum Computing in one sentence."
    print(f"USER: {user_input_1}\n")
    
    for event in app.stream({"messages": [HumanMessage(content=user_input_1)]}, stream_mode="updates"):
        for node_name, state_update in event.items():
            print(f"[Graph Event] Node '{node_name}' finished executing!")
            print(f"[Graph Event] Output: {state_update['messages'][-1].content}\n")


    print("\n====================================")
    print("SCENARIO 2: Streaming LLM Tokens")
    print("====================================")
    
    # stream_mode="messages" yields the actual tokens as the LLM generates them!
    # This is how ChatGPT gives you that typing effect.
    user_input_2 = "Write a short poem about Python programming."
    print(f"USER: {user_input_2}\n")
    print("BOT: ", end="", flush=True)
    
    # We get a tuple of (message_chunk, metadata) back
    for msg_chunk, metadata in app.stream({"messages": [HumanMessage(content=user_input_2)]}, stream_mode="messages"):
        # We only want to print tokens, we don't need to print empty chunks or HumanMessages
        if msg_chunk.content:
            print(msg_chunk.content, end="", flush=True)
            
    print("\n\n[INFO] Streaming complete!")
