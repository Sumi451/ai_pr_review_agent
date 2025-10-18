"""
Base adapter interface for Git platform integrations.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from ai_pr_agent.core.models import PullRequest, FileChange, Comment
from ai_pr_agent.utils import get_logger

logger = get_logger(__name__)


class PlatformType(Enum):
    """Supported Git platforms."""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


@dataclass
class AdapterConfig:
    """Configuration for adapter instances."""
    platform: PlatformType
    base_url: str
    token: str
    timeout: int = 30
    max_retries: int = 3
    verify_ssl: bool = True
    custom_headers: Optional[Dict[str, str]] = None


@dataclass
class RateLimitInfo:
    """Rate limit information from the platform."""
    limit: int
    remaining: int
    reset_at: int  # Unix timestamp
    resource: str = "core"


@dataclass
class Repository:
    """Repository information."""
    owner: str
    name: str
    full_name: str
    default_branch: str = "main"
    is_private: bool = False
    url: Optional[str] = None


class BaseAdapter(ABC):
    """
    Base adapter interface for Git platform integrations.
    
    All platform-specific adapters must inherit from this class
    and implement all abstract methods.
    """
    
    def __init__(self, config: AdapterConfig):
        """
        Initialize the adapter.
        
        Args:
            config: Adapter configuration
        """
        self.config = config
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initializing {self.__class__.__name__}")
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Validate that the adapter can connect to the platform.
        
        Returns:
            True if connection is valid
        
        Raises:
            ConnectionError: If connection fails
        """
        pass
    
    @abstractmethod
    def get_pull_request(
        self, 
        repository: str, 
        pr_number: int
    ) -> PullRequest:
        """
        Fetch pull request details from the platform.
        
        Args:
            repository: Repository identifier (e.g., "owner/repo")
            pr_number: Pull request number
        
        Returns:
            PullRequest object with all details
        
        Raises:
            NotFoundError: If PR doesn't exist
            PermissionError: If access is denied
            APIError: For other API errors
        """
        pass
    
    @abstractmethod
    def get_pull_request_files(
        self, 
        repository: str, 
        pr_number: int
    ) -> List[FileChange]:
        """
        Get list of changed files in a pull request.
        
        Args:
            repository: Repository identifier
            pr_number: Pull request number
        
        Returns:
            List of FileChange objects
        
        Raises:
            NotFoundError: If PR doesn't exist
            APIError: For API errors
        """
        pass
    
    @abstractmethod
    def get_file_content(
        self, 
        repository: str, 
        file_path: str, 
        ref: str
    ) -> str:
        """
        Get content of a specific file at a given reference.
        
        Args:
            repository: Repository identifier
            file_path: Path to file in repository
            ref: Git reference (branch, tag, commit SHA)
        
        Returns:
            File content as string
        
        Raises:
            NotFoundError: If file doesn't exist
            APIError: For API errors
        """
        pass
    
    @abstractmethod
    def post_review_comment(
        self,
        repository: str,
        pr_number: int,
        comment: Comment
    ) -> str:
        """
        Post a review comment on a pull request.
        
        Args:
            repository: Repository identifier
            pr_number: Pull request number
            comment: Comment to post
        
        Returns:
            Comment ID from the platform
        
        Raises:
            PermissionError: If lacking write permissions
            APIError: For API errors
        """
        pass
    
    @abstractmethod
    def post_review(
        self,
        repository: str,
        pr_number: int,
        comments: List[Comment],
        summary: str,
        event: str = "COMMENT"
    ) -> str:
        """
        Post a complete review with multiple comments.
        
        Args:
            repository: Repository identifier
            pr_number: Pull request number
            comments: List of review comments
            summary: Overall review summary
            event: Review event type (COMMENT, APPROVE, REQUEST_CHANGES)
        
        Returns:
            Review ID from the platform
        
        Raises:
            PermissionError: If lacking write permissions
            APIError: For API errors
        """
        pass
    
    @abstractmethod
    def update_comment(
        self,
        repository: str,
        comment_id: str,
        new_body: str
    ) -> bool:
        """
        Update an existing comment.
        
        Args:
            repository: Repository identifier
            comment_id: Platform-specific comment ID
            new_body: New comment text
        
        Returns:
            True if successful
        
        Raises:
            NotFoundError: If comment doesn't exist
            PermissionError: If lacking permissions
            APIError: For API errors
        """
        pass
    
    @abstractmethod
    def delete_comment(
        self,
        repository: str,
        comment_id: str
    ) -> bool:
        """
        Delete a comment.
        
        Args:
            repository: Repository identifier
            comment_id: Platform-specific comment ID
        
        Returns:
            True if successful
        
        Raises:
            NotFoundError: If comment doesn't exist
            PermissionError: If lacking permissions
            APIError: For API errors
        """
        pass
    
    @abstractmethod
    def list_pull_requests(
        self,
        repository: str,
        state: str = "open",
        limit: int = 30
    ) -> List[PullRequest]:
        """
        List pull requests in a repository.
        
        Args:
            repository: Repository identifier
            state: PR state (open, closed, all)
            limit: Maximum number of PRs to return
        
        Returns:
            List of PullRequest objects
        
        Raises:
            APIError: For API errors
        """
        pass
    
    @abstractmethod
    def get_repository_info(self, repository: str) -> Repository:
        """
        Get repository information.
        
        Args:
            repository: Repository identifier
        
        Returns:
            Repository object with details
        
        Raises:
            NotFoundError: If repository doesn't exist
            APIError: For API errors
        """
        pass
    
    @abstractmethod
    def get_rate_limit(self) -> RateLimitInfo:
        """
        Get current rate limit status.
        
        Returns:
            RateLimitInfo with current limits
        
        Raises:
            APIError: For API errors
        """
        pass
    
    def parse_repository(self, repository: str) -> tuple[str, str]:
        """
        Parse repository string into owner and name.
        
        Args:
            repository: Repository string (e.g., "owner/repo")
        
        Returns:
            Tuple of (owner, repo_name)
        
        Raises:
            ValueError: If repository format is invalid
        """
        parts = repository.split('/')
        if len(parts) != 2:
            raise ValueError(
                f"Invalid repository format: {repository}. "
                "Expected format: 'owner/repo'"
            )
        return parts[0], parts[1]
    
    def format_comment_body(self, comment: Comment) -> str:
        """
        Format a comment for the platform.
        
        Args:
            comment: Comment to format
        
        Returns:
            Formatted comment text (markdown)
        """
        severity_emoji = {
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "suggestion": "💡"
        }
        
        emoji = severity_emoji.get(comment.severity.value, "•")
        text = f"{emoji} **{comment.severity.value.upper()}**: {comment.body}"
        
        if comment.suggestion:
            text += f"\n\n**Suggestion:**\n```python\n{comment.suggestion}\n```"
        
        return text
    
    def __repr__(self) -> str:
        """String representation of adapter."""
        return (
            f"{self.__class__.__name__}("
            f"platform={self.config.platform.value}, "
            f"base_url={self.config.base_url})"
        )