"""
Authentication dependencies for FastAPI routes using Authentik.

This module provides reusable authentication dependencies for protecting
FastAPI endpoints with Bearer token authentication validated via Authentik API.

Usage Example:
    from core.auth import get_token_from_header
    
    @app.get("/protected")
    async def protected_route(user: dict = Depends(get_token_from_header)):
        return {"message": f"Hello {user['username']}"}
"""

import os
from typing import Dict
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .authentik_client import AuthentikClient

# HTTPBearer instance for extracting Bearer tokens from Authorization header
security = HTTPBearer()


def get_authentik_client() -> AuthentikClient:
    """
    Create and return an Authentik API client instance.
    
    This function retrieves Authentik configuration from environment variables
    and initializes the client. It's used as a FastAPI dependency.
    
    Returns:
        AuthentikClient: Configured Authentik API client
        
    Raises:
        RuntimeError: If AUTHENTIK_API_URL or AUTHENTIK_API_TOKEN are not set
        
    Environment Variables:
        AUTHENTIK_API_URL: Base URL of Authentik API (e.g., http://authentik.example.com/api/v3)
        AUTHENTIK_API_TOKEN: Admin API token for authentication
        
    Example:
        >>> client = get_authentik_client()
        >>> result = client.validate_token(user_token)
    """
    api_url = os.getenv("AUTHENTIK_API_URL")
    api_token = os.getenv("AUTHENTIK_API_TOKEN")
    
    if not api_url or not api_token:
        raise RuntimeError(
            "AUTHENTIK_API_URL and AUTHENTIK_API_TOKEN must be set in environment. "
            "These are required for authentication to work."
        )
    
    return AuthentikClient(api_url, api_token)


async def get_token_from_header(
    credentials: HTTPAuthorizationCredentials = Security(security),
    client: AuthentikClient = Depends(get_authentik_client),
) -> Dict:
    """
    Validate Bearer token and return authenticated user information.
    
    This is the main authentication dependency for FastAPI routes.
    It extracts the Bearer token from the Authorization header,
    validates it against Authentik, and returns the user object.
    
    Args:
        credentials: Bearer token credentials from Authorization header
        client: Authentik API client (injected by dependency)
        
    Returns:
        dict: Authenticated user object containing:
            - pk: User ID
            - username: Username
            - email: Email address
            - name: Display name
            - is_active: Whether user is active
            - groups: List of user groups
            
    Raises:
        HTTPException: 401 if token is missing, empty, invalid, or inactive
        
    Example:
        @app.get("/api/data")
        async def get_data(user: dict = Depends(get_token_from_header)):
            return {"data": "secret", "user": user["username"]}
    """
    token_value = credentials.credentials
    
    if not token_value:
        raise HTTPException(
            status_code=401,
            detail="Token value is required"
        )
    
    # Validate token with Authentik API
    result = client.validate_token(token_value)
    
    if not result.get("active"):
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive token"
        )
    
    return result["user"]