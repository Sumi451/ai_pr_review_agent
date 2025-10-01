# Core Data Models Reference

## Overview

This document provides a quick reference for the core data models used throughout the AI PR Review Agent.

## Models

### FileChange

Represents a file that has been changed in a pull request.

**Attributes:**
- `filename`: Path to the file
- `status`: FileStatus enum (ADDED, MODIFIED, DELETED, RENAMED)
- `additions`: Number of lines added
- `deletions`: Number of lines deleted
- `patch`: The diff patch (optional)
- `language`: Auto-detected programming language

**Key Properties:**
- `total_changes`: Sum of additions and deletions
- `is_new_file`: True if file was added
- `is_deleted_file`: True if file was deleted

### Comment

Represents a code review comment.

**Attributes:**
- `body`: The comment text
- `severity`: SeverityLevel enum (ERROR, WARNING, INFO, SUGGESTION)
- `line`: Line number (optional)
- `path`: File path
- `suggestion`: Code suggestion (optional)
- `analysis_type`: AnalysisType enum (STATIC, AI, SECURITY, PERFORMANCE)

**Key Properties:**
- `is_inline`: True if comment has a line number
- `is_critical`: True if severity is ERROR

### AnalysisResult

Results from analyzing a single file.

**Attributes:**
- `filename`: Path to analyzed file
- `comments`: List of Comment objects
- `metadata`: Additional analysis data
- `analysis_type`: Type of analysis performed
- `execution_time`: Time taken in seconds
- `success`: Whether analysis completed successfully

**Key Methods:**
- `add_comment()`: Add a new comment
- `get_comments_by_severity()`: Filter comments by severity

**Key Properties:**
- `has_errors`: True if any ERROR comments exist
- `error_count`: Number of ERROR comments
- `warning_count`: Number of WARNING comments

### PullRequest

Represents a pull request.

**Attributes:**
- `id`: PR number
- `title`: PR title
- `description`: PR description
- `author`: PR author username
- `source_branch`: Source branch name
- `target_branch`: Target branch name
- `files_changed`: List of FileChange objects
- `created_at`: Creation timestamp
- `repository`: Repository identifier (e.g., "owner/repo")

**Key Properties:**
- `total_additions`: Total lines added
- `total_deletions`: Total lines deleted
- `total_changes`: Total lines changed
- `languages`: List of programming languages
- `new_files`: List of added files
- `modified_files`: List of modified files
- `deleted_files`: List of deleted files

**Key Methods:**
- `get_files_by_language()`: Filter files by language

### ReviewSummary

Summary of an entire review process.

**Attributes:**
- `pull_request`: The PullRequest object
- `analysis_results`: List of AnalysisResult objects
- `overall_status`: Status string (success, partial_failure, failure)
- `total_comments`: Total number of comments
- `total_execution_time`: Total time taken
- `timestamp`: When review was performed

**Key Properties:**
- `has_errors`: True if any analysis found errors
- `total_errors`: Total ERROR count across all files
- `total_warnings`: Total WARNING count across all files
- `files_with_issues`: List of files that have comments

**Key Methods:**
- `get_all_comments()`: Get all comments from all analyses
- `get_comments_by_severity()`: Filter all comments by severity

## Enums

### SeverityLevel
- `ERROR`: Critical issues that must be fixed
- `WARNING`: Issues that should be addressed
- `INFO`: Informational notes
- `SUGGESTION`: Suggestions for improvement

### FileStatus
- `ADDED`: File was added
- `MODIFIED`: File was modified
- `DELETED`: File was deleted
- `RENAMED`: File was renamed

### AnalysisType
- `STATIC`: Static code analysis
- `AI`: AI-powered analysis
- `SECURITY`: Security-focused analysis
- `PERFORMANCE`: Performance analysis

## Usage Examples

### Creating a Simple PR
```python
from ai_pr_agent.core import PullRequest, FileChange, FileStatus

file = FileChange(
    filename="app.py",
    status=FileStatus.MODIFIED,
    additions=10,
    deletions=5
)

pr = PullRequest(
    id=1,
    title="Fix bug",
    description="This fixes issue #42",
    author="developer",
    source_branch="bugfix",
    files_changed=[file]
)