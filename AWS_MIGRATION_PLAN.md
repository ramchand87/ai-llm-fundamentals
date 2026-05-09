# AWS Bedrock Migration Plan

If you decide to move this local architecture into an enterprise AWS environment, you have two primary migration paths. The path you choose depends on how much control you want over the workflow versus how much you want AWS to manage for you.

## Path A: Bring Your Own Graph (LangGraph + Bedrock LLMs)
In this path, you keep all the LangGraph code we wrote, but you swap out the local Ollama models for powerful cloud models hosted on AWS Bedrock (like Anthropic Claude 3.5 Sonnet).

### What changes?
1. **Dependency Swap**: You install `langchain-aws` instead of `langchain-ollama`.
2. **LLM Initialization**: You replace `ChatOllama(...)` with `ChatBedrock(model_id="anthropic.claude-3-sonnet-20240229-v1:0")`.
3. **Authentication**: Your environment needs AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).

### What stays the same?
**Everything else.** This is the magic of the LangChain abstraction!
*   Your `StateGraph`, Nodes, and Edges remain completely unchanged.
*   Your `tools` (Python functions) remain unchanged.
*   Your `MemorySaver` and `interrupt_before` logic remain unchanged.

**Code Example (Path A: Checking Refund Status)**
```python
import os
from langchain_aws import ChatBedrock
from langchain_core.tools import tool
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

# 1. ONLY THIS LINE CHANGES! We swap ChatOllama for ChatBedrock.
os.environ["AWS_ACCESS_KEY_ID"] = "..."
os.environ["AWS_SECRET_ACCESS_KEY"] = "..."
llm = ChatBedrock(model_id="anthropic.claude-3-sonnet-20240229-v1:0")

# 2. Everything else remains identical to our local LangGraph code!
@tool
def check_refund(order_id: str) -> str:
    """Check the status of a refund."""
    return "Refund processed."

llm_with_tools = llm.bind_tools([check_refund])

# The graph logic is exactly the same as phase 6
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode([check_refund]))
builder.add_conditional_edges("agent", tools_condition)
# ... compile and invoke ...
```

*Pros: Ultimate control over the exact routing and state. No vendor lock-in (you can swap Bedrock for OpenAI tomorrow).*

---

## Path B: Fully Managed (Agents for Amazon Bedrock)
Amazon offers a fully managed service called **Agents for Amazon Bedrock**. If you use this, you are throwing away LangGraph entirely and letting AWS handle the orchestration on their servers.

### What changes?
1. **Goodbye LangGraph**: You delete your `StateGraph` python code. AWS handles the memory, state, and routing internally.
2. **Tools become Lambda Functions**: Instead of `@tool` Python functions in your script, you must deploy your tools as AWS Lambda functions and define an OpenAPI schema (Action Groups) so Bedrock knows how to call them.
3. **RAG becomes Knowledge Bases**: Instead of building your own retrieval nodes, you point AWS Bedrock to an S3 bucket and use their managed "Knowledge Bases for Amazon Bedrock".

### The Migration Effort:
This is a **heavy** migration. You are moving from a code-first architecture (LangGraph) to an infrastructure-first architecture (AWS Console, Terraform, or AWS CloudFormation).

*Pros: Serverless, highly scalable, zero orchestration code to maintain.*
*Cons: High vendor lock-in. You lose the ability to easily debug the exact step-by-step state of the agent, and complex custom routing (like our Multi-Agent Supervisor) is much harder to implement.*

**Code Example (Path B: Checking Refund Status)**

Notice there is NO LangGraph code here. You do not define nodes or routing. You only write the backend Lambda function that the AWS Agent automatically invokes when it decides a tool is needed.

```python
# 1. AWS Lambda Function (The Tool Execution)
def lambda_handler(event, context):
    actionGroup = event['actionGroup']
    function = event['function']
    
    if function == 'check_refund':
        order_id = event['parameters'][0]['value']
        # Execute business logic
        result = "Refund processed."
        
        # Bedrock requires a very specific return payload
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": actionGroup,
                "function": function,
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {"body": result}
                    }
                }
            }
        }
```

```yaml
# 2. OpenAPI Schema (Given to AWS Console so the Agent knows how to call your Lambda)
openapi: 3.0.0
info:
  title: Refund API
  version: 1.0.0
paths:
  /check_refund:
    get:
      description: Check the status of a refund
      parameters:
        - name: order_id
          in: query
          required: true
          schema:
            type: string
```
