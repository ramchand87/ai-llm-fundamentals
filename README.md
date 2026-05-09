# LangGraph & LangChain Fundamentals Learning Path

This repository contains practical examples and learning materials for mastering the LangChain ecosystem, specifically focusing on building Agentic workflows using **LangGraph**.

## Core Concepts

### LangChain SDK
LangChain is a framework for developing applications powered by LLMs.
- **ChatModels**: Wrappers around LLM APIs (e.g., `ChatOllama`, `ChatOpenAI`). They take a list of messages and return an AI message.
- **PromptTemplates**: Reusable templates for generating prompts dynamically. They inject variables into instructions.
- **LCEL (LangChain Expression Language)**: A declarative way to compose chains using the pipe `|` operator. Example: `chain = prompt | llm | output_parser`.

### LangGraph SDK
LangGraph is an extension of LangChain designed for building stateful, multi-actor applications with LLMs. It models agent workflows as graphs (state machines).
- **State (`TypedDict` or Pydantic)**: The central data structure (like a Java POJO/DTO) that gets passed from node to node. Every node reads from it and returns updates to it.
- **Nodes**: Python functions that perform work (e.g., calling an LLM or an API). They receive the current `State` and return a dictionary of updates.
- **Edges**: Connect nodes together to define the flow.
- **Conditional Edges (Routers)**: Functions containing logic (`if/else`) that inspect the state and decide which node should execute next. This is what gives an agent its "decision-making" capability.

## Project Structure

- `phase1_basics.py`: Demonstrates fundamental LangChain concepts like basic LLM invocation and LCEL chains using local Ollama models.
- `phase2_langgraph_intro.py`: Introduces the `StateGraph`. Shows how to define state, create simple nodes, and route between them in a loop.
- `practical_customer_bot.py`: A practical implementation of a Customer Service Chatbot. Demonstrates advanced routing by categorizing user intent and routing the conversation to specialized agent nodes (Sales, Support, Escalation).

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate it: `.\venv\Scripts\Activate.ps1`
3. Install dependencies: `pip install -r requirements.txt`
4. Ensure Ollama is running locally with the `llama3` model: `ollama run llama3`
