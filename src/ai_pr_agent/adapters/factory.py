"""
Factory for creating platform-specific adapters.
"""
from typing import Optional

from ai_pr_agent.utils import get_logger
from ai_pr_agent.config import get_settings
from .base import BaseAdapter, AdapterConfig, PlatformType

logger = get_logger(__name__)


class AdapterFactory:
    """Factory for creating platform adapters."""
    
    _adapters = {}  # Registry of available adapters
    
    @classmethod
    def register_adapter(cls, platform: PlatformType, adapter_class: type):
        """
        Register an adapter class for a platform.
        
        Args:
            platform: Platform type
            adapter_class: Adapter class to register
        """
        cls._adapters[platform] = adapter_class
        logger.debug(f"Registered adapter for {platform.value}: {adapter_class.__name__}")
    
    @classmethod
    def create_adapter(
        cls,
        platform: PlatformType,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ) -> BaseAdapter:
        """
        Create an adapter instance for the specified platform.
        
        Args:
            platform: Platform type
            token: Authentication token (reads from config if not provided)
            base_url: Platform base URL (uses default if not provided)
            **kwargs: Additional configuration options
        
        Returns:
            Configured adapter instance
        
        Raises:
            ValueError: If platform is not supported
            ConfigurationError: If required configuration is missing
        """
        if platform not in cls._adapters:
            available = ", ".join(p.value for p in cls._adapters.keys())
            raise ValueError(
                f"Unsupported platform: {platform.value}. "
                f"Available platforms: {available}"
            )
        
        # Get settings
        settings = get_settings()
        
        # Determine base URL
        if base_url is None:
            base_url = cls._get_default_base_url(platform)
        
        # Get token
        if token is None:
            if platform == PlatformType.GITHUB:
                token = settings.github.token
            else:
                raise ValueError(f"No token provided for {platform.value}")
        
        if not token:
            raise ValueError(f"Authentication token required for {platform.value}")
        
        # Create configuration
        config = AdapterConfig(
            platform=platform,
            base_url=base_url,
            token=token,
            timeout=kwargs.get('timeout', settings.github.timeout),
            max_retries=kwargs.get('max_retries', settings.github.max_retries),
            verify_ssl=kwargs.get('verify_ssl', True),
            custom_headers=kwargs.get('custom_headers')
        )
        
        # Instantiate adapter
        adapter_class = cls._adapters[platform]
        adapter = adapter_class(config)
        
        logger.info(f"Created {platform.value} adapter")
        return adapter
    
    @classmethod
    def create_github_adapter(
        cls,
        token: Optional[str] = None,
        **kwargs
    ) -> BaseAdapter:
        """
        Convenience method to create GitHub adapter.
        
        Args:
            token: GitHub token
            **kwargs: Additional configuration
        
        Returns:
            GitHubAdapter instance
        """
        return cls.create_adapter(PlatformType.GITHUB, token=token, **kwargs)
    
    @staticmethod
    def _get_default_base_url(platform: PlatformType) -> str:
        """Get default base URL for a platform."""
        urls = {
            PlatformType.GITHUB: "https://api.github.com",
            PlatformType.GITLAB: "https://gitlab.com/api/v4",
            PlatformType.BITBUCKET: "https://api.bitbucket.org/2.0"
        }
        return urls.get(platform, "")
    
    @classmethod
    def list_available_platforms(cls) -> list[str]:
        """Get list of available platforms."""
        return [platform.value for platform in cls._adapters.keys()]


# Auto-register adapters when they're imported
def _auto_register_adapters():
    """Auto-register available adapters."""
    try:
        from .github import GitHubAdapter
        AdapterFactory.register_adapter(PlatformType.GITHUB, GitHubAdapter)
    except ImportError:
        logger.debug("GitHubAdapter not available")
    
    # Future adapters will be registered here
    # try:
    #     from .gitlab import GitLabAdapter
    #     AdapterFactory.register_adapter(PlatformType.GITLAB, GitLabAdapter)
    # except ImportError:
    #     pass


# Register adapters on module import
_auto_register_adapters()