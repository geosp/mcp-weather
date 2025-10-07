"""
auth_provider.py - Authentik authentication adapter for Weather MCP Server

This module adapts the existing core.auth infrastructure for use with FastMCP.
It bridges between FastMCP's auth protocol and your existing Authentik client.
"""

import logging
from typing import Optional, Dict, Any
import flatdict
from fastmcp.server.auth import AuthProvider

# Import your existing auth infrastructure
try:
    from core.auth import get_token_from_header, get_authentik_client
    from core.authentik_client import AuthentikClient
    CORE_AUTH_AVAILABLE = True
except ImportError:
    CORE_AUTH_AVAILABLE = False
    # Fallback if core modules not available
    get_token_from_header = None
    get_authentik_client = None
    AuthentikClient = None

from .config import get_config

logger = logging.getLogger(__name__)


class AuthInfo:
    """
    Flexible authentication information that accepts any attributes.
    
    This class dynamically accepts any field returned by Authentik's token
    introspection and makes them accessible as attributes.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize with any keyword arguments.
        
        Args:
            **kwargs: Any authentication fields from token introspection
        """
        # Set all provided attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        # Ensure required attributes have defaults
        if not hasattr(self, 'client_id'):
            self.client_id = ""
        if not hasattr(self, 'scopes'):
            self.scopes = []
        if not hasattr(self, 'expires_at'):
            self.expires_at = None
    
    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"AuthInfo({attrs})"


class AuthentikAuthProvider(AuthProvider):
    """
    Authentik authentication provider for FastMCP
    
    This adapter wraps your existing AuthentikClient to work with FastMCP's
    auth protocol. It validates Bearer tokens and returns user information
    that FastMCP can use for authorization.
    
    Architecture:
        FastMCP Auth Protocol -> AuthentikAuthProvider -> Your AuthentikClient -> Authentik API
    
    Usage:
        auth_provider = AuthentikAuthProvider()
        mcp = FastMCP("weather", auth=auth_provider)
    """
    
    # Required by FastMCP - scopes needed for authentication
    required_scopes: list = []
    
    # Required by FastMCP - base URL for OAuth metadata
    base_url: Optional[str] = None
    
    def __init__(self):
        """
        Initialize Authentik auth provider
        
        Uses your existing get_authentik_client() to get a configured client.
        """
        if not CORE_AUTH_AVAILABLE:
            raise RuntimeError(
                "Core auth modules not available. "
                "Ensure core.auth and core.authentik_client are accessible."
            )
        
        # Get Authentik client using your existing factory function
        self.client = get_authentik_client()
        logger.info("Initialized AuthentikAuthProvider for FastMCP using core.auth")
    
    async def __call__(self, token: str) -> Optional[AuthInfo]:
        """
        Verify a Bearer token with Authentik (FastMCP auth callback)
        
        This method is called by FastMCP's auth middleware to validate tokens.
        It uses your existing AuthentikClient.validate_token() method.
        
        Args:
            token: Bearer token string to verify
            
        Returns:
            AuthInfo object with user info if valid, None if invalid
            
        Note:
            FastMCP expects this to be an async callable that returns
            an object with user info or None for invalid tokens.
        """
        return await self.verify_token(token)
    
    async def verify_token(self, token: str) -> Optional[AuthInfo]:
        """
        Verify a Bearer token with Authentik
        
        This is the actual implementation called by both __call__ and
        FastMCP's authentication middleware.
        
        Args:
            token: Bearer token string to verify
            
        Returns:
            AuthInfo object with user info if valid, None if invalid
        """
        try:
            # Use your existing token validation
            result = self.client.validate_token(token)
            
            if not result.get("active"):
                logger.warning(f"Invalid or inactive token: {token[:20]}...")
                return None
            
            # Extract user information from your auth result
            user = flatdict.FlatDict(result.get("user", {}), delimiter='.')
            username = user.get("user.username")
            
            logger.info(f"✓ Authenticated MCP request for user: {username}")
            
            # Get token metadata
            expires_at = result.get("exp")
            scopes_str = result.get("scope", "")
            scopes = scopes_str.split() if scopes_str else []
            client_id = result.get("client_id", "")
            
            # Return flexible AuthInfo with all available fields
            return AuthInfo(
                user=username,
                user_id=str(user.get("pk", "")),
                email=user.get("email", ""),
                name=user.get("name", ""),
                is_active=user.get("is_active", False),
                groups=user.get("groups", []),
                client_id=client_id,
                scopes=scopes,
                expires_at=expires_at,
                # Pass through any other fields from Authentik
                **{k: v for k, v in result.items() if k not in ['active', 'user']}
            )
            
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None


# ============================================================================
# Helper Functions
# ============================================================================

def create_mcp_auth_provider() -> AuthentikAuthProvider:
    """
    Factory function to create MCP auth provider
    
    Returns:
        AuthentikAuthProvider instance for use with FastMCP
        
    Raises:
        RuntimeError: If core auth modules not available
    """
    return AuthentikAuthProvider()


# Global auth provider instance (initialized by server startup)
_mcp_auth_provider: Optional[AuthentikAuthProvider] = None


def get_mcp_auth_provider() -> AuthentikAuthProvider:
    """
    Get or create global MCP auth provider
    
    Lazily initializes the auth provider on first access.
    
    Returns:
        AuthentikAuthProvider instance
        
    Raises:
        RuntimeError: If core auth not available
    """
    global _mcp_auth_provider
    
    if _mcp_auth_provider is None:
        _mcp_auth_provider = create_mcp_auth_provider()
        logger.info("MCP auth provider initialized")
    
    return _mcp_auth_provider


def initialize_mcp_auth() -> AuthentikAuthProvider:
    """
    Explicitly initialize MCP auth provider
    
    Call this during application startup to fail fast if auth is misconfigured.
    
    Returns:
        AuthentikAuthProvider instance
    """
    global _mcp_auth_provider
    
    _mcp_auth_provider = create_mcp_auth_provider()
    logger.info("MCP auth provider explicitly initialized")
    
    return _mcp_auth_provider


# ============================================================================
# Re-export FastAPI Auth Dependencies
# ============================================================================

# Re-export your existing FastAPI auth dependencies
# This allows other modules to import from this file consistently

if CORE_AUTH_AVAILABLE:
    # Export your existing FastAPI dependencies
    __all__ = [
        'AuthentikAuthProvider',
        'AuthInfo',
        'get_mcp_auth_provider',
        'initialize_mcp_auth',
        'create_mcp_auth_provider',
        'get_token_from_header',  # Your existing FastAPI dependency
        'get_authentik_client',   # Your existing client factory
    ]
else:
    __all__ = [
        'AuthentikAuthProvider',
        'AuthInfo',
        'get_mcp_auth_provider',
        'initialize_mcp_auth',
        'create_mcp_auth_provider',
    ]