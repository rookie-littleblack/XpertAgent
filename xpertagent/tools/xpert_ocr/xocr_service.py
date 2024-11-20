"""
XpertOCR Service: A FastAPI-based service for XOCR using GOT-OCR2_0 model.
This service provides an HTTP endpoint for performing XOCR on images via URLs.
"""

import os
import io
import torch
import asyncio
import requests

from PIL import Image
from dotenv import load_dotenv
from fastapi import FastAPI, Request, APIRouter
from pydantic import BaseModel
from GOT.model import GOTQwenForCausalLM
from transformers import AutoTokenizer
from GOT.utils.utils import disable_torch_init, KeywordsStoppingCriteria
from fastapi.responses import JSONResponse
from concurrent.futures import ThreadPoolExecutor
from GOT.utils.conversation import conv_templates, SeparatorStyle
from xpertagent.utils.xlogger import logger
from GOT.model.plug.blip_process import BlipImageEvalProcessor

# Load environment variables from .env file
load_dotenv()

# Base path configuration for the application
XAPP_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class XOCRRequest(BaseModel):
    """
    Request model for XOCR endpoint.
    Defines the structure of incoming XOCR requests.
    """
    img_url: str

    class Config:
        extra = "allow"  # Allow additional fields in request

# Define constants for image tokens
DEFAULT_IMAGE_TOKEN = "<image>"
DEFAULT_IMAGE_PATCH_TOKEN = '<imgpad>'
DEFAULT_IM_START_TOKEN = '<img>'
DEFAULT_IM_END_TOKEN = '</img>'

class XOCRModel:
    """
    XOCR Model wrapper class that handles the initialization and inference of the GOT-OCR2_0 model.
    Provides methods for processing images and generating XOCR results.
    """
    
    def __init__(self, model_name: str):
        """
        Initialize the XOCR model with the specified model path.
        
        Args:
            model_name (str): Path to the pre-trained model
        """
        disable_torch_init()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = GOTQwenForCausalLM.from_pretrained(
            model_name, 
            low_cpu_mem_usage=True,
            device_map='cuda',
            use_safetensors=True,
            pad_token_id=151643
        ).eval()
        self.model.to(device='cuda', dtype=torch.bfloat16)
        
        # Initialize image processors for different resolutions
        self.image_processor = BlipImageEvalProcessor(image_size=1024)
        self.image_processor_high = BlipImageEvalProcessor(image_size=1024)
        
    async def process_image(self, image: Image.Image) -> str:
        """
        Process an image and generate XOCR results.
        
        Args:
            image (Image.Image): PIL Image object to process
            
        Returns:
            str: Extracted text from the image
        """
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
                stopping_criteria=[stopping_criteria]
            )

        # Decode and clean up the output
        outputs = self.tokenizer.decode(output_ids[0, input_ids.shape[1]:]).strip()
        if outputs.endswith(stop_str):
            outputs = outputs[:-len(stop_str)]
            
        return outputs.strip()

async def download_image(url: str) -> Image.Image:
    """
    Download an image from a URL and convert it to PIL Image format.
    
    Args:
        url (str): URL of the image to download
        
    Returns:
        Image.Image: Downloaded image in PIL format
        
    Raises:
        Exception: If download fails or image processing fails
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Failed to download image")
    return Image.open(io.BytesIO(response.content)).convert('RGB')

async def get_xocr_router(executor: ThreadPoolExecutor = None) -> APIRouter:
    """
    Create and return the OCR service router with thread pool support.
    
    Args:
        executor: ThreadPoolExecutor for handling heavy processing tasks
    
    Returns:
        APIRouter: FastAPI router configured with XOCR endpoints
        
    Raises:
        Exception: If the required model path does not exist
    """
    logger.info(">>> Initializing XOCR service...")
    router = APIRouter(prefix="/xocr", tags=["XOCR Services"])
    
    # Initialize the model
    model_path = os.path.join(XAPP_PATH, "data/models/GOT-OCR2_0")
    if not os.path.exists(model_path):
        raise Exception(f"GOT-OCR2_0 model path does not exist: `{model_path}`!")
    model = XOCRModel(model_path)
    logger.info(f">>> XOCR Model initialized: `{model_path}`")

    async def process_xocr_request(data: dict) -> str:
        """Internal method that can be called directly or via API"""
        image = await download_image(data["img_url"])
        # Run heavy processing in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            lambda: asyncio.run(model.process_image(image))  # 注意这里的修改
        )
        return result
    
    @router.post("/process")
    async def xocr_endpoint(request: Request) -> JSONResponse:
        """
        XOCR endpoint that processes incoming image URLs and returns extracted text.
        
        Args:
            request (Request): FastAPI request object containing image URL
            
        Returns:
            JSONResponse: XOCR results or error message
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
    
    # Expose internal processing method for direct calls
    router.process_xocr = process_xocr_request
    return router

# Standalone deployment section
if __name__ == "__main__":
    """
    Standalone deployment entry point for XOCR service.
    This section allows the XOCR service to be run independently without the main application.
    
    Usage:
        Navigate to the project root directory and run:
        python -m xpertagent.tools.xpert_ocr.xocr_service
        
    Note:
        This will start only the XOCR service on the configured host and port.
        For production deployment, consider using the main application with multiple services.
    """
    import asyncio
    
    app = FastAPI()
    
    async def init():
        """
        Initialize and configure the standalone FastAPI application.
        This function sets up the XOCR router for independent deployment.
        """
        router = await get_xocr_router()
        app.include_router(router)
    
    asyncio.run(init())
