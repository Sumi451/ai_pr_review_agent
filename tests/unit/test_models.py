"""Tests for core data models."""

import pytest
from datetime import datetime

from ai_pr_agent.core import (
    SeverityLevel,
    FileStatus,
    AnalysisType,
    FileChange,
    Comment,
    AnalysisResult,
    PullRequest,
    ReviewSummary,
)


class TestFileChange:
    """Test FileChange model."""
    
    def test_file_change_creation(self):
        """Test creating a FileChange instance."""
        file_change = FileChange(
            filename="src/main.py",
            status=FileStatus.MODIFIED,
            additions=10,
            deletions=5
        )
        
        assert file_change.filename == "src/main.py"
        assert file_change.status == FileStatus.MODIFIED
        assert file_change.additions == 10
        assert file_change.deletions == 5
        assert file_change.language == "python"
    
    def test_language_detection(self):
        """Test automatic language detection."""
        test_cases = [
            ("app.py", "python"),
            ("script.js", "javascript"),
            ("component.ts", "typescript"),
            ("Main.java", "java"),
            ("utils.cpp", "cpp"),
            ("config.go", "go"),
            ("unknown.txt", "unknown"),
        ]
        
        for filename, expected_lang in test_cases:
            fc = FileChange(filename=filename, status=FileStatus.ADDED)
            assert fc.language == expected_lang
    
    def test_total_changes(self):
        """Test total_changes property."""
        fc = FileChange(
            filename="test.py",
            status=FileStatus.MODIFIED,
            additions=15,
            deletions=8
        )
        assert fc.total_changes == 23
    
    def test_is_new_file(self):
        """Test is_new_file property."""
        new_file = FileChange(filename="new.py", status=FileStatus.ADDED)
        modified_file = FileChange(filename="old.py", status=FileStatus.MODIFIED)
        
        assert new_file.is_new_file is True
        assert modified_file.is_new_file is False
    
    def test_string_status_conversion(self):
        """Test automatic string to enum conversion."""
        fc = FileChange(filename="test.py", status="modified")
        assert fc.status == FileStatus.MODIFIED


class TestComment:
    """Test Comment model."""
    
    def test_comment_creation(self):
        """Test creating a Comment instance."""
        comment = Comment(
            body="This function is too complex",
            line=42,
            severity=SeverityLevel.WARNING,
            path="src/complex.py"
        )
        
        assert comment.body == "This function is too complex"
        assert comment.line == 42
        assert comment.severity == SeverityLevel.WARNING
        assert comment.path == "src/complex.py"
    
    def test_is_inline(self):
        """Test is_inline property."""
        inline_comment = Comment(body="Fix this", line=10)
        file_comment = Comment(body="General issue")
        
        assert inline_comment.is_inline is True
        assert file_comment.is_inline is False
    
    def test_is_critical(self):
        """Test is_critical property."""
        error_comment = Comment(body="Error!", severity=SeverityLevel.ERROR)
        warning_comment = Comment(body="Warning", severity=SeverityLevel.WARNING)
        
        assert error_comment.is_critical is True
        assert warning_comment.is_critical is False
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        comment = Comment(
            body="Test comment",
            severity=SeverityLevel.INFO,
            line=5,
            path="test.py"
        )
        
        result = comment.to_dict()
        
        assert result['body'] == "Test comment"
        assert result['severity'] == "info"
        assert result['line'] == 5
        assert result['path'] == "test.py"


class TestAnalysisResult:
    """Test AnalysisResult model."""
    
    def test_analysis_result_creation(self):
        """Test creating an AnalysisResult instance."""
        result = AnalysisResult(
            filename="test.py",
            analysis_type=AnalysisType.STATIC,
            execution_time=1.5
        )
        
        assert result.filename == "test.py"
        assert result.analysis_type == AnalysisType.STATIC
        assert result.execution_time == 1.5
        assert result.success is True
        assert len(result.comments) == 0
    
    def test_add_comment(self):
        """Test adding comments to analysis result."""
        result = AnalysisResult(filename="test.py")
        
        result.add_comment("Issue 1", line=10, severity=SeverityLevel.ERROR)
        result.add_comment("Issue 2", line=20, severity=SeverityLevel.WARNING)
        
        assert len(result.comments) == 2
        assert result.comments[0].severity == SeverityLevel.ERROR
        assert result.comments[1].severity == SeverityLevel.WARNING
    
    def test_has_errors_and_warnings(self):
        """Test error and warning detection."""
        result = AnalysisResult(filename="test.py")
        
        assert result.has_errors is False
        assert result.has_warnings is False
        
        result.add_comment("Error", severity=SeverityLevel.ERROR)
        result.add_comment("Warning", severity=SeverityLevel.WARNING)
        
        assert result.has_errors is True
        assert result.has_warnings is True
    
    def test_comment_counts(self):
        """Test comment counting."""
        result = AnalysisResult(filename="test.py")
        
        result.add_comment("Error 1", severity=SeverityLevel.ERROR)
        result.add_comment("Error 2", severity=SeverityLevel.ERROR)
        result.add_comment("Warning", severity=SeverityLevel.WARNING)
        
        assert result.error_count == 2
        assert result.warning_count == 1
    
    def test_get_comments_by_severity(self):
        """Test filtering comments by severity."""
        result = AnalysisResult(filename="test.py")
        
        result.add_comment("Error", severity=SeverityLevel.ERROR)
        result.add_comment("Warning", severity=SeverityLevel.WARNING)
        result.add_comment("Info", severity=SeverityLevel.INFO)
        
        errors = result.get_comments_by_severity(SeverityLevel.ERROR)
        assert len(errors) == 1
        assert errors[0].body == "Error"


