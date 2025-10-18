"""Adapter modules for Git platform integrations."""

from .base import (
    BaseAdapter,
    AdapterConfig,
    PlatformType,
    RateLimitInfo,
    Repository,
)
from .factory import AdapterFactory

__all__ = [
    "BaseAdapter",
    "AdapterConfig",
    "PlatformType",
    "RateLimitInfo",
    "Repository",
    "AdapterFactory",
]