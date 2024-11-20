"""
XMedOCR APP: A specialized XOCR service for medical reports and ID cards.

Handles XOCR processing and structured data extraction for:
1. Laboratory Reports
2. CT/Imaging Reports
3. ID Cards

Supports both HTTP and gRPC interfaces.
"""

import time
import traceback

from typing import Dict, Any
from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse
from concurrent.futures import ThreadPoolExecutor
from xpertagent.core.agent import XpertAgent
from xpertagent.utils.xlogger import logger
from xpertagent.utils.helpers import extract_json_from_string
from xpertagent.prompts.p_xocr import PROMPTS_FOR_XMEDOCR
from xpertagent.tools.xpert_ocr.xocr_service import get_xocr_router

class XMedOCR:
    """
    Specialized XOCR service for medical documents and ID cards.
    Provides structured data extraction and formatting.
    """
    
    def __init__(self):
        """Initialize the XMedOCR service."""
        self.agent = XpertAgent(name="XMedOCR_APP")
        logger.info("XMedOCR APP service initialized")

    def process(self, img_url: str, img_type: int, xpert_ocr_tool_result: str | None = None) -> Dict[str, Any]:
        """
        Process XOCR text and return structured data.
        
        Args:
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
            if xpert_ocr_tool_result is None:
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

async def get_xmedocr_router(executor: ThreadPoolExecutor = None) -> APIRouter:
    """
    Create and return the XMedOCR service router.
    Uses the same thread pool as XOCR service for processing.
    
    Returns:
        APIRouter: FastAPI router configured with XMedOCR endpoints
        
    Raises:
        Exception: If the required model path does not exist
    """
    logger.info(">>> Initializing XMedOCR service...")
    router = APIRouter(prefix="/xmedocr", tags=["XMedOCR Services"])

    # Initialize XMedOCR service
    xmedocr = XMedOCR()

    # Get XOCR router for internal use
    xocr_router = await get_xocr_router(executor)
    
    @router.post("/process")
    async def xmedocr_endpoint(request: Request) -> JSONResponse:
        """
        XMedOCR endpoint that processes incoming image URLs and returns extracted text.
        
        Args:
            request (Request): FastAPI request object containing image URL
            
        Returns:
            JSONResponse: XMedOCR results or error message
        """
        try:
            # Print JSON request data
            json_data = await request.json()
            logger.info(f"JSON request: `{json_data}`")

            # Use internal OCR processing instead of HTTP call
            xocr_result = await xocr_router.process_xocr(json_data)
            
            # Process the image
            result = xmedocr.process(
                json_data["img_url"], 
                json_data["img_type"], 
                xocr_result
            )

            # Return the result as a JSON response
            result = {"success": True, "result": result}
            logger.info(f"XMedOCR Result: `{result}`")
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"XMedOCR Error: `{str(e)}`")
            print(f"Traceback: \n`{traceback.format_exc()}`")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": str(e)}
            )
    
    return router

if __name__ == "__main__":
    start_time = time.time()
    xmedocr = XMedOCR()
    structured_data = xmedocr.process("https://backstage.iandun.com/andun-app/images/temp/e4501f95fb2444bd9df36afbe1143654.png", 1)
    logger.info(f"XMedOCR APP service execution time: {time.time() - start_time} seconds")
    logger.info(f"Structured data: `{structured_data}`")
