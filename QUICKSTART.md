# Weather MCP Server

A secure, Authentik-authenticated MCP server providing weather data via Open-Meteo API.

## Features

- FastMCP 2.0 integration for AI tool access
- REST API endpoints for web applications
- Authentik Bearer token authentication
- Location caching for performance
- Free Open-Meteo API (no API key required)
- Support for stdio and HTTP transports

## Quick Start

This project uses `uv` for Python package management.

### Setup

```bash
# Set up the development environment
./setup-dev.sh
```

### Run the Server

```bash
# Run in MCP-only mode
./run-server.sh

# Run in REST API mode (includes MCP endpoints)
./run-server.sh rest
```

#### Available Endpoints in REST mode

- **Server**: http://0.0.0.0:3000
- **API Documentation**: http://0.0.0.0:3000/docs
- **Health Check**: http://0.0.0.0:3000/health (no auth required)
- **MCP Endpoint**: http://0.0.0.0:3000/mcp

REST API endpoints:
- `GET /` - Service information
- `GET /health` - Health check (no auth)
- `GET /weather?location=<city>` - Get weather (auth required)
- `POST /weather` - Get weather via JSON body (auth required)

All endpoints except `/health` require Authentik Bearer token authentication.

### Testing

#### Test the MCP Client

```bash
# Run the MCP test client with your Authentik token
./run-test.sh YOUR_AUTHENTIK_TOKEN
```

#### Test the REST API

First, ensure the server is running in REST mode:
```bash
./run-server.sh rest
```

Then, in another terminal, test the REST API endpoints:

```bash
# Using the Bash script (requires curl and jq)
./test-rest-api.sh YOUR_AUTHENTIK_TOKEN

# Or using the Python script
uv run python tools/test_rest_api.py YOUR_AUTHENTIK_TOKEN
```

## Development

This project uses a core auth provider module for authentication, which is shared
across multiple services. The auth provider integrates with Authentik for secure 
token-based authentication.

## License

MIT