FROM python:3.11-slim

# Install uv (needed to run MCP servers from PyPI/Git)
RUN pip install uv

# Expose standard MCP port (if it binds to HTTP)
EXPOSE 3000

# Default to printing help
CMD ["uvx", "--help"]
