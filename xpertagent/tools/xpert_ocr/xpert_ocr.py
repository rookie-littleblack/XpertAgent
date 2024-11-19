"""
XpertOCR Tool: A comprehensive tool for text recognition with structured output.
This tool provides functionality to extract text from images using OCR technology,
supporting both single image URLs and text containing multiple image URLs.
"""

import re
import json
import time
import requests
from typing import Dict, Any, Tuple, List
from pathlib import Path
from ..base import BaseTool, ToolResult
from urllib.parse import urlparse
from ...utils.helpers import logger
from ...config.settings import settings
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL verification warnings for requests
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Global variable
service_name = "xpert_ocr"

class XpertOCRTool(BaseTool):
    """
    A tool for performing OCR on images using the XpertOCR service.
    Supports both direct URL processing and extraction of URLs from text.
    """
    
    def __init__(self):
        """Initialize the XpertOCR tool with service configuration."""
        super().__init__()
        self.name = "xpert_ocr_tool"
        self.description = "Extract text from images using XpertOCR"
        self.service_url = f"http://127.0.0.1:{settings.XOCR_SERVICE_PORT}/xocr"
        self.max_retries = 3
        self.retry_delay = 2
        #self._check_service()

    def extract_image_urls(self, text: str) -> List[str]:
        """
        Extract image URLs from input text.
        
        Args:
            text (str): Input text containing potential image URLs
            
        Returns:
            List[str]: List of extracted image URLs
        """
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff')
        protocols = ('http://', 'https://', 'ftp://')
        url_pattern = r'(?:http|https|ftp)://[^\s]+'
        
        potential_urls = re.findall(url_pattern, text)
        image_urls = []
        
        for url in potential_urls:
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            if (url.lower().startswith(protocols) and 
                any(path.endswith(ext) for ext in image_extensions)):
                image_urls.append(url)
        
        return image_urls

    def verify_image_urls(self, urls: List[str]) -> Tuple[List[str], List[str]]:
        """
        Verify accessibility of image URLs.
        
        Args:
            urls (List[str]): List of URLs to verify
            
        Returns:
            Tuple[List[str], List[str]]: Tuple of (valid_urls, invalid_urls)
        """
        valid_urls = []
        invalid_urls = []
        
        session = requests.Session()
        session.verify = False
        
        try:
            for url in urls:
                try:
                    response = session.head(url, timeout=5)
                    if response.status_code == 200:
                        valid_urls.append(url)
                    else:
                        invalid_urls.append(url)
                except requests.RequestException:
                    invalid_urls.append(url)
                finally:
                    if 'response' in locals():
                        response.close()
        finally:
            session.close()
        
        return valid_urls, invalid_urls

    def process_text_input(self, text: str) -> Dict:
        """
        Process text input containing image URLs.
        
        Args:
            text (str): Input text containing image URLs
            
        Returns:
            Dict: Processing results including status and OCR output
        """
        # Extract image URLs from text
        image_urls = self.extract_image_urls(text)
        if not image_urls:
            return {
                "status_code": 1,
                "desc": "No image URLs found in the text",
                "result": []
            }
        
        # Verify URL accessibility
        valid_urls, invalid_urls = self.verify_image_urls(image_urls)
        if not valid_urls:
            return {
                "status_code": 2,
                "desc": "None of the image URLs are accessible",
                "result": []
            }
        
        # Perform OCR on valid URLs
        results = []
        ocr_errors = []
        
        for url in valid_urls:
            try:
                ocr_result = self.execute(url)
                if ocr_result.success:
                    results.append({
                        "img_url": url,
                        "ocr_result": ocr_result.result
                    })
                else:
                    ocr_errors.append(url)
            except Exception as e:
                ocr_errors.append(url)
                logger.error(f"Error processing URL {url}: {str(e)}")
        
        # Generate return results
        if not results:
            return {
                "status_code": 3,
                "desc": "OCR failed for all valid images",
                "result": []
            }
        
        # Build description
        desc_parts = []
        if results:
            desc_parts.append(f"Successfully processed {len(results)} image(s)")
        if invalid_urls:
            desc_parts.append(f"{len(invalid_urls)} URL(s) were inaccessible")
        if ocr_errors:
            desc_parts.append(f"OCR failed for {len(ocr_errors)} image(s)")
        
        return {
            "status_code": 0 if len(results) == len(valid_urls) else 4,
            "desc": ". ".join(desc_parts),
            "result": results
        }

    def execute(self, input_text: str) -> ToolResult:
        """
        Execute OCR recognition on the input.
        Supports both direct image URLs and text containing image URLs.
        
        Args:
            input_text (str): Input text or URL to process
            
        Returns:
            ToolResult: OCR processing result
        """
        try:
            # Handle direct URL input
            if input_text.startswith(('http://', 'https://')):
                return self._process_single_url(input_text)
            
            # Handle text containing URLs
            result = self.process_text_input(input_text)
            
            # Format results
            if result["status_code"] in [0, 4]:  # Complete or partial success
                combined_text = "\n".join(
                    f"Image {i+1} ({r['img_url']}):\n{r['ocr_result']}"
                    for i, r in enumerate(result["result"])
                )
                return ToolResult(
                    success=True,
                    result=combined_text,
                    metadata={
                        "service": service_name,
                        "status": result["desc"],
                        "processed_urls": [r["img_url"] for r in result["result"]]
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    result="",
                    error=result["desc"],
                    metadata={
                        "service": service_name,
                        "status_code": result["status_code"]
                    }
                )
                
        except Exception as e:
            return self.handle_error(e)

    def _process_single_url(self, url: str) -> ToolResult:
        """
        Process a single image URL for OCR.
        
        Args:
            url (str): Image URL to process
            
        Returns:
            ToolResult: OCR processing result
        """
        try:
            # Verify URL accessibility
            valid_urls, _ = self.verify_image_urls([url])
            if not valid_urls:
                return self.handle_error(ValueError("Image URL is not accessible"))

            # Send OCR request
            response = requests.post(
                self.service_url,
                json={"img_url": url},
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                timeout=30
            )
            
            # Validate response
            is_valid, error_msg = self._validate_service_response(response)
            if not is_valid:
                return self.handle_error(RuntimeError(error_msg))
            
            # Process result
            result = response.json()
            return self.format_result({
                "text": result["result"],
                "service": service_name,
                "image_path": url
            })
            
        except Exception as e:
            return self.handle_error(e)

    def _check_service(self) -> None:
        """
        Check if the OCR service is available.
        Validates service status by sending a test request.
        Implements retry mechanism for reliability.
        """
        logger.info(f"Checking OCR service at {self.service_url}")
        
        for attempt in range(self.max_retries):
            try:
                # Prepare test request
                test_payload = {
                    "img_url": "https://www.tsinghua.edu.cn/image/lishiyange03.jpg"
                }
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-Request-Type": "health-check"
                }
                
                # Send request
                response = requests.post(
                    self.service_url,
                    json=test_payload,
                    headers=headers,
                    timeout=15
                )
                
                # Check response status
                if response.status_code == 200:
                    logger.info("XpertOCR service is available")
                    return
                else:
                    logger.warning(
                        f"XpertOCR service check failed (attempt {attempt + 1}/{self.max_retries}): "
                        f"Status code {response.status_code}"
                    )
                    
            except requests.exceptions.Timeout:
                logger.warning(
                    f"XpertOCR service timeout (attempt {attempt + 1}/{self.max_retries})"
                )
            except requests.exceptions.ConnectionError:
                logger.warning(
                    f"XpertOCR service connection failed (attempt {attempt + 1}/{self.max_retries})"
                )
            except Exception as e:
                logger.warning(
                    f"XpertOCR service check error (attempt {attempt + 1}/{self.max_retries}): {str(e)}"
                )
            
            # Wait before retry if not the last attempt
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
        
        # All retries failed
        logger.error(
            f"XpertOCR service is not available at {self.service_url} "
            f"after {self.max_retries} attempts"
        )

    def _validate_service_response(self, response: requests.Response) -> Tuple[bool, str]:
        """
        Validate the service response.
        
        Args:
            response: Service response object
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            if response.status_code != 200:
                return False, f"Service returned status code {response.status_code}"
            
            data = response.json()
            if not isinstance(data, dict):
                return False, "Invalid response format"
                
            if "success" not in data:
                return False, "Missing 'success' field in response"
                
            if not data["success"]:
                error_msg = data.get("error", "Unknown error")
                return False, f"Service error: {error_msg}"
                
            if "result" not in data:
                return False, "Missing 'result' field in response"
                
            return True, ""
            
        except json.JSONDecodeError:
            return False, "Invalid JSON response"
        except Exception as e:
            return False, f"Response validation error: {str(e)}"

    def validate_input(self, image_path: str) -> bool:
        """
        Validate the input image path or URL.
        
        Args:
            image_path (str): Path or URL to validate
            
        Returns:
            bool: True if input is valid
        """
        if image_path.startswith(('http://', 'https://')):
            return True
            
        path = Path(image_path)
        return (
            path.exists() and
            path.is_file() and
            path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        )

    def format_result(self, result: Dict[str, Any]) -> ToolResult:
        """
        Format the OCR result into a standardized output.
        
        Args:
            result (Dict[str, Any]): Raw OCR result
            
        Returns:
            ToolResult: Formatted result
        """
        return ToolResult(
            success=True,
            result=result["text"],
            metadata={
                "service": result["service"],
                "image_path": result["image_path"]
            }
        )

    def handle_error(self, error: Exception) -> ToolResult:
        """
        Handle errors in OCR processing.
        
        Args:
            error (Exception): Error to handle
            
        Returns:
            ToolResult: Error result
        """
        logger.error(f"OCR error: {str(error)}")
        return ToolResult(
            success=False,
            result="",
            error=str(error),
            metadata={
                "service": service_name,
                "error_type": error.__class__.__name__
            }
        )
