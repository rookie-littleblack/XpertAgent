# Configuration Guide

## Settings Overview

XpertAgent can be configured through environment variables or the settings file.

### Core Settings

```python
# xpertagent/config/settings.py

# API Configuration
API_KEY = "your-api-key"
API_BASE = "https://api.deepseek.com/beta"
DEFAULT_MODEL = "deepseek-chat"

# Agent Behavior
MAX_STEPS = 10
TEMPERATURE = 0.7
MEMORY_LIMIT = 1000

# Rate Limiting
API_MIN_REQUEST_INTERVAL = 0.5
API_MAX_RETRIES = 3
```

### Environment Variables

Priority order:
1. Environment variables
2. Settings file
3. Default values

```bash
# API Settings
export XPERT_API_KEY="your-api-key"
export XPERT_API_BASE="https://api.deepseek.com/beta"
export XPERT_DEFAULT_MODEL="deepseek-chat"

# Agent Settings
export XPERT_MAX_STEPS=10
export XPERT_TEMPERATURE=0.7
```

### Custom Paths

```python
# Base paths
XAPP_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(XAPP_PATH, "data")
CUSTOM_TOOLS_PATH = os.path.join(DATA_PATH, "custom_tools")
```

### Memory Settings

```python
# Vector DB Settings
COLLECTION_NAME = "agent_memories"
EMBEDDING_DIMENSION = 384
DISTANCE_METRIC = "cosine"
```

### Advanced Configuration

```python
# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Performance
BATCH_SIZE = 32
CACHE_SIZE = 1000