"""
Helper utilities module for XpertAgent.
This module provides common utility functions used across the project.
"""

import re
import json
from typing import Any, Dict
from xpertagent.utils.xlogger import logger

RESPONSE_STATUS_SUCCESS = "0"
RESPONSE_STATUS_FAILED = "1"

def http_response(success: bool, result: Any, msg: str) -> Dict[str, Any]:
    """Format tool execution result into standard response format."""
    return {
        "success": success,
        "status": RESPONSE_STATUS_SUCCESS if success else RESPONSE_STATUS_FAILED,
        "result": str(result),
        "msg": msg
    }

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

def extract_json_from_string(text: str) -> str:
    """
    Extract valid JSON object from a string that might contain extra text.
    
    Args:
        text: String that contains a JSON object
        
    Returns:
        Extracted JSON string or empty string if no valid JSON found
        
    Examples:
        >>> text = "Some text before {\"key\": \"value\"} some text after"
        >>> extract_json_from_string(text)
        '{"key": "value"}'
        
        >>> text = "Text {\"items\": [{\"id\": 1}, {\"id\": 2}]} text"
        >>> extract_json_from_string(text)
        '{"items": [{"id": 1}, {"id": 2}]}'
    """
    try:
        # Find potential JSON by matching balanced braces
        stack = []
        start = -1
        candidates = []
        
        for i, char in enumerate(text):
            if char == '{':
                if not stack:  # First opening brace
                    start = i
                stack.append(char)
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack:  # All braces are matched
                        candidates.append(text[start:i+1])
        
        # Try each candidate, starting with the longest ones first
        # This ensures we get the most complete JSON object
        for candidate in sorted(candidates, key=len, reverse=True):
            try:
                # Verify it's valid JSON by parsing it
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                continue
                
        return ""
        
    except Exception as e:
        print(f"Error extracting JSON: {str(e)}")
        return ""

def format_tool_response(success: bool, result: Any) -> Dict[str, Any]:
    """
    Format tool execution result into standard response format.
    
    Args:
        success: Boolean indicating if tool execution succeeded
        result: Tool execution result or error message
        
    Returns:
        Dict containing success status and result string
    """
    return http_response(success, str(result), "")

def safe_parse_bool(value: str) -> bool:
    """Parse string to boolean value.
    
    Args:
        value (str): String value to parse
        
    Returns:
        bool: Parsed boolean value
    """
    return str(value).lower() in ('true', '1', 'yes', 'on', 't')

def format_prompt(prompt_template: str, **kwargs) -> str:
    """Format prompt template with provided values."""
    return prompt_template.format(**kwargs)