"""Custom exceptions for AI PR Review Agent."""

from ai_pr_agent.utils import get_logger

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