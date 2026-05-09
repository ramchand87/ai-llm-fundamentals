import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

load_dotenv(override=True)
llm = ChatOllama(model="llama3", temperature=0)

# ==========================================
# Phase 5: Human-in-the-Loop (HITL)
# ==========================================

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    refund_authorized: bool

# 1. Chatbot Node
def chatbot_node(state: AgentState):
    print("\n--- [Node: Chatbot] Processing ---")
    
    last_message = state["messages"][-1].content.lower()
    
    # Simple hardcoded routing for the sake of the HITL demo
    if "refund" in last_message:
        msg = AIMessage(content="I see you want a refund. I am routing your request to a human manager for approval.")
        # By default, authorization is False
        return {"messages": [msg], "refund_authorized": False}
    else:
        # Normal chat
        response = llm.invoke(state["messages"])
        return {"messages": [response]}

# 2. Refund Action Node (SENSITIVE ACTION)
def refund_action_node(state: AgentState):
    print("\n--- [Node: Refund Action] Executing SENSITIVE code ---")
    
    # This node checks the state to see if the human updated it!
    if state.get("refund_authorized"):
        msg = "SYSTEM SUCCESS: Refund has been securely processed back to your card."
    else:
        msg = "SYSTEM FAILURE: Refund was DENIED by the human manager."
        
    return {"messages": [AIMessage(content=msg)]}

# 3. Router
def route_after_chat(state: AgentState):
    # Check what the bot just said
    last_message = state["messages"][-1].content
    if "human manager for approval" in last_message:
        return "refund_action"
    return END

# Build Graph
builder = StateGraph(AgentState)
builder.add_node("chatbot", chatbot_node)
builder.add_node("refund_action", refund_action_node)

builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", route_after_chat)
builder.add_edge("refund_action", END)

# --- 4. THE MAGIC: INTERRUPT BEFORE ---
memory = MemorySaver()

# We tell LangGraph to PAUSE execution right before the 'refund_action' node runs!
app = builder.compile(
    checkpointer=memory,
    interrupt_before=["refund_action"]
)

if __name__ == "__main__":
    # We must use a thread_id so the graph can save and reload its paused state
    config = {"configurable": {"thread_id": "hitl_demo_session"}}
    
    print("====================================")
    print("SCENARIO 1: User asks a normal question")
    print("====================================")
    user_input = "Hi, what are your store hours?"
    print(f"USER: {user_input}")
    
    # Run the graph. It won't hit the refund node, so it completes normally.
    final_state = app.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
    print(f"\n[BOT]: {final_state['messages'][-1].content}")
    
    
    print("\n\n====================================")
    print("SCENARIO 2: User asks for a refund!")
    print("====================================")
    user_input_2 = "My product is broken. I want a refund."
    print(f"USER: {user_input_2}")
    
    # Run the graph. It will route to 'refund_action', which will trigger an INTERRUPT!
    # app.invoke will RETURN EARLY, allowing our Python script to continue!
    paused_state = app.invoke({"messages": [HumanMessage(content=user_input_2)]}, config=config)
    
    print(f"\n[BOT]: {paused_state['messages'][-1].content}")
    print("\n" + "!"*40)
    print(">>> GRAPH EXECUTION PAUSED <<<")
    print("!"*40)
    
    # Check the state of the graph
    current_state = app.get_state(config)
    next_node = current_state.next
    print(f"The graph is currently frozen, waiting to execute: {next_node}")
    
    # --- HUMAN INTERVENTION ---
    # We prompt the user in the terminal
    decision = input("\n[MANAGER APPROVAL] Do you authorize this refund? (y/n): ")
    
    if decision.lower() == 'y':
        print("\nManager authorized. Updating graph state...")
        # We manually update the graph's memory BEFORE it continues!
        app.update_state(config, {"refund_authorized": True})
    else:
        print("\nManager denied. Updating graph state...")
        app.update_state(config, {"refund_authorized": False})
        
    print("\n>>> RESUMING GRAPH EXECUTION <<<")
    
    # By passing None as the input, we tell the graph to just pick up exactly where it left off
    final_state_after_resume = app.invoke(None, config=config)
    
    print(f"\n[FINAL SYSTEM RESPONSE]:\n{final_state_after_resume['messages'][-1].content}")
