"""
CLI for Authentik user and token management.
"""

import argparse
import os
from authentik_client import AuthentikClient


def main():
    parser = argparse.ArgumentParser(description="Authentik User and Token Management CLI")
    parser.add_argument('--api-url', required=False, help='Authentik API URL', default=os.getenv('AUTHENTIK_API_URL'))
    parser.add_argument('--token', required=False, help='Authentik API Token', default=os.getenv('AUTHENTIK_API_TOKEN'))

    subparsers = parser.add_subparsers(dest='command')

    # Create user command
    create_user_parser = subparsers.add_parser('create-user', help='Create a new user')
    create_user_parser.add_argument('--username', required=True, type=str, help='Username for the new user')
    create_user_parser.add_argument('--name', required=True, type=str, help='Full name for the new user')
    create_user_parser.add_argument('--email', required=True, type=str, help='Email for the new user')
    create_user_parser.add_argument('--password', required=True, type=str, help='Password for the new user')

    # Generate token command
    generate_token_parser = subparsers.add_parser('generate-token', help='Generate a token for a user')
    generate_token_parser.add_argument('user_id', help='User ID for token generation')
    generate_token_parser.add_argument('--name', default='api-token', help='Token name (default: api-token)')

    # Validate token command
    validate_token_parser = subparsers.add_parser('validate-token', help='Validate a token')
    validate_token_parser.add_argument('token', help='Token string to validate')

    args = parser.parse_args()

    if not args.api_url or not args.token:
        print("API URL and Token are required. Use --api-url and --token or set AUTHENTIK_API_URL and AUTHENTIK_API_TOKEN.")
        exit(1)

    client = AuthentikClient(args.api_url, args.token)

    if args.command == 'create-user':
        try:
            user = client.create_user(args.username, args.name, args.email, args.password)
            print("User created:", user)
        except Exception as e:
            print(f"Error creating user: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                print(f"Response: {e.response.text}")
    elif args.command == 'generate-token':
        try:
            token = client.generate_token(args.user_id, args.name)
            print("Token generated:", token)
        except Exception as e:
            print(f"Error generating token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                print(f"Response: {e.response.text}")
    elif args.command == 'validate-token':
        try:
            result = client.validate_token(args.token)
            print("Token validation result:", result)
        except Exception as e:
            print(f"Error validating token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                print(f"Response: {e.response.text}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
