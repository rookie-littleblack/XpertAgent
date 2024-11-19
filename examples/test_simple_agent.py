"""
A simple example demonstrating how to use the XpertAgent.
This script creates an agent instance and runs a basic calculation task.
"""

from xpertagent.core.agent import XpertAgent
from xpertagent.utils.helpers import logger

def main():
    """
    Main function to demonstrate XpertAgent capabilities.
    Creates an agent instance and runs a sample query for calculation and explanation.
    """
    logger.info(">>> [test_simple_agent.py] Starting simple agent...")
    
    # Create an agent instance
    agent = XpertAgent(name="XAgent")
    
    # Sample query: multiply two numbers and explain the result
    query = "Calculate 123*456 and explain the result in simple terms."
    logger.info(f">>> [test_simple_agent.py] User Input: `{query}`...")
    
    # Run the agent and get response
    response = agent.run(query)
    logger.info(f">>> [test_simple_agent.py] Agent Response: `{response}`")

    # Log completion
    logger.info(">>> [test_simple_agent.py] Simple agent completed.")

if __name__ == "__main__":
    main()