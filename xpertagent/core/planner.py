"""
Task planning module for XpertAgent.
This module handles the creation and refinement of execution plans.
"""

from typing import List, Dict
from pydantic import BaseModel
from xpertagent.utils.client import APIClient
from xpertagent.utils.xlogger import logger
from xpertagent.config.settings import settings

class Task(BaseModel):
    """
    Task model representing a single step in the execution plan.
    
    Attributes:
        description: Detailed description of the task
        status: Current status of the task (pending, in_progress, completed, failed)
        subtasks: List of smaller tasks that make up this task
    """
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    subtasks: List[Dict] = []

class Planner:
    """
    Planner class responsible for creating and refining execution plans.
    Uses LLM to break down complex goals into manageable tasks.
    """
    
    def __init__(self):
        """Initialize the planner with an API client."""
        self.client = APIClient()
    
    def create_plan(self, goal: str, context: str = "") -> List[Task]:
        """
        Create an execution plan for a given goal.
        
        Args:
            goal: The main objective to achieve
            context: Additional context information (optional)
            
        Returns:
            List[Task]: List of tasks forming the execution plan
            
        Note:
            Uses LLM to break down the goal into concrete, executable steps
        """
        prompt = f"""You are an AI task planner that creates efficient, programmatic execution plans.

Key principles:
1. Keep plans minimal and direct
2. Focus on automated operations
3. Avoid unnecessary steps
4. Consider available system tools
5. Combine related operations

Example tasks and their plans:

1. Image OCR:
Input: "Extract text from image: https://example.com/img.jpg"
Plan: "Use OCR tool to extract and return text from the image URL"

2. Math calculation:
Input: "Calculate 15% of 850"
Plan: "Perform mathematical calculation and format the result"

3. Data processing:
Input: "Convert this CSV to JSON"
Plan:
- Parse CSV data
- Transform to JSON format
- Return formatted result

Current goal: {goal}
Additional context: {context}

Create a minimal, executable plan focusing only on necessary steps.
Format each step as a numbered list:
1. Step one
2. Step two
...
"""
        
        try:
            logger.debug(f"Creating plan for goal: `{goal}`")
            response = self.client.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are an AI planner focused on creating minimal, executable task plans."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.TEMPERATURE
            )
            
            # Parse returned steps
            steps = response.choices[0].message.content.strip().split("\n")
            tasks = []
            
            for step in steps:
                if step.strip() and not step.startswith("Example") and not step.startswith("Key"):
                    # Remove numbering and create task
                    if ". " in step:
                        task_desc = step.split(". ", 1)[-1].strip()
                        if task_desc:
                            tasks.append(Task(description=task_desc))
            
            logger.info(f"Created plan with `{len(tasks)}` tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"Error creating plan: `{str(e)}`")
            # Return a single task as fallback
            return [Task(description=goal)]
    
    def refine_plan(self, tasks: List[Task], feedback: str) -> List[Task]:
        """
        Optimize the plan based on feedback.
        
        Args:
            tasks: Current list of tasks
            feedback: Feedback for plan improvement
            
        Returns:
            List[Task]: Updated list of tasks
            
        Note:
            - Maintains the structure of the original plan
            - Incorporates feedback to improve task definitions
            - May add, remove, or modify tasks as needed
        """
        current_plan = "\n".join([t.description for t in tasks])
        
        prompt = f"""Current plan:
{current_plan}

Feedback:
{feedback}

Please optimize this plan following these principles:
1. Keep steps minimal and programmatic
2. Focus on automated operations
3. Remove any manual/human steps
4. Combine related operations
5. Ensure each step is executable by the system

Return the optimized steps in numbered format:
1. Step one
2. Step two
...
"""
        
        try:
            logger.debug(f"Refining plan based on feedback: {feedback}")
            response = self.client.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are an AI planner focused on optimizing task plans for automated execution."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.TEMPERATURE
            )
            
            # Parse returned steps
            steps = response.choices[0].message.content.strip().split("\n")
            new_tasks = []
            
            for step in steps:
                if step.strip():
                    # Remove numbering and create task
                    if ". " in step:
                        task_desc = step.split(". ", 1)[-1].strip()
                        if task_desc:
                            new_tasks.append(Task(description=task_desc))
            
            logger.info(f"Refined plan: {len(new_tasks)} tasks")
            return new_tasks
            
        except Exception as e:
            logger.error(f"Error refining plan: {str(e)}")
            return tasks  # Return original tasks if refinement fails