class TestPullRequest:
    """Test PullRequest model."""
    
    def test_pull_request_creation(self):
        """Test creating a PullRequest instance."""
        pr = PullRequest(
            id=123,
            title="Add new feature",
            description="This PR adds a new feature",
            author="developer",
            source_branch="feature/new-feature",
            target_branch="main"
        )
        
        assert pr.id == 123
        assert pr.title == "Add new feature"
        assert pr.author == "developer"
        assert pr.source_branch == "feature/new-feature"
        assert pr.target_branch == "main"
    
    def test_with_file_changes(self):
        """Test PR with file changes."""
        file1 = FileChange(
            filename="file1.py",
            status=FileStatus.MODIFIED,
            additions=10,
            deletions=5
        )
        file2 = FileChange(
            filename="file2.js",
            status=FileStatus.ADDED,
            additions=20,
            deletions=0
        )
        
        pr = PullRequest(
            id=123,
            title="Test PR",
            description="Test",
            author="test",
            source_branch="test",
            files_changed=[file1, file2]
        )
        
        assert len(pr.files_changed) == 2
        assert pr.total_additions == 30
        assert pr.total_deletions == 5
        assert pr.total_changes == 35
    
    def test_languages_property(self):
        """Test languages property."""
        files = [
            FileChange(filename="app.py", status=FileStatus.MODIFIED),
            FileChange(filename="script.js", status=FileStatus.MODIFIED),
            FileChange(filename="utils.py", status=FileStatus.ADDED),
        ]
        
        pr = PullRequest(
            id=1,
            title="Test",
            description="Test",
            author="test",
            source_branch="test",
            files_changed=files
        )
        
        assert set(pr.languages) == {"python", "javascript"}
    
    def test_file_filtering(self):
        """Test file filtering methods."""
        files = [
            FileChange(filename="new.py", status=FileStatus.ADDED),
            FileChange(filename="modified.py", status=FileStatus.MODIFIED),
            FileChange(filename="deleted.py", status=FileStatus.DELETED),
        ]
        
        pr = PullRequest(
            id=1,
            title="Test",
            description="Test",
            author="test",
            source_branch="test",
            files_changed=files
        )
        
        assert len(pr.new_files) == 1
        assert len(pr.modified_files) == 1
        assert len(pr.deleted_files) == 1
    
    def test_get_files_by_language(self):
        """Test filtering files by language."""
        files = [
            FileChange(filename="app.py", status=FileStatus.MODIFIED),
            FileChange(filename="script.js", status=FileStatus.MODIFIED),
            FileChange(filename="utils.py", status=FileStatus.ADDED),
        ]
        
        pr = PullRequest(
            id=1,
            title="Test",
            description="Test",
            author="test",
            source_branch="test",
            files_changed=files
        )
        
        python_files = pr.get_files_by_language("python")
        assert len(python_files) == 2


class TestReviewSummary:
    """Test ReviewSummary model."""
    
    def test_review_summary_creation(self):
        """Test creating a ReviewSummary instance."""
        pr = PullRequest(
            id=1,
            title="Test",
            description="Test",
            author="test",
            source_branch="test"
        )
        
        result1 = AnalysisResult(filename="file1.py")
        result1.add_comment("Issue", severity=SeverityLevel.ERROR)
        
        result2 = AnalysisResult(filename="file2.py")
        result2.add_comment("Warning", severity=SeverityLevel.WARNING)
        
        summary = ReviewSummary(
            pull_request=pr,
            analysis_results=[result1, result2]
        )
        
        all_comments = summary.get_all_comments()
        assert len(all_comments) == 2
    
    def test_get_comments_by_severity(self):
        """Test filtering comments by severity."""
        pr = PullRequest(
            id=1,
            title="Test",
            description="Test",
            author="test",
            source_branch="test"
        )
        
        result = AnalysisResult(filename="test.py")
        result.add_comment("Error", severity=SeverityLevel.ERROR)
        result.add_comment("Warning", severity=SeverityLevel.WARNING)
        result.add_comment("Info", severity=SeverityLevel.INFO)
        
        summary = ReviewSummary(
            pull_request=pr,
            analysis_results=[result]
        )
        
        errors = summary.get_comments_by_severity(SeverityLevel.ERROR)
        assert len(errors) == 1
        assert errors[0].body == "Error"