from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# ==========================================
# Phase 2: Introduction to LangGraph
# ==========================================

# 1. Define the State
# In LangGraph, the 'State' is like a shared POJO/Record in Java 
# that gets passed to every node in the graph. 
class GraphState(TypedDict):
    message: str
    counter: int

# 2. Define the Nodes
# Nodes are just Python functions that take the current state, 
# perform some logic, and return a dictionary with the state updates.
def node_a(state: GraphState):
    print("--- Entering Node A ---")
    # We read from the state
    msg = state.get("message", "")
    count = state.get("counter", 0)
    
    # We return ONLY the fields we want to update/overwrite
    return {
        "message": msg + " -> Node A",
        "counter": count + 1
    }

def node_b(state: GraphState):
    print("--- Entering Node B ---")
    msg = state.get("message", "")
    count = state.get("counter", 0)
    
    return {
        "message": msg + " -> Node B",
        "counter": count + 1
    }

# 3. Define the Router (Conditional Edge)
# This function decides which node to go to next based on the state.
def router(state: GraphState):
    # If we've hit the nodes 3 times, let's end the graph
    if state.get("counter", 0) >= 3:
        print("    [Router]: Counter is >= 3, routing to END")
        return END
    
    # Otherwise, go to Node B
    print("    [Router]: Routing to node_b")
    return "node_b"

# 4. Build the Graph
builder = StateGraph(GraphState)

# Add our nodes to the graph
builder.add_node("node_a", node_a)
builder.add_node("node_b", node_b)

# Define the edges (the flow)
# START is a special node that indicates where the graph begins.
builder.add_edge(START, "node_a")

# After node_a, we use our router to decide what's next.
builder.add_conditional_edges("node_a", router)

# After node_b, we loop back to node_a (Cyclic Graph!)
builder.add_edge("node_b", "node_a")

# Compile the graph into an executable agent
graph = builder.compile()

if __name__ == "__main__":
    print("Starting LangGraph Execution...\n")
    
    # Initialize the state and invoke the graph
    initial_state = {"message": "Start", "counter": 0}
    
    # The invoke method runs the graph and returns the final state
    final_state = graph.invoke(initial_state)
    
    print("\n--- Final State ---")
    print(final_state)
