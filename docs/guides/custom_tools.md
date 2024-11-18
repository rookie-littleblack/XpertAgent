# Creating Custom Tools

Learn how to extend XpertAgent's capabilities by creating custom tools.

## Tool Structure

A custom tool consists of two main parts:
1. The tool function
2. The registration function

## Basic Example

Create a new file in `data/custom_tools/`:

```python
# data/custom_tools/time_tool.py

from datetime import datetime

def get_current_time() -> str:
    """Get the current time."""
    return str(datetime.now())

def register_tools(registry):
    """Register custom tools with the agent."""
    registry.register(
        "time",
        "Get the current time",
        get_current_time
    )
```

## Tool Guidelines

1. Function Requirements:
   - Clear input/output types
   - Comprehensive docstrings
   - Error handling

2. Registration:
   - Unique tool names
   - Clear descriptions
   - Proper error handling

## Advanced Example

```python
# data/custom_tools/advanced_tool.py

from typing import Dict, Any
import json

class DataProcessor:
    def process_data(self, data: str) -> Dict[str, Any]:
        """
        Process input data.
        
        Args:
            data: JSON string to process
            
        Returns:
            Dict containing processed data
        """
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON"}

def register_tools(registry):
    processor = DataProcessor()
    registry.register(
        "process_data",
        "Process JSON data and return structured result",
        processor.process_data
    )
```

## Testing Tools

Create test cases for your tools:

```python
# tests/test_custom_tools.py

def test_time_tool():
    from custom_tools.time_tool import get_current_time
    result = get_current_time()
    assert isinstance(result, str)
```