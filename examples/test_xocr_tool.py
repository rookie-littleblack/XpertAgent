"""
Test script for XpertOCR Tool.
This script demonstrates how to use the XpertOCR tool for both single URL and multiple URLs embedded in text.

IMPORTANT: Before running this test script, please ensure that the xocr_service in this project 
is already started and running properly. The OCR service must be active for this test to work.
"""

from xpertagent.tools import XpertOCRTool
from xpertagent.utils.xlogger import logger

def test_single_url():
    """Test OCR with a single image URL"""
    url = "https://www.tsinghua.edu.cn/image/lishiyange03.jpg"
    result = ocr_tool.execute(url)
    return result

def test_multiple_urls():
    """Test OCR with text containing multiple image URLs"""
    text = """
    This is a text containing multiple images:
    1. https://www.tsinghua.edu.cn/image/lishiyange03.jpg
    2. Here's the second image https://www.tsinghua.edu.cn/image/lishiyange03.jpg
    3. And the third one https://www.tsinghua.edu.cn/image/lishiyange03.jpg
    """
    result = ocr_tool.execute(text)
    return result

def process_result(result, test_name):
    """Process and log OCR result"""
    if result.success:
        logger.info(f"{test_name} - XOCR Results: `{result.result}`")
        logger.info(f"{test_name} - Metadata: `{result.metadata}`")
    else:
        logger.error(f"{test_name} - Error: `{result.error}`")

def main():
    """Main function to run OCR tests"""
    logger.info(">>> [test_xocr_tool.py] Starting XOCR tests...")

    # Initialize the OCR tool
    global ocr_tool
    ocr_tool = XpertOCRTool()

    # Test 1: Single URL (commented out by default)
    logger.info(">>> [test_xocr_tool.py] Running Single URL Test...")
    result = test_single_url()
    process_result(result, "Single URL Test")

    # # Test 2: Multiple URLs in text
    # logger.info(">>> [test_xocr_tool.py] Running Multiple URLs Test...")
    # result = test_multiple_urls()
    # process_result(result, "Multiple URLs Test")

    # Log completion
    logger.info(">>> [test_xocr_tool.py] XOCR tests completed.")

if __name__ == "__main__":
    main()