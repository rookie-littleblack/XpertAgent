# XpertAgent

XpertAgent is an open-source platform for building and deploying AI applications. It combines intelligent workflow orchestration, knowledge enhancement, and multi-agent collaboration in an intuitive interface, helping you transform ideas into production-ready solutions.

## Features

- 🤖 Intelligent reasoning and decision making
- 🛠️ Extensible tool system
- 💾 Vector-based memory management
- 📋 Task planning and execution
- 🔧 Easy configuration and customization

## Installation

```bash
git clone https://github.com/rookie-littleblack/XpertAgent.git
cd XpertAgent
pip install .
```

## Configuration

```bash
cp .env.example .env
vim .env
```

> For a basic using of XpertAgent, you only need to configure the `API configurations (Required)` in the `.env` file.

## Quick Start

```bash
python -m examples.test_simple_agent
```

## Custom Tools

Create your own tools in `data/custom_tools/` like the following example:

```python
# data/custom_tools/weather_tool.py

def get_weather(location: str) -> str:
    """Get weather information for a location."""
    return f"Weather information for {location}"

def register_tools(registry):
    """Register custom tools with the agent."""
    registry.register(
        "weather",
        "Get weather information for a location",
        get_weather
    )
```

## Documentation

For detailed documentation, please visit:
- [Getting Started](docs/guides/getting_started.md)
- [API Reference](docs/api/index.md)
- [Examples](docs/examples/index.md)

## Contributing

Contributions are welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.