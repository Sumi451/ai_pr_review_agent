"""Tests for logging functionality."""

import logging
import tempfile
import os
from pathlib import Path
import pytest

from ai_pr_agent.utils.logger import LoggerSetup, get_logger
from ai_pr_agent.config import get_settings


class TestLogging:
    """Test logging functionality."""
    
    def test_logger_setup(self):
        """Test basic logger setup."""
        # Reset logging state
        LoggerSetup._loggers_configured = False
        LoggerSetup.setup_logging()
        
        assert LoggerSetup._loggers_configured is True
        assert LoggerSetup._file_handler is not None
        assert LoggerSetup._console_handler is not None
    
    def test_get_logger(self):
        """Test getting logger instances."""
        logger1 = get_logger("test.module1")
        logger2 = get_logger("test.module2")
        logger3 = get_logger("test.module1")  # Same name
        
        assert logger1.name == "test.module1"
        assert logger2.name == "test.module2"
        assert logger1 is logger3  # Should be same instance
    
    def test_log_levels(self):
        """Test different log levels."""
        logger = get_logger("test.levels")
        
        # These should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
    
    def test_log_file_creation(self):
        """Test that log files are created."""
        settings = get_settings()
        log_file = Path(settings.logging.file)
        
        # Create a test message
        logger = get_logger("test.file")
        logger.info("Test message for file creation")
        
        # Log file should exist
        assert log_file.exists()
        
        # Should contain our message
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Test message for file creation" in content
    
    def test_logger_reconfiguration(self):
        """Test logger reconfiguration."""
        # Initial setup
        LoggerSetup.setup_logging()
        initial_handler_count = len(logging.getLogger().handlers)
        
        # Reconfigure
        LoggerSetup.reconfigure()
        
        # Should still work
        logger = get_logger("test.reconfig")
        logger.info("After reconfiguration")
        
        # Just verify we still have handlers and logging works
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) >= 1  # Should have at least one handler
        assert LoggerSetup._loggers_configured is True
    
    def test_exception_logging(self):
        """Test exception logging."""
        logger = get_logger("test.exception")
        
        try:
            # Create an exception
            raise ValueError("Test exception")
        except ValueError:
            # This should not raise an exception itself
            logger.exception("Caught test exception")
    
    def test_function_decorator(self):
        """Test the function call logging decorator."""
        from ai_pr_agent.utils.logger import log_function_call
        
        @log_function_call
        def test_function(x: int, y: str = "default") -> str:
            return f"{x}-{y}"
        
        # This should not raise an exception
        result = test_function(42, y="test")
        assert result == "42-test"
        
        # Test with exception
        @log_function_call
        def failing_function():
            raise RuntimeError("Test error")
        
        with pytest.raises(RuntimeError):
            failing_function()


def test_logger_integration():
    """Test logger integration with other components."""
    from ai_pr_agent.core.exceptions import ConfigurationError
    
    # This should create log entries without raising exceptions
    try:
        raise ConfigurationError("Test configuration error", "Additional details")
    except ConfigurationError:
        pass  # Expected