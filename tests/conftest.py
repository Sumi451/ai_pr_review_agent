"""
Shared test fixtures and configuration for pytest.
This file is automatically discovered by pytest.
"""

import pytest
from datetime import datetime
from pathlib import Path

from ai_pr_agent.core import (
    FileChange,
    FileStatus,
    Comment,
    SeverityLevel,
    AnalysisResult,
    AnalysisType,
    PullRequest,
    ReviewSummary,
)
from ai_pr_agent.config import Settings


@pytest.fixture
def sample_file_change():
    """Create a sample FileChange for testing."""
    return FileChange(
        filename="src/main.py",
        status=FileStatus.MODIFIED,
        additions=10,
        deletions=5,
        patch="@@ -1,5 +1,10 @@\n+ new line\n- old line"
    )


@pytest.fixture
def sample_file_changes():
    """Create multiple sample FileChanges for testing."""
    return [
        FileChange(
            filename="src/main.py",
            status=FileStatus.MODIFIED,
            additions=10,
            deletions=5
        ),
        FileChange(
            filename="tests/test_main.py",
            status=FileStatus.ADDED,
            additions=20,
            deletions=0
        ),
        FileChange(
            filename="docs/old_file.md",
            status=FileStatus.DELETED,
            additions=0,
            deletions=15
        ),
    ]


@pytest.fixture
def sample_comment():
    """Create a sample Comment for testing."""
    return Comment(
        body="This is a test comment",
        line=42,
        severity=SeverityLevel.WARNING,
        path="src/main.py",
        suggestion="Consider refactoring this function"
    )


@pytest.fixture
def sample_comments():
    """Create multiple sample Comments for testing."""
    return [
        Comment(
            body="Critical error found",
            line=10,
            severity=SeverityLevel.ERROR,
            path="src/main.py"
        ),
        Comment(
            body="Potential issue",
            line=20,
            severity=SeverityLevel.WARNING,
            path="src/main.py"
        ),
        Comment(
            body="Consider this improvement",
            severity=SeverityLevel.SUGGESTION,
            path="src/main.py"
        ),
    ]


@pytest.fixture
def sample_analysis_result():
    """Create a sample AnalysisResult for testing."""
    result = AnalysisResult(
        filename="src/main.py",
        analysis_type=AnalysisType.STATIC,
        execution_time=1.5
    )
    result.add_comment("Error found", line=10, severity=SeverityLevel.ERROR)
    result.add_comment("Warning found", line=20, severity=SeverityLevel.WARNING)
    return result


@pytest.fixture
def sample_pull_request(sample_file_changes):
    """Create a sample PullRequest for testing."""
    return PullRequest(
        id=123,
        title="Add new feature",
        description="This PR adds a cool new feature",
        author="developer",
        source_branch="feature/new-feature",
        target_branch="main",
        files_changed=sample_file_changes,
        created_at=datetime.now(),
        repository="org/repo",
        url="https://github.com/org/repo/pull/123"
    )


@pytest.fixture
def sample_review_summary(sample_pull_request, sample_analysis_result):
    """Create a sample ReviewSummary for testing."""
    return ReviewSummary(
        pull_request=sample_pull_request,
        analysis_results=[sample_analysis_result],
        total_execution_time=2.5
    )


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_content = """
app:
  name: "Test AI PR Review Agent"
  debug: true
  log_level: "DEBUG"

github:
  timeout: 30

analysis:
  static_analysis:
    enabled: true
  ai_feedback:
    enabled: false
"""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def mock_settings():
    """Create a mock Settings object for testing."""
    return Settings()


@pytest.fixture
def sample_diff():
    """Create a sample git diff for testing."""
    return """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,5 +1,10 @@
 def main():
-    print("Hello")
+    print("Hello, World!")
+    return 0
"""


@pytest.fixture
def sample_python_code():
    """Create sample Python code for testing."""
    return '''
def calculate_sum(a, b):
    """Calculate the sum of two numbers."""
    return a + b

def divide(a, b):
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
'''


@pytest.fixture
def sample_javascript_code():
    """Create sample JavaScript code for testing."""
    return '''
function calculateSum(a, b) {
    return a + b;
}

function divide(a, b) {
    if (b === 0) {
        throw new Error("Cannot divide by zero");
    }
    return a / b;
}
'''


# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-add 'unit' marker to tests in tests/unit/
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        # Auto-add 'integration' marker to tests in tests/integration/
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


@pytest.fixture
def sample_git_diff():
    """Sample git diff for testing."""
    return """diff --git a/test.py b/test.py
index abc123..def456 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("old")
+    print("new")
+    return True
"""


@pytest.fixture
def sample_multi_file_diff():
    """Sample multi-file git diff."""
    return """diff --git a/file1.py b/file1.py
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