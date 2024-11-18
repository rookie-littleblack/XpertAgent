"""
Task planning module for XpertAgent.
This module handles the creation and refinement of execution plans.
"""

from typing import List, Dict
from pydantic import BaseModel
from ..utils.client import APIClient
from ..config.settings import settings

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
        prompt = f"""
        Goal: {goal}
        Context: {context}
        
        Please break down this goal into specific executable steps.
        Each step should be clear and actionable.
        Return in the following format:
        1. Step 1
        2. Step 2
        ...
        """
        
        response = self.client.create_chat_completion(
            messages=[
                {"role": "system", "content": "You are a task planning expert, skilled at breaking down complex goals into executable steps."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.TEMPERATURE
        )
        
        # Parse returned steps
        steps = response.choices[0].message.content.strip().split("\n")
        tasks = []
        for step in steps:
            if step.strip():
                # Remove numbering and create task
                task_desc = step.split(". ", 1)[-1]
                tasks.append(Task(description=task_desc))
        
        return tasks
    
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
        
        prompt = f"""
        Current Plan:
        {current_plan}
        
        Feedback:
        {feedback}
        
        Please optimize the plan based on the feedback.
        Return the modified steps.
        """
        
        response = self.client.create_chat_completion(
            messages=[
                {"role": "system", "content": "You are a task planning expert, skilled at optimizing execution plans."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.TEMPERATURE
        )
        
        # Parse returned steps
        steps = response.choices[0].message.content.strip().split("\n")
        new_tasks = []
        for step in steps:
            if step.strip():
                task_desc = step.split(". ", 1)[-1]
                new_tasks.append(Task(description=task_desc))
        
        return new_tasks