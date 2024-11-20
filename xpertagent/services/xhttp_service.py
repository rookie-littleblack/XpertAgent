import uvicorn
import asyncio

from typing import Dict
from fastapi import FastAPI
from concurrent.futures import ThreadPoolExecutor
from xpertagent.utils.xlogger import logger
from xpertagent.config.settings import settings

class XHTTPService:
    """
    HTTP Service Manager that handles multiple API services with lazy loading.
    Each service can be initialized independently when needed.
    """
    
    def __init__(self):
        """Initialize the HTTP service manager with FastAPI application"""
        self.app = FastAPI()
        self._routers: Dict[str, bool] = {
            "xocr": False,
            "xmedocr": False
        }
        # Create thread pool for handling OCR requests
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    async def init_router(self, router_name: str):
        """
        Lazily initialize a specific router service.
        
        Args:
            router_name (str): Name of the router service to initialize
            
        Raises:
            ValueError: If the router_name is not registered in self._routers
        """
        if router_name not in self._routers:
            raise ValueError(f"Unknown router service: {router_name}")
            
        if self._routers[router_name]:
            return  # Already initialized
            
        if router_name == "xocr":
            # Dynamically import XOCR service to avoid loading model unnecessarily
            from xpertagent.tools.xpert_ocr.xocr_service import get_xocr_router
            router = await get_xocr_router(self.executor)  # Pass executor to router
            self.app.include_router(router)
            self._routers["xocr"] = True
            
        elif router_name == "xmedocr":
            # Initialize xmedocr services
            from xpertagent.apps.XMedOCR.XMedOCR import get_xmedocr_router
            router = await get_xmedocr_router(self.executor)  # Pass executor to router
            self.app.include_router(router)
            self._routers["xmedocr"] = True
    
    async def start(self, services: list[str]):
        """
        Start the specified services and run the FastAPI application.
        
        Args:
            services (list[str]): List of service names to initialize and start
        """
        # Initialize requested services
        for service in services:
            await self.init_router(service)
            
        # Configure uvicorn server
        config = uvicorn.Config(
            app=self.app,
            host=settings.XHTTP_SERVICE_HOST,
            port=settings.XHTTP_SERVICE_PORT
        )
        
        # Create and start server
        server = uvicorn.Server(config)
        await server.serve()

# Command-line deployment section
if __name__ == "__main__":
    """
    Command-line deployment entry point for HTTP services.
    
    Usage:
        python -m xpertagent.services.xhttp_service --services xocr xmedocr
        python -m xpertagent.services.xhttp_service -s xocr xmedocr
        
    Arguments:
        --services, -s: List of services to start (space-separated)
                       Available services: xocr, xmedocr
    """
    import asyncio
    import argparse
    
    # Configure command line argument parser
    parser = argparse.ArgumentParser(
        description='Start HTTP services with specified components'
    )
    parser.add_argument(
        '--services', '-s',
        nargs='+',
        default=['xocr'],
        help='List of services to start (e.g., xocr xmedocr)'
    )
    
    # Parse command line arguments
    args = parser.parse_args()
    
    # Initialize and start services
    service = XHTTPService()
    logger.info(f"Starting services: {args.services}")
    asyncio.run(service.start(args.services))