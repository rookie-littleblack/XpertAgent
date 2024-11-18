# Agent API Reference

## XpertAgent

The main agent class that handles reasoning and execution.

### Constructor

```python
def __init__(self, name: str = "XAgent")
```

**Parameters:**
- `name` (str): Agent's identifier name

### Methods

#### run
```python
def run(self, input_text: str, max_steps: int | None = None) -> str
```

Execute the agent's main loop.

**Parameters:**
- `input_text` (str): User input text
- `max_steps` (int, optional): Maximum execution steps

**Returns:**
- str: Agent's final response

#### think
```python
def think(self, input_text: str, last_result: Any = None) -> Dict[str, Any]
```

Process input and decide next action.

**Parameters:**
- `input_text` (str): Current context
- `last_result` (Any): Previous action result

**Returns:**
- Dict[str, Any]: Thought process and action decision

#### execute
```python
def execute(self, action: str, action_input: str) -> str
```

Execute the decided action.

**Parameters:**
- `action` (str): Tool name or 'respond'
- `action_input` (str): Tool input or response text

**Returns:**
- str: Execution result