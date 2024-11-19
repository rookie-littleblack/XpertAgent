"""
XpertOCR Service: A FastAPI-based service for XOCR using GOT-OCR2_0 model.
This service provides an HTTP endpoint for performing XOCR on images via URLs.
"""

import os
import io
import torch
import uvicorn
import requests

from PIL import Image
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from GOT.model import GOTQwenForCausalLM
from transformers import AutoTokenizer
from GOT.utils.utils import disable_torch_init, KeywordsStoppingCriteria
from fastapi.responses import JSONResponse
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

app = FastAPI()

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

# Initialize global model instance
model = None

@app.on_event("startup")
async def startup_event():
    """
    Startup event handler that initializes the XOCR model when the service starts.
    Raises an exception if the model path doesn't exist.
    """
    global model
    model_path = os.path.join(XAPP_PATH, "data/models/GOT-OCR2_0")
    if not os.path.exists(model_path):
        raise Exception(f"GOT-OCR2_0 model path does not exist: `{model_path}`!")
    model = XOCRModel(model_path)

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

@app.post("/xocr")
async def xocr_endpoint(request: Request) -> JSONResponse:
    """
    XOCR endpoint that processes incoming image URLs and returns extracted text.
    
    Args:
        request (Request): FastAPI request object containing image URL
        
    Returns:
        JSONResponse: XOCR results or error message
    """
    try:
        # Print raw request body for debugging
        body = await request.body()
        logger.info("Raw request body:", body)
        
        # Print JSON request data
        json_data = await request.json()
        logger.info("JSON request:", json_data)
        
        # Print request headers
        logger.info("Headers:", request.headers)
        
        # Process the request
        xocr_request = XOCRRequest(**json_data)
        image = await download_image(xocr_request.img_url)
        result = await model.process_image(image)

        # Return the result as a JSON response
        result = {"success": True, "result": result}
        logger.info("XOCR Result:", result)
        return JSONResponse(content=result)
    except Exception as e:
        result = {"success": False, "error": str(e)}
        logger.error("XOCR Error:", result)
        return JSONResponse(
            status_code=500,
            content=result
        )

# Usage: Navigate to this project's directory and run:
# python ./xpertagent/tools/xpert_ocr/xocr_service.py
if __name__ == "__main__":
    uvicorn.run(
        app, 
        host=os.getenv("XOCR_SERVICE_HOST", "127.0.0.1"), 
        port=int(os.getenv("XOCR_SERVICE_PORT", 7835))
    )
