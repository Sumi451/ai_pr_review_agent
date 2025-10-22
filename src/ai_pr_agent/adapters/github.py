"""
GitHub adapter for fetching and posting pull request reviews.
"""
from typing import List, Optional
from datetime import datetime
import time

from github import Github, GithubException, RateLimitExceededException
from github.Repository import Repository as GHRepository
from github.PullRequest import PullRequest as GHPullRequest

from ai_pr_agent.utils import get_logger
from ai_pr_agent.core.models import (
    PullRequest,
    FileChange,
    FileStatus,
    Comment,
)
from ai_pr_agent.core.exceptions import (
    NotFoundError,
    AccessPermissionError as CustomPermissionError,
    APIError,
    RateLimitError,
)
from .base import (
    BaseAdapter,
    AdapterConfig,
    RateLimitInfo,
    Repository,
)

logger = get_logger(__name__)


class GitHubAdapter(BaseAdapter):
    """
    GitHub-specific adapter implementation.
    
    Uses PyGithub library to interact with GitHub's REST API.
    """
    
    def __init__(self, config: AdapterConfig):
        """
        Initialize GitHub adapter.
        
        Args:
            config: Adapter configuration with GitHub token
        """
        super().__init__(config)
        
        # Initialize PyGithub client
        self.client = Github(
            login_or_token=config.token,
            base_url=config.base_url,
            timeout=config.timeout,
            retry=config.max_retries,
        )
        
        logger.info("GitHubAdapter initialized successfully")
    
    def validate_connection(self) -> bool:
        """
        Validate GitHub API connection.
        
        Returns:
            True if connection is valid
        
        Raises:
            APIError: If connection fails
        """
        try:
            # Test connection by getting authenticated user
            user = self.client.get_user()
            username = user.login
            logger.info(f"Successfully authenticated as: {username}")
            return True
        except GithubException as e:
            logger.error(f"GitHub connection validation failed: {e}")
            raise APIError(
                f"Failed to validate GitHub connection: {e.data.get('message', str(e))}",
                status_code=e.status
            )
    
    def get_pull_request(
        self, 
        repository: str, 
        pr_number: int
    ) -> PullRequest:
        """
        Fetch pull request details from GitHub.
        
        Args:
            repository: Repository identifier (e.g., "owner/repo")
            pr_number: Pull request number
        
        Returns:
            PullRequest object with all details
        
        Raises:
            NotFoundError: If PR doesn't exist
            APIError: For other API errors
        """
        try:
            logger.info(f"Fetching PR #{pr_number} from {repository}")
            
            # Get repository
            repo = self.client.get_repo(repository)
            
            # Get pull request
            gh_pr = repo.get_pull(pr_number)
            
            # Get changed files
            files = self.get_pull_request_files(repository, pr_number)
            
            # Convert to our PullRequest model
            pr = self._convert_github_pr(gh_pr, files)
            
            logger.info(f"Successfully fetched PR #{pr_number}: '{pr.title}'")
            return pr
            
        except GithubException as e:
            if e.status == 404:
                raise NotFoundError(f"Pull request #{pr_number} not found in {repository}")
            elif e.status == 403:
                raise CustomPermissionError(f"Access denied to {repository}")
            else:
                raise APIError(
                    f"Failed to fetch PR #{pr_number}: {e.data.get('message', str(e))}",
                    status_code=e.status
                )
    
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
        try:
            logger.debug(f"Fetching files for PR #{pr_number} in {repository}")
            
            repo = self.client.get_repo(repository)
            gh_pr = repo.get_pull(pr_number)
            
            files = []
            for gh_file in gh_pr.get_files():
                file_change = FileChange(
                    filename=gh_file.filename,
                    status=self._map_github_status(gh_file.status),
                    additions=gh_file.additions,
                    deletions=gh_file.deletions,
                    patch=gh_file.patch if hasattr(gh_file, 'patch') else None,
                    old_filename=gh_file.previous_filename if gh_file.previous_filename else None
                )
                files.append(file_change)
            
            logger.debug(f"Found {len(files)} changed files in PR #{pr_number}")
            return files
            
        except GithubException as e:
            if e.status == 404:
                raise NotFoundError(f"Pull request #{pr_number} not found")
            else:
                raise APIError(
                    f"Failed to fetch PR files: {e.data.get('message', str(e))}",
                    status_code=e.status
                )
    
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
        try:
            logger.debug(f"Fetching content of {file_path} at ref {ref}")
            
            repo = self.client.get_repo(repository)
            content = repo.get_contents(file_path, ref=ref)
            
            # Decode content
            if hasattr(content, 'decoded_content'):
                return content.decoded_content.decode('utf-8')
            else:
                return content.content
                
        except GithubException as e:
            if e.status == 404:
                raise NotFoundError(f"File {file_path} not found at ref {ref}")
            else:
                raise APIError(
                    f"Failed to fetch file content: {e.data.get('message', str(e))}",
                    status_code=e.status
                )
    
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
            Comment ID from GitHub
        
        Raises:
            PermissionError: If lacking write permissions
            APIError: For API errors
        """
        try:
            logger.info(f"Posting comment on PR #{pr_number}")
            
            repo = self.client.get_repo(repository)
            gh_pr = repo.get_pull(pr_number)
            
            # Format comment body
            body = self.format_comment_body(comment)
            
            if comment.line and comment.path:
                # Inline comment
                gh_comment = gh_pr.create_review_comment(
                    body=body,
                    commit=gh_pr.head.sha,
                    path=comment.path,
                    line=comment.line
                )
            else:
                # General comment
                gh_comment = gh_pr.create_issue_comment(body=body)
            
            logger.info(f"Comment posted successfully: {gh_comment.id}")
            return str(gh_comment.id)
            
        except GithubException as e:
            if e.status == 403:
                raise CustomPermissionError("Insufficient permissions to post comments")
            else:
                raise APIError(
                    f"Failed to post comment: {e.data.get('message', str(e))}",
                    status_code=e.status
                )
    
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
            Review ID from GitHub
        
        Raises:
            PermissionError: If lacking write permissions
            APIError: For API errors
        """
        try:
            logger.info(f"Posting review on PR #{pr_number} with {len(comments)} comments")
            
            repo = self.client.get_repo(repository)
            gh_pr = repo.get_pull(pr_number)
            
            # Prepare review comments
            review_comments = []
            for comment in comments:
                if comment.line and comment.path:
                    review_comments.append({
                        'path': comment.path,
                        'line': comment.line,
                        'body': self.format_comment_body(comment)
                    })
            
            # Create review
            review = gh_pr.create_review(
                body=summary,
                event=event,
                comments=review_comments if review_comments else None
            )
            
            logger.info(f"Review posted successfully: {review.id}")
            return str(review.id)
            
        except GithubException as e:
            if e.status == 403:
                raise CustomPermissionError("Insufficient permissions to post review")
            else:
                raise APIError(
                    f"Failed to post review: {e.data.get('message', str(e))}",
                    status_code=e.status
                )
    
    def update_comment(
        self,
        repository: str,
        pr_number: int,  # NEW
        comment_id: str,
        new_body: str
    ) -> bool:
        """
        Update an existing comment.
        
        Args:
            repository: Repository identifier
            pr_number: Pull request number (needed for review comments)
            comment_id: GitHub comment ID
            new_body: New comment text
        """
        try:
            logger.debug(f"Updating comment {comment_id}")
            
            repo = self.client.get_repo(repository)
            comment_id_int = int(comment_id)
            
            try:
                # Try as issue comment first - need to get through the issue
                issue = repo.get_issue(pr_number)
                comment = issue.get_comment(comment_id_int)
                comment.edit(new_body)
            except GithubException as e:
                if e.status == 404:
                    # Try as review comment
                    try:
                        pr = repo.get_pull(pr_number)
                        comment = pr.get_review_comment(comment_id_int)
                        comment.edit(new_body)
                    except GithubException:
                        raise NotFoundError(f"Comment {comment_id} not found")
                else:
                    raise
        
            logger.info(f"Comment {comment_id} updated successfully")
            return True
            
        except NotFoundError:
            raise
        except GithubException as e:
            message = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
            raise APIError(f"Failed to update comment: {message}", status_code=e.status)
    
    def delete_comment(
        self,
        repository: str,
        pr_number: int,  # Add pr_number parameter
        comment_id: str
    ) -> bool:
        """
        Delete a comment.
        
        Args:
            repository: Repository identifier
            pr_number: Pull request number (needed for review comments)
            comment_id: GitHub comment ID
        
        Returns:
            True if successful
        
        Raises:
            NotFoundError: If comment doesn't exist
            APIError: For API errors
        """
        try:
            logger.debug(f"Deleting comment {comment_id}")
            
            repo = self.client.get_repo(repository)
            comment_id_int = int(comment_id)
            
            try:
                # Try as issue comment first - need to get through the issue
                issue = repo.get_issue(pr_number)
                comment = issue.get_comment(comment_id_int)
                comment.delete()
            except GithubException as e:
                if e.status == 404:
                    # Try as review comment
                    try:
                        pr = repo.get_pull(pr_number)
                        comment = pr.get_review_comment(comment_id_int)
                        comment.delete()
                    except GithubException:
                        raise NotFoundError(f"Comment {comment_id} not found")
                else:
                    raise
            
            logger.info(f"Comment {comment_id} deleted successfully")
            return True
            
        except NotFoundError:
            raise
        except GithubException as e:
            message = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
            raise APIError(f"Failed to delete comment: {message}", status_code=e.status)
    
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
        try:
            logger.info(f"Listing {state} PRs in {repository} (limit: {limit})")
            
            repo = self.client.get_repo(repository)
            gh_prs = repo.get_pulls(state=state, sort='updated', direction='desc')
            
            prs = []
            for i, gh_pr in enumerate(gh_prs):
                if i >= limit:
                    break
                
                # Create placeholder FileChange objects for display (without fetching full file details)
                # This gives us the file count and additions/deletions for listing purposes
                placeholder_files = []
                if gh_pr.changed_files > 0:
                    # Create a single placeholder to represent the file count
                    # The actual files will be fetched when get_pull_request() is called
                    for _ in range(gh_pr.changed_files):
                        placeholder_files.append(FileChange(
                            filename="",
                            status=FileStatus.MODIFIED,
                            additions=0,
                            deletions=0
                        ))
                
                # Convert to our model (without fetching full file details for efficiency)
                pr = self._convert_github_pr(gh_pr, files=placeholder_files)
                prs.append(pr)
            
            logger.info(f"Found {len(prs)} pull requests")
            return prs
            
        except GithubException as e:
            raise APIError(
                f"Failed to list PRs: {e.data.get('message', str(e))}",
                status_code=e.status
            )
    
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
        try:
            logger.debug(f"Fetching repository info for {repository}")
            
            repo = self.client.get_repo(repository)
            
            return Repository(
                owner=repo.owner.login,
                name=repo.name,
                full_name=repo.full_name,
                default_branch=repo.default_branch,
                is_private=repo.private,
                url=repo.html_url
            )
            
        except GithubException as e:
            if e.status == 404:
                raise NotFoundError(f"Repository {repository} not found")
            else:
                raise APIError(
                    f"Failed to fetch repository info: {e.data.get('message', str(e))}",
                    status_code=e.status
                )
    
    def get_rate_limit(self) -> RateLimitInfo:
        """
        Get current rate limit status.
        
        Returns:
            RateLimitInfo with current limits
        
        Raises:
            APIError: For API errors
        """
        try:
            rate_limit = self.client.get_rate_limit()
            # Access core rate limit info using resources attribute
            core = rate_limit.resources.core  # type: ignore
            
            return RateLimitInfo(
                limit=core.limit,
                remaining=core.remaining,
                reset_at=int(core.reset.timestamp()),
                resource="core"
            )
            
        except GithubException as e:
            message = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
            raise APIError(
                f"Failed to get rate limit: {message}",
                status_code=e.status
            )
        except AttributeError as e:
            logger.error(f"Error accessing rate limit data: {e}")
            raise APIError(f"Failed to parse rate limit response: {str(e)}")
    
    def _convert_github_pr(
        self, 
        gh_pr: GHPullRequest, 
        files: List[FileChange]
    ) -> PullRequest:
        """
        Convert GitHub PR object to our PullRequest model.
        
        Args:
            gh_pr: GitHub pull request object
            files: List of file changes
        
        Returns:
            PullRequest object
        """
        # If files list is empty or contains placeholders, use PR-level stats
        total_additions = sum(f.additions for f in files) if files else gh_pr.additions
        total_deletions = sum(f.deletions for f in files) if files else gh_pr.deletions
        
        return PullRequest(
            id=gh_pr.number,
            title=gh_pr.title,
            description=gh_pr.body or "",
            author=gh_pr.user.login,
            source_branch=gh_pr.head.ref,
            target_branch=gh_pr.base.ref,
            files_changed=files,
            created_at=gh_pr.created_at,
            updated_at=gh_pr.updated_at,
            url=gh_pr.html_url,
            repository=gh_pr.base.repo.full_name,
            status=gh_pr.state,
            platform="github",
            api_url=gh_pr.url,
            state=gh_pr.state,
            mergeable=gh_pr.mergeable,
            merged=gh_pr.merged,
            merged_at=gh_pr.merged_at,
            head_sha=gh_pr.head.sha,
            base_sha=gh_pr.base.sha
        )
    
    def _map_github_status(self, status: str) -> FileStatus:
        """
        Map GitHub file status to our FileStatus enum.
        
        Args:
            status: GitHub file status
        
        Returns:
            FileStatus enum value
        """
        status_map = {
            'added': FileStatus.ADDED,
            'modified': FileStatus.MODIFIED,
            'removed': FileStatus.DELETED,
            'renamed': FileStatus.RENAMED,
        }
        return status_map.get(status, FileStatus.MODIFIED)