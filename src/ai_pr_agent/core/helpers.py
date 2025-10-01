"""Helper functions for working with core data models."""

from typing import List, Dict
from collections import defaultdict

from .models import (
    PullRequest,
    AnalysisResult,
    Comment,
    SeverityLevel,
    FileChange,
)


def filter_files_by_extension(
    files: List[FileChange],
    extensions: List[str]
) -> List[FileChange]:
    """
    Filter files by their extensions.
    
    Args:
        files: List of file changes
        extensions: List of extensions to include (e.g., ['.py', '.js'])
    
    Returns:
        Filtered list of files
    """
    return [
        f for f in files 
        if any(f.filename.endswith(ext) for ext in extensions)
    ]


def group_files_by_language(
    files: List[FileChange]
) -> Dict[str, List[FileChange]]:
    """
    Group files by their programming language.
    
    Args:
        files: List of file changes
    
    Returns:
        Dictionary mapping language to list of files
    """
    grouped = defaultdict(list)
    for file in files:
        grouped[file.language].append(file)
    return dict(grouped)


def calculate_pr_complexity(pr: PullRequest) -> Dict[str, any]:
    """
    Calculate complexity metrics for a pull request.
    
    Args:
        pr: Pull request to analyze
    
    Returns:
        Dictionary with complexity metrics
    """
    return {
        'total_files': len(pr.files_changed),
        'total_changes': pr.total_changes,
        'languages_count': len(pr.languages),
        'new_files': len(pr.new_files),
        'modified_files': len(pr.modified_files),
        'deleted_files': len(pr.deleted_files),
        'avg_changes_per_file': (
            pr.total_changes / len(pr.files_changed) 
            if pr.files_changed else 0
        ),
        'complexity_score': _calculate_complexity_score(pr),
    }


def _calculate_complexity_score(pr: PullRequest) -> str:
    """Calculate a simple complexity score (low, medium, high)."""
    total_changes = pr.total_changes
    file_count = len(pr.files_changed)
    
    if total_changes > 500 or file_count > 20:
        return "high"
    elif total_changes > 200 or file_count > 10:
        return "medium"
    else:
        return "low"


def prioritize_comments(
    comments: List[Comment]
) -> List[Comment]:
    """
    Sort comments by priority (errors first, then warnings, etc.).
    
    Args:
        comments: List of comments to sort
    
    Returns:
        Sorted list of comments
    """
    severity_order = {
        SeverityLevel.ERROR: 0,
        SeverityLevel.WARNING: 1,
        SeverityLevel.INFO: 2,
        SeverityLevel.SUGGESTION: 3,
    }
    
    return sorted(
        comments,
        key=lambda c: (severity_order[c.severity], c.line or 0)
    )


def format_comment_summary(
    results: List[AnalysisResult]
) -> str:
    """
    Create a formatted summary of all comments.
    
    Args:
        results: List of analysis results
    
    Returns:
        Formatted string summary
    """
    total_comments = sum(len(r.comments) for r in results)
    total_errors = sum(r.error_count for r in results)
    total_warnings = sum(r.warning_count for r in results)
    
    summary = f"""
Analysis Summary
================
Total files analyzed: {len(results)}
Total comments: {total_comments}
  - Errors: {total_errors}
  - Warnings: {total_warnings}
  - Info/Suggestions: {total_comments - total_errors - total_warnings}
"""
    
    return summary.strip()


def merge_analysis_results(
    results: List[AnalysisResult],
    filename: str
) -> AnalysisResult:
    """
    Merge multiple analysis results for the same file.
    
    Args:
        results: List of analysis results for the same file
        filename: The filename being analyzed
    
    Returns:
        Merged analysis result
    """
    merged = AnalysisResult(filename=filename)
    
    for result in results:
        merged.comments.extend(result.comments)
        merged.execution_time += result.execution_time
        merged.metadata.update(result.metadata)
        
        if not result.success:
            merged.success = False
            if result.error_message:
                if merged.error_message:
                    merged.error_message += f"; {result.error_message}"
                else:
                    merged.error_message = result.error_message
    
    return merged