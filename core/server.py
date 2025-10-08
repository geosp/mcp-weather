"""
Base MCP server implementation for reusable server components

Provides abstract base classes and factory functions for creating MCP servers
that can be easily extended for different service types (weather, translations, etc.)
while maintaining consistent authentication, error handling, and configuration.
"""

import abc
import logging
import sys
from typing import Any, List, Optional, Type, TypeVar

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP
import uvicorn
import flatdict

from .config import BaseServerConfig


# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Get module logger
logger = logging.getLogger(__name__)

# Type variables
T = TypeVar('T')
ConfigT = TypeVar('ConfigT', bound=BaseServerConfig)


class BaseService(abc.ABC):
    """
    Abstract base class for MCP services
    
    Service classes handle business logic and should be independent of the
    transport mechanism (HTTP, stdio) and protocol (REST, MCP).
    """
    
    @abc.abstractmethod
    def initialize(self) -> None:
        """
        Initialize the service
        
        This method is called during application startup to prepare
        any resources needed by the service.
        """
        pass
    
    @abc.abstractmethod
    def get_service_name(self) -> str:
        """
        Get the name of this service
        
        Returns:
            Name of the service (used for MCP tools namespace)
        """
        pass
    
    @abc.abstractmethod
    def register_mcp_tools(self, mcp: FastMCP) -> None:
        """
        Register MCP tools for this service
        
        This method should register all MCP tools provided by the service.
        
        Args:
            mcp: FastMCP instance to register tools with
        """
        pass
    
    def cleanup(self) -> None:
        """
        Clean up service resources
        
        This method is called during application shutdown to release
        any resources held by the service. Default implementation does nothing.
        """
        pass


