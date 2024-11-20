"""
XOCR Agent: An intelligent agent for performing Optical Character Recognition (XOCR) 
on images and extracting structured data.
"""

import argparse

from xpertagent.core.agent import XpertAgent
from xpertagent.utils.xlogger import logger
from xpertagent.prompts.p_xocr import PROMPTS_FOR_XAGENT_OCR_DESC

def main(input_text: str):
    """
    Main function to demonstrate XOCR Agent capabilities.
    
    This function:
    1. Creates an XOCR agent instance
    2. Processes the input text containing image URLs
    3. Returns structured XOCR results
    
    Args:
        input_text (str): User input text containing image URLs or XOCR task description
    """
    logger.info(">>> [xagent_ocr.py] Initializing XOCR agent...")

    # Create an agent instance with XOCR capabilities
    agent = XpertAgent(name="XAgent_OCR", description=PROMPTS_FOR_XAGENT_OCR_DESC)
    
    # Process input and get response
    logger.info(f">>> [xagent_ocr.py] Processing user input: `{input_text}`...")
    response = agent.run(input_text)
    logger.info(f">>> [xagent_ocr.py] XOCR processing completed. Response: `{response}`")

    # Log completion status
    logger.info(">>> [xagent_ocr.py] XOCR agent task completed successfully.")

if __name__ == "__main__":
    # Set up command line argument parser
    parser = argparse.ArgumentParser(
        description="XOCR Agent - Intelligent XOCR Processing Tool",
        epilog="""
        Example usage:
        python -m xpertagent.agents.xagent_ocr --input_text "Please extract text from this image: https://www.tsinghua.edu.cn/image/lishiyange03.jpg"
        """
    )
    
    # Add command line arguments
    parser.add_argument(
        "--input_text",
        type=str,
        required=True,
        help="Input text containing image URLs and XOCR task description"
    )

    # Parse command line arguments
    args = parser.parse_args()

    # Execute main function
    main(args.input_text)
