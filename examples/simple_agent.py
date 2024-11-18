"""
A simple example demonstrating how to use the XpertAgent.
This script creates an agent instance and runs a basic calculation task.
"""

from dotenv import load_dotenv
from xpertagent.core.agent import XpertAgent

# Load environment variables from .env file
load_dotenv()

def main():
    """
    Main function to demonstrate XpertAgent capabilities.
    Creates an agent instance and runs a sample query for calculation and explanation.
    """
    # Create an agent instance
    agent = XpertAgent(name="XAgent")
    
    # Sample query: multiply two numbers and explain the result
    query = "Calculate 123*456 and explain the result in simple terms."
    
    # Print separator line
    print("-" * 50)
    print(">>> User Input:", query)
    print("-" * 50)
    
    # Run the agent and get response
    response = agent.run(query)
    
    # Print the agent's response
    print("-" * 50)
    print(">>> Agent Response:", response)
    print("-" * 50)

if __name__ == "__main__":
    # Entry point of the script
    main()