class BaseMCPServer(abc.ABC):
    """
    Base class for MCP servers
    
    Provides common functionality for MCP servers including:
    - Configuration loading and validation
    - Server startup in different modes (stdio, http)
    - Authentication integration
    - Service registration
    
    This class should be extended for specific service types.
    """
    
    def __init__(self, config: BaseServerConfig, service: BaseService):
        """
        Initialize the MCP server
        
        Args:
            config: Server configuration
            service: Service instance to expose via MCP
        """
        self.config = config
        self.service = service
        self._mcp_app: Optional[FastMCP] = None
        self._fastapi_app: Optional[FastAPI] = None
        # Create flattened configuration for easier access
        try:
            # Convert config to dict if it's a Pydantic model
            if hasattr(config, 'model_dump'):  # Pydantic v2
                config_dict = config.model_dump()
            elif hasattr(config, 'dict'):  # Pydantic v1
                config_dict = config.dict()
            else:
                # Try a direct conversion or fall back to empty dict
                config_dict = dict(config) if config else {}
            
            self._flat_config = flatdict.FlatDict(config_dict, delimiter='.')
        except Exception as e:
            logger.warning(f"Failed to create flattened config: {e}")
            self._flat_config = flatdict.FlatDict({}, delimiter='.')
            
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using flattened dot notation
        
        Args:
            key: Configuration key using dot notation (e.g., 'server.transport')
            default: Default value to return if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        try:
            return self._flat_config.get(key, default)
        except Exception:
            # Fallback to direct attribute access if needed
            parts = key.split('.')
            current = self.config
            
            try:
                for part in parts:
                    if not hasattr(current, part):
                        return default
                    current = getattr(current, part)
                return current
            except (AttributeError, KeyError):
                return default
    
    @property
    @abc.abstractmethod
    def service_title(self) -> str:
        """
        Get the title for this MCP service (shown in API docs)
        """
        pass
    
    @property
    @abc.abstractmethod
    def service_description(self) -> str:
        """
        Get the description for this MCP service (shown in API docs)
        """
        pass
    
    @property
    @abc.abstractmethod
    def service_version(self) -> str:
        """
        Get the version string for this MCP service
        """
        pass
    
    @property
    @abc.abstractmethod
    def allowed_cors_origins(self) -> List[str]:
        """
        Get list of allowed origins for CORS
        """
        pass
    
    @abc.abstractmethod
    def create_auth_provider(self) -> Optional[Any]:
        """
        Create an authentication provider for this server
        
        Returns:
            Authentication provider or None if not using authentication
        """
        pass
    
    @abc.abstractmethod
    def create_router(self) -> Any:
        """
        Create a FastAPI router for REST endpoints
        
        Returns:
            Router with REST API endpoints
        """
        pass
    
    @abc.abstractmethod
    def register_exception_handlers(self, app: FastAPI) -> None:
        """
        Register exception handlers for the FastAPI application
        
        Args:
            app: FastAPI application to register handlers with
        """
        pass
    
    def create_mcp_app(self) -> FastMCP:
        """
        Create FastMCP application for this server
        
        Returns:
            Configured FastMCP application with tools registered
        """
        # Initialize authentication if configured and enabled
        auth_provider = None
        # Check for transport using the flattened configuration
        transport = self.get_config("server.transport", self.get_config("transport", "stdio"))
        auth_enabled = self.get_config("server.auth_enabled", self.get_config("auth_enabled", True))
        
        if transport == "http" and auth_enabled:
            logger.info("Authentication is enabled for HTTP transport")
            auth_provider = self.create_auth_provider()
        elif transport == "http" and not auth_enabled:
            logger.warning("Authentication is DISABLED for HTTP transport (AUTH_ENABLED=false)")
            logger.warning("This is not recommended for production environments")
        
        # Create MCP app
        mcp = FastMCP(
            self.service.get_service_name(),
            auth=auth_provider
        )
        
        # Register service tools
        self.service.register_mcp_tools(mcp)
        
        logger.info(f"FastMCP application created for {self.service.get_service_name()}")
        return mcp
    
    def create_fastapi_app(self, mcp: FastMCP) -> FastAPI:
        """
        Create FastAPI application with MCP mounted and REST routes
        
        Args:
            mcp: FastMCP application to mount
            
        Returns:
            Configured FastAPI application
        """
        # Get MCP ASGI app
        mcp_app = mcp.http_app()
        
        # Create FastAPI app
        app = FastAPI(
            title=self.service_title,
            description=self.service_description,
            version=self.service_version,
            lifespan=mcp_app.lifespan,  # Use MCP's lifespan for proper session management
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.allowed_cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
        
        # Create and include REST routes
        router = self.create_router()
        app.include_router(router)
        
        # Mount MCP server at /mcp - using the HTTP app implementation
        app.mount("/mcp", mcp_app)
        
        # Add exception handlers
        self.register_exception_handlers(app)
        
        logger.info("FastAPI application created with MCP mounted at /mcp")
        return app
    
    def validate_configuration(self) -> None:
        """
        Validate server configuration
        
        This method should be overridden to perform service-specific
        configuration validation.
        
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    def run_mcp_only(self) -> None:
        """
        Run MCP-only server (no REST API endpoints)
        """
        # Get host and port using flattened configuration
        host = self.get_config("server.host", self.get_config("host", "0.0.0.0"))
        port = self.get_config("server.port", self.get_config("port", 3000))
        
        # Only log if not already logged by a child class
        if not hasattr(self, "_already_logged"):
            logger.info(f"Starting {self.service_title} in MCP-only mode")
            logger.info("=" * 70)
            logger.info(f"MCP Endpoint: http://{host}:{port}/mcp")
            logger.info("=" * 70)
            self._already_logged = True
        
        # Create MCP app
        self._mcp_app = self.create_mcp_app()
        
        # Important: We need to directly run the HTTP app from FastMCP
        # When in MCP-only mode, FastMCP should be directly run as a standalone app
        # The http_app() method returns an ASGI app that can be run directly with uvicorn
        asgi_app = self._mcp_app.http_app()
        
        # Store this for reference
        self._fastapi_app = None
        
        # Run with uvicorn
        uvicorn.run(
            asgi_app,
            host=host,
            port=port,
            log_level="info"
        )
        
        # Run with uvicorn
        uvicorn.run(
            self._fastapi_app,
            host=host,
            port=port,
            log_level="info"
        )
    
    def run_rest_and_mcp(self) -> None:
        """
        Run FastAPI + MCP server (REST endpoints + MCP protocol)
        """
        # Get host and port using flattened configuration
        host = self.get_config("server.host", self.get_config("host", "0.0.0.0"))
        port = self.get_config("server.port", self.get_config("port", 3000))
        
        # Only log if not already logged by a child class
        if not hasattr(self, "_already_logged"):
            logger.info(f"Starting {self.service_title} with REST API + MCP")
            logger.info("=" * 70)
            logger.info(f"Server: http://{host}:{port}")
            logger.info(f"API Docs: http://{host}:{port}/docs")
            logger.info(f"Health Check: http://{host}:{port}/health")
            logger.info(f"MCP Endpoint: http://{host}:{port}/mcp")
            logger.info("=" * 70)
            self._already_logged = True
        
        # Create MCP app
        self._mcp_app = self.create_mcp_app()
        
        # Create FastAPI app with MCP mounted
        self._fastapi_app = self.create_fastapi_app(self._mcp_app)
        
        # Run with uvicorn
        uvicorn.run(
            self._fastapi_app,
            host=host,
            port=port,
            log_level="info"
        )
    
    def create_app(self) -> FastAPI:
        """
        Factory function to create FastAPI application
        
        This is useful for deployment with ASGI servers like gunicorn
        
        Returns:
            Configured FastAPI application with MCP mounted
        """
        self.validate_configuration()
        
        mcp = self.create_mcp_app()
        app = self.create_fastapi_app(mcp)
        
        self._mcp_app = mcp
        self._fastapi_app = app
        
        return app
    
    def run(self) -> None:
        """
        Run the server based on configuration
        
        This method determines the mode (stdio, http) and type (mcp-only, rest+mcp)
        based on the configuration and starts the appropriate server.
        """
        try:
            # Validate configuration
            self.validate_configuration()
            
            # Initialize service
            self.service.initialize()
            
            # Determine server mode using flattened configuration
            transport = self.get_config("server.transport", self.get_config("transport", "stdio"))
            mcp_only = self.get_config("server.mcp_only", self.get_config("mcp_only", False))
            
            # Start server based on configuration
            if mcp_only:
                # Pure MCP protocol (stdio or HTTP)
                self.run_mcp_only()
            else:
                # REST API + MCP protocol (always HTTP)
                self.run_rest_and_mcp()
                
        except KeyboardInterrupt:
            logger.info("\nShutdown requested by user")
            sys.exit(0)
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Fatal error during startup: {e}", exc_info=True)
            sys.exit(1)
        finally:
            # Ensure service cleanup is called
            if hasattr(self, "service"):
                self.service.cleanup()


# Type-safe factory function for creating server instances
def create_server(
    server_class: Type[T],
    config: Any,
    service: BaseService
) -> T:
    """
    Create a server instance with the specified configuration and service
    
    Args:
        server_class: Class to instantiate (must extend BaseMCPServer)
        config: Server configuration
        service: Service instance to expose
        
    Returns:
        Configured server instance
    """
    return server_class(config, service)