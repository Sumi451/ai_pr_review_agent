"""Integration tests for GitHub adapter with real API."""

import pytest
import os

from ai_pr_agent.adapters import AdapterFactory, PlatformType
from ai_pr_agent.core import NotFoundError


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv('GITHUB_TOKEN'),
    reason="GITHUB_TOKEN not set - skipping integration tests"
)
class TestGitHubIntegration:
    """Integration tests with real GitHub API."""
    
    @pytest.fixture
    def github_adapter(self):
        """Create GitHub adapter with real token."""
        token = os.getenv('GITHUB_TOKEN')
        return AdapterFactory.create_github_adapter(token=token)
    
    def test_validate_connection(self, github_adapter):
        """Test real connection validation."""
        result = github_adapter.validate_connection()
        assert result is True
    
    def test_get_rate_limit(self, github_adapter):
        """Test getting real rate limit."""
        rate_info = github_adapter.get_rate_limit()
        
        assert rate_info.limit > 0
        assert rate_info.remaining >= 0
        assert rate_info.reset_at > 0
    
    def test_get_repository_info(self, github_adapter):
        """Test fetching real repository info."""
        # Use a public repository
        repo_info = github_adapter.get_repository_info("microsoft/vscode")
        
        assert repo_info.owner == "microsoft"
        assert repo_info.name == "vscode"
        assert repo_info.full_name == "microsoft/vscode"
    
    def test_list_pull_requests(self, github_adapter):
        """Test listing real PRs."""
        # Use a public repository
        prs = github_adapter.list_pull_requests("microsoft/vscode", state="closed", limit=5)
        
        assert len(prs) > 0
        assert all(pr.platform == "github" for pr in prs)
    
    def test_get_nonexistent_pr(self, github_adapter):
        """Test fetching non-existent PR."""
        with pytest.raises(NotFoundError):
            github_adapter.get_pull_request("microsoft/vscode", 999999999)