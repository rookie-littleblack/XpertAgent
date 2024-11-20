"""
XMedOCR APP: A specialized XOCR service for medical reports and ID cards.

This module provides a comprehensive OCR solution specifically designed for medical documents:
1. Laboratory Reports - Processes and structures lab test results
2. CT/Imaging Reports - Extracts findings and diagnoses from medical imaging reports
3. ID Cards - Captures and validates personal identification information

Key Features:
- Singleton pattern implementation for resource efficiency
- Thread-safe processing with asyncio locks
- Support for both HTTP and gRPC interfaces
- Integrated with XpertAgent for intelligent text processing
- Structured data extraction and formatting

Technical Details:
- Uses shared model instances for optimal resource utilization
- Implements both REST and gRPC endpoints
- Provides comprehensive error handling and logging
- Supports standalone deployment for testing and development
"""

import time
import asyncio
import traceback
from typing import Dict, Any, Optional
from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse
from xpertagent.protos import xmedocr_pb2, xmedocr_pb2_grpc, xcommon_pb2
from concurrent.futures import ThreadPoolExecutor
from xpertagent.core.agent import XpertAgent
from xpertagent.utils.xlogger import logger
from xpertagent.utils.helpers import extract_json_from_string
from xpertagent.prompts.p_xocr import PROMPTS_FOR_XMEDOCR
from xpertagent.tools.xpert_ocr.xocr_service import get_xocr_router, XOCRServicer

