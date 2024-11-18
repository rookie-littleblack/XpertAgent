"""
Custom weather tool for XpertAgent.
"""

def get_weather(location: str) -> str:
    """Get weather information for a location."""
    # Implementation here
    return f"===> Weather information for {location}"

def register_tools(registry):
    """Register custom tools with the agent."""
    registry.register(
        "weather",
        "Get weather information for a location",
        get_weather
    )