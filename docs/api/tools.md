# Tools API Reference

## Tool

Model representing a single agent capability.

### Attributes

- `name` (str): Unique tool identifier
- `description` (str): Human-readable description
- `func` (Callable): Implementation function

## ToolRegistry

Registry for managing available tools.

### Methods

#### register
```python
def register(self, name: str, description: str, func: Callable) -> None
```

Register a new tool.

**Parameters:**
- `name` (str): Tool identifier
- `description` (str): Tool description
- `func` (Callable): Tool implementation

#### get_tool
```python
def get_tool(self, name: str) -> Tool | None
```

Retrieve a tool by name.

**Parameters:**
- `name` (str): Tool identifier

**Returns:**
- Tool | None: Tool instance if found

#### list_tools
```python
def list_tools() -> List[str]
```

List all available tools.

**Returns:**
- List[str]: Tool names