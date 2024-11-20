"""
XMedOCR APP: A specialized XOCR service for medical reports and ID cards.

Handles XOCR processing and structured data extraction for:
1. Laboratory Reports
2. CT/Imaging Reports
3. ID Cards

Supports both HTTP and gRPC interfaces.
"""

import time

from typing import Dict, Any
from xpertagent.core.agent import XpertAgent
from xpertagent.utils.xlogger import logger
from xpertagent.utils.helpers import extract_json_from_string
from xpertagent.prompts.p_xocr import PROMPTS_FOR_XMEDOCR

class XMedOCR:
    """
    Specialized OCR service for medical documents and ID cards.
    Provides structured data extraction and formatting.
    """
    
    def __init__(self):
        """Initialize the XMedOCR service."""
        self.agent = XpertAgent(name="XMedOCR_APP")
        logger.info("XMedOCR APP service initialized")

    def process(self, img_url: str, img_type: int) -> Dict[str, Any]:
        """
        Process OCR text and return structured data.
        
        Args:
            ocr_text: Raw OCR text from the image
            img_url: URL of the processed image
            img_type: Type of document (1: Lab Report, 2: CT Report, 3: ID Card)
            
        Returns:
            Dict containing structured data or error message
        """
        try:
            # Get prompt for specific document type
            if img_type in PROMPTS_FOR_XMEDOCR:
                prompt = PROMPTS_FOR_XMEDOCR[img_type]
            else:
                raise ValueError(f"Invalid image type: `{img_type}`")
            
            # Execute XOCR tool
            start_time = time.time()
            xpert_ocr_tool_result = self.agent.execute(
                "xpert_ocr_tool",
                img_url
            )
            logger.info(f"XOCR tool execution time: {time.time() - start_time} seconds")
            # Format final response
            final_response = self.agent.format_final_response(prompt, xpert_ocr_tool_result)

            # Return result
            return extract_json_from_string(final_response)
            
        except Exception as e:
            logger.error(f"Error processing XOCR text: {str(e)}")
            return None
        
if __name__ == "__main__":
    start_time = time.time()
    xmedocr = XMedOCR()
    structured_data = xmedocr.process("https://backstage.iandun.com/andun-app/images/temp/e4501f95fb2444bd9df36afbe1143654.png", 1)
    logger.info(f"XMedOCR APP service execution time: {time.time() - start_time} seconds")
    logger.info(f"Structured data: `{structured_data}`")
