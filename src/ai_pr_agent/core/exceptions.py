"""Custom exceptions for AI PR Review Agent."""

from ai_pr_agent.utils import get_logger
from typing import Optional

logger = get_logger(__name__)


class AIReviewAgentError(Exception):
    """Base exception for AI PR Review Agent."""
    
    def __init__(self, message: str, details: str = None):
        super().__init__(message)
        self.message = message
        self.details = details
        
        # Log the exception when created
        logger.error(f"Exception raised: {message}")
        if details:
            logger.debug(f"Exception details: {details}")


class ConfigurationError(AIReviewAgentError):
    """Raised when there's a configuration problem."""
    pass


class GitHubAPIError(AIReviewAgentError):
    """Raised when GitHub API calls fail."""
    pass


class AnalysisError(AIReviewAgentError):
    """Raised when code analysis fails."""
    pass


class AIModelError(AIReviewAgentError):
    """Raised when AI model operations fail."""
    pass

class NotFoundError(AIReviewAgentError):
    """Raised when a resource is not found."""
    pass


class AccessPermissionError(AIReviewAgentError):
    """Raised when lacking required permissions."""
    pass


class APIError(AIReviewAgentError):
    """Raised when API calls fail."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, details: str = None):
        super().__init__(message, details)
        self.status_code = status_code


class RateLimitError(APIError):
    """Raised when hitting rate limits."""
    
    def __init__(
        self, 
        message: str, 
        reset_at: Optional[int] = None, 
        details: str = None
    ):
        super().__init__(message, status_code=429, details=details)
        self.reset_at = reset_at