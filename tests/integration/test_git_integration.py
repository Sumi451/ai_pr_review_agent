"""Integration tests for git functionality."""

import gc
import pytest
import tempfile
import time
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
        
        tmpdir = tempfile.mkdtemp()
        repo = None
        
        try:
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
        finally:
            # Clean up: close git repository to release file handles
            if repo is not None:
                repo.close()
                del repo
            
            # Force garbage collection to release file handles
            gc.collect()
            time.sleep(0.1)
            
            # Try to remove directory with retry logic for Windows
            import shutil
            try:
                shutil.rmtree(tmpdir, ignore_errors=False)
            except PermissionError:
                # On Windows, git may still hold locks
                gc.collect()
                time.sleep(0.5)
                try:
                    shutil.rmtree(tmpdir, ignore_errors=False)
                except PermissionError:
                    # If it still fails, use ignore_errors to avoid test failure
                    shutil.rmtree(tmpdir, ignore_errors=True)
    
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
        
        try:
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
        finally:
            # Close the repository to release file handles
            repo.repo.close()
    
    def test_analyze_uncommitted_changes(self, temp_git_repo):
        """Test analyzing uncommitted changes."""
        tmpdir, _ = temp_git_repo
        
        # Modify file
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("def hello():\n    print('Modified')\n")
        
        # Get uncommitted changes
        repo = GitRepository(tmpdir)
        
        try:
            diff_text = repo.get_uncommitted_changes()
            
            assert diff_text
            
            # Parse
            parser = DiffParser()
            file_changes = parser.parse_diff(diff_text)
            
            assert len(file_changes) == 1
            assert file_changes[0].filename == "test.py"
        finally:
            # Close the repository to release file handles
            repo.repo.close()


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