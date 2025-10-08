# Shared Components

This directory contains shared components used across multiple features in the MCP Weather service.

## models.py

Contains shared data models:
- Base models that other models extend
- Error response models
- Common data structures (measurements, coordinates, etc.)
- Models used in multiple features

## Future Components

Future shared components might include:
- `utils.py` - Shared utility functions
- `middleware.py` - Common middleware
- `validation.py` - Shared validation logic
- `config.py` - Common configuration models

## Usage Guidelines

When deciding where to place code, follow these guidelines:

1. If a model is used in multiple features, place it in `shared/models.py`
2. If a model is specific to a feature, place it in `features/<feature>/models.py`
3. If a utility function is used in multiple features, place it in `shared/utils.py` (future)
4. If a utility is specific to a feature, place it in the feature's directory