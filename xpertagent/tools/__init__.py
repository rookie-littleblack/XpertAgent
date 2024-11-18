"""Built-in tools package for XpertAgent."""

from typing import Dict, Type
from .base import BaseTool
from .xpert_ocr.xpert_ocr import XpertOCRTool
from .xpert_calc.xpert_calc import XpertCalculatorTool
# Import other tools...

# Tool registry
BUILT_IN_TOOLS: Dict[str, Type[BaseTool]] = {
    "xpert_calc": XpertCalculatorTool,  # Xpert Calculator
    "xpert_ocr": XpertOCRTool,  # Xpert OCR
    # Add other tools...
}

def register_built_in_tools(registry) -> None:
    """Register all built-in tools with the registry."""
    for _, tool_class in BUILT_IN_TOOLS.items():
        tool_instance = tool_class()
        registry.register(
            name=tool_instance.name,
            description=tool_instance.description,
            func=tool_instance.execute
        )