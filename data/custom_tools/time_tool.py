"""
Custom time tool for XpertAgent.
"""

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