"""Calculator tool implementation for XpertAgent."""

from typing import Union
from ..base import BaseTool, ToolResult

class XpertCalculatorTool(BaseTool):
    """Tool for performing basic mathematical calculations."""
    
    def __init__(self):
        super().__init__()
        self.name = "xpert_calculator_tool"
        self.description = "Perform basic mathematical calculations"
    
    def execute(self, expression: str) -> ToolResult:
        """
        Execute mathematical calculation.
        
        Args:
            expression: Mathematical expression as string
            
        Returns:
            ToolResult containing the calculation result
            
        Example:
            >>> calculator.execute("2 + 2")
            ToolResult(success=True, result=4.0)
        """
        try:
            # Validate input
            if not self.validate_input(expression):
                raise ValueError("Invalid mathematical expression")
            
            # Perform calculation
            result = eval(expression)
            
            return self.format_result(result)
            
        except Exception as e:
            return self.handle_error(e)
    
    def validate_input(self, expression: str) -> bool:
        """
        Validate the mathematical expression.
        
        Args:
            expression: Expression to validate
            
        Returns:
            bool: True if expression is valid
            
        Note:
            - Checks for basic safety
            - Only allows basic mathematical operations
        """
        # Check if expression is string
        if not isinstance(expression, str):
            return False
            
        # Check for forbidden characters/words
        forbidden = ['import', 'exec', 'eval', 'os', 'sys', '__']
        if any(word in expression for word in forbidden):
            return False
            
        # Check for valid characters
        allowed = set('0123456789+-*/().% ')
        if not set(expression).issubset(allowed):
            return False
            
        return True