from typing import List, Optional, Dict, Any
from datetime import datetime

from ai_pr_agent.utils import get_logger
from ai_pr_agent.core.models import (
    ReviewSummary,
    AnalysisResult,
    Comment,
    SeverityLevel,
)
from ai_pr_agent.adapters.base import BaseAdapter
from ai_pr_agent.reporters.formatter import MarkdownFormatter

logger = get_logger(__name__)


class GitHubReporter:
    """Reporter for posting reviews to GitHub pull requests."""
    
    def __init__(self, adapter: BaseAdapter):
        """
        Initialize GitHub reporter.
        
        Args:
            adapter: GitHub adapter instance
        """
        self.adapter = adapter
        self.formatter = MarkdownFormatter()
        logger.info("GitHub reporter initialized")
    
    def post_review(
        self,
        repository: str,
        pr_number: int,
        summary: ReviewSummary,
        event: str = "COMMENT",
        max_comments: Optional[int] = None
    ) -> str:
        """
        Post a complete review with comments to GitHub.
        
        Args:
            repository: Repository identifier (owner/repo)
            pr_number: Pull request number
            summary: Review summary with analysis results
            event: Review event (COMMENT, APPROVE, REQUEST_CHANGES)
            max_comments: Maximum number of inline comments (None = unlimited)
        
        Returns:
            Review ID
        """
        logger.info(f"Posting review to {repository} PR #{pr_number}")
        
        # Get all comments
        all_comments = summary.get_all_comments()
        
        # Filter and prioritize comments
        comments_to_post = self._prioritize_comments(
            all_comments,
            max_comments
        )
        
        # Format review body
        review_body = self._format_review_body(summary)
        
        # Determine review event based on findings
        if event == "COMMENT":
            event = self._determine_review_event(summary)
        
        # Check if we're reviewing our own PR
        # GitHub doesn't allow REQUEST_CHANGES or APPROVE on your own PRs
        pr = self.adapter.get_pull_request(repository, pr_number)
        current_user = self.adapter.client.get_user().login
        
        if pr.author == current_user:
            if event in ("REQUEST_CHANGES", "APPROVE"):
                logger.warning(
                    f"Cannot use event '{event}' on own PR. "
                    f"Falling back to COMMENT."
                )
                event = "COMMENT"
        
        # Post review
        try:
            review_id = self.adapter.post_review(
                repository,
                pr_number,
                comments_to_post,
                review_body,
                event
            )
            
            logger.info(
                f"Posted review (ID: {review_id}) with "
                f"{len(comments_to_post)} comments"
            )
            
            return review_id
            
        except Exception as e:
            logger.error(f"Failed to post review: {e}")
            raise
    
    def post_summary_comment(
        self,
        repository: str,
        pr_number: int,
        summary: ReviewSummary
    ) -> str:
        """
        Post a summary comment to PR (not a review).
        
        Args:
            repository: Repository identifier
            pr_number: Pull request number
            summary: Review summary
        
        Returns:
            Comment ID
        """
        logger.info(f"Posting summary comment to {repository} PR #{pr_number}")
        
        # Create summary comment
        body = self._format_summary_comment(summary)
        
        # Post as general comment
        comment = Comment(body=body, severity=SeverityLevel.INFO)
        
        comment_id = self.adapter.post_review_comment(
            repository,
            pr_number,
            comment
        )
        
        logger.info(f"Posted summary comment (ID: {comment_id})")
        return comment_id
    
    def post_inline_comments(
        self,
        repository: str,
        pr_number: int,
        comments: List[Comment],
        batch_size: int = 10
    ) -> List[str]:
        """
        Post multiple inline comments individually.
        
        Args:
            repository: Repository identifier
            pr_number: Pull request number
            comments: List of comments to post
            batch_size: Number of comments to post at once
        
        Returns:
            List of comment IDs
        """
        logger.info(
            f"Posting {len(comments)} inline comments to "
            f"{repository} PR #{pr_number}"
        )
        
        comment_ids = []
        
        # Post in batches to avoid rate limits
        for i in range(0, len(comments), batch_size):
            batch = comments[i:i + batch_size]
            
            for comment in batch:
                if not comment.is_inline:
                    continue
                
                try:
                    comment_id = self.adapter.post_review_comment(
                        repository,
                        pr_number,
                        comment
                    )
                    comment_ids.append(comment_id)
                    
                except Exception as e:
                    logger.error(
                        f"Failed to post comment at "
                        f"{comment.path}:{comment.line}: {e}"
                    )
        
        logger.info(f"Posted {len(comment_ids)} inline comments")
        return comment_ids
    
    def update_review_comment(
        self,
        repository: str,
        comment_id: str,
        new_comment: Comment
    ) -> bool:
        """
        Update an existing review comment.
        
        Args:
            repository: Repository identifier
            comment_id: ID of comment to update
            new_comment: Updated comment content
        
        Returns:
            True if successful
        """
        body = self.formatter.format_comment(new_comment)
        
        return self.adapter.update_comment(
            repository,
            comment_id,
            body
        )
    
    def _format_review_body(self, summary: ReviewSummary) -> str:
        """Format the main review body."""
        return self.formatter.format_review_summary(summary)
    
    def _format_summary_comment(self, summary: ReviewSummary) -> str:
        """Format a summary comment (not a review)."""
        return self.formatter.format_summary_comment(summary)
    
    def _prioritize_comments(
        self,
        comments: List[Comment],
        max_comments: Optional[int]
    ) -> List[Comment]:
        """
        Prioritize and filter comments.
        
        Args:
            comments: All comments
            max_comments: Maximum number to return
        
        Returns:
            Filtered and sorted comments
        """
        # Sort by severity (errors first, then warnings, etc.)
        severity_order = {
            SeverityLevel.ERROR: 0,
            SeverityLevel.WARNING: 1,
            SeverityLevel.INFO: 2,
            SeverityLevel.SUGGESTION: 3,
        }
        
        sorted_comments = sorted(
            comments,
            key=lambda c: (severity_order[c.severity], c.path or "", c.line or 0)
        )
        
        # Filter only inline comments for review
        inline_comments = [c for c in sorted_comments if c.is_inline]
        
        # Limit if specified
        if max_comments:
            inline_comments = inline_comments[:max_comments]
        
        return inline_comments
    
    def _determine_review_event(self, summary: ReviewSummary) -> str:
        """
        Determine appropriate review event based on findings.
        
        Args:
            summary: Review summary
        
        Returns:
            Review event (COMMENT, APPROVE, REQUEST_CHANGES)
        """
        # REQUEST_CHANGES if there are errors
        if summary.total_errors > 0:
            return "REQUEST_CHANGES"
        
        # APPROVE if no errors or warnings
        if summary.total_warnings == 0:
            return "APPROVE"
        
        # COMMENT for warnings only
        return "COMMENT"


