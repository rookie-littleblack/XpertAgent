"""
Tool management module for XpertAgent.
This module handles the registration and management of agent tools.
"""

import os
import importlib.util
from typing import List, Dict, Callable
from pydantic import BaseModel
from xpertagent.tools import register_built_in_tools
from xpertagent.utils.xlogger import logger
from xpertagent.config.settings import settings

class Tool(BaseModel):
    """
    Tool model representing a single capability of the agent.
    
    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description of the tool's functionality
        func: Callable function that implements the tool's logic
    """
    name: str
    description: str
    func: Callable
    
class ToolRegistry:
    """
    Registry class for managing available tools.
    Handles tool registration, retrieval, and listing.
    """
    
    def __init__(self):
        """Initialize an empty tool registry, register built-in tools, and load custom tools."""
        self._tools: Dict[str, Tool] = {}
        # First register built-in tools
        register_built_in_tools(self)
        # Then load custom tools
        self._load_custom_tools()

    def _load_custom_tools(self) -> None:
        """
        Load custom tools from the user's tools directory.
        
        Note:
            - Looks for Python files in the custom tools directory
            - Each tool file should define register_tools() function
            - Safely skips files that don't match the expected format
        """
        custom_tools_dir = settings.CUSTOM_TOOLS_PATH
        logger.debug(f"Loading custom tools from directory: {custom_tools_dir}")
        logger.debug(f"Current tools before loading: {self.list_tools()}")
        
        # Create __init__.py if it doesn't exist
        init_file = os.path.join(custom_tools_dir, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "w").close()
        
        # Load each Python file in the directory
        for filename in os.listdir(custom_tools_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                try:
                    file_path = os.path.join(custom_tools_dir, filename)
                    spec = importlib.util.spec_from_file_location(
                        f"custom_tools.{filename[:-3]}", 
                        file_path
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Call register_tools if it exists
                        if hasattr(module, "register_tools"):
                            module.register_tools(self)
                            logger.debug(f"Successfully loaded tools from {filename}")
                            logger.debug(f"Current tools after loading {filename}: {self.list_tools()}")
                        else:
                            logger.warning(f"No register_tools function found in {filename}")
                            
                except Exception as e:
                    logger.error(f"Error loading custom tools from {filename}: {str(e)}")

        logger.debug(f"Final tool list: {self.list_tools()}")

    def register(self, name: str, description: str, func: Callable) -> None:
        """
        Register a new tool in the registry.
        
        Args:
            name: Unique identifier for the tool
            description: Human-readable description of the tool
            func: Function implementing the tool's logic
            
        Note:
            - Tool names must be unique
            - Overwrites existing tool if name already exists
        """
        self._tools[name] = Tool(
            name=name,
            description=description,
            func=func
        )
        logger.debug(f"Registered tool: {name}")
    
    def get_tool(self, name: str) -> Tool | None:
        """
        Retrieve a tool by its name.
        
        Args:
            name: The unique identifier of the tool
            
        Returns:
            Tool if found, None otherwise
        """
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """
        List all available tool names.
        
        Returns:
            List[str]: Names of all registered tools
        """
        return list(self._tools.keys())
    
    def get_tool_descriptions(self) -> str:
        """
        Get formatted descriptions of all tools.
        
        Returns:
            str: Newline-separated list of tool descriptions
            
        Format:
            tool_name: tool_description
        """
        return "\n".join([
            f"{tool.name}: {tool.description}"
            for tool in self._tools.values()
        ])

# Create global tool registry instance
tool_registry = ToolRegistry()