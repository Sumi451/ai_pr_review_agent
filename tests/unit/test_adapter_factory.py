"""Tests for adapter factory."""

import pytest
from ai_pr_agent.adapters.factory import AdapterFactory
from ai_pr_agent.adapters.base import BaseAdapter, PlatformType, AdapterConfig
from ai_pr_agent.core import (
    PullRequest,
    FileChange,
    Comment,
)
from ai_pr_agent.core.exceptions import ConfigurationError


class DummyAdapter(BaseAdapter):
    """Dummy adapter for testing factory - implements all abstract methods."""
    
    def validate_connection(self) -> bool:
        """Validate connection."""
        return True
    
    def get_pull_request(self, repository: str, pr_number: int) -> PullRequest:
        """Get pull request."""
        return PullRequest(
            id=pr_number,
            title="Test",
            description="Test",
            author="test",
            source_branch="test",
            target_branch="main"
        )
    
    def get_pull_request_files(self, repository: str, pr_number: int) -> list:
        """Get PR files."""
        return []
    
    def get_file_content(self, repository: str, file_path: str, ref: str) -> str:
        """Get file content."""
        return "test content"
    
    def post_review_comment(self, repository: str, pr_number: int, comment: Comment) -> str:
        """Post review comment."""
        return "comment_123"
    
    def post_review(self, repository: str, pr_number: int, comments: list, summary: str, event: str = "COMMENT") -> str:
        """Post review."""
        return "review_123"
    
    def update_comment(self, repository: str, comment_id: str, new_body: str) -> bool:
        """Update comment."""
        return True
    
    def delete_comment(self, repository: str, comment_id: str) -> bool:
        """Delete comment."""
        return True
    
    def list_pull_requests(self, repository: str, state: str = "open", limit: int = 30) -> list:
        """List PRs."""
        return []
    
    def get_repository_info(self, repository: str):
        """Get repository info."""
        from ai_pr_agent.adapters.base import Repository
        owner, name = self.parse_repository(repository)
        return Repository(owner=owner, name=name, full_name=repository)
    
    def get_rate_limit(self):
        """Get rate limit."""
        from ai_pr_agent.adapters.base import RateLimitInfo
        return RateLimitInfo(limit=5000, remaining=4999, reset_at=1234567890)


class TestAdapterFactory:
    """Test adapter factory."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Store original adapters
        original_adapters = AdapterFactory._adapters.copy()
        
        # Register test adapter
        AdapterFactory.register_adapter(PlatformType.GITHUB, DummyAdapter)
        
        yield
        
        # Restore original adapters
        AdapterFactory._adapters = original_adapters
    
    def test_register_adapter(self):
        """Test registering an adapter."""
        # Register a test adapter (already done in setup)
        
        # Should be in registry
        assert PlatformType.GITHUB in AdapterFactory._adapters
        assert AdapterFactory._adapters[PlatformType.GITHUB] == DummyAdapter
    
    def test_list_available_platforms(self):
        """Test listing available platforms."""
        platforms = AdapterFactory.list_available_platforms()
        
        assert isinstance(platforms, list)
        assert len(platforms) > 0
        assert 'github' in platforms
    
    def test_create_adapter_with_token(self):
        """Test creating adapter with explicit token."""
        adapter = AdapterFactory.create_adapter(
            PlatformType.GITHUB,
            token="test_token_123"
        )
        
        assert adapter is not None
        assert isinstance(adapter, DummyAdapter)
        assert adapter.config.token == "test_token_123"
        assert adapter.config.platform == PlatformType.GITHUB
    
    def test_create_adapter_missing_token(self):
        """Test creating adapter without token."""
        # Should raise ValueError when no token provided and not in config
        with pytest.raises(ValueError, match="token required"):
            AdapterFactory.create_adapter(PlatformType.GITHUB)
    
    def test_create_adapter_with_custom_config(self):
        """Test creating adapter with custom configuration."""
        adapter = AdapterFactory.create_adapter(
            PlatformType.GITHUB,
            token="test_token",
            timeout=60,
            max_retries=5,
            verify_ssl=False
        )
        
        assert adapter.config.timeout == 60
        assert adapter.config.max_retries == 5
        assert adapter.config.verify_ssl is False
    
    def test_create_github_adapter_convenience_method(self):
        """Test convenience method for creating GitHub adapter."""
        adapter = AdapterFactory.create_github_adapter(token="test_token")
        
        assert adapter is not None
        assert adapter.config.platform == PlatformType.GITHUB
        assert adapter.config.token == "test_token"
    
    def test_parse_repository_format(self):
        """Test repository format parsing."""
        config = AdapterConfig(
            platform=PlatformType.GITHUB,
            base_url="https://api.github.com",
            token="test"
        )
        adapter = DummyAdapter(config)
        
        owner, repo = adapter.parse_repository("microsoft/vscode")
        assert owner == "microsoft"
        assert repo == "vscode"
    
    def test_adapter_validate_connection(self):
        """Test adapter connection validation."""
        adapter = AdapterFactory.create_adapter(
            PlatformType.GITHUB,
            token="test_token"
        )
        
        # Should not raise exception
        result = adapter.validate_connection()
        assert result is True
    
    def test_adapter_get_rate_limit(self):
        """Test getting rate limit info."""
        adapter = AdapterFactory.create_adapter(
            PlatformType.GITHUB,
            token="test_token"
        )
        
        rate_limit = adapter.get_rate_limit()
        
        assert rate_limit is not None
        assert rate_limit.limit > 0
        assert rate_limit.remaining >= 0