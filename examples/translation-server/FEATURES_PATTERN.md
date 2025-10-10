# Features Pattern - Automatic Discovery

This translation server demonstrates the **features pattern** from `mcp-weather` - a modular, scalable way to organize MCP servers.

## What is the Features Pattern?

Instead of defining all tools and routes inline, features are organized into self-contained modules that are automatically discovered and registered.

## Structure

```
mcp_translation/features/
├── translate/           # Feature: Translation
│   ├── models.py       # Pydantic models for this feature
│   ├── tool.py         # MCP tool with register_tool() function
│   └── routes.py       # REST routes with create_router() function
├── detect_language/     # Feature: Language Detection
│   ├── models.py
│   ├── tool.py
│   └── routes.py
└── supported_languages/ # Feature: Supported Languages
    ├── models.py
    ├── tool.py
    └── routes.py
```

## How It Works

### MCP Tools (service.py)

```python
def register_mcp_tools(self, mcp: FastMCP) -> None:
    """Automatically discover and register tools from features"""
    for feature in discover_features():
        if feature.has_tool():
            feature.register_tool(mcp, self.service)
```

### REST Routes (server.py)

```python
def create_router(self) -> APIRouter:
    """Automatically discover and include routes from features"""
    router = APIRouter()
    for feature in discover_features():
        if feature.has_routes():
            router.include_router(feature.create_router(self.service))
    return router
```

## Adding a New Feature

Want to add a new capability? Just create a feature directory!

### Example: Add "Translate File" Feature

1. **Create directory**:
   ```bash
   mkdir -p mcp_translation/features/translate_file
   ```

2. **Create models.py**:
   ```python
   from pydantic import BaseModel

   class TranslateFileRequest(BaseModel):
       file_path: str
       target_language: str
   ```

3. **Create tool.py**:
   ```python
   def register_tool(mcp: FastMCP, translation_service):
       @mcp.tool()
       async def translate_file(file_path: str, target_language: str):
           """Translate a file to target language"""
           # Implementation
           return {"status": "translated"}
   ```

4. **Create routes.py** (optional):
   ```python
   def create_router(translation_service):
       router = APIRouter(prefix="/translate-file")
       
       @router.post("")
       async def translate_file_endpoint(request: TranslateFileRequest):
           # Implementation
           return {"status": "translated"}
       
       return router
   ```

5. **Done!** - No manual registration needed. The feature is automatically:
   - Discovered at startup
   - MCP tool registered
   - REST routes included

## Benefits

✅ **Modular** - Each feature is self-contained
✅ **Scalable** - Easy to add new features
✅ **Maintainable** - Clear organization
✅ **Testable** - Features can be tested independently
✅ **Discoverable** - No manual registration
✅ **Consistent** - Same pattern across all features

## Feature Template

```
features/my_feature/
├── __init__.py         # Export public models
├── models.py           # Pydantic models
├── tool.py             # MCP tool(s)
└── routes.py           # REST endpoint(s)
```

### __init__.py
```python
from mcp_translation.features.my_feature.models import MyRequest, MyResponse

__all__ = ["MyRequest", "MyResponse"]
```

### models.py
```python
from pydantic import BaseModel

class MyRequest(BaseModel):
    param: str

class MyResponse(BaseModel):
    result: str
```

### tool.py
```python
def register_tool(mcp: FastMCP, service):
    @mcp.tool()
    async def my_tool(param: str) -> dict:
        """Tool description for AI"""
        return {"result": param}
```

### routes.py
```python
from fastapi import APIRouter

def create_router(service):
    router = APIRouter(prefix="/my-feature")
    
    @router.post("")
    async def my_endpoint(request: MyRequest):
        return {"result": "value"}
    
    return router
```

## Comparison

### Old Pattern (Inline)

❌ All tools defined in one file
❌ All routes defined in one file
❌ Hard to maintain as project grows
❌ Difficult to test individual features
❌ No clear boundaries

```python
def register_mcp_tools(self, mcp: FastMCP):
    @mcp.tool()
    async def tool1(...): ...
    
    @mcp.tool()
    async def tool2(...): ...
    
    @mcp.tool()
    async def tool3(...): ...
    # ... 50 more tools
```

### New Pattern (Features)

✅ Each feature in its own directory
✅ Clear separation of concerns
✅ Scales to hundreds of features
✅ Easy to test and maintain
✅ Automatic discovery

```
features/
├── feature1/
│   ├── tool.py
│   └── routes.py
├── feature2/
│   ├── tool.py
│   └── routes.py
└── feature3/
    ├── tool.py
    └── routes.py
```

## Learn More

- See [mcp-weather](../../) for the original implementation
- Check [service.py](mcp_translation/service.py) for discovery code
- Review [server.py](mcp_translation/server.py) for route composition
- Study [features/translate/](mcp_translation/features/translate/) as an example
