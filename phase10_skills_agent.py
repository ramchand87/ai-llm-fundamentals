import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv(override=True)

# ==========================================
# Phase 10: Skills & SOPs (Standard Operating Procedures)
# ==========================================

# 1. Define the Tool to read the skills file
@tool
def read_project_skills() -> str:
    """Read the skills.md file to learn the project's coding standards and formatting rules."""
    print("\n   [🛠️ TOOL] Agent is reading the skills.md file to learn the rules...")
    try:
        with open("skills.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "skills.md file not found."

tools = [read_project_skills]

# 2. Setup LLM
llm = ChatOllama(model="llama3.1", temperature=0)
llm_with_tools = llm.bind_tools(tools)

# 3. Define State
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# 4. Define Agent Node
def agent_node(state: AgentState):
    print("\n--- [Node: Agent] Thinking ---")
    
    # We give the agent a very strict system prompt forcing it to read the skills file!
    system_prompt = (
        "You are an AI assistant in a corporate repository. "
        "BEFORE you answer any user request, you MUST use the `read_project_skills` tool "
        "to check for any specific formatting rules or SOPs you need to follow. "
        "If you find rules that apply to the user's request, follow them perfectly."
    )
    
    # We inject the system prompt as the first message
    messages = [HumanMessage(content=system_prompt)] + state["messages"]
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# 5. Build Graph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

app = builder.compile()

if __name__ == "__main__":
    print("====================================")
    print("SCENARIO: Agent reads skills.md to learn how to write an email")
    print("====================================")
    
    # We ask the agent to write an email. Without skills.md, it would write a generic email.
    # With skills.md, it will use our exact sign-off and apology format!
    user_input = "Please write an email to our customer John Smith. His product arrived broken and he wants a refund."
    print(f"USER: {user_input}\n")
    
    final_state = app.invoke({"messages": [HumanMessage(content=user_input)]})
    
    print("\n\n[FINAL BOT RESPONSE]:\n")
    print(final_state['messages'][-1].content)
