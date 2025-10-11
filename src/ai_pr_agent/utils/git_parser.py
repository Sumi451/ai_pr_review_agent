"""
Git diff parsing utilities.
"""
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from ai_pr_agent.utils import get_logger
from ai_pr_agent.core.models import FileChange, FileStatus

logger = get_logger(__name__)


class DiffParser:
    """Parser for git diff output."""
    
    @staticmethod
    def parse_diff(diff_text: str) -> List[FileChange]:
        """
        Parse git diff output into FileChange objects.
        
        Args:
            diff_text: Output from git diff command
        
        Returns:
            List of FileChange objects
        """
        if not diff_text or not diff_text.strip():
            logger.debug("Empty diff provided")
            return []
        
        file_changes = []
        current_file = None
        current_patch = []
        
        lines = diff_text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # New file diff starts with "diff --git"
            if line.startswith('diff --git'):
                # Save previous file if exists
                if current_file:
                    file_changes.append(current_file)
                
                # Parse file paths
                match = re.match(r'diff --git a/(.*?) b/(.*?)$', line)
                if match:
                    old_path = match.group(1)
                    new_path = match.group(2)
                    
                    current_file = {
                        'old_filename': old_path,
                        'filename': new_path,
                        'status': FileStatus.MODIFIED,
                        'additions': 0,
                        'deletions': 0,
                        'patch': []
                    }
                    current_patch = []
            
            # File status indicators
            elif line.startswith('new file mode'):
                if current_file:
                    current_file['status'] = FileStatus.ADDED
            
            elif line.startswith('deleted file mode'):
                if current_file:
                    current_file['status'] = FileStatus.DELETED
            
            elif line.startswith('rename from'):
                if current_file:
                    current_file['status'] = FileStatus.RENAMED
            
            # Patch content
            elif line.startswith('@@'):
                # Hunk header - marks start of actual diff content
                current_patch.append(line)
            
            elif line.startswith('+') and not line.startswith('+++'):
                # Added line
                if current_file:
                    current_file['additions'] += 1
                    current_patch.append(line)
            
            elif line.startswith('-') and not line.startswith('---'):
                # Deleted line
                if current_file:
                    current_file['deletions'] += 1
                    current_patch.append(line)
            
            elif current_patch:  # Context line (inside a hunk)
                current_patch.append(line)
            
            i += 1
        
        # Don't forget the last file
        if current_file:
            file_changes.append(current_file)
        
        # Convert to FileChange objects
        result = []
        for file_data in file_changes:
            patch_text = '\n'.join(current_patch) if current_patch else '\n'.join(file_data['patch'])
            
            file_change = FileChange(
                filename=file_data['filename'],
                status=file_data['status'],
                additions=file_data['additions'],
                deletions=file_data['deletions'],
                patch=patch_text if patch_text.strip() else None,
                old_filename=file_data.get('old_filename')
            )
            result.append(file_change)
        
        logger.info(f"Parsed {len(result)} file changes from diff")
        return result
    
    @staticmethod
    def extract_changed_lines(patch: str) -> Dict[int, str]:
        """
        Extract changed line numbers and content from a patch.
        
        Args:
            patch: Git diff patch
        
        Returns:
            Dictionary mapping line numbers to line content
        """
        changed_lines = {}
        current_line = 0
        
        for line in patch.split('\n'):
            # Parse hunk header to get starting line number
            if line.startswith('@@'):
                match = re.search(r'\+(\d+)', line)
                if match:
                    current_line = int(match.group(1))
                continue
            
            # Track line numbers for added/context lines
            if line.startswith('+') and not line.startswith('+++'):
                changed_lines[current_line] = line[1:]  # Remove '+'
                current_line += 1
            elif not line.startswith('-'):
                # Context line
                current_line += 1
        
        return changed_lines
    
    @staticmethod
    def get_file_content_from_patch(patch: str) -> str:
        """
        Extract the new file content from a patch (best effort).
        
        Args:
            patch: Git diff patch
        
        Returns:
            Reconstructed file content
        """
        lines = []
        
        for line in patch.split('\n'):
            # Skip diff metadata
            if line.startswith('@@') or line.startswith('---') or line.startswith('+++'):
                continue
            
            # Keep added and context lines
            if line.startswith('+'):
                lines.append(line[1:])
            elif not line.startswith('-'):
                lines.append(line)
        
        return '\n'.join(lines)


