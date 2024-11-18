"""
Global settings configuration for XpertAgent.
This module handles environment variables, paths, and other configuration settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_env_float(key: str, default: float) -> float:
    """
    Get environment variable and convert to float.
    
    Args:
        key: Environment variable key
        default: Default value if key not found or conversion fails
        
    Returns:
        float: Converted value or default
    """
    value = os.getenv(key)
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def get_env_int(key: str, default: int) -> int:
    """
    Get environment variable and convert to integer.
    
    Args:
        key: Environment variable key
        default: Default value if key not found or conversion fails
        
    Returns:
        int: Converted value or default
    """
    value = os.getenv(key)
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

class Settings:
    """
    Global settings class containing all configuration parameters.
    Handles paths, API settings, and other global configurations.
    """
    # Base path configuration
    XAPP_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Data related paths
    DATA_PATH = os.path.join(XAPP_PATH, "data")
    CHROMA_PATH = os.path.join(DATA_PATH, "chromadb")  # Vector database storage
    LOGS_PATH = os.path.join(DATA_PATH, "logs")        # Application logs
    CACHE_PATH = os.path.join(DATA_PATH, "cache")      # Temporary cache files
    CONFIG_PATH = os.path.join(DATA_PATH, "config")    # Additional configurations
    MODELS_PATH = os.path.join(DATA_PATH, "models")    # Model weights and configs
    CUSTOM_TOOLS_PATH = os.path.join(DATA_PATH, "custom_tools")  # Custom tools directory
    
    # Ensure all required directories exist
    for path in [DATA_PATH, CHROMA_PATH, LOGS_PATH, CACHE_PATH, CONFIG_PATH, MODELS_PATH, CUSTOM_TOOLS_PATH]:
        os.makedirs(path, exist_ok=True)
        
    # API configuration
    API_KEY = os.getenv("LLM_API_KEY")
    API_BASE = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")  # Default OpenAI endpoint
    DEFAULT_MODEL = os.getenv("LLM_API_MODEL", "gpt-3.5-turbo")        # Default model name

    # API request settings with type conversion
    API_LAST_REQUEST_TIME = get_env_float("LLM_API_LAST_REQUEST_TIME", 0)          # Last request timestamp
    API_MIN_REQUEST_INTERVAL = get_env_float("LLM_API_MIN_REQUEST_INTERVAL", 1.0)  # Minimum seconds between requests
    API_MAX_RETRIES = get_env_int("LLM_API_MAX_RETRIES", 3)                        # Maximum retry attempts
    
    # Memory configuration
    MEMORY_COLLECTION = "xpertagent_memory"  # ChromaDB collection name
    MAX_MEMORY_ITEMS = 1000                  # Maximum items in memory
    
    # Tool configuration
    DEFAULT_TOOLS = ["search", "calculator", "weather"]  # List of default available tools
    
    # Agent configuration
    MAX_STEPS = get_env_int("LLM_MAX_STEPS", 5)              # Maximum steps per task
    TEMPERATURE = get_env_float("LLM_API_TEMPERATURE", 0.7)  # LLM temperature setting

# Create global settings instance
settings = Settings()