"""Tests for CLI functionality."""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile

from ai_pr_agent.cli import main, config, analyze, scan, demo, info


class TestCLI:
    """Test CLI commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_main_help(self):
        """Test main command help."""
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'AI Pull Request Review Agent CLI' in result.output
    
    def test_config_command(self):
        """Test config command."""
        result = self.runner.invoke(config)
        assert result.exit_code == 0
    
    def test_config_validate(self):
        """Test config validation."""
        result = self.runner.invoke(config, ['--validate'])
        # May fail if GitHub token not set, but shouldn't crash
        assert result.exit_code in [0, 1]
    
    def test_info_command(self):
        """Test info command."""
        result = self.runner.invoke(info)
        assert result.exit_code == 0
        assert 'AI PR Review Agent' in result.output
    
    def test_info_with_stats(self):
        """Test info command with statistics."""
        result = self.runner.invoke(info, ['--show-stats'])
        assert result.exit_code == 0
        assert 'Engine Statistics' in result.output
    
    def test_demo_command(self):
        """Test demo command."""
        result = self.runner.invoke(demo)
        assert result.exit_code == 0
        assert 'Demo complete' in result.output
    
    def test_analyze_no_files(self):
        """Test analyze with no files."""
        result = self.runner.invoke(analyze, [])
        assert result.exit_code == 1
        assert 'No files specified' in result.output
    
    def test_analyze_with_file(self):
        """Test analyze with a Python file."""
        # Create temporary Python file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as tmp_file:
            tmp_file.write('def hello():\n    print("Hello")\n')
            tmp_path = tmp_file.name
        
        try:
            result = self.runner.invoke(analyze, [tmp_path])
            assert result.exit_code == 0
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_scan_command(self):
        """Test scan command."""
        # Use current directory
        result = self.runner.invoke(scan, ['.'])
        assert result.exit_code == 0


class TestCLIHelpers:
    """Test CLI helper functions."""
    
    def test_find_python_files(self):
        """Test finding Python files."""
        from ai_pr_agent.utils.cli_helpers import find_python_files
        
        # Should find Python files in src directory
        files = find_python_files(Path('src'))
        assert len(files) > 0
        assert all(f.suffix == '.py' for f in files)
    
    def test_format_file_size(self):
        """Test file size formatting."""
        from ai_pr_agent.utils.cli_helpers import format_file_size
        
        assert format_file_size(100) == "100.0 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"