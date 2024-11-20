"""
XpertOCR Service: A FastAPI-based service for OCR using GOT-OCR2_0 model.

This service provides:
1. HTTP and gRPC endpoints for OCR processing
2. High-performance image processing with CUDA support
3. Thread-safe model inference
4. Comprehensive error handling and logging

Key Components:
- GOT-OCR2_0 model integration
- Image preprocessing pipeline
- Asynchronous request handling
- Resource-efficient singleton pattern

Technical Features:
- CUDA-accelerated inference
- Configurable image processing
- Standardized error reporting
- Performance optimization
"""

import os
import io
import torch
import asyncio
import requests
import traceback

from PIL import Image
from dotenv import load_dotenv
from fastapi import FastAPI, Request, APIRouter
from pydantic import BaseModel
from GOT.model import GOTQwenForCausalLM
from transformers import AutoTokenizer
from GOT.utils.utils import disable_torch_init, KeywordsStoppingCriteria
from fastapi.responses import JSONResponse
from xpertagent.protos import xocr_pb2, xocr_pb2_grpc, xcommon_pb2
from concurrent.futures import ThreadPoolExecutor
from GOT.utils.conversation import conv_templates, SeparatorStyle
from xpertagent.utils.xlogger import logger
from GOT.model.plug.blip_process import BlipImageEvalProcessor

# Load environment configuration
load_dotenv()

# Configure base application path
XAPP_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class XOCRRequest(BaseModel):
    """
    Pydantic model for XOCR API requests.
    
    Attributes:
        img_url (str): URL of the image to process
        
    Note:
        Allows additional fields through Config.extra setting
    """
    img_url: str

    class Config:
        extra = "allow"  # Enable additional request parameters

# Define model-specific tokens
DEFAULT_IMAGE_TOKEN = "<image>"
DEFAULT_IMAGE_PATCH_TOKEN = '<imgpad>'
DEFAULT_IM_START_TOKEN = '<img>'
DEFAULT_IM_END_TOKEN = '</img>'

class XOCRModel:
    """
    XOCR Model wrapper implementing singleton pattern.
    
    This class provides:
    1. Thread-safe model inference
    2. Efficient resource management
    3. Optimized image processing
    4. CUDA acceleration support
    
    Attributes:
        _instance (XOCRModel): Singleton instance
        _lock (asyncio.Lock): Thread synchronization lock
        _initialized (bool): Initialization status flag
    """
    _instance = None
    _lock = asyncio.Lock()
    _initialized = False
    
    def __new__(cls, model_name: str):
        """
        Implements singleton pattern for model instance.
        
        Args:
            model_name (str): Path to the pre-trained model
            
        Returns:
            XOCRModel: Singleton model instance
        """
        if cls._instance is None:
            cls._instance = super(XOCRModel, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, model_name: str):
        """
        Initializes the XOCR model with optimized settings.
        
        Args:
            model_name (str): Path to the pre-trained model
            
        Note:
            Configures model for CUDA acceleration and FP16 precision
        """
        if self._initialized:
            return
            
        disable_torch_init()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = GOTQwenForCausalLM.from_pretrained(
            model_name, 
            low_cpu_mem_usage=True,
            device_map='cuda',
            use_safetensors=True,
            torch_dtype=torch.float16
        ).eval()
        
        self.image_processor = BlipImageEvalProcessor(image_size=1024)
        self.image_processor_high = BlipImageEvalProcessor(image_size=1024)
        self._initialized = True

    async def process_image(self, image: Image.Image) -> str:
        """
        Processes image and generates OCR results asynchronously.
        
        This method:
        1. Prepares image and model inputs
        2. Performs inference with CUDA acceleration
        3. Post-processes model outputs
        
        Args:
            image (Image.Image): PIL Image object to process
            
        Returns:
            str: Extracted text from the image
            
        Raises:
            Exception: For any processing or inference errors
            
        Note:
            Thread-safe execution through asyncio lock
        """
        async with self._lock:
            try:
                # Set XOCR prompt
                qs = 'OCR: '  # DONOT CHANGE THIS PROMPT!

                # Add image tokens to the prompt
                qs = f"{DEFAULT_IM_START_TOKEN}{DEFAULT_IMAGE_PATCH_TOKEN*256}{DEFAULT_IM_END_TOKEN}\n{qs}"

                # Prepare conversation template
                conv = conv_templates["mpt"].copy()
                conv.append_message(conv.roles[0], qs)
                conv.append_message(conv.roles[1], None)
                prompt = conv.get_prompt()

                # Process inputs
                inputs = self.tokenizer([prompt])
                image_tensor = self.image_processor(image)
                image_tensor_1 = self.image_processor_high(image)
                input_ids = torch.as_tensor(inputs.input_ids).cuda()

                # Set stopping criteria
                stop_str = conv.sep if conv.sep_style != SeparatorStyle.TWO else conv.sep2
                stopping_criteria = KeywordsStoppingCriteria([stop_str], self.tokenizer, input_ids)

                # Generate results
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    output_ids = self.model.generate(
                        input_ids,
                        images=[(image_tensor.unsqueeze(0).half().cuda(), 
                                image_tensor_1.unsqueeze(0).half().cuda())],
                        do_sample=False,
                        num_beams=1,
                        no_repeat_ngram_size=20,
                        max_new_tokens=4096,
                        stopping_criteria=[stopping_criteria],

                        pad_token_id=self.tokenizer.pad_token_id,
                        eos_token_id=self.tokenizer.eos_token_id,
                        # Add above two lines to avoid the following warnings:
                        # The attention mask and the pad token id were not set. As a consequence, you may observe unexpected behavior. Please pass your input's `attention_mask` to obtain reliable results.
                        # Setting `pad_token_id` to `eos_token_id`:151643 for open-end generation.
                    )

                # Decode and clean up the output
                outputs = self.tokenizer.decode(output_ids[0, input_ids.shape[1]:]).strip()
                if outputs.endswith(stop_str):
                    outputs = outputs[:-len(stop_str)]
                    
                return outputs.strip()

            except Exception as e:
                logger.error(f"Error processing image: {str(e)}")
                raise

