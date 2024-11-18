# Getting Started with XpertAgent

This guide will help you get started with XpertAgent, from installation to your first agent implementation.

## Installation

1. Install using pip:

```bash
pip install xpertagent
```

2. Set up your environment variables:

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_API_BASE="https://api.deepseek.com/beta"
```

## Basic Usage

1. Create your first agent:

```python
from xpertagent.core.agent import XpertAgent

# Initialize agent
agent = XpertAgent(name="MyAgent")
```

2. Run a simple task:
```python
response = agent.run("Calculate 123*456 and explain the result")
print(response)
```

## Configuration

Configure your agent through `settings.py`:

```python
# xpertagent/config/settings.py
API_KEY = "your-api-key"
API_BASE = "https://api.deepseek.com/beta"
MAX_STEPS = 10
TEMPERATURE = 0.7
```

## Memory Management

XpertAgent uses vector-based memory for context awareness:

```python
# Add memory
agent.memory.add("Important information", {"type": "note"})

# Search memory
results = agent.memory.search("relevant query")
```

## Next Steps

- Learn about [Custom Tools](custom_tools.md)
- Explore [Configuration Options](configuration.md)
- Check out [Examples](../examples/basic_usage.md)