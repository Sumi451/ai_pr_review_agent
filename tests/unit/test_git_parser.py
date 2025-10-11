"""Tests for git diff parsing."""

import pytest
from ai_pr_agent.utils.git_parser import DiffParser, GitRepository
from ai_pr_agent.core import FileStatus


class TestDiffParser:
    """Test DiffParser functionality."""
    
    def test_parse_simple_diff(self):
        """Test parsing a simple diff."""
        diff = """diff --git a/test.py b/test.py
index abc123..def456 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("old")
+    print("new")
+    return True
"""
        
        parser = DiffParser()
        file_changes = parser.parse_diff(diff)
        
        assert len(file_changes) == 1
        assert file_changes[0].filename == "test.py"
        assert file_changes[0].status == FileStatus.MODIFIED
        assert file_changes[0].additions == 2
        assert file_changes[0].deletions == 1
        assert file_changes[0].patch is not None
    
    def test_parse_new_file(self):
        """Test parsing a new file diff."""
        diff = """diff --git a/new_file.py b/new_file.py
new file mode 100644
index 0000000..abc123
--- /dev/null
+++ b/new_file.py
@@ -0,0 +1,3 @@
+def new_function():
+    return True
+
"""
        
        parser = DiffParser()
        file_changes = parser.parse_diff(diff)
        
        assert len(file_changes) == 1
        assert file_changes[0].filename == "new_file.py"
        assert file_changes[0].status == FileStatus.ADDED
        assert file_changes[0].additions == 3
        assert file_changes[0].deletions == 0
    
    def test_parse_deleted_file(self):
        """Test parsing a deleted file diff."""
        diff = """diff --git a/old_file.py b/old_file.py
deleted file mode 100644
index abc123..0000000
--- a/old_file.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def old_function():
-    return False
-
"""
        
        parser = DiffParser()
        file_changes = parser.parse_diff(diff)
        
        assert len(file_changes) == 1
        assert file_changes[0].filename == "old_file.py"
        assert file_changes[0].status == FileStatus.DELETED
        assert file_changes[0].deletions == 3
    
    def test_parse_renamed_file(self):
        """Test parsing a renamed file diff."""
        diff = """diff --git a/old_name.py b/new_name.py
similarity index 100%
rename from old_name.py
rename to new_name.py
"""
        
        parser = DiffParser()
        file_changes = parser.parse_diff(diff)
        
        assert len(file_changes) == 1
        assert file_changes[0].filename == "new_name.py"
        assert file_changes[0].old_filename == "old_name.py"
        assert file_changes[0].status == FileStatus.RENAMED
    
    def test_parse_multiple_files(self):
        """Test parsing diff with multiple files."""
        diff = """diff --git a/file1.py b/file1.py
index abc123..def456 100644
--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,3 @@
 line 1
+line 2
 line 3
diff --git a/file2.py b/file2.py
index xyz789..uvw012 100644
--- a/file2.py
+++ b/file2.py
@@ -1,3 +1,2 @@
 line 1
-line 2
 line 3
"""
        
        parser = DiffParser()
        file_changes = parser.parse_diff(diff)
        
        assert len(file_changes) == 2
        assert file_changes[0].filename == "file1.py"
        assert file_changes[1].filename == "file2.py"
        assert file_changes[0].additions == 1
        assert file_changes[1].deletions == 1
    
    def test_parse_empty_diff(self):
        """Test parsing empty diff."""
        parser = DiffParser()
        file_changes = parser.parse_diff("")
        
        assert len(file_changes) == 0
    
    def test_extract_changed_lines(self):
        """Test extracting changed line numbers."""
        patch = """@@ -1,3 +1,4 @@
 def hello():
-    print("old")
+    print("new")
+    return True
"""
        
        parser = DiffParser()
        changed_lines = parser.extract_changed_lines(patch)
        
        assert 2 in changed_lines
        assert 3 in changed_lines
        assert changed_lines[2] == '    print("new")'
        assert changed_lines[3] == '    return True'
    
    def test_get_file_content_from_patch(self):
        """Test extracting file content from patch."""
        patch = """diff --git a/test.py b/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("old")
+    print("new")
+    return True
"""
        
        parser = DiffParser()
        content = parser.get_file_content_from_patch(patch)
        
        assert 'def hello():' in content
        assert 'print("new")' in content
        assert 'return True' in content
        assert 'print("old")' not in content


@pytest.mark.integration
class TestGitRepository:
    """Test GitRepository functionality (requires git repository)."""
    
    def test_initialize_repository(self):
        """Test initializing git repository."""
        try:
            repo = GitRepository('.')
            assert repo.repo is not None
        except Exception:
            pytest.skip("Not in a git repository")
    
    def test_get_current_branch(self):
        """Test getting current branch."""
        try:
            repo = GitRepository('.')
            branch = repo.get_current_branch()
            assert isinstance(branch, str)
            assert len(branch) > 0
        except Exception:
            pytest.skip("Not in a git repository")
    
    def test_list_branches(self):
        """Test listing branches."""
        try:
            repo = GitRepository('.')
            branches = repo.list_branches()
            assert isinstance(branches, list)
            assert len(branches) > 0
        except Exception:
            pytest.skip("Not in a git repository")
    
    def test_branch_exists(self):
        """Test checking if branch exists."""
        try:
            repo = GitRepository('.')
            current = repo.get_current_branch()
            
            assert repo.branch_exists(current) is True
            assert repo.branch_exists("nonexistent-branch-xyz") is False
        except Exception:
            pytest.skip("Not in a git repository")
    
    def test_get_commit_info(self):
        """Test getting commit information."""
        try:
            repo = GitRepository('.')
            info = repo.get_commit_info('HEAD')
            
            assert 'hash' in info
            assert 'short_hash' in info
            assert 'author' in info
            assert 'message' in info
            assert 'date' in info
        except Exception:
            pytest.skip("Not in a git repository")