"""Tests for GitHub adapter."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from ai_pr_agent.adapters.github import GitHubAdapter
from ai_pr_agent.adapters.base import AdapterConfig, PlatformType
from ai_pr_agent.core import (
    PullRequest,
    FileChange,
    FileStatus,
    Comment,
    SeverityLevel,
    NotFoundError,
    APIError,
)
from ai_pr_agent.core.exceptions import AccessPermissionError as CustomPermissionError


@pytest.fixture
def adapter_config():
    """Create adapter configuration."""
    return AdapterConfig(
        platform=PlatformType.GITHUB,
        base_url="https://api.github.com",
        token="test_token_123"
    )


@pytest.fixture
def mock_github():
    """Create mock GitHub client."""
    with patch('ai_pr_agent.adapters.github.Github') as mock:
        yield mock


@pytest.fixture
def github_adapter(adapter_config, mock_github):
    """Create GitHub adapter instance."""
    return GitHubAdapter(adapter_config)


class TestGitHubAdapterInit:
    """Test adapter initialization."""
    
    def test_adapter_initialization(self, adapter_config, mock_github):
        """Test adapter initialization."""
        adapter = GitHubAdapter(adapter_config)
        
        assert adapter is not None
        assert adapter.config == adapter_config
        mock_github.assert_called_once_with(
            login_or_token=adapter_config.token,
            base_url=adapter_config.base_url,
            timeout=adapter_config.timeout,
            retry=adapter_config.max_retries,
        )
    
    def test_validate_connection_success(self, github_adapter, mock_github):
        """Test successful connection validation."""
        # Setup mock
        mock_client = mock_github.return_value
        mock_user = Mock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user
        
        result = github_adapter.validate_connection()
        
        assert result is True
        mock_client.get_user.assert_called_once()
    
    def test_validate_connection_failure(self, github_adapter, mock_github):
        """Test connection validation failure."""
        from github import GithubException
        
        mock_client = mock_github.return_value
        mock_client.get_user.side_effect = GithubException(
            status=401,
            data={'message': 'Bad credentials'}
        )
        
        with pytest.raises(APIError, match="Failed to validate"):
            github_adapter.validate_connection()


class TestGitHubAdapterPROperations:
    """Test pull request operations."""
    
    def test_get_pull_request_success(self, github_adapter, mock_github):
        """Test fetching a pull request."""
        # Setup mocks
        mock_client = mock_github.return_value
        mock_repo = Mock()
        mock_pr = self._create_mock_pr()
        mock_file = self._create_mock_file()
        
        mock_client.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr
        mock_pr.get_files.return_value = [mock_file]
        
        # Test
        pr = github_adapter.get_pull_request("owner/repo", 123)
        
        # Assertions
        assert pr is not None
        assert pr.id == 123
        assert pr.title == "Test PR"
        assert pr.author == "testuser"
        assert pr.platform == "github"
        assert len(pr.files_changed) == 1
    
    def test_get_pull_request_not_found(self, github_adapter, mock_github):
        """Test fetching non-existent PR."""
        from github import GithubException
        
        mock_client = mock_github.return_value
        mock_repo = Mock()
        mock_client.get_repo.return_value = mock_repo
        mock_repo.get_pull.side_effect = GithubException(
            status=404,
            data={'message': 'Not Found'}
        )
        
        with pytest.raises(NotFoundError, match="not found"):
            github_adapter.get_pull_request("owner/repo", 999)
    
    def test_get_pull_request_permission_denied(self, github_adapter, mock_github):
        """Test fetching PR with insufficient permissions."""
        from github import GithubException
        
        mock_client = mock_github.return_value
        mock_repo = Mock()
        mock_client.get_repo.return_value = mock_repo
        mock_repo.get_pull.side_effect = GithubException(
            status=403,
            data={'message': 'Forbidden'}
        )
        
        with pytest.raises(CustomPermissionError, match="Access denied"):
            github_adapter.get_pull_request("owner/repo", 123)
    
    def test_get_pull_request_files(self, github_adapter, mock_github):
        """Test fetching PR files."""
        mock_client = mock_github.return_value
        mock_repo = Mock()
        mock_pr = Mock()
        mock_file = self._create_mock_file()
        
        mock_client.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr
        mock_pr.get_files.return_value = [mock_file]
        
        files = github_adapter.get_pull_request_files("owner/repo", 123)
        
        assert len(files) == 1
        assert files[0].filename == "test.py"
        assert files[0].status == FileStatus.MODIFIED
        assert files[0].additions == 10
        assert files[0].deletions == 5
    
    def test_list_pull_requests(self, github_adapter, mock_github):
        """Test listing pull requests."""
        mock_client = mock_github.return_value
        mock_repo = Mock()
        mock_pr1 = self._create_mock_pr(number=1, title="PR 1")
        mock_pr2 = self._create_mock_pr(number=2, title="PR 2")
        
        mock_client.get_repo.return_value = mock_repo
        mock_repo.get_pulls.return_value = [mock_pr1, mock_pr2]
        
        prs = github_adapter.list_pull_requests("owner/repo", state="open", limit=10)
        
        assert len(prs) == 2
        assert prs[0].id == 1
        assert prs[1].id == 2
    
    @staticmethod
    def _create_mock_pr(number=123, title="Test PR"):
        """Create a mock GitHub PR object."""
        mock_pr = Mock()
        mock_pr.number = number
        mock_pr.title = title
        mock_pr.body = "Test description"
        mock_pr.state = "open"
        mock_pr.created_at = datetime(2024, 1, 1)
        mock_pr.updated_at = datetime(2024, 1, 2)
        mock_pr.html_url = f"https://github.com/owner/repo/pull/{number}"
        mock_pr.url = f"https://api.github.com/repos/owner/repo/pulls/{number}"
        mock_pr.merged = False
        mock_pr.merged_at = None
        mock_pr.mergeable = True
        mock_pr.changed_files = 3  # Add this for the file count
        mock_pr.additions = 50  # Add this for additions count
        mock_pr.deletions = 20  # Add this for deletions count
        
        # Mock user
        mock_pr.user = Mock()
        mock_pr.user.login = "testuser"
        
        # Mock head and base
        mock_pr.head = Mock()
        mock_pr.head.ref = "feature-branch"
        mock_pr.head.sha = "abc123"
        
        mock_pr.base = Mock()
        mock_pr.base.ref = "main"
        mock_pr.base.sha = "def456"
        mock_pr.base.repo = Mock()
        mock_pr.base.repo.full_name = "owner/repo"
        
        return mock_pr
    
    @staticmethod
    def _create_mock_file(filename="test.py"):
        """Create a mock GitHub file object."""
        mock_file = Mock()
        mock_file.filename = filename
        mock_file.status = "modified"
        mock_file.additions = 10
        mock_file.deletions = 5
        mock_file.patch = "@@ -1,5 +1,10 @@\n test"
        mock_file.previous_filename = None
        return mock_file


class TestGitHubAdapterComments:
    """Test comment operations."""
    
    def test_post_review_comment_inline(self, github_adapter, mock_github):
        """Test posting inline review comment."""
        mock_client = mock_github.return_value
        mock_repo = Mock()
        mock_pr = Mock()
        mock_comment = Mock()
        mock_comment.id = 123456
        
        mock_client.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr
        mock_pr.head.sha = "abc123"
        mock_pr.create_review_comment.return_value = mock_comment
        
        comment = Comment(
            body="Test comment",
            line=10,
            path="test.py",
            severity=SeverityLevel.WARNING
        )
        
        comment_id = github_adapter.post_review_comment("owner/repo", 1, comment)
        
        assert comment_id == "123456"
        mock_pr.create_review_comment.assert_called_once()
    
    def test_post_review_comment_general(self, github_adapter, mock_github):
        """Test posting general comment."""
        mock_client = mock_github.return_value
        mock_repo = Mock()
        mock_pr = Mock()
        mock_comment = Mock()
        mock_comment.id = 789
        
        mock_client.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr
        mock_pr.create_issue_comment.return_value = mock_comment
        
        comment = Comment(
            body="General comment",
            severity=SeverityLevel.INFO
        )
        
        comment_id = github_adapter.post_review_comment("owner/repo", 1, comment)
        
        assert comment_id == "789"
        mock_pr.create_issue_comment.assert_called_once()
    
    def test_post_review(self, github_adapter, mock_github):
        """Test posting complete review."""
        mock_client = mock_github.return_value
        mock_repo = Mock()
        mock_pr = Mock()
        mock_review = Mock()
        mock_review.id = 999
        
        mock_client.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr
        mock_pr.create_review.return_value = mock_review
        
        comments = [
            Comment(body="Issue 1", line=10, path="test.py", severity=SeverityLevel.ERROR),
            Comment(body="Issue 2", line=20, path="test.py", severity=SeverityLevel.WARNING),
        ]
        
        review_id = github_adapter.post_review(
            "owner/repo", 1, comments, "Overall good", "COMMENT"
        )
        
        assert review_id == "999"
        mock_pr.create_review.assert_called_once()


class TestGitHubAdapterRepository:
    """Test repository operations."""
    
    def test_get_repository_info(self, github_adapter, mock_github):
        """Test fetching repository info."""
        mock_client = mock_github.return_value
        mock_repo = Mock()
        mock_repo.owner.login = "testowner"
        mock_repo.name = "testrepo"
        mock_repo.full_name = "testowner/testrepo"
        mock_repo.default_branch = "main"
        mock_repo.private = False
        mock_repo.html_url = "https://github.com/testowner/testrepo"
        
        mock_client.get_repo.return_value = mock_repo
        
        repo_info = github_adapter.get_repository_info("testowner/testrepo")
        
        assert repo_info.owner == "testowner"
        assert repo_info.name == "testrepo"
        assert repo_info.full_name == "testowner/testrepo"
        assert repo_info.default_branch == "main"
        assert repo_info.is_private is False
    
    def test_get_file_content(self, github_adapter, mock_github):
        """Test fetching file content."""
        mock_client = mock_github.return_value
        mock_repo = Mock()
        mock_content = Mock()
        mock_content.decoded_content = b"def hello():\n    pass"
        
        mock_client.get_repo.return_value = mock_repo
        mock_repo.get_contents.return_value = mock_content
        
        content = github_adapter.get_file_content("owner/repo", "test.py", "main")
        
        assert "def hello():" in content
        mock_repo.get_contents.assert_called_once_with("test.py", ref="main")


class TestGitHubAdapterRateLimit:
    """Test rate limit operations."""
    
    def test_get_rate_limit(self, github_adapter, mock_github):
        """Test getting rate limit info."""
        mock_client = mock_github.return_value
        mock_rate_limit = Mock()
        mock_resources = Mock()
        mock_core = Mock()
        mock_core.limit = 5000
        mock_core.remaining = 4500
        mock_core.reset = Mock()
        mock_core.reset.timestamp = Mock(return_value=1234567890)
        
        mock_resources.core = mock_core
        mock_rate_limit.resources = mock_resources
        mock_client.get_rate_limit.return_value = mock_rate_limit
        
        rate_info = github_adapter.get_rate_limit()
        
        assert rate_info.limit == 5000
        assert rate_info.remaining == 4500
        assert rate_info.reset_at == 1234567890


class TestGitHubAdapterHelpers:
    """Test helper methods."""
    
    def test_map_github_status(self, github_adapter):
        """Test GitHub status mapping."""
        assert github_adapter._map_github_status('added') == FileStatus.ADDED
        assert github_adapter._map_github_status('modified') == FileStatus.MODIFIED
        assert github_adapter._map_github_status('removed') == FileStatus.DELETED
        assert github_adapter._map_github_status('renamed') == FileStatus.RENAMED
        assert github_adapter._map_github_status('unknown') == FileStatus.MODIFIED
    
    def test_convert_github_pr(self, github_adapter):
        """Test converting GitHub PR to our model."""
        mock_pr = TestGitHubAdapterPROperations._create_mock_pr()
        files = [
            FileChange(
                filename="test.py",
                status=FileStatus.MODIFIED,
                additions=10,
                deletions=5
            )
        ]
        
        pr = github_adapter._convert_github_pr(mock_pr, files)
        
        assert pr.id == 123
        assert pr.title == "Test PR"
        assert pr.author == "testuser"
        assert pr.platform == "github"
        assert pr.source_branch == "feature-branch"
        assert pr.target_branch == "main"
        assert len(pr.files_changed) == 1