class XMedOCR:
    """
    Specialized XOCR service for medical documents and ID cards.
    
    This class implements a singleton pattern to ensure resource efficiency
    while providing thread-safe document processing capabilities.
    
    Attributes:
        _instance (XMedOCR): Singleton instance of the service
        _lock (asyncio.Lock): Thread synchronization lock
        _initialized (bool): Flag indicating initialization status
        agent (XpertAgent): Instance of XpertAgent for text processing
    """
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        """
        Implements singleton pattern for XMedOCR service.
        
        Returns:
            XMedOCR: Singleton instance of the service
            
        Note:
            This ensures only one instance of the service exists throughout the application
        """
        if cls._instance is None:
            cls._instance = super(XMedOCR, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        Initializes the XMedOCR service with XpertAgent.
        
        Note:
            This method is called only once due to singleton pattern
            Subsequent calls will return immediately if already initialized
        """
        if self._initialized:
            return
            
        self.agent = XpertAgent(name="XMedOCR_APP")
        self._initialized = True
        logger.info("XMedOCR APP service initialized")

    async def process(self, img_url: str, img_type: int, xpert_ocr_tool_result: Optional[str] = None) -> Dict[str, Any]:
        """
        Processes XOCR text and returns structured data.
        
        This method provides thread-safe processing of medical documents by:
        1. Selecting appropriate prompt based on document type
        2. Executing OCR if results not provided
        3. Formatting and structuring the extracted data
        
        Args:
            img_url (str): URL of the image to process
            img_type (int): Document type identifier (1: Lab Report, 2: CT Report, 3: ID Card)
            xpert_ocr_tool_result (Optional[str]): Pre-processed OCR result if available
            
        Returns:
            Dict[str, Any]: Structured data containing extracted information
            
        Raises:
            ValueError: If provided image type is invalid
            Exception: For any processing errors during execution
            
        Note:
            Method is thread-safe due to asyncio lock implementation
        """
        async with self._lock:
            try:
                # Get prompt for specific document type
                if img_type in PROMPTS_FOR_XMEDOCR:
                    prompt = PROMPTS_FOR_XMEDOCR[img_type]
                else:
                    raise ValueError(f"Invalid image type: `{img_type}`")
                
                # Execute XOCR tool if result not provided
                start_time = time.time()
                if xpert_ocr_tool_result is None:
                    xpert_ocr_tool_result = self.agent.execute(
                        "xpert_ocr_tool",
                        img_url
                    )
                logger.info(f"XOCR tool execution time: {time.time() - start_time} seconds")

                # Format final response
                final_response = self.agent.format_final_response(prompt, xpert_ocr_tool_result)

                # Extract and return structured data
                return extract_json_from_string(final_response)
                
            except Exception as e:
                logger.error(f"Error processing XOCR text: {str(e)}")
                raise

async def get_xmedocr_router(executor: ThreadPoolExecutor = None) -> APIRouter:
    """
    Creates and returns the XMedOCR service router.
    
    This function initializes a FastAPI router with XMedOCR endpoints and:
    1. Sets up shared thread pool for resource-efficient processing
    2. Configures endpoints with proper error handling
    3. Integrates with XOCR service for base OCR functionality
    
    Args:
        executor (ThreadPoolExecutor, optional): Thread pool for handling CPU-intensive tasks
        
    Returns:
        APIRouter: Configured FastAPI router with XMedOCR endpoints
        
    Note:
        Uses the same thread pool as XOCR service when provided
    """
    logger.info(">>> Initializing XMedOCR service...")
    router = APIRouter(prefix="/xmedocr", tags=["XMedOCR Services"])
    
    # Initialize services
    xmedocr = XMedOCR()
    xocr_router = await get_xocr_router(executor)
    
    @router.post("/process")
    async def xmedocr_endpoint(request: Request) -> JSONResponse:
        """
        XMedOCR endpoint for processing medical documents and ID cards.
        
        This endpoint:
        1. Receives image URL and type via HTTP POST
        2. Processes image through XOCR service
        3. Extracts structured data based on document type
        4. Returns formatted JSON response
        
        Args:
            request (Request): FastAPI request object containing image URL and type
            
        Returns:
            JSONResponse: Structured data or error message
            
        Note:
            Implements comprehensive error handling and logging
        """
        try:
            # Parse and log request data
            json_data = await request.json()
            logger.info(f"JSON request: `{json_data}`")

            # Process with base XOCR service
            xocr_result = await xocr_router.process_xocr(json_data)
            
            # Extract structured data
            result = await xmedocr.process(
                json_data["img_url"], 
                json_data["img_type"], 
                xocr_result
            )

            # Format and return response
            response = {"success": True, "result": result}
            logger.info(f"XMedOCR Result: `{response}`")
            return JSONResponse(content=response)
        except Exception as e:
            logger.error(f"XMedOCR Error: `{str(e)}`")
            print(f"Traceback: \n`{traceback.format_exc()}`")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": str(e)}
            )
    
    return router

class XMedOCRServicer(xmedocr_pb2_grpc.XMedOCRServiceServicer):
    """
    Implementation of XMedOCR gRPC service.
    
    This class provides the gRPC interface for XMedOCR service:
    1. Handles gRPC-specific request/response protocols
    2. Integrates with base XOCR service
    3. Provides structured data extraction for medical documents
    
    Note:
        Implements the service interface defined in xmedocr.proto
    """
    
    def __init__(self):
        """
        Initializes the gRPC servicer with required components.
        
        Sets up:
        1. XMedOCR instance for document processing
        2. XOCR servicer for base OCR functionality
        """
        self.xmedocr = XMedOCR()
        self.xocr_servicer = XOCRServicer()
    
    async def ProcessImage(self, request, context):
        """
        Processes medical document images via gRPC.
        
        This method:
        1. Processes image through base XOCR service
        2. Extracts structured data using XMedOCR
        3. Handles errors and returns appropriate responses
        
        Args:
            request: gRPC request containing image URL and type
            context: gRPC context for request handling
            
        Returns:
            xmedocr_pb2.MedOCRResponse: Structured data or error message
            
        Note:
            Uses xcommon_pb2.Status for standardized status reporting
        """
        try:
            # Process with base XOCR service
            xocr_response = await self.xocr_servicer.ProcessImage(request, context)
            if not xocr_response.status.success:
                return xmedocr_pb2.MedOCRResponse(
                    status=xcommon_pb2.Status(
                        success=False,
                        error=xocr_response.status.error
                    )
                )

            # Extract structured data
            result = await self.xmedocr.process(
                request.img_url,
                request.img_type,
                xocr_response.result
            )
            
            # Return successful response
            return xmedocr_pb2.MedOCRResponse(
                status=xcommon_pb2.Status(success=True),
                result=result
            )
        except Exception as e:
            logger.error(f"XMedOCR gRPC Error: {str(e)}")
            return xmedocr_pb2.MedOCRResponse(
                status=xcommon_pb2.Status(
                    success=False,
                    error=str(e)
                )
            )
