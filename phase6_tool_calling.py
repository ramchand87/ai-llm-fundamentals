import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# LangGraph gives us pre-built nodes and routers for tool calling!
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv(override=True)

# ==========================================
# Phase 6: Tool Calling (Function Calling)
# ==========================================

# 1. Define the Tool
# The @tool decorator turns a standard Python function into a LangChain Tool.
# The docstring is CRITICAL: it's how the LLM knows when and how to use this tool!
@tool
def get_weather(location: str) -> str:
    """Get the current weather for a specific location."""
    
    # In a real app, you would make an API call to OpenWeatherMap or similar.
    print(f"\n   [🛠️ TOOL EXECUTION] Fetching weather API for: {location}...")
    
    if "new york" in location.lower():
        return "It's 75°F and sunny in New York."
    elif "london" in location.lower():
        return "It's 55°F and rainy in London."
    else:
        return f"It's 70°F and partly cloudy in {location}."

# We bundle all our tools into a list
tools = [get_weather]

# 2. Bind the tools to the LLM
# This gives the LLM the 'instructions' and schema for the tools it has access to.
# We must use llama3.1 (or mistral/qwen) because the base llama3 does NOT support tool calling in Ollama!
llm = ChatOllama(model="llama3.1", temperature=0)
llm_with_tools = llm.bind_tools(tools)

# 3. Define the State
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# 4. Define the Agent Node
def agent_node(state: AgentState):
    print("\n--- [Node: Agent] Thinking ---")
    
    # Notice we invoke llm_with_tools, NOT the standard llm!
    response = llm_with_tools.invoke(state["messages"])
    
    if response.tool_calls:
        print(f"   -> Agent decided to call a tool: {response.tool_calls[0]['name']}")
    else:
        print("   -> Agent decided to respond directly to the user.")
        
    return {"messages": [response]}

# 5. Build the Graph
builder = StateGraph(AgentState)

# Add our agent
builder.add_node("agent", agent_node)

# Add the ToolNode. This is a pre-built node that takes our list of tools, 
# reads the LLM's requested 'tool_calls', and executes the corresponding Python functions!
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")

# Add the Conditional Router
# 'tools_condition' is a pre-built router. It inspects the last message:
# - If it has tool_calls, it routes to the "tools" node.
# - If it does NOT have tool_calls, it routes to END.
builder.add_conditional_edges("agent", tools_condition)

# After the tools run and return their data, we MUST route back to the agent
# so the agent can read the new data and formulate a final conversational answer!
builder.add_edge("tools", "agent")

app = builder.compile()

if __name__ == "__main__":
    print("====================================")
    print("SCENARIO 1: Normal Question (No Tool Needed)")
    print("====================================")
    
    user_input_1 = "Hi, my name is Alice. How are you doing?"
    print(f"USER: {user_input_1}")
    
    final_state_1 = app.invoke({"messages": [HumanMessage(content=user_input_1)]})
    print(f"\n[FINAL BOT RESPONSE]: {final_state_1['messages'][-1].content}")
    
    
    print("\n\n====================================")
    print("SCENARIO 2: Question Requiring an External Tool")
    print("====================================")
    
    user_input_2 = "I'm traveling tomorrow. What is the weather like in London today?"
    print(f"USER: {user_input_2}")
    
    # Watch the graph bounce from Agent -> Tools -> Agent!
    final_state_2 = app.invoke({"messages": [HumanMessage(content=user_input_2)]})
    print(f"\n[FINAL BOT RESPONSE]: {final_state_2['messages'][-1].content}")
