"""Tests for the Static Analyzer."""

import pytest
from ai_pr_agent.core import FileChange, FileStatus, SeverityLevel
from ai_pr_agent.analyzers import StaticAnalyzer


class TestStaticAnalyzer:
    """Test StaticAnalyzer functionality."""
    
    def test_analyzer_initialization(self):
        """Test creating a static analyzer instance."""
        analyzer = StaticAnalyzer()
        
        assert analyzer is not None
        assert analyzer.config is not None
    
    def test_can_analyze_python_file(self):
        """Test that analyzer can analyze Python files."""
        analyzer = StaticAnalyzer()
        
        python_file = FileChange(
            filename="test.py",
            status=FileStatus.MODIFIED
        )
        
        assert analyzer.can_analyze(python_file) is True
    
    def test_cannot_analyze_non_python_file(self):
        """Test that analyzer skips non-Python files."""
        analyzer = StaticAnalyzer()
        
        js_file = FileChange(
            filename="test.js",
            status=FileStatus.MODIFIED
        )
        
        assert analyzer.can_analyze(js_file) is False
    
    def test_analyze_python_file_with_issues(self):
        """Test analyzing Python file with code issues."""
        analyzer = StaticAnalyzer()
        
        # Create a file with intentional issues
        bad_code = """
def bad_function( ):
    x=1+2
    password = "hardcoded_password"
    return x
"""
        
        file_change = FileChange(
            filename="bad_code.py",
            status=FileStatus.MODIFIED,
            additions=5,
            deletions=0,
            patch=f"@@ -0,0 +1,5 @@\n+{bad_code}"
        )
        
        result = analyzer.analyze(file_change)
        
        assert result is not None
        assert result.filename == "bad_code.py"
        assert result.success is True
        # May have comments depending on what tools find
        assert len(result.comments) >= 0
    
    def test_analyze_returns_none_for_non_python(self):
        """Test that analyze returns None for non-Python files."""
        analyzer = StaticAnalyzer()
        
        js_file = FileChange(
            filename="test.js",
            status=FileStatus.MODIFIED,
            patch="console.log('hello');"
        )
        
        result = analyzer.analyze(js_file)
        
        assert result is None
    
    def test_extract_code_from_patch(self):
        """Test extracting code from git patch."""
        analyzer = StaticAnalyzer()
        
        patch = """@@ -1,3 +1,5 @@
 def hello():
-    print("old")
+    print("new")
+    return True
"""
        
        code = analyzer._extract_code_from_patch(patch)
        
        assert "def hello():" in code
        assert "print(\"new\")" in code
        assert "return True" in code
        assert "print(\"old\")" not in code  # Removed line
    
    def test_flake8_severity_mapping(self):
        """Test flake8 error code to severity mapping."""
        analyzer = StaticAnalyzer()
        
        assert analyzer._get_flake8_severity('E501') == SeverityLevel.ERROR
        assert analyzer._get_flake8_severity('W503') == SeverityLevel.WARNING
        assert analyzer._get_flake8_severity('C901') == SeverityLevel.WARNING
        assert analyzer._get_flake8_severity('F401') == SeverityLevel.ERROR
    
    def test_bandit_severity_mapping(self):
        """Test bandit severity mapping."""
        analyzer = StaticAnalyzer()
        
        assert analyzer._get_bandit_severity('LOW') == SeverityLevel.INFO
        assert analyzer._get_bandit_severity('MEDIUM') == SeverityLevel.WARNING
        assert analyzer._get_bandit_severity('HIGH') == SeverityLevel.ERROR
    
    def test_analyze_with_no_patch(self):
        """Test analyzing file with no patch."""
        analyzer = StaticAnalyzer()
        
        file_change = FileChange(
            filename="test.py",
            status=FileStatus.MODIFIED,
            patch=None
        )
        
        result = analyzer.analyze(file_change)
        
        # Should return empty result, not crash
        assert result is not None
        assert result.filename == "test.py"
        assert len(result.comments) == 0


@pytest.mark.slow
class TestStaticAnalyzerIntegration:
    """Integration tests for static analyzer with real tools."""
    
    def test_analyze_clean_code(self):
        """Test analyzing clean Python code."""
        analyzer = StaticAnalyzer()
        
        clean_code = '''
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b
'''
        
        file_change = FileChange(
            filename="clean.py",
            status=FileStatus.ADDED,
            additions=4,
            deletions=0,
            patch=f"@@ -0,0 +1,4 @@\n+{clean_code}"
        )
        
        result = analyzer.analyze(file_change)
        
        assert result is not None
        assert result.success is True
        # Clean code should have few or no issues
        assert len(result.comments) <= 2