"""Tests for base adapter interface."""

import pytest
from ai_pr_agent.adapters.base import (
    BaseAdapter,
    AdapterConfig,
    PlatformType,
    RateLimitInfo,
    Repository,
)
from ai_pr_agent.core import PullRequest, FileChange, Comment


class MockAdapter(BaseAdapter):
    """Mock adapter for testing."""
    
    def validate_connection(self) -> bool:
        return True
    
    def get_pull_request(self, repository: str, pr_number: int) -> PullRequest:
        return PullRequest(
            id=pr_number,
            title="Test PR",
            description="Test",
            author="test",
            source_branch="test",
            target_branch="main"
        )
    
    def get_pull_request_files(self, repository: str, pr_number: int) -> list:
        return []
    
    def get_file_content(self, repository: str, file_path: str, ref: str) -> str:
        return "test content"
    
    def post_review_comment(self, repository: str, pr_number: int, comment: Comment) -> str:
        return "comment_id_123"
    
    def post_review(self, repository: str, pr_number: int, comments: list, summary: str, event: str = "COMMENT") -> str:
        return "review_id_123"
    
    def update_comment(self, repository: str, comment_id: str, new_body: str) -> bool:
        return True
    
    def delete_comment(self, repository: str, comment_id: str) -> bool:
        return True
    
    def list_pull_requests(self, repository: str, state: str = "open", limit: int = 30) -> list:
        return []
    
    def get_repository_info(self, repository: str) -> Repository:
        owner, name = self.parse_repository(repository)
        return Repository(owner=owner, name=name, full_name=repository)
    
    def get_rate_limit(self) -> RateLimitInfo:
        return RateLimitInfo(limit=5000, remaining=4999, reset_at=1234567890)


class TestBaseAdapter:
    """Test base adapter functionality."""
    
    @pytest.fixture
    def adapter_config(self):
        """Create adapter configuration."""
        return AdapterConfig(
            platform=PlatformType.GITHUB,
            base_url="https://api.github.com",
            token="test_token"
        )
    
    @pytest.fixture
    def mock_adapter(self, adapter_config):
        """Create mock adapter instance."""
        return MockAdapter(adapter_config)
    
    def test_adapter_initialization(self, mock_adapter, adapter_config):
        """Test adapter initialization."""
        assert mock_adapter.config == adapter_config
        assert mock_adapter.logger is not None
    
    def test_parse_repository(self, mock_adapter):
        """Test repository string parsing."""
        owner, repo = mock_adapter.parse_repository("owner/repo")
        
        assert owner == "owner"
        assert repo == "repo"
    
    def test_parse_repository_invalid(self, mock_adapter):
        """Test invalid repository format."""
        with pytest.raises(ValueError):
            mock_adapter.parse_repository("invalid")
        
        with pytest.raises(ValueError):
            mock_adapter.parse_repository("too/many/parts")
    
    def test_format_comment_body(self, mock_adapter):
        """Test comment formatting."""
        from ai_pr_agent.core import SeverityLevel
        
        comment = Comment(
            body="Test issue",
            severity=SeverityLevel.ERROR,
            line=10
        )
        
        formatted = mock_adapter.format_comment_body(comment)
        
        assert "❌" in formatted
        assert "ERROR" in formatted
        assert "Test issue" in formatted
    
    def test_format_comment_with_suggestion(self, mock_adapter):
        """Test comment formatting with suggestion."""
        from ai_pr_agent.core import SeverityLevel
        
        comment = Comment(
            body="Test issue",
            severity=SeverityLevel.WARNING,
            suggestion="fixed_code()"
        )
        
        formatted = mock_adapter.format_comment_body(comment)
        
        assert "⚠️" in formatted
        assert "Suggestion" in formatted
        assert "fixed_code()" in formatted
    
    def test_adapter_repr(self, mock_adapter):
        """Test adapter string representation."""
        repr_str = repr(mock_adapter)
        
        assert "MockAdapter" in repr_str
        assert "github" in repr_str
        assert "https://api.github.com" in repr_str


class TestAdapterConfig:
    """Test adapter configuration."""
    
    def test_config_creation(self):
        """Test creating adapter configuration."""
        config = AdapterConfig(
            platform=PlatformType.GITHUB,
            base_url="https://api.github.com",
            token="test_token",
            timeout=30,
            max_retries=3
        )
        
        assert config.platform == PlatformType.GITHUB
        assert config.base_url == "https://api.github.com"
        assert config.token == "test_token"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.verify_ssl is True
    
    def test_config_with_custom_headers(self):
        """Test configuration with custom headers."""
        headers = {"X-Custom": "value"}
        
        config = AdapterConfig(
            platform=PlatformType.GITHUB,
            base_url="https://api.github.com",
            token="test_token",
            custom_headers=headers
        )
        
        assert config.custom_headers == headers


class TestRateLimitInfo:
    """Test rate limit information."""
    
    def test_rate_limit_creation(self):
        """Test creating rate limit info."""
        rate_limit = RateLimitInfo(
            limit=5000,
            remaining=4500,
            reset_at=1234567890,
            resource="core"
        )
        
        assert rate_limit.limit == 5000
        assert rate_limit.remaining == 4500
        assert rate_limit.reset_at == 1234567890
        assert rate_limit.resource == "core"


class TestRepository:
    """Test repository information."""
    
    def test_repository_creation(self):
        """Test creating repository info."""
        repo = Repository(
            owner="test-owner",
            name="test-repo",
            full_name="test-owner/test-repo",
            default_branch="main",
            is_private=False
        )
        
        assert repo.owner == "test-owner"
        assert repo.name == "test-repo"
        assert repo.full_name == "test-owner/test-repo"
        assert repo.default_branch == "main"
        assert repo.is_private is False