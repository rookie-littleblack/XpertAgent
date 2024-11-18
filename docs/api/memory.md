# Memory API Reference

## Memory

Vector database management for agent memories.

### Constructor

```python
def __init__(self)
```

Initializes the memory system with ChromaDB backend.

### Methods

#### add
```python
def add(self, text: str, metadata: Dict[str, Any] = None) -> None
```

Add a new memory entry.

**Parameters:**
- `text` (str): Memory content
- `metadata` (Dict[str, Any]): Additional metadata

#### search
```python
def search(self, query: str, limit: int = 5) -> List[str]
```

Search for relevant memories.

**Parameters:**
- `query` (str): Search query
- `limit` (int): Maximum results

**Returns:**
- List[str]: Relevant memory texts

#### clear
```python
def clear() -> None
```

Clear all stored memories.