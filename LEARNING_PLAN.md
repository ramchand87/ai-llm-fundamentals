# Mastering LangGraph & LangChain: Learning Plan

This document tracks our progress in mastering the LangChain ecosystem, focusing on Agentic workflows.

## ✅ Completed Milestones

- [x] **Workspace Setup**
  - [x] Initialize Python virtual environment
  - [x] Configure `.env` file for secrets management
  - [x] Set up Git version control and remote repository

- [x] **Phase 1: LangChain Foundations**
  - [x] Connect local LLMs (`ChatOllama` with `llama3`)
  - [x] Utilize `ChatPromptTemplate` for dynamic instructions
  - [x] Master LangChain Expression Language (LCEL) syntax (`prompt | llm`)

- [x] **Phase 2: Introduction to LangGraph**
  - [x] Understand `StateGraph` and strongly-typed Agent State (`TypedDict`)
  - [x] Build simple sequential workflows with Nodes and Edges
  - [x] Use `START` and `END` virtual nodes
  - [x] Compile graphs into executable runnables

- [x] **Phase 2.5: Advanced Graph Routing**
  - [x] Build a multi-node Customer Service Chatbot
  - [x] Implement dynamic routing using `add_conditional_edges`
  - [x] Create an intent categorizer node to direct traffic

- [x] **Phase 3: Observability & Tracing**
  - [x] Create a Langfuse Cloud project
  - [x] Integrate `CallbackHandler` into LangGraph configurations
  - [x] Monitor token usage, latency, and LLM generation outputs

- [x] **Phase 4: Agent Memory & Checkpointing**
  - [x] Implement `MemorySaver` checkpointers
  - [x] Use the `add_messages` reducer to safely append conversation history
  - [x] Persist conversational memory across invocations using `thread_id`

---

## 🚀 Unexplored / Upcoming Milestones

- [x] **Phase 5: Human-in-the-Loop (HITL)**
  - [x] Use `interrupt_before` to pause graph execution
  - [x] Allow a human manager to approve or reject actions (e.g., processing refunds)
  - [x] Manually update the graph's internal state before resuming execution

- [x] **Phase 6: Tool Calling (Function Calling)**
  - [x] Bind external Python tools to the LLM (e.g., web searching, API calling)
  - [x] Create a `ToolNode` in LangGraph to execute the functions chosen by the LLM
  - [x] Handle ToolMessages and feed results back to the agent

- [x] **Phase 7: Multi-Agent Systems**
  - [x] Understand the "Supervisor" architectural pattern
  - [x] Create specialized sub-agents (e.g., a "Researcher" and a "Coder")
  - [x] Build a Supervisor node that delegates tasks to sub-agents and synthesizes the final answer

- [x] **Phase 8: RAG (Retrieval-Augmented Generation)**
  - [x] Connect the agent to a Vector Database
  - [x] Build a workflow that routes unknown queries to a retrieval node before answering

- [x] **Phase 9: Streaming & Production**
  - [x] Implement token-by-token streaming for a responsive UI
  - [x] Stream graph events (e.g., knowing when the graph switches from Node A to Node B)
