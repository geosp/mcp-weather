"""
Authentik API client library for user and token management.

Token Validation Workflow:
-------------------------
1. Token Creation:
     - Use the CLI command:
         uv run python tools/main.py --api-url <url> --token <admin_token> generate-token <user_id> --name <token_name>
     - The response will include the secret token string. Save this value; it is only shown once.

2. Token Validation:
     - Use the CLI command:
         uv run python tools/main.py --api-url <url> --token <admin_token> validate-token <actual_token_string>
     - The CLI calls AuthentikClient.validate_token(), which makes an authenticated request to /api/v3/core/users/me/ using the token as the Authorization header.
     - If the token is valid, the response will include user info and 'active': True.
     - If the token is invalid, expired, or revoked, the response will include 'active': False.

Notes:
- Always use the actual secret token string for validation, not the UUID or identifier.
- API tokens are validated by making an authenticated API call, not via OAuth2 introspection.
- The CLI supports user creation, token generation, and token validation.
"""

import requests
import os

class AuthentikClient:
    def __init__(self, api_url: str, token: str):
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        def create_user(self, username: str, name: str, email: str, password: str) -> dict:
            """
            Create a new user in Authentik.
            """
            url = f"{self.api_url}/api/v3/core/users/"
            payload = {
                "username": username,
                "name": name,
                "email": email,
                "password": password
            }
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()

    def generate_token(self, user_id: str, name: str = "api-token") -> dict:
        """
        Generate an API token for a user in Authentik.
        """
        url = f"{self.api_url}/api/v3/core/tokens/"
        payload = {
            "user": user_id,
            "name": name
        }
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_user(self, username: str, name: str, email: str, password: str) -> dict:
        """
        Create a new user in Authentik.
        """
        url = f"{self.api_url}/api/v3/core/users/"
        payload = {
            "username": username,
            "name": name,
            "email": email,
            "password": password
        }
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def generate_token(self, user_id: str, name: str = "api-token") -> dict:
        """
        Generate a token for a user in Authentik.
        """
        url = f"{self.api_url}/api/v3/core/tokens/"
        payload = {
            "user": user_id,
            "name": name,
            "identifier": name,
            "intent": "api",
            "expiring": False
        }
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def validate_token(self, token: str) -> dict:
        """
        Validate an API token by making an authenticated request to /api/v3/core/users/me/.
        Returns user info if valid, or error if invalid.
        """
        url = f"{self.api_url}/api/v3/core/users/me/"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return {"active": True, "user": response.json()}
        else:
            return {"active": False, "status_code": response.status_code, "detail": response.text}
    
""""
(mcp-weather) geo@provisioner:~/projects/mcp/mcp-weather$ uv run python tools/main.py --api-url http://authentik.mixwarecs-home.net/ --token phtNgtfeDKkifwbIttcNrvoZlfvHOhb9jCKtid2iRc6W4fCzX5fAs43LpIZZ create-user --username adam --name "Adam Firstman" --email adam@example.com --password firstman123
warning: No `requires-python` value found in the workspace. Defaulting to `>=3.13`.
User created: {'pk': 5, 'username': 'adam', 'name': 'Adam Firstman', 'is_active': True, 'last_login': None, 'is_superuser': False, 'groups': [], 'groups_obj': [], 'email': 'adam@example.com', 'avatar': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2NHB4IiBoZWlnaHQ9IjY0cHgiIHZpZXdCb3g9IjAgMCA2NCA2NCIgdmVyc2lvbj0iMS4xIj48cmVjdCBmaWxsPSIjNzRjODM3IiBjeD0iMzIiIGN5PSIzMiIgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiByPSIzMiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBzdHlsZT0iY29sb3I6ICNmZmY7IGxpbmUtaGVpZ2h0OiAxOyBmb250LWZhbWlseTogJ1JlZEhhdFRleHQnLCdPdmVycGFzcycsb3ZlcnBhc3MsaGVsdmV0aWNhLGFyaWFsLHNhbnMtc2VyaWY7ICIgZmlsbD0iI2ZmZiIgYWxpZ25tZW50LWJhc2VsaW5lPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtc2l6ZT0iMjgiIGZvbnQtd2VpZ2h0PSI0MDAiIGR5PSIuMWVtIj5BRjwvdGV4dD48L3N2Zz4=', 'attributes': {}, 'uid': '614d0d822335416dd12bfdb6ec6caaa2d71fdab61ea062c686bdd22b17b86be8', 'path': 'users', 'type': 'internal', 'uuid': 'f9a8214c-5b5d-4abd-92b9-33e5a09b80f2'}
(mcp-weather) geo@provisioner:~/projects/mcp/mcp-weather$ 
"""

"""
(mcp-weather) geo@provisioner:~/projects/mcp/mcp-weather$ uv run python tools/main.py --api-url http://authentik.mixwarecs-home.net/ --token phtNgtfeDKkifwbIttcNrvoZlfvHOhb9jCKtid2iRc6W4fCzX5fAs43LpIZZ generate-token 5 --name "adam-api-token"
warning: No `requires-python` value found in the workspace. Defaulting to `>=3.13`.
Token generated: {'pk': 'a3f80f85-21f5-4ed9-bf30-8d4d2d95631b', 'managed': None, 'identifier': 'adam-api-token', 'intent': 'api', 'user': 5, 'user_obj': {'pk': 5, 'username': 'adam', 'name': 'Adam Firstman', 'is_active': True, 'last_login': None, 'is_superuser': False, 'groups': [], 'groups_obj': [], 'email': 'adam@example.com', 'avatar': 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2NHB4IiBoZWlnaHQ9IjY0cHgiIHZpZXdCb3g9IjAgMCA2NCA2NCIgdmVyc2lvbj0iMS4xIj48cmVjdCBmaWxsPSIjNzRjODM3IiBjeD0iMzIiIGN5PSIzMiIgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiByPSIzMiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBzdHlsZT0iY29sb3I6ICNmZmY7IGxpbmUtaGVpZ2h0OiAxOyBmb250LWZhbWlseTogJ1JlZEhhdFRleHQnLCdPdmVycGFzcycsb3ZlcnBhc3MsaGVsdmV0aWNhLGFyaWFsLHNhbnMtc2VyaWY7ICIgZmlsbD0iI2ZmZiIgYWxpZ25tZW50LWJhc2VsaW5lPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtc2l6ZT0iMjgiIGZvbnQtd2VpZ2h0PSI0MDAiIGR5PSIuMWVtIj5BRjwvdGV4dD48L3N2Zz4=', 'attributes': {}, 'uid': '614d0d822335416dd12bfdb6ec6caaa2d71fdab61ea062c686bdd22b17b86be8', 'path': 'users', 'type': 'internal', 'uuid': 'f9a8214c-5b5d-4abd-92b9-33e5a09b80f2'}, 'description': '', 'expires': '2025-10-07T06:18:28.385767Z', 'expiring': False}
"""


