"""Base classes and utilities for XpertAgent tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

class ToolResult(BaseModel):
    """Model for tool execution results."""
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}

class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    def __init__(self):
        self.name: str = self.__class__.__name__
        self.description: str = self.__doc__ or "No description available"
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> ToolResult:
        """Execute the tool's main functionality."""
        pass
    
    def validate_input(self, *args, **kwargs) -> bool:
        """Validate input parameters."""
        return True
    
    def format_result(self, result: Any) -> ToolResult:
        """Format the execution result."""
        return ToolResult(
            success=True,
            result=result
        )
    
    def handle_error(self, error: Exception) -> ToolResult:
        """Handle execution errors."""
        return ToolResult(
            success=False,
            result=None,
            error=str(error)
        )