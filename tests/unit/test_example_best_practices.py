"""
Example test file demonstrating testing best practices.
Use this as a template for writing new tests.
"""

import pytest
from ai_pr_agent.core import FileChange, FileStatus, SeverityLevel


class TestExampleBestPractices:
    """Example test class showing best practices."""
    
    def test_using_fixtures(self, sample_file_change):
        """
        Test using fixtures for test data.
        
        Fixtures make tests more readable and maintainable.
        """
        # Act
        result = sample_file_change.total_changes
        
        # Assert
        assert result == 15
        assert sample_file_change.language == "python"
    
    def test_with_parametrize(self):
        """
        Test using parametrize for multiple test cases.
        
        This is more efficient than writing multiple similar tests.
        """
        test_cases = [
            ("test.py", "python"),
            ("script.js", "javascript"),
            ("app.java", "java"),
            ("unknown.txt", "unknown"),
        ]
        
        for filename, expected_lang in test_cases:
            file_change = FileChange(filename=filename, status=FileStatus.ADDED)
            assert file_change.language == expected_lang
    
    @pytest.mark.parametrize("filename,expected_lang", [
        ("test.py", "python"),
        ("script.js", "javascript"),
        ("app.java", "java"),
        ("unknown.txt", "unknown"),
    ])
    def test_with_parametrize_decorator(self, filename, expected_lang):
        """
        Better way: Use pytest's parametrize decorator.
        
        This creates separate test cases automatically.
        """
        file_change = FileChange(filename=filename, status=FileStatus.ADDED)
        assert file_change.language == expected_lang
    
    def test_with_proper_naming(self):
        """
        Test names should clearly describe what is being tested.
        
        Format: test_<what>_<condition>_<expected_result>
        """
        # Arrange
        file_change = FileChange(
            filename="test.py",
            status=FileStatus.MODIFIED,
            additions=10,
            deletions=5
        )
        
        # Act
        is_new = file_change.is_new_file
        
        # Assert
        assert is_new is False
    
    def test_error_handling(self):
        """Test that errors are raised correctly."""
        with pytest.raises(ValueError):
            # This should raise ValueError
            FileStatus("invalid_status")
    
    @pytest.mark.slow
    def test_marked_as_slow(self):
        """
        Tests can be marked for selective execution.
        
        Run only slow tests: pytest -m slow
        Skip slow tests: pytest -m "not slow"
        """
        # Simulate slow operation
        import time
        time.sleep(0.1)
        assert True
    
    def test_with_setup_and_teardown(self, tmp_path):
        """
        Use fixtures for setup and teardown.
        
        tmp_path is a built-in pytest fixture for temporary directories.
        """
        # Setup: Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Test
        assert test_file.exists()
        assert test_file.read_text() == "test content"
        
        # Teardown happens automatically


class TestMockingExample:
    """Example of mocking external dependencies."""
    
    def test_with_mock(self, mocker):
        """
        Test using pytest-mock for mocking.
        
        Mocking is useful for testing without external dependencies.
        """
        # Mock a function
        mock_logger = mocker.patch('ai_pr_agent.core.models.logger')
        
        # Create object that uses the logger
        file_change = FileChange(filename="test.py", status=FileStatus.ADDED)
        
        # Verify logger was called
        mock_logger.debug.assert_called()