class ReviewBatcher:
    """Helper for batching review comments to avoid rate limits."""
    
    def __init__(self, max_batch_size: int = 30):
        """
        Initialize batcher.
        
        Args:
            max_batch_size: Maximum comments per batch
        """
        self.max_batch_size = max_batch_size
    
    def batch_comments(
        self,
        comments: List[Comment]
    ) -> List[List[Comment]]:
        """
        Split comments into batches.
        
        Args:
            comments: All comments
        
        Returns:
            List of comment batches
        """
        batches = []
        
        for i in range(0, len(comments), self.max_batch_size):
            batch = comments[i:i + self.max_batch_size]
            batches.append(batch)
        
        return batches
    
    def group_by_file(
        self,
        comments: List[Comment]
    ) -> Dict[str, List[Comment]]:
        """
        Group comments by file.
        
        Args:
            comments: All comments
        
        Returns:
            Dictionary mapping filepath to comments
        """
        grouped = {}
        
        for comment in comments:
            if not comment.path:
                continue
            
            if comment.path not in grouped:
                grouped[comment.path] = []
            
            grouped[comment.path].append(comment)
        
        return grouped


class ReviewThreadManager:
    """Manage review comment threads."""
    
    def __init__(self, adapter: BaseAdapter):
        """
        Initialize thread manager.
        
        Args:
            adapter: GitHub adapter instance
        """
        self.adapter = adapter
        self.threads = {}
    
    def create_thread(
        self,
        repository: str,
        pr_number: int,
        initial_comment: Comment
    ) -> str:
        """
        Create a new review thread.
        
        Args:
            repository: Repository identifier
            pr_number: Pull request number
            initial_comment: First comment in thread
        
        Returns:
            Thread ID (comment ID)
        """
        comment_id = self.adapter.post_review_comment(
            repository,
            pr_number,
            initial_comment
        )
        
        thread_key = f"{repository}#{pr_number}:{comment_id}"
        self.threads[thread_key] = {
            'id': comment_id,
            'comments': [initial_comment],
        }
        
        return comment_id
    
    def reply_to_thread(
        self,
        repository: str,
        pr_number: int,
        thread_id: str,
        reply: Comment
    ) -> str:
        """
        Add a reply to an existing thread.
        
        Args:
            repository: Repository identifier
            pr_number: Pull request number
            thread_id: ID of thread to reply to
            reply: Reply comment
        
        Returns:
            Reply comment ID
        """
        # Note: GitHub API doesn't have direct thread replies
        # This is a placeholder for future implementation
        return self.adapter.post_review_comment(
            repository,
            pr_number,
            reply
        )