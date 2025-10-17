"""
Example 1: Basic Browser-Use Search
====================================

This example demonstrates the fundamentals of browser-use:
- Creating an agent
- Defining a task in natural language
- Running the agent
- Getting results

This is your starting point for understanding how browser-use works.
"""

import asyncio
from dotenv import load_dotenv
from browser_use import Agent, ChatOpenAI

load_dotenv()


async def main():
    """Simple example: Search for Tesla news and summarize."""
    
    # Initialize the LLM (uses OPENAI_API_KEY from .env)
    llm = ChatOpenAI(
        model="gpt-4o-mini",  # Fast and cost-effective
        temperature=0.0  # Deterministic results
    )
    
    # Define your task in natural language
    task = """
    Go to Google and search for 'Tesla stock news today'.
    Look at the top 3 results and summarize what's being discussed.
    """
    
    # Create the agent
    agent = Agent(
        task=task,
        llm=llm
    )
    
    # Run the agent
    print("🚀 Starting agent...")
    result = await agent.run(max_steps=10)
    
    print("\n✅ Agent completed!")
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())

