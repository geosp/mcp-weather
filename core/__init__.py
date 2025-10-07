"""
Core infrastructure shared across projects

This package contains reusable infrastructure components that can be
shared across multiple projects, including authentication, configuration,
and other common utilities.
"""

from .config import (
    AuthentikConfig,
    BaseCacheConfig,
    BaseServerConfig,
)

from .auth import (
    get_authentik_client,
    get_token_from_header,
)

from .authentik_client import (
    AuthentikClient,
)

from .auth_provider import (
    AuthInfo,
    AuthentikAuthProvider,
    create_auth_provider,
    get_auth_provider,
)