class GitRepository:
    """Interface for git repository operations."""
    
    def __init__(self, repo_path: str = '.'):
        """
        Initialize git repository interface.
        
        Args:
            repo_path: Path to git repository
        """
        try:
            import git
            self.repo = git.Repo(repo_path)
            self.git = self.repo.git
            logger.info(f"Initialized git repository at {repo_path}")
        except Exception as e:
            logger.error(f"Failed to initialize git repository: {e}")
            raise
    
    def get_branch_diff(
        self, 
        base_branch: str, 
        compare_branch: str
    ) -> str:
        """
        Get diff between two branches.
        
        Args:
            base_branch: Base branch name
            compare_branch: Branch to compare
        
        Returns:
            Git diff output
        """
        try:
            diff = self.git.diff(base_branch, compare_branch)
            logger.debug(f"Got diff between {base_branch} and {compare_branch}")
            return diff
        except Exception as e:
            logger.error(f"Failed to get branch diff: {e}")
            raise
    
    def get_commit_diff(self, commit: str) -> str:
        """
        Get diff for a specific commit.
        
        Args:
            commit: Commit hash or reference
        
        Returns:
            Git diff output
        """
        try:
            diff = self.git.show(commit, format='')
            logger.debug(f"Got diff for commit {commit}")
            return diff
        except Exception as e:
            logger.error(f"Failed to get commit diff: {e}")
            raise
    
    def get_commit_range_diff(
        self, 
        start_commit: str, 
        end_commit: str
    ) -> str:
        """
        Get diff for a range of commits.
        
        Args:
            start_commit: Start commit
            end_commit: End commit
        
        Returns:
            Git diff output
        """
        try:
            diff = self.git.diff(f"{start_commit}..{end_commit}")
            logger.debug(f"Got diff for {start_commit}..{end_commit}")
            return diff
        except Exception as e:
            logger.error(f"Failed to get commit range diff: {e}")
            raise
    
    def get_uncommitted_changes(self) -> str:
        """
        Get diff of uncommitted changes.
        
        Returns:
            Git diff output
        """
        try:
            # Get both staged and unstaged changes
            staged = self.git.diff('--cached')
            unstaged = self.git.diff()
            
            # Combine them
            diff = staged
            if unstaged:
                if diff:
                    diff += "\n"
                diff += unstaged
            
            logger.debug("Got uncommitted changes")
            return diff
        except Exception as e:
            logger.error(f"Failed to get uncommitted changes: {e}")
            raise
    
    def get_current_branch(self) -> str:
        """
        Get the current branch name.
        
        Returns:
            Current branch name
        """
        return self.repo.active_branch.name
    
    def get_commit_info(self, commit: str = 'HEAD') -> Dict[str, str]:
        """
        Get information about a commit.
        
        Args:
            commit: Commit reference
        
        Returns:
            Dictionary with commit info
        """
        try:
            commit_obj = self.repo.commit(commit)
            return {
                'hash': commit_obj.hexsha,
                'short_hash': commit_obj.hexsha[:7],
                'author': commit_obj.author.name,
                'email': commit_obj.author.email,
                'message': commit_obj.message.strip(),
                'date': commit_obj.committed_datetime.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get commit info: {e}")
            raise
    
    def list_branches(self) -> List[str]:
        """
        List all branches in the repository.
        
        Returns:
            List of branch names
        """
        return [branch.name for branch in self.repo.branches]