"""
CLI for Authentik user and token management.

Usage Examples:
    # Create a user
    uv run python tools/authentik_manager.py create-user --username adam --name "Adam Firstman" --email adam@example.com --password secret123
    
    # Generate a token (displays the actual Bearer token)
    uv run python tools/authentik_manager.py generate-token 5 --name "adam-api-token"

    # Validate a token
    uv run python tools/authentik_manager.py validate-token <actual-token-string>
"""

import argparse
import os
import json
from core.authentik_client import AuthentikClient
from core.config import AuthentikConfig


def print_token_info(token_response):
    """
    Pretty print token information with emphasis on the actual token key.
    
    Args:
        token_response: Dict response from Authentik token generation
    """
    print("\n" + "=" * 70)
    print("TOKEN GENERATED SUCCESSFULLY")
    print("=" * 70)
    
    # Display the critical information first
    if 'key' in token_response:
        print("\n⚠️  CRITICAL: SAVE THIS TOKEN - IT WILL ONLY BE SHOWN ONCE!")
        print("-" * 70)
        print(f"Bearer Token: {token_response['key']}")
        print("-" * 70)
        print("\nUse this token in your Authorization header:")
        print(f"  Authorization: Bearer {token_response['key']}")
    else:
        print("\n⚠️  WARNING: No 'key' field found in response!")
        print("The actual Bearer token may not be visible.")
        print("Available fields:", list(token_response.keys()))
    
    # Display other token information
    print("\n" + "-" * 70)
    print("Token Details:")
    print("-" * 70)
    print(f"Token ID:     {token_response.get('pk', 'N/A')}")
    print(f"Identifier:   {token_response.get('identifier', 'N/A')}")
    print(f"User ID:      {token_response.get('user', 'N/A')}")
    print(f"Intent:       {token_response.get('intent', 'N/A')}")
    print(f"Expiring:     {token_response.get('expiring', 'N/A')}")
    
    if token_response.get('expires'):
        print(f"Expires:      {token_response['expires']}")
    
    if token_response.get('user_obj'):
        user = token_response['user_obj']
        print(f"\nUser Info:")
        print(f"  Username:   {user.get('username', 'N/A')}")
        print(f"  Name:       {user.get('name', 'N/A')}")
        print(f"  Email:      {user.get('email', 'N/A')}")
    
    print("=" * 70)
    
    # Save to file option
    print("\n💡 Tip: Save this token to your .env file:")
    if 'key' in token_response:
        print(f"   AUTHENTIK_TOKEN={token_response['key']}")
    print()


def print_user_info(user_response):
    """
    Pretty print user information.
    
    Args:
        user_response: Dict response from Authentik user creation
    """
    print("\n" + "=" * 70)
    print("USER CREATED SUCCESSFULLY")
    print("=" * 70)
    print(f"User ID:      {user_response.get('pk', 'N/A')}")
    print(f"UUID:         {user_response.get('uuid', 'N/A')}")
    print(f"Username:     {user_response.get('username', 'N/A')}")
    print(f"Name:         {user_response.get('name', 'N/A')}")
    print(f"Email:        {user_response.get('email', 'N/A')}")
    print(f"Active:       {user_response.get('is_active', 'N/A')}")
    print(f"Superuser:    {user_response.get('is_superuser', 'N/A')}")
    print("=" * 70)
    print(f"\n💡 Next step: Generate a token for this user:")
    print(f"   python tools/main.py generate-token {user_response.get('pk')} --name \"my-token\"")
    print()


