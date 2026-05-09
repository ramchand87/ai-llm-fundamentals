# LangGraph & LangChain Fundamentals Learning Path

This repository contains practical examples and learning materials for mastering the LangChain ecosystem, specifically focusing on building Agentic workflows using **LangGraph**, and observability using **Langfuse**.

## Core Concepts & API Reference

### LangChain Core SDK
LangChain is a framework for developing applications powered by LLMs.

*   **`ChatModels` (e.g. `ChatOllama`)**: Wrappers around LLM APIs that take a list of messages and return an AI message. We use the local Ollama integration for this project.
    *   [ChatModels API Spec](https://python.langchain.com/v0.2/docs/concepts/#chat-models)
    *   [LangChain Ollama Spec](https://python.langchain.com/v0.2/docs/integrations/chat/ollama/)
*   **`ChatPromptTemplate`**: Reusable templates for generating prompts dynamically. They inject variables into instructions seamlessly.
    *   [Prompt Templates API Spec](https://python.langchain.com/v0.2/docs/concepts/#prompt-templates)
*   **`MessagesPlaceholder`**: A special prompt component used to inject an entire list of historical conversation messages into a prompt dynamically.
    *   [MessagesPlaceholder API Spec](https://python.langchain.com/v0.2/docs/concepts/#messagesplaceholder)
*   **`HumanMessage` / `AIMessage`**: Standardized data classes representing different roles in a conversation.
    *   [Messages API Spec](https://python.langchain.com/v0.2/docs/concepts/#messages)
*   **`LCEL` (LangChain Expression Language)**: A declarative way to compose chains using the pipe `|` operator (e.g., `chain = prompt | llm`).
    *   [LCEL Documentation](https://python.langchain.com/v0.2/docs/concepts/#langchain-expression-language)

### LangGraph SDK
LangGraph is an extension of LangChain designed for building stateful, multi-actor applications with LLMs. It models agent workflows as graphs (state machines).

*   **`StateGraph`**: The core class that represents the workflow. It takes a typed State (like a Java DTO) as its schema.
    *   [StateGraph API Spec](https://langchain-ai.github.io/langgraph/reference/graphs/#stategraph)
*   **Nodes (`add_node`)**: Python functions that perform work (e.g., calling an LLM). They receive the current `State` and return a dictionary of updates.
*   **Edges (`add_edge`)**: Connects nodes together to define a strict linear flow from one node to another.
*   **Conditional Edges (`add_conditional_edges`)**: Routers! Functions containing logic (`if/else`) that inspect the state and decide which node should execute next.
*   **`START` / `END`**: Special virtual nodes provided by the SDK to define the entry and exit points of the graph.
*   **`compile()`**: The method called on the `StateGraph` builder to lock the graph definition and return an executable `CompiledGraph` (Runnable).
    *   [Graph API Concepts](https://langchain-ai.github.io/langgraph/concepts/low_level/)
*   **`MemorySaver`**: An in-memory checkpointer that saves graph state. Crucial for giving bots memory and for implementing Human-in-the-Loop workflows.
    *   [Persistence API Spec](https://langchain-ai.github.io/langgraph/concepts/persistence/)
*   **`add_messages`**: A LangGraph reducer function used in the `State` class. Instead of overwriting the messages list during a node update, it ensures new messages are intelligently appended to the conversation history.
*   **Human-in-the-Loop (`interrupt_before`)**: A compile-time argument that instructs the graph to pause execution before specific nodes. Used in tandem with `app.update_state()` to allow human managers to modify state before resuming execution.
    *   [HITL API Concepts](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)
*   **Tool Calling (`@tool` & `ToolNode`)**: Allows the LLM to trigger external Python functions. You bind tools to an LLM (`llm.bind_tools`), and LangGraph's pre-built `ToolNode` automatically executes the function requested by the LLM's `tool_calls` output.
    *   [Tool Calling Docs](https://python.langchain.com/v0.2/docs/concepts/#functiontool-calling)
*   **Structured Output (`with_structured_output`)**: A powerful method to force an LLM to respond with a strict JSON format matching a Pydantic schema. Essential for the Supervisor multi-agent pattern!
    *   [Structured Output Docs](https://python.langchain.com/v0.2/docs/how_to/structured_output/)
*   **RAG (Retrieval-Augmented Generation)**: The architecture of fetching internal company data from a Vector Database and injecting it into the LLM's system prompt before generation.

### Langfuse SDK
Langfuse is an open-source observability platform for LLMs.

*   **`CallbackHandler`**: The Langfuse integration object that hooks into LangChain's callback system. By passing it to `app.invoke(config={"callbacks": [langfuse_handler]})`, it automatically traces all LLM calls, prompts, and graph nodes.
    *   [Langfuse Python SDK Docs](https://langfuse.com/docs/integrations/langchain/tracing)

---

## Project Structure

- `phase1_basics.py`: Demonstrates fundamental LangChain concepts like basic LLM invocation and LCEL chains using local Ollama models.
- `phase2_langgraph_intro.py`: Introduces the `StateGraph`. Shows how to define state, create simple nodes, and route between them in a loop.
- `practical_customer_bot.py`: A practical implementation of a Customer Service Chatbot. Demonstrates advanced routing by categorizing user intent and routing the conversation to specialized agent nodes.
- `phase3_langfuse_tracing.py`: Integrates the Langfuse `CallbackHandler` into the Customer Service Bot to trace and monitor token usage, latency, and routing decisions.
- `phase4_memory_agent.py`: Demonstrates how to give agents stateful memory using LangGraph checkpointers (`MemorySaver`). Shows how to persist conversational history across multiple invocations using `thread_id`.
- `phase5_human_in_the_loop.py`: Demonstrates how to pause an AI agent before a sensitive action (like processing a refund), allowing a human to review and authorize the action by manually modifying the graph state.
- `phase6_tool_calling.py`: Demonstrates how to give the LLM access to external APIs using the `@tool` decorator, `bind_tools`, and LangGraph's pre-built `ToolNode` and conditional routers.
- `phase7_multi_agent.py`: Introduces the Supervisor architecture! A central LLM manager routes tasks to specialized worker nodes (`Researcher` and `Coder`) using strict structured output.
- `phase8_rag_agent.py`: Demonstrates a Retrieval-Augmented Generation workflow where a router decides if external context is needed, queries a mock vector database, and augments the LLM's prompt.

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate it: `.\venv\Scripts\Activate.ps1`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and add your Langfuse API Keys.
5. Ensure Ollama is running locally with the `llama3` model: `ollama run llama3`
