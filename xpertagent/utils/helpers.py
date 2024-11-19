"""
Helper utilities module for XpertAgent.
This module provides common utility functions used across the project.
"""

import re
import json
from typing import Any, Dict
from xpertagent.utils.xlogger import logger

def safe_json_loads(text: str) -> Dict[str, Any]:
    """
    Safely parse JSON string with fallback mechanisms.
    
    Args:
        text: String containing JSON data
        
    Returns:
        Dict containing parsed data with keys: thought, action, action_input
        
    Note:
        - First attempts direct JSON parsing
        - Falls back to regex extraction if direct parsing fails
        - Returns default response if all parsing attempts fail
    """
    try:
        # First attempt: direct JSON parsing
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Direct JSON parsing failed, attempting cleanup and extraction: {text}")
        try:
            # Second attempt: extract JSON-formatted content
            # Use regex to match thought, action, and action_input
            thought_match = re.search(r'"thought"\s*:\s*"([^"]*)"', text)
            action_match = re.search(r'"action"\s*:\s*"([^"]*)"', text)
            action_input_match = re.search(r'"action_input"\s*:\s*"([^"]*)"', text)
            
            result = {
                "thought": thought_match.group(1) if thought_match else "",
                "action": action_match.group(1) if action_match else "respond",
                "action_input": action_input_match.group(1) if action_input_match else text
            }
            
            logger.info(f"Successfully extracted JSON content: {result}")
            return result
            
        except Exception as e:
            logger.error(f"JSON extraction failed: {str(e)}")
            # Return default response if all attempts fail
            return {
                "thought": "Failed to parse response",
                "action": "respond",
                "action_input": text
            }

def format_tool_response(success: bool, result: Any) -> Dict[str, Any]:
    """
    Format tool execution result into standard response format.
    
    Args:
        success: Boolean indicating if tool execution succeeded
        result: Tool execution result or error message
        
    Returns:
        Dict containing success status and result string
    """
    return {
        "success": success,
        "result": str(result)
    }

def safe_parse_bool(value: str) -> bool:
    """Parse string to boolean value.
    
    Args:
        value (str): String value to parse
        
    Returns:
        bool: Parsed boolean value
    """
    return str(value).lower() in ('true', '1', 'yes', 'on', 't')