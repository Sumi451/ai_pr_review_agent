"""
Core data models for AI PR Review Agent.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from ai_pr_agent.utils import get_logger

logger = get_logger(__name__)


class SeverityLevel(Enum):
    """Severity levels for code review feedback."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


class FileStatus(Enum):
    """Status of a file in a pull request."""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


class AnalysisType(Enum):
    """Type of analysis performed."""
    STATIC = "static"
    AI = "ai"
    SECURITY = "security"
    PERFORMANCE = "performance"


@dataclass
class FileChange:
    """
    Represents a changed file in a pull request.
    
    Attributes:
        filename: Path to the file
        status: Status of the file (added, modified, deleted, renamed)
        additions: Number of lines added
        deletions: Number of lines deleted
        patch: The diff patch for this file
        old_filename: Original filename (for renamed files)
        language: Programming language of the file
    """
    filename: str
    status: FileStatus
    additions: int = 0
    deletions: int = 0
    patch: Optional[str] = None
    old_filename: Optional[str] = None
    language: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Convert string status to enum if needed
        if isinstance(self.status, str):
            self.status = FileStatus(self.status.lower())
        
        
        
        # Auto-detect language from file extension if not provided
        if self.language is None:
            self.language = self._detect_language()
        
        logger.debug(
            f"Created FileChange: {self.filename} "
            f"({self.status.value}, +{self.additions}/-{self.deletions})"
        )
    
    def _detect_language(self) -> str:
        """Detect programming language from file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.cs': 'csharp',
        }
        
        for ext, lang in extension_map.items():
            if self.filename.endswith(ext):
                return lang
        
        return 'unknown'
    
    @property
    def total_changes(self) -> int:
        """Total number of lines changed."""
        return self.additions + self.deletions
    
    @property
    def is_new_file(self) -> bool:
        """Check if this is a newly added file."""
        return self.status == FileStatus.ADDED
    
    @property
    def is_deleted_file(self) -> bool:
        """Check if this file was deleted."""
        return self.status == FileStatus.DELETED


@dataclass
class Comment:
    """
    Represents a review comment on code.
    
    Attributes:
        body: The comment text
        line: Line number in the file (None for file-level comments)
        severity: Severity level of the comment
        path: File path this comment refers to
        suggestion: Optional code suggestion to fix the issue
        analysis_type: Type of analysis that generated this comment
    """
    body: str
    severity: SeverityLevel = SeverityLevel.INFO
    line: Optional[int] = None
    path: Optional[str] = None
    suggestion: Optional[str] = None
    analysis_type: Optional[AnalysisType] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Convert string severity to enum if needed
        if isinstance(self.severity, str):
            self.severity = SeverityLevel(self.severity.lower())
        
        # Convert string analysis type to enum if needed
        if isinstance(self.analysis_type, str):
            self.analysis_type = AnalysisType(self.analysis_type.lower())
        
        logger.debug(
            f"Created Comment: {self.severity.value} "
            f"at {self.path or 'file'}:{self.line or 'N/A'}"
        )
    
    @property
    def is_inline(self) -> bool:
        """Check if this is an inline comment (has line number)."""
        return self.line is not None
    
    @property
    def is_critical(self) -> bool:
        """Check if this is a critical issue."""
        return self.severity == SeverityLevel.ERROR
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert comment to dictionary format."""
        return {
            'body': self.body,
            'severity': self.severity.value,
            'line': self.line,
            'path': self.path,
            'suggestion': self.suggestion,
            'analysis_type': self.analysis_type.value if self.analysis_type else None,
        }