async def download_image(url: str) -> Image.Image:
    """
    Downloads and validates image from URL.
    
    Args:
        url (str): URL of the image to download
        
    Returns:
        Image.Image: PIL Image object
        
    Raises:
        Exception: If download fails or image is invalid
        
    Note:
        Implements timeout and error handling
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content))
    except Exception as e:
        logger.error(f"Error downloading image: {str(e)}")
        raise

def init_xocr_model() -> XOCRModel:
    """
    Initializes XOCR model with default configuration.
    
    Returns:
        XOCRModel: Initialized model instance
        
    Raises:
        Exception: If model initialization fails
        
    Note:
        Uses singleton pattern for resource efficiency
    """
    model_path = os.path.join(XAPP_PATH, "data/models/GOT-OCR2_0")
    logger.info(f">>> Initializing XOCR service...")
    model = XOCRModel(model_path)
    logger.info(f">>> XOCR Model initialized: `{model_path}`")
    return model

async def get_xocr_router(executor: ThreadPoolExecutor = None) -> APIRouter:
    """
    Creates and configures XOCR FastAPI router.
    
    Args:
        executor (ThreadPoolExecutor, optional): Thread pool for CPU tasks
        
    Returns:
        APIRouter: Configured FastAPI router
        
    Note:
        Implements both endpoint and direct call interfaces
    """
    logger.info(">>> Initializing XOCR service...")
    router = APIRouter(prefix="/xocr", tags=["XOCR Services"])
    
    # Initialize model instance
    model = init_xocr_model()
    
    async def process_xocr_request(data: dict) -> str:
        """
        Internal processing method for OCR requests.
        
        Args:
            data (dict): Request data with image URL
            
        Returns:
            str: OCR result text
            
        Note:
            Can be called directly or via API endpoint
        """
        image = await download_image(data["img_url"])
        result = await model.process_image(image)
        return result
    
    @router.post("/process")
    async def xocr_endpoint(request: Request) -> JSONResponse:
        """
        HTTP endpoint for OCR processing.
        
        Args:
            request (Request): FastAPI request object
            
        Returns:
            JSONResponse: OCR results or error message
            
        Note:
            Implements comprehensive error handling
        """
        try:
            json_data = await request.json()
            logger.debug(f"JSON request: `{json_data}`")
            result = await process_xocr_request(json_data)
            return JSONResponse(content={"success": True, "result": result})
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": str(e)}
            )
    
    # Expose internal method for direct calls
    router.process_xocr = process_xocr_request
    return router

class XOCRServicer(xocr_pb2_grpc.XOCRServiceServicer):
    """
    Implementation of XOCR gRPC service.
    
    This class provides:
    1. gRPC interface for OCR processing
    2. Integration with XOCRModel
    3. Standardized error handling
    4. Status reporting through protobuf
    """
    
    def __init__(self):
        """
        Initializes the gRPC servicer with model instance.
        
        Note:
            Uses shared model instance through singleton pattern
        """
        self.model = init_xocr_model()
    
    async def ProcessImage(self, request, context):
        """
        Processes OCR request via gRPC.
        
        Args:
            request: gRPC request containing image URL
            context: gRPC context for request handling
            
        Returns:
            xocr_pb2.OCRResponse: Response with results or error
            
        Note:
            Uses xcommon_pb2.Status for standardized status reporting
        """
        try:
            # Process image
            image = await download_image(request.img_url)
            result = await self.model.process_image(image)
            
            # Return successful response
            return xocr_pb2.OCRResponse(
                status=xcommon_pb2.Status(success=True),
                result=result
            )
        except Exception as e:
            logger.error(f"XOCR gRPC Error: {str(e)}")
            return xocr_pb2.OCRResponse(
                status=xcommon_pb2.Status(
                    success=False,
                    error=str(e)
                )
            )
