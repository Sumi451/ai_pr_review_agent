import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from ai_pr_agent.reporters import GitHubReporter, MarkdownFormatter
from ai_pr_agent.core import (
    ReviewSummary,
    PullRequest,
    AnalysisResult,
    Comment,
    SeverityLevel,
    AnalysisType,
    FileChange,
    FileStatus,
)


@pytest.fixture
def mock_adapter():
    """Create mock adapter."""
    adapter = Mock()
    adapter.post_review.return_value = "review_123"
    adapter.post_review_comment.return_value = "comment_456"
    return adapter


@pytest.fixture
def sample_summary():
    """Create sample review summary."""
    pr = PullRequest(
        id=123,
        title="Test PR",
        description="Test",
        author="developer",
        source_branch="feature",
        target_branch="main"
    )
    
    result = AnalysisResult(
        filename="test.py",
        analysis_type=AnalysisType.STATIC
    )
    result.add_comment(
        "Error found",
        line=10,
        severity=SeverityLevel.ERROR
    )
    result.add_comment(
        "Warning found",
        line=20,
        severity=SeverityLevel.WARNING
    )
    
    return ReviewSummary(
        pull_request=pr,
        analysis_results=[result]
    )


class TestGitHubReporter:
    """Test GitHub reporter functionality."""
    
    def test_initialization(self, mock_adapter):
        """Test reporter initialization."""
        reporter = GitHubReporter(mock_adapter)
        assert reporter is not None
        assert reporter.adapter == mock_adapter
    
    def test_post_review(self, mock_adapter, sample_summary):
        """Test posting complete review."""
        reporter = GitHubReporter(mock_adapter)
        
        review_id = reporter.post_review(
            "owner/repo",
            123,
            sample_summary,
            event="COMMENT"
        )
        
        assert review_id == "review_123"
        mock_adapter.post_review.assert_called_once()
    
    def test_post_summary_comment(self, mock_adapter, sample_summary):
        """Test posting summary comment."""
        reporter = GitHubReporter(mock_adapter)
        
        comment_id = reporter.post_summary_comment(
            "owner/repo",
            123,
            sample_summary
        )
        
        assert comment_id == "comment_456"
        mock_adapter.post_review_comment.assert_called_once()
    
    def test_prioritize_comments(self, mock_adapter):
        """Test comment prioritization."""
        reporter = GitHubReporter(mock_adapter)
        
        comments = [
            Comment("Info", line=1, severity=SeverityLevel.INFO, path="a.py"),
            Comment("Error", line=2, severity=SeverityLevel.ERROR, path="a.py"),
            Comment("Warning", line=3, severity=SeverityLevel.WARNING, path="a.py"),
        ]
        
        prioritized = reporter._prioritize_comments(comments, None)
        
        # Should be sorted by severity
        assert prioritized[0].severity == SeverityLevel.ERROR
        assert prioritized[1].severity == SeverityLevel.WARNING
    
    def test_determine_review_event(self, mock_adapter, sample_summary):
        """Test review event determination."""
        reporter = GitHubReporter(mock_adapter)
        
        # Has errors - should request changes
        event = reporter._determine_review_event(sample_summary)
        assert event == "REQUEST_CHANGES"