@dataclass
class AnalysisResult:
    """
    Results from analyzing a file.
    
    Attributes:
        filename: Path to the analyzed file
        comments: List of review comments
        metadata: Additional analysis metadata
        analysis_type: Type of analysis performed
        execution_time: Time taken for analysis in seconds
        success: Whether the analysis completed successfully
        error_message: Error message if analysis failed
    """
    filename: str
    comments: List[Comment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    analysis_type: Optional[AnalysisType] = None
    execution_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Convert string analysis type to enum if needed
        if isinstance(self.analysis_type, str):
            self.analysis_type = AnalysisType(self.analysis_type.lower())
        
        logger.debug(
            f"Created AnalysisResult for {self.filename}: "
            f"{len(self.comments)} comments, success={self.success}"
        )
    
    def add_comment(
        self,
        body: str,
        line: Optional[int] = None,
        severity: SeverityLevel = SeverityLevel.INFO,
        suggestion: Optional[str] = None
    ) -> None:
        """
        Add a comment to this analysis result.
        
        Args:
            body: Comment text
            line: Line number (optional)
            severity: Severity level
            suggestion: Code suggestion (optional)
        """
        comment = Comment(
            body=body,
            line=line,
            severity=severity,
            path=self.filename,
            suggestion=suggestion,
            analysis_type=self.analysis_type
        )
        self.comments.append(comment)
        logger.debug(f"Added comment to {self.filename}: {severity.value}")
    
    @property
    def has_errors(self) -> bool:
        """Check if analysis found any errors."""
        return any(c.severity == SeverityLevel.ERROR for c in self.comments)
    
    @property
    def has_warnings(self) -> bool:
        """Check if analysis found any warnings."""
        return any(c.severity == SeverityLevel.WARNING for c in self.comments)
    
    @property
    def error_count(self) -> int:
        """Count of error-level comments."""
        return sum(1 for c in self.comments if c.severity == SeverityLevel.ERROR)
    
    @property
    def warning_count(self) -> int:
        """Count of warning-level comments."""
        return sum(1 for c in self.comments if c.severity == SeverityLevel.WARNING)
    
    def get_comments_by_severity(self, severity: SeverityLevel) -> List[Comment]:
        """Get all comments of a specific severity level."""
        return [c for c in self.comments if c.severity == severity]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis result to dictionary format."""
        return {
            'filename': self.filename,
            'comments': [c.to_dict() for c in self.comments],
            'metadata': self.metadata,
            'analysis_type': self.analysis_type.value if self.analysis_type else None,
            'execution_time': self.execution_time,
            'success': self.success,
            'error_message': self.error_message,
            'summary': {
                'total_comments': len(self.comments),
                'error_count': self.error_count,
                'warning_count': self.warning_count,
            }
        }


"""
Core data models for AI PR Review Agent - FIXED VERSION
Add this to your existing models.py, replacing the PullRequest class
"""

@dataclass
class PullRequest:
    """
    Represents a pull request.
    
    Attributes:
        id: PR identifier (number)
        title: PR title
        description: PR description/body
        author: Username of PR author
        source_branch: Source branch name
        target_branch: Target branch name (usually main/master)
        files_changed: List of changed files
        created_at: Timestamp when PR was created
        updated_at: Timestamp when PR was last updated
        url: URL to the pull request (web URL)
        repository: Repository identifier (e.g., "owner/repo")
        status: Current status of the PR (open, closed, merged)
        
        # Platform-specific fields
        platform: Platform identifier (github, gitlab, etc.)
        api_url: API endpoint for this PR
        state: PR state (open, closed, merged)
        mergeable: Whether PR can be merged
        merged: Whether PR is merged
        merged_at: Merge timestamp
        head_sha: SHA of head commit
        base_sha: SHA of base commit
    """
    id: int
    title: str
    description: str
    author: str
    source_branch: str
    target_branch: str = "main"
    files_changed: List[FileChange] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    url: Optional[str] = None  # Keep as regular field for backward compatibility
    repository: Optional[str] = None
    status: str = "open"
    
    # Platform-specific fields (NEW)
    platform: str = "unknown"  # github, gitlab, bitbucket
    api_url: Optional[str] = None  # API endpoint for this PR
    state: str = "open"  # open, closed, merged
    mergeable: Optional[bool] = None
    merged: bool = False
    merged_at: Optional[datetime] = None
    head_sha: Optional[str] = None  # SHA of head commit
    base_sha: Optional[str] = None  # SHA of base commit
    
    def __post_init__(self):
        """Post-initialization processing."""
        logger.info(
            f"Created PullRequest #{self.id}: '{self.title}' by {self.author} "
            f"({self.source_branch} -> {self.target_branch})"
        )
        logger.debug(f"PR has {len(self.files_changed)} file changes")
    
    @property
    def html_url(self) -> Optional[str]:
        """Alias for url (for platform consistency)."""
        return self.url
    
    @property
    def total_additions(self) -> int:
        """Total lines added across all files."""
        return sum(f.additions for f in self.files_changed)
    
    @property
    def total_deletions(self) -> int:
        """Total lines deleted across all files."""
        return sum(f.deletions for f in self.files_changed)
    
    @property
    def total_changes(self) -> int:
        """Total lines changed across all files."""
        return self.total_additions + self.total_deletions
    
    @property
    def languages(self) -> List[str]:
        """List of unique programming languages in this PR."""
        return list(set(f.language for f in self.files_changed if f.language != 'unknown'))
    
    @property
    def new_files(self) -> List[FileChange]:
        """List of newly added files."""
        return [f for f in self.files_changed if f.is_new_file]
    
    @property
    def deleted_files(self) -> List[FileChange]:
        """List of deleted files."""
        return [f for f in self.files_changed if f.is_deleted_file]
    
    @property
    def modified_files(self) -> List[FileChange]:
        """List of modified files."""
        return [f for f in self.files_changed if f.status == FileStatus.MODIFIED]
    
    def get_files_by_language(self, language: str) -> List[FileChange]:
        """Get all files of a specific programming language."""
        return [f for f in self.files_changed if f.language == language]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pull request to dictionary format."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'author': self.author,
            'source_branch': self.source_branch,
            'target_branch': self.target_branch,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'url': self.url,
            'repository': self.repository,
            'status': self.status,
            'platform': self.platform,
            'api_url': self.api_url,
            'state': self.state,
            'mergeable': self.mergeable,
            'merged': self.merged,
            'merged_at': self.merged_at.isoformat() if self.merged_at else None,
            'head_sha': self.head_sha,
            'base_sha': self.base_sha,
            'files_changed': [
                {
                    'filename': f.filename,
                    'status': f.status.value,
                    'additions': f.additions,
                    'deletions': f.deletions,
                    'language': f.language,
                }
                for f in self.files_changed
            ],
            'summary': {
                'total_files': len(self.files_changed),
                'total_additions': self.total_additions,
                'total_deletions': self.total_deletions,
                'total_changes': self.total_changes,
                'languages': self.languages,
                'new_files': len(self.new_files),
                'deleted_files': len(self.deleted_files),
                'modified_files': len(self.modified_files),
            }
        }

@dataclass
class ReviewSummary:
    """
    Summary of the entire review process.
    
    Attributes:
        pull_request: The pull request that was reviewed
        analysis_results: Results from all analysis modules
        overall_status: Overall status (success, partial_failure, failure)
        total_comments: Total number of comments generated
        total_execution_time: Total time taken for review
        timestamp: When the review was performed
    """
    pull_request: PullRequest
    analysis_results: List[AnalysisResult] = field(default_factory=list)
    overall_status: str = "success"
    total_comments: int = 0
    total_execution_time: float = 0.0
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        # Calculate total comments if not provided
        if self.total_comments == 0:
            self.total_comments = sum(len(r.comments) for r in self.analysis_results)
        
        logger.info(
            f"Created ReviewSummary for PR #{self.pull_request.id}: "
            f"{len(self.analysis_results)} files analyzed, "
            f"{self.total_comments} comments"
        )
    
    @property
    def has_errors(self) -> bool:
        """Check if any analysis found errors."""
        return any(r.has_errors for r in self.analysis_results)
    
    @property
    def total_errors(self) -> int:
        """Total number of error-level comments."""
        return sum(r.error_count for r in self.analysis_results)
    
    @property
    def total_warnings(self) -> int:
        """Total number of warning-level comments."""
        return sum(r.warning_count for r in self.analysis_results)
    
    @property
    def files_with_issues(self) -> List[str]:
        """List of files that have issues."""
        return [r.filename for r in self.analysis_results if r.comments]
    
    def get_all_comments(self) -> List[Comment]:
        """Get all comments from all analysis results."""
        all_comments = []
        for result in self.analysis_results:
            all_comments.extend(result.comments)
        return all_comments
    
    def get_comments_by_severity(self, severity: SeverityLevel) -> List[Comment]:
        """Get all comments of a specific severity level."""
        return [c for c in self.get_all_comments() if c.severity == severity]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert review summary to dictionary format."""
        return {
            'pull_request': self.pull_request.to_dict(),
            'analysis_results': [r.to_dict() for r in self.analysis_results],
            'overall_status': self.overall_status,
            'total_comments': self.total_comments,
            'total_execution_time': self.total_execution_time,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'summary': {
                'has_errors': self.has_errors,
                'total_errors': self.total_errors,
                'total_warnings': self.total_warnings,
                'files_analyzed': len(self.analysis_results),
                'files_with_issues': len(self.files_with_issues),
            }
        }