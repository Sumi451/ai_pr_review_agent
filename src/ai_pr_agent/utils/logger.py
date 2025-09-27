"""
Logging utilities for AI PR Review Agent.
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

from ai_pr_agent.config import get_settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green  
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        # Get the original formatted message
        formatted = super().format(record)
        
        # Add color if this is for console output
        if hasattr(record, 'console_output') and record.console_output:
            color = self.COLORS.get(record.levelname, '')
            return f"{color}{formatted}{self.RESET}"
        
        return formatted


class LoggerSetup:
    """Handles logger setup and configuration."""
    
    _loggers_configured = False
    _file_handler = None
    _console_handler = None

    @classmethod
    def setup_logging(cls, force_reconfigure: bool = False) -> None:
        """Set up logging configuration based on settings."""
        if cls._loggers_configured and not force_reconfigure:
            return

        settings = get_settings()
        
        # Create logs directory if it doesn't exist
        log_file_path = Path(settings.logging.file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get root logger
        root_logger = logging.getLogger()
        
        # Clear existing handlers if reconfiguring
        if force_reconfigure:
            root_logger.handlers.clear()
            cls._file_handler = None
            cls._console_handler = None
        
        # Set root logger level
        log_level = getattr(logging, settings.app.log_level.upper(), logging.INFO)
        root_logger.setLevel(log_level)
        
        # Create formatters
        file_formatter = logging.Formatter(
            fmt=settings.logging.format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = ColoredFormatter(
            fmt='%(levelname)-8s | %(name)-20s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Set up file handler with rotation
        if cls._file_handler is None:
            cls._file_handler = logging.handlers.RotatingFileHandler(
                filename=settings.logging.file,
                maxBytes=settings.logging.max_size_mb * 1024 * 1024,  # Convert MB to bytes
                backupCount=settings.logging.backup_count,
                encoding='utf-8'
            )
            cls._file_handler.setFormatter(file_formatter)
            cls._file_handler.setLevel(log_level)
            root_logger.addHandler(cls._file_handler)
        
        # Set up console handler
        if cls._console_handler is None:
            cls._console_handler = logging.StreamHandler(sys.stdout)
            cls._console_handler.setFormatter(console_formatter)
            
            # Console should show INFO and above, unless debug mode
            console_level = logging.DEBUG if settings.app.debug else logging.INFO
            cls._console_handler.setLevel(console_level)
            
            # Add marker for colored output
            class ConsoleFilter(logging.Filter):
                def filter(self, record):
                    record.console_output = True
                    return True
            
            cls._console_handler.addFilter(ConsoleFilter())
            root_logger.addHandler(cls._console_handler)
        
        # Set up third-party library logging levels
        cls._setup_third_party_loggers()
        
        cls._loggers_configured = True
        
        # Log the successful setup
        logger = logging.getLogger(__name__)
        logger.info(f"Logging configured - Level: {settings.app.log_level}, File: {settings.logging.file}")

    @classmethod
    def _setup_third_party_loggers(cls) -> None:
        """Configure logging levels for third-party libraries."""
        # Reduce noise from common libraries
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("github").setLevel(logging.INFO)
        logging.getLogger("transformers").setLevel(logging.WARNING)
        
        # Keep our own loggers at the configured level
        our_modules = [
            "ai_pr_agent",
            "__main__"
        ]
        settings = get_settings()
        our_level = getattr(logging, settings.app.log_level.upper(), logging.INFO)
        
        for module in our_modules:
            logging.getLogger(module).setLevel(our_level)

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger instance with automatic setup."""
        # Ensure logging is set up
        cls.setup_logging()
        
        # Return logger for the given name
        return logging.getLogger(name)

    @classmethod 
    def reconfigure(cls) -> None:
        """Reconfigure logging (useful when settings change)."""
        cls._loggers_configured = False
        cls.setup_logging(force_reconfigure=True)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Convenience function to get a logger instance.
    
    Args:
        name: Logger name. If None, uses the calling module's name.
    
    Returns:
        Configured logger instance.
    """
    if name is None:
        # Get the calling module's name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return LoggerSetup.get_logger(name)


def log_function_call(func):
    """Decorator to log function calls (useful for debugging)."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        # Log function entry
        args_str = ', '.join([str(arg) for arg in args])
        kwargs_str = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
        all_args = ', '.join(filter(None, [args_str, kwargs_str]))
        
        logger.debug(f"Calling {func.__name__}({all_args})")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}")
            raise
    
    return wrapper


def log_exception(logger: logging.Logger, message: str) -> None:
    """Log an exception with full traceback."""
    logger.exception(message)


# Initialize logging when module is imported
LoggerSetup.setup_logging()