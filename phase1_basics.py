import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables (if any)
load_dotenv()

# ==========================================
# Phase 1: LangChain Foundations with Ollama
# ==========================================

# Initialize the Ollama Chat Model
# NOTE: Ensure you have Ollama running locally.
# If you haven't already, run `ollama run llama3` in a separate terminal to pull the model.
# You can change "llama3" to "mistral" or any other model you have pulled.
llm = ChatOllama(model="llama3") 

def run_basic_call():
    print("--- 1. Basic LLM Call ---")
    # Sending a direct message to the model
    response = llm.invoke("What is LangChain? Answer in one short sentence.")
    print(response.content)

def run_chain():
    print("\n--- 2. LCEL Chain Call ---")
    # PromptTemplates allow us to parameterize our inputs
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Python developer explaining concepts to a Java developer. Use analogies to Java when possible."),
        ("user", "Explain {concept}.")
    ])

    # LCEL (LangChain Expression Language) uses the pipe '|' operator to chain components.
    # It passes the output of one component as the input to the next.
    chain = prompt | llm | StrOutputParser()

    # Invoke the chain with variables
    result = chain.invoke({"concept": "Python Virtual Environments (venv) vs Maven"})
    print(result)

if __name__ == "__main__":
    print("Starting Phase 1 Examples...")
    # run_basic_call()
    run_chain()
