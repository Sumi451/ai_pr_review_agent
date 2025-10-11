"""Integration tests for git functionality."""

import pytest
import tempfile
import os
from pathlib import Path

from ai_pr_agent.utils.git_parser import GitRepository, DiffParser
from ai_pr_agent.core import FileStatus


@pytest.mark.integration
class TestGitIntegration:
    """Integration tests for git operations."""
    
    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary git repository for testing."""
        pytest.importorskip("git")  # Skip if GitPython not installed
        
        import git
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize repo
            repo = git.Repo.init(tmpdir)
            
            # Configure git
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@example.com").release()
            
            # Create initial file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello():\n    print('Hello')\n")
            
            repo.index.add(["test.py"])
            repo.index.commit("Initial commit")
            
            yield tmpdir, repo
    
    def test_parse_real_git_diff(self, temp_git_repo):
        """Test parsing a real git diff."""
        tmpdir, git_repo = temp_git_repo
        
        # Modify file
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("def hello():\n    print('Hello, World!')\n    return True\n")
        
        # Get diff
        diff_text = git_repo.git.diff()
        
        # Parse diff
        parser = DiffParser()
        file_changes = parser.parse_diff(diff_text)
        
        assert len(file_changes) == 1
        assert file_changes[0].filename == "test.py"
        assert file_changes[0].additions == 2
        assert file_changes[0].deletions == 1
    
    def test_git_repository_operations(self, temp_git_repo):
        """Test GitRepository class operations."""
        tmpdir, _ = temp_git_repo
        
        repo = GitRepository(tmpdir)
        
        # Test getting current branch
        branch = repo.get_current_branch()
        assert branch in ["master", "main"]
        
        # Test listing branches
        branches = repo.list_branches()
        assert len(branches) >= 1
        
        # Test commit info
        info = repo.get_commit_info()
        assert 'hash' in info
        assert 'author' in info
        assert info['author'] == "Test User"
    
    def test_analyze_uncommitted_changes(self, temp_git_repo):
        """Test analyzing uncommitted changes."""
        tmpdir, _ = temp_git_repo
        
        # Modify file
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("def hello():\n    print('Modified')\n")
        
        # Get uncommitted changes
        repo = GitRepository(tmpdir)
        diff_text = repo.get_uncommitted_changes()
        
        assert diff_text
        
        # Parse
        parser = DiffParser()
        file_changes = parser.parse_diff(diff_text)
        
        assert len(file_changes) == 1
        assert file_changes[0].filename == "test.py"


@pytest.mark.skipif(
    not Path('.git').exists(),
    reason="Not in a git repository"
)
class TestRealRepository:
    """Tests using the actual repository."""
    
    def test_current_repository(self):
        """Test operations on current repository."""
        repo = GitRepository('.')
        
        # Should not raise
        branch = repo.get_current_branch()
        assert isinstance(branch, str)
        
        branches = repo.list_branches()
        assert len(branches) > 0
        
        info = repo.get_commit_info()
        assert 'hash' in info