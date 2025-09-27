"""Core data models for AI PR Review Agent."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from ai_pr_agent.utils import get_logger

logger = get_logger(__name__)


class SeverityLevel(Enum):
    """Severity levels for feedback."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


@dataclass
class FileChange:
    """Represents a changed file in a pull request."""
    filename: str
    status: str  # added, modified, deleted
    additions: int = 0
    deletions: int = 0
    patch: Optional[str] = None
    
    def __post_init__(self):
        logger.debug(f"Created FileChange: {self.filename} ({self.status})")


@dataclass
class Comment:
    """Represents a review comment."""
    body: str
    line: Optional[int] = None
    severity: SeverityLevel = SeverityLevel.INFO
    
    def __post_init__(self):
        logger.debug(f"Created Comment: {self.severity.value} at line {self.line}")


@dataclass
class AnalysisResult:
    """Results from code analysis."""
    filename: str
    comments: List[Comment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_comment(self, body: str, line: int = None, severity: SeverityLevel = SeverityLevel.INFO):
        """Add a comment to this analysis result."""
        comment = Comment(body=body, line=line, severity=severity)
        self.comments.append(comment)
        logger.debug(f"Added comment to {self.filename}: {severity.value}")
    
    def __post_init__(self):
        logger.debug(f"Created AnalysisResult for {self.filename} with {len(self.comments)} comments")


@dataclass
class PullRequest:
    """Represents a pull request."""
    id: int
    title: str
    description: str
    author: str
    files_changed: List[FileChange] = field(default_factory=list)
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        logger.info(f"Created PullRequest #{self.id}: '{self.title}' by {self.author}")
        logger.debug(f"PR has {len(self.files_changed)} file changes")