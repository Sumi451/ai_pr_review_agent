import pytest
from ai_pr_agent.reporters import MarkdownFormatter
from ai_pr_agent.core.models import Comment, SeverityLevel, ReviewSummary

class TestMarkdownFormatter:
    """Test markdown formatter."""
    
    def test_format_comment(self):
        """Test comment formatting."""
        formatter = MarkdownFormatter()
        
        comment = Comment(
            body="Test issue",
            line=10,
            severity=SeverityLevel.ERROR,
            path="test.py"
        )
        
        formatted = formatter.format_comment(comment)
        
        assert "ERROR" in formatted
        assert "Test issue" in formatted
    
    def test_format_review_summary(self, sample_review_summary):
        """Test review summary formatting."""
        formatter = MarkdownFormatter()
        
        formatted = formatter.format_review_summary(sample_review_summary)
        
        assert "Code Review" in formatted
        assert "Files Analyzed" in formatted
        assert "Total Comments" in formatted
    
    def test_format_summary_comment(self, sample_review_summary):
        """Test summary comment formatting."""
        formatter = MarkdownFormatter()
        
        formatted = formatter.format_summary_comment(sample_review_summary)
        
        assert "Summary" in formatted
        assert "Files" in formatted
