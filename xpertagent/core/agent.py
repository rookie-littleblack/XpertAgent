"""
Core agent implementation for XpertAgent.
This module contains the main agent class that handles the thinking and execution loop.
"""

from typing import List, Dict, Any
from xpertagent.core.tools import tool_registry
from xpertagent.core.memory import Memory
from xpertagent.core.planner import Planner, Task
from xpertagent.utils.client import APIClient
from xpertagent.utils.helpers import safe_json_loads, format_tool_response
from xpertagent.utils.xlogger import logger
from xpertagent.config.settings import settings

class XpertAgent:
    """
    Main agent class that handles the reasoning and execution loop.
    
    Attributes:
        name: Agent's identifier
        memory: Vector database for storing and retrieving memories
        planner: Task planning component
        client: API client for LLM interactions
        current_tasks: List of tasks in the current execution plan
    """
    
    def __init__(self, name: str = "XAgent", description: str = ""):
        """Initialize the agent with necessary components."""
        self.name = name
        self.description = description
        self.memory = Memory()
        self.planner = Planner()
        self.client = APIClient()
        self.current_tasks: List[Task] = []
        logger.info(f"Agent `{name}` initialized")

    def think(self, input_text: str, last_result: Any = None) -> Dict[str, Any]:
        """
        Process input and decide next action.
        
        Args:
            input_text: User input or current context
            last_result: Result from previous action execution
            
        Returns:
            Dict containing thought process, chosen action, and action input
        """
        try:
            # If we have a result, format final response
            if last_result is not None:
                return {
                    "thought": "We have the result, now let's explain it clearly.",
                    "action": "respond",
                    "action_input": self.format_final_response(input_text, last_result)
                }
            
            # Retrieve relevant memories
            relevant_memories = self.memory.search(input_text)
            
            # Get available tools description
            tools_desc = tool_registry.get_tool_descriptions()
            
            # Construct prompt
            prompt = f"""Input: 
{input_text}
            
Relevant Memories:
{chr(10).join(relevant_memories)}

Available Tools:
{tools_desc}

Previous Result: {last_result if last_result is not None else 'None'}

Analyze the situation and decide the next action. Response must be in JSON format:
{{"thought": "your reasoning", 
    "action": "tool_name or 'respond'", 
    "action_input": "input for tool or response",
    "task_complete": true/false}}
"""
            
            # Get LLM response
            logger.debug(f">>> Prompt: `{prompt}`")
            response = self.client.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are an intelligent AI assistant. Analyze the situation and determine the best course of action."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.TEMPERATURE
            )
            logger.debug(f">>> LLM response: `{response.choices[0].message.content}`")
            
            # Parse and validate response
            result = safe_json_loads(response.choices[0].message.content)
            
            # Verify required keys exist
            if not all(k in result for k in ["thought", "action", "action_input"]):
                logger.warning(f"Response missing required keys: {result}")
                return {
                    "thought": "Incomplete response format",
                    "action": "respond",
                    "action_input": "I apologize, but I received an incomplete response format."
                }
                
            return result
            
        except Exception as e:
            logger.error(f"Error in thinking process: {str(e)}")
            return {
                "thought": f"Error occurred: {str(e)}",
                "action": "respond",
                "action_input": "I apologize, but an error occurred while processing your request."
            }
    
    def execute(self, action: str, action_input: str) -> str:
        """
        Execute the decided action.
        
        Args:
            action: Name of the tool to use or 'respond'
            action_input: Input for the tool or response content
            
        Returns:
            str: Result of the action execution
        """
        try:
            if action == "respond":
                return action_input
            
            tool = tool_registry.get_tool(action)
            if tool:
                try:
                    result = tool.func(action_input)
                    response = format_tool_response(True, result)
                    return str(response["result"])
                except Exception as e:
                    logger.error(f"Tool execution error: {str(e)}")
                    response = format_tool_response(False, str(e))
                    return str(response["result"])
            
            logger.warning(f"Tool not found: {action}")
            return f"I apologize, but I couldn't find the tool: {action}"
            
        except Exception as e:
            logger.error(f"Error in execute process: {str(e)}")
            raise
    
    def format_final_response(self, input_text: str, result: Any) -> str:
        """
        Format the final response with explanation.
        
        Args:
            input_text: Original user input
            result: Result to explain
            
        Returns:
            str: Formatted response with explanation
        """
        prompt = f"""{self.description}

        Original question: {input_text}

        Agent result: {result}
        
        Please generate output as above mentioned format.
        """
        
        logger.debug(f">>> Prompt for final response: `{prompt}`")
        response = self.client.create_chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        result = response.choices[0].message.content.strip()
        logger.debug(f">>> Final response: `{result}`")
        
        return result
    
    def run(self, input_text: str, max_steps: int | None = None) -> str:
        """
        Run the agent's main loop.
        
        Args:
            input_text: User input text
            max_steps: Maximum number of steps to execute
            
        Returns:
            str: Agent's final response
        """
        max_steps = max_steps if max_steps is not None else settings.MAX_STEPS
        
        # Log available tools
        logger.info(f"Available tools: {tool_registry.list_tools()}")
        
        # Record input
        self.memory.clear()  # Clear all memories
        self.memory.add(input_text, {"type": "user_input"})
        
        # Create initial plan
        self.current_tasks = self.planner.create_plan(input_text)
        logger.debug(f"Initial plan: `{self.current_tasks}`")
        
        step_count = 0
        final_response = ""
        last_result = None
        
        # Execute each task in the plan
        for task in self.current_tasks:
            if step_count >= max_steps:
                break
                
            logger.info(f"Executing task {step_count}: `{task.description}`")
            
            # Think about task
            thought_result = self.think(task.description, last_result)
            
            # Execute action
            action_result = self.execute(
                thought_result["action"],
                thought_result["action_input"]
            )
            logger.debug(f"===> Action result: `{action_result}`")
            
            # Record action and result
            self.memory.add(
                f"Task: {task.description}\nThought: {thought_result['thought']}\nResult: {action_result}",
                {"type": "task_execution"}
            )
            
            # Update progress
            if thought_result["action"] != "respond":
                last_result = action_result
            else:
                final_response = action_result
                break
                
            step_count += 1
        
        logger.info(f"Completed {step_count} tasks")
        return final_response or "Reached maximum steps without completing all tasks."