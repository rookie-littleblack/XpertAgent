"""
API client module for XpertAgent.
This module handles communication with the LLM API service.
"""

import time
import openai
from typing import Optional
from ..config.settings import settings

class APIClient:
    """
    API client class for handling LLM service communication.
    Implements rate limiting, retries, and error handling.
    """
    
    def __init__(self):
        """
        Initialize API client with configuration from settings.
        Sets up OpenAI client and rate limiting parameters.
        """
        # Initialize OpenAI client with API credentials
        self.client = openai.OpenAI(
            api_key=settings.API_KEY,
            base_url=settings.API_BASE
        )
        
        # Set up rate limiting parameters
        self.last_request_time = float(settings.API_LAST_REQUEST_TIME)
        self.min_request_interval = float(settings.API_MIN_REQUEST_INTERVAL)
        self.max_retries = int(settings.API_MAX_RETRIES)
    
    def _wait_for_rate_limit(self):
        """
        Ensure request intervals comply with rate limits.
        
        Note:
            - Calculates time since last request
            - Sleeps if minimum interval hasn't elapsed
            - Updates last request timestamp
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def create_chat_completion(
        self, 
        messages: list, 
        **kwargs
    ) -> Optional[openai.types.chat.ChatCompletion]:
        """
        Create a chat completion with retry logic and rate limiting.
        
        Args:
            messages: List of message dictionaries for the conversation
            **kwargs: Additional parameters for the API call
            
        Returns:
            ChatCompletion: API response object
            
        Raises:
            RateLimitError: If rate limit is exceeded after all retries
            Exception: For other API errors
            
        Note:
            - Implements exponential backoff for retries
            - Handles rate limiting automatically
            - Adapts to different API response formats
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                # Wait for rate limit
                self._wait_for_rate_limit()
                
                # Make API request
                response = self.client.chat.completions.create(
                    model=settings.DEFAULT_MODEL,
                    messages=messages,
                    **kwargs
                )
                return response
                
            except openai.RateLimitError as e:
                retries += 1
                if retries > self.max_retries:
                    raise Exception(
                        f"Maximum retry attempts ({self.max_retries}) reached"
                    )
                
                # Calculate wait time with exponential backoff
                wait_time = 2 ** retries
                print(
                    f"Rate limit reached, waiting {wait_time}s "
                    f"(attempt {retries}/{self.max_retries})"
                )
                time.sleep(wait_time)
                
            except Exception as e:
                print(f"API call error: {str(e)}")
                raise