"""
Test script for XLogger functionality.
This script demonstrates how to use the MongoDB log query capabilities.

Usage:
    Run from project root:
    python -m examples.test_xlogger
"""

from xpertagent.utils.xlogger import LogMongoDBClient, logger

def test_advanced_query():
    """
    Test advanced log querying capabilities.
    Demonstrates how to use multiple query parameters and filters.
    """
    try:
        # Initialize MongoDB log client
        logger.info("Initializing MongoDB log client...")
        log_client = LogMongoDBClient()

        # Define query parameters
        query_params = {
            "text": None,              # Text to search in log messages
            "level": "INFO",           # Log level to filter
            "category": "test_xocr_tool.py",  # Source file/category
            "start_time": "2024-11-11 00:00:00",  # Query start time
            "end_time": "2024-12-00 00:00:00",    # Query end time
            "tags": None,              # Specific tags to filter
            "env": "dev",              # Environment (dev/prod)
            "limit": 100               # Maximum number of results
        }

        # Perform advanced query
        logs = log_client.find_logs_advanced(**query_params)

        # Process results
        logger.info(f"Found {len(logs)} matching logs")
        print("=" * 30)
        for log in logs:
            print(log)
        print("=" * 30)

    except Exception as e:
        logger.error(f"Error during log query: {str(e)}")
        raise

def main():
    """Main function to run logger tests"""
    logger.info("Starting logger test...")
    test_advanced_query()
    logger.info("Logger test completed.")

if __name__ == "__main__":
    main()