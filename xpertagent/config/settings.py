"""
Global settings configuration for XpertAgent.
This module handles environment variables, paths, and other configuration settings.
"""

import os
from dotenv import load_dotenv

__EMAIL__ = "rookielittblack@yeah.net"
__AUTHOR__ = "rookielittleblack"
__XAPP_NAME__ = "XpertAgent"
__XAPP_PATH__ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

def get_version():
    """
    Get the current version of XpertAgent.
    
    Args:
        None
        
    Returns:
        str: Version string read from VERSION file
    """
    version_file = os.path.join(__XAPP_PATH__, "VERSION")
    with open(version_file) as f:
        return f.read().strip()

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
    XAPP_PATH = __XAPP_PATH__
    XAPP_NAME = __XAPP_NAME__
    XAPP_EMAIL = __EMAIL__
    XAPP_AUTHOR = __AUTHOR__
    XAPP_VERSION = get_version()
    
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

    # Project level configuration
    PROJ_ENV = os.getenv("PROJ_ENV", "dev")  # Project environment
        
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
    MAX_MEMORY_ITEMS = 100                   # Maximum items in memory
    
    # Tool configuration
    DEFAULT_TOOLS = ["search", "calculator", "weather"]  # List of default available tools
    
    # Agent configuration
    MAX_STEPS = get_env_int("LLM_MAX_STEPS", 5)              # Maximum steps per task
    TEMPERATURE = get_env_float("LLM_API_TEMPERATURE", 0.7)  # LLM temperature setting

    # Service configuration
    XHTTP_SERVICE_HOST = os.getenv("XHTTP_SERVICE_HOST", "127.0.0.1")  # XpertAgent HTTP service host
    XHTTP_SERVICE_PORT = get_env_int("XHTTP_SERVICE_PORT", 7833)  # XpertAgent HTTP service port
    XGRPC_SERVICE_HOST = os.getenv("XGRPC_SERVICE_HOST", "127.0.0.1")  # XpertAgent GRPC service host
    XGRPC_SERVICE_PORT = get_env_int("XGRPC_SERVICE_PORT", 7834)  # XpertAgent GRPC service port

    # Logging configuration
    XLOGGER_LOG_VER = get_version()  # Log version
    XLOGGER_LOG_DIR = LOGS_PATH  # Log directory
    XLOGGER_LOG_FILENAME = "xlogger.log"  # Log file name
    XLOGGER_LOG_MONGODB_ENABLE = str(os.getenv("XLOGGER_MONGODB_ENABLE", "false")).lower() in ('true', '1', 'yes', 'on', 't')  # MongoDB logging enable
    XLOGGER_LOG_MONGODB_CONFIG = {
        "user": os.getenv("XLOGGER_MONGODB_USER", "xpertagent_user"),
        "pass": os.getenv("XLOGGER_MONGODB_PASS", "xpertagent_pass"),
        "host": os.getenv("XLOGGER_MONGODB_HOST", "127.0.0.1"),
        "port": os.getenv("XLOGGER_MONGODB_PORT", "27017"),
        "dbnm": os.getenv("XLOGGER_MONGODB_DBNM", "xpertagent_db"),
        "clnm": os.getenv("XLOGGER_MONGODB_CLNM", "xpertagent_cl"),
        "tbnm": os.getenv("XLOGGER_MONGODB_TBNM", "xpertagent_log")
    }

    # Dingtalk configurations
    XDINGTALK_APP_KEY = os.getenv("XDINGTALK_APP_KEY")
    XDINGTALK_APP_SECRET = os.getenv("XDINGTALK_APP_SECRET")
    XDINGTALK_WEBHOOK_TOKEN = os.getenv("XDINGTALK_WEBHOOK_TOKEN")

    def __str__(self):
        return f"Settings(XAPP_PATH={self.XAPP_PATH}, XAPP_NAME={self.XAPP_NAME}, XAPP_EMAIL={self.XAPP_EMAIL}, XAPP_AUTHOR={self.XAPP_AUTHOR}, XAPP_VERSION={self.XAPP_VERSION})"

# Create global settings instance
settings = Settings()