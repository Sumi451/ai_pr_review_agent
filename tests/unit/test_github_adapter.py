"""Tests for GitHub adapter."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from ai_pr_agent.adapters.github import GitHubAdapter
from ai_pr_agent.adapters.base import AdapterConfig, PlatformType
from ai_pr_agent.core import NotFoundError, APIError
from ai_pr_agent.core.exceptions import AccessPermissionError as CustomPermissionError


class TestGitHubAdapter:
    """Test GitHub adapter functionality."""
    
    @pytest.fixture
    def adapter_config(self):
        """Create adapter configuration."""
        return AdapterConfig(
            platform=PlatformType.GITHUB,
            base_url="https://api.github.com",
            token="test_token_123"
        )
    
    @pytest.fixture
    def mock_github_client(self):
        """Create mock GitHub client."""
        with patch('ai_pr_agent.adapters.github.Github') as mock:
            yield mock
    
    def test_adapter_initialization(self, adapter_config, mock_github_client):
        """Test adapter initialization."""
        adapter = GitHubAdapter(adapter_config)
        
        assert adapter is not None
        assert adapter.config == adapter_config
        mock_github_client.assert_called_once()
    
    def test_validate_connection_success(self, adapter_config, mock_github_client):
        """Test successful connection validation."""
        # Setup mock
        mock_client = mock_github_client.return_value
        mock_user = Mock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user
        
        adapter = GitHubAdapter(adapter_config)
        result = adapter.validate_connection()
        
        assert result is True
    
    def test_map_github_status(self, adapter_config, mock_github_client):
        """Test GitHub status mapping."""
        from ai_pr_agent.core import FileStatus
        
        adapter = GitHubAdapter(adapter_config)
        
        assert adapter._map_github_status('added') == FileStatus.ADDED
        assert adapter._map_github_status('modified') == FileStatus.MODIFIED
        assert adapter._map_github_status('removed') == FileStatus.DELETED
        assert adapter._map_github_status('renamed') == FileStatus.RENAMED