def print_validation_result(result):
    """
    Pretty print token validation result.
    
    Args:
        result: Dict response from token validation
    """
    print("\n" + "=" * 70)
    print("TOKEN VALIDATION RESULT")
    print("=" * 70)
    
    if result.get("active"):
        print("✅ Token is VALID and ACTIVE")
        print("-" * 70)
        
        user = result.get("user", {})
        print(f"User ID:      {user.get('pk', 'N/A')}")
        print(f"Username:     {user.get('username', 'N/A')}")
        print(f"Name:         {user.get('name', 'N/A')}")
        print(f"Email:        {user.get('email', 'N/A')}")
        print(f"Active:       {user.get('is_active', 'N/A')}")
        print(f"Superuser:    {user.get('is_superuser', 'N/A')}")
        
        if user.get('groups'):
            print(f"Groups:       {', '.join(user.get('groups', []))}")
        
    else:
        print("❌ Token is INVALID or INACTIVE")
        print("-" * 70)
        print(f"Status Code:  {result.get('status_code', 'N/A')}")
        print(f"Detail:       {result.get('detail', 'No details available')}")
    
    print("=" * 70)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Authentik User and Token Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a user
  %(prog)s create-user --username john --name "John Doe" --email john@example.com --password secret123

  # Generate a token for user ID 5
  %(prog)s generate-token 5 --name "my-api-token"

  # Validate a token
  %(prog)s validate-token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Environment Variables:
  AUTHENTIK_API_URL    - Authentik API endpoint (e.g., http://authentik.example.com/api/v3)
  AUTHENTIK_API_TOKEN  - Admin API token for Authentik
        """
    )
    
    # Try to load from config first, then fall back to direct env vars
    try:
        config = AuthentikConfig.from_env_optional()
        default_url = config.api_url if config else os.getenv('AUTHENTIK_API_URL')
        default_token = config.api_token if config else os.getenv('AUTHENTIK_API_TOKEN')
    except:
        default_url = os.getenv('AUTHENTIK_API_URL')
        default_token = os.getenv('AUTHENTIK_API_TOKEN')
        
    parser.add_argument(
        '--api-url', 
        required=False, 
        help='Authentik API URL (or set AUTHENTIK_API_URL)', 
        default=default_url
    )
    parser.add_argument(
        '--token', 
        required=False, 
        help='Authentik Admin API Token (or set AUTHENTIK_API_TOKEN)', 
        default=default_token
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output (shows full JSON responses)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create user command
    create_user_parser = subparsers.add_parser(
        'create-user', 
        help='Create a new user in Authentik',
        description='Create a new user with specified credentials'
    )
    create_user_parser.add_argument('--username', required=True, type=str, help='Username for the new user')
    create_user_parser.add_argument('--name', required=True, type=str, help='Full name for the new user')
    create_user_parser.add_argument('--email', required=True, type=str, help='Email for the new user')
    create_user_parser.add_argument('--password', required=True, type=str, help='Password for the new user')

    # Generate token command
    generate_token_parser = subparsers.add_parser(
        'generate-token', 
        help='Generate an API token for a user',
        description='Generate a new API token for an existing user. The token will only be displayed once!'
    )
    generate_token_parser.add_argument('user_id', help='User ID (pk) for token generation')
    generate_token_parser.add_argument('--name', default='api-token', help='Token name/identifier (default: api-token)')

    # Validate token command
    validate_token_parser = subparsers.add_parser(
        'validate-token', 
        help='Validate an API token',
        description='Check if a token is valid and active, and retrieve user information'
    )
    validate_token_parser.add_argument('token', help='Token string to validate (the actual Bearer token)')

    args = parser.parse_args()

    # Validate required credentials
    if not args.api_url or not args.token:
        print("\n❌ ERROR: API credentials required")
        print("-" * 70)
        print("Provide credentials via:")
        print("  1. Command line: --api-url <url> --token <token>")
        print("  2. Environment:  AUTHENTIK_API_URL and AUTHENTIK_API_TOKEN")
        print()
        print("Example:")
        print("  export AUTHENTIK_API_URL=http://authentik.example.com/api/v3")
        print("  export AUTHENTIK_API_TOKEN=your-admin-token-here")
        print()
        exit(1)

    # Initialize Authentik client
    client = AuthentikClient(args.api_url, args.token)
    
    if args.debug:
        print(f"🔧 Debug: Using API URL: {args.api_url}")
        print(f"🔧 Debug: Using token: {args.token[:20]}...")
        print()

    # Handle commands
    try:
        if args.command == 'create-user':
            user = client.create_user(args.username, args.name, args.email, args.password)
            
            if args.debug:
                print("\n🔧 Debug: Full response:")
                print(json.dumps(user, indent=2))
            
            print_user_info(user)
            
        elif args.command == 'generate-token':
            token_response = client.generate_token(args.user_id, args.name)
            
            if args.debug:
                print("\n🔧 Debug: Full response:")
                print(json.dumps(token_response, indent=2))
            
            print_token_info(token_response)
            
        elif args.command == 'validate-token':
            result = client.validate_token(args.token)
            
            if args.debug:
                print("\n🔧 Debug: Full response:")
                print(json.dumps(result, indent=2))
            
            print_validation_result(result)
            
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        
        if args.debug and hasattr(e, 'response') and e.response is not None:
            print(f"\n🔧 Debug: HTTP Status: {e.response.status_code}")
            print(f"🔧 Debug: Response: {e.response.text}")
        
        exit(1)


if __name__ == "__main__":
    main()