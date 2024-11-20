"""
XService: Unified Service Manager for HTTP and gRPC Services.

This module provides:
1. Dynamic service initialization and management
2. Support for both HTTP (FastAPI) and gRPC protocols
3. Resource-efficient lazy loading of services
4. Comprehensive error handling and logging

Key Features:
- Flexible service type configuration
- Independent service initialization
- Thread pool management
- Graceful shutdown handling

Technical Details:
- Uses FastAPI for HTTP services
- Implements async gRPC server
- Manages shared thread pool
- Supports command-line deployment
"""
import uvicorn
import grpc
import asyncio

from typing import Dict, List
from fastapi import FastAPI
from concurrent.futures import ThreadPoolExecutor
from xpertagent.utils.xlogger import logger
from xpertagent.config.settings import settings

class XService:
    """
    Unified Service Manager that handles both HTTP and gRPC services.
    
    This class provides:
    1. Lazy loading of services
    2. Protocol-specific initialization
    3. Resource management
    4. Service lifecycle control
    
    Attributes:
        service_type (str): Type of service ("http" or "grpc")
        _services (Dict[str, bool]): Service initialization status
        executor (ThreadPoolExecutor): Shared thread pool
        app (FastAPI): FastAPI instance for HTTP services
        _server (grpc.aio.Server): gRPC server instance
    """
    
    def __init__(self, service_type: str = "http"):
        """
        Initialize the service manager.
        
        Args:
            service_type (str): Service protocol type
            
        Raises:
            ValueError: If service_type is invalid
        """
        self.service_type = service_type
        self._services = {
            "xocr": False,
            "xmedocr": False
        }
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        if service_type == "http":
            self.app = FastAPI()
        elif service_type == "grpc":
            self._server = None
        else:
            raise ValueError(f"Unknown service type: {service_type}")
    
    async def init_service(self, service_name: str):
        """
        Lazily initialize a specific service.
        
        Args:
            service_name (str): Name of service to initialize
            
        Raises:
            ValueError: If service is not registered
            
        Note:
            Implements lazy loading pattern
        """
        if service_name not in self._services:
            raise ValueError(f"Unknown service: {service_name}")
            
        if self._services[service_name]:
            return
            
        if self.service_type == "http":
            await self._init_http_service(service_name)
        else:
            await self._init_grpc_service(service_name)
            
        self._services[service_name] = True
    
    async def _init_http_service(self, service_name: str):
        """
        Initialize HTTP service router.
        
        Args:
            service_name (str): Name of service to initialize
            
        Note:
            Dynamically imports and configures FastAPI routers
        """
        if service_name == "xocr":
            from xpertagent.tools.xpert_ocr.xocr_service import get_xocr_router
            router = await get_xocr_router(self.executor)
            self.app.include_router(router)
        elif service_name == "xmedocr":
            from xpertagent.apps.XMedOCR.XMedOCR import get_xmedocr_router
            router = await get_xmedocr_router(self.executor)
            self.app.include_router(router)
    
    async def _init_grpc_service(self, service_name: str):
        """
        Initialize gRPC service.
        
        Args:
            service_name (str): Name of service to initialize
            
        Note:
            Dynamically imports and registers gRPC servicers
        """
        if service_name == "xocr":
            from xpertagent.tools.xpert_ocr.xocr_service import XOCRServicer
            from xpertagent.protos import xocr_pb2_grpc
            servicer = XOCRServicer()
            xocr_pb2_grpc.add_XOCRServiceServicer_to_server(servicer, self._server)
            logger.info("XOCR gRPC service initialized")
        elif service_name == "xmedocr":
            from xpertagent.apps.XMedOCR.XMedOCR import XMedOCRServicer
            from xpertagent.protos import xmedocr_pb2_grpc
            servicer = XMedOCRServicer()
            xmedocr_pb2_grpc.add_XMedOCRServiceServicer_to_server(servicer, self._server)
            logger.info("XMedOCR gRPC service initialized")
    
    def run(self, services: List[str]):
        """
        Main entry point for running the service.
        
        This method:
        1. Creates and manages event loop
        2. Initializes requested services
        3. Starts appropriate server type
        4. Handles graceful shutdown
        
        Args:
            services (List[str]): List of services to start
            
        Note:
            Implements comprehensive error handling and cleanup
        """
        async def _run_server():
            """
            Internal async server runner.
            
            This function:
            1. Initializes server based on protocol
            2. Configures all requested services
            3. Starts server and handles lifecycle
            
            Raises:
                Exception: For any server initialization or runtime errors
            """
            try:
                # Initialize gRPC server if needed
                if self.service_type == "grpc":
                    self._server = grpc.aio.server(
                        options=[
                            ('grpc.max_send_message_length', 50 * 1024 * 1024),
                            ('grpc.max_receive_message_length', 50 * 1024 * 1024)
                        ]
                    )

                # Initialize all services
                for service in services:
                    await self.init_service(service)

                if self.service_type == "http":
                    # Configure and start HTTP server
                    config = uvicorn.Config(
                        app=self.app,
                        host=settings.XHTTP_SERVICE_HOST,
                        port=settings.XHTTP_SERVICE_PORT
                    )
                    server = uvicorn.Server(config)
                    await server.serve()
                else:
                    # Configure and start gRPC server
                    addr = f"{settings.XGRPC_SERVICE_HOST}:{settings.XGRPC_SERVICE_PORT}"
                    self._server.add_insecure_port(addr)
                    logger.info(f"Starting gRPC server on {addr}")
                    
                    await self._server.start()
                    logger.info("gRPC server started successfully")
                    
                    # Wait for termination
                    await self._server.wait_for_termination()
            except Exception as e:
                logger.error(f"Service Error: {str(e)}")
                if self.service_type == "grpc" and self._server:
                    await self._server.stop(5)
                raise
            finally:
                if self.service_type == "grpc" and self._server:
                    await self._server.stop(0)

        # Create and configure event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Run server in event loop
            loop.run_until_complete(_run_server())
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        except Exception as e:
            logger.error(f"Service encountered an error: {e}")
        finally:
            # Clean up resources
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

if __name__ == "__main__":
    """
    Command-line deployment entry point.
    
    This section provides:
    1. Command-line argument parsing
    2. Service type configuration
    3. Service initialization and startup
    
    Usage:
        python -m xpertagent.services.xservice -t [http|grpc] -s [service_names]

    Examples:
        python -m xpertagent.services.xservice -t grpc -s xocr xmedocr
        python -m xpertagent.services.xservice -t http -s xocr xmedocr
    """
    import argparse
    
    # Configure argument parser
    parser = argparse.ArgumentParser(
        description='Start services with specified components'
    )
    parser.add_argument(
        '--type', '-t',
        choices=['http', 'grpc'],
        default='http',
        help='Type of service to start (http or grpc)'
    )
    parser.add_argument(
        '--services', '-s',
        nargs='+',
        default=['xocr'],
        help='List of services to start (e.g., xocr xmedocr)'
    )
    
    args = parser.parse_args()
    
    # Initialize and start services
    service = XService(args.type)
    logger.info(f"Starting {args.type.upper()} services: {args.services}")
    
    # Run the service
    service.run(args.services)