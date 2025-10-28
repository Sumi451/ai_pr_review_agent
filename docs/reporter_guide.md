"""
# GitHub Reporter Guide

## Overview

The GitHub Reporter formats and posts code review comments to GitHub pull requests.

## Features

- ✅ Post complete reviews with multiple comments
- ✅ Post individual inline comments
- ✅ Post summary comments
- ✅ Markdown formatting with GitHub-flavored syntax
- ✅ Severity-based comment prioritization
- ✅ Batch posting to avoid rate limits
- ✅ Review event determination (APPROVE/REQUEST_CHANGES/COMMENT)

## Basic Usage

### 1. Initialize Reporter

```python
from ai_pr_agent.adapters import AdapterFactory
from ai_pr_agent.reporters import GitHubReporter

adapter = AdapterFactory.create_github_adapter(token="your_token")
reporter = GitHubReporter(adapter)
```

### 2. Post Complete Review

```python
# After running analysis
review_id = reporter.post_review(
    "owner/repo",
    123,  # PR number
    summary,  # ReviewSummary object
    event="COMMENT",
    max_comments=30
)
```

### 3. Post Summary Comment

```python
comment_id = reporter.post_summary_comment(
    "owner/repo",
    123,
    summary
)
```

### 4. Post Individual Comments

```python
comments = [...]  # List of Comment objects
comment_ids = reporter.post_inline_comments(
    "owner/repo",
    123,
    comments
)
```

## CLI Commands

### Review PR and Post

```bash
# Dry run (preview)
ai-pr-review github review owner/repo 123 --dry-run

# Post review
ai-pr-review github review owner/repo 123 --post

# Request changes
ai-pr-review github review owner/repo 123 --post --event REQUEST_CHANGES

# Approve
ai-pr-review github review owner/repo 123 --post --event APPROVE

# Limit comments
ai-pr-review github review owner/repo 123 --post --max-comments 20
```

### Post Summary Only

```bash
ai-pr-review github post-summary owner/repo 123
```

## Markdown Formatting

The reporter uses clean, professional symbols instead of emojis for better readability:
- ✗ for ERROR
- ! for WARNING  
- i for INFO
- → for SUGGESTION

### Comment Format

```markdown
✗ [ERROR]

Your error message here

**Suggestion:**
```python
corrected_code()
```

*— static analysis*
```

### Review Summary Format

```markdown
## Code Review Report

✓ **Status:** Success

### Summary

- **Files Analyzed:** 5
- **Total Comments:** 12
- **Errors:** 2
- **Warnings:** 10
- **Execution Time:** 3.5s

### Files with Issues

- `src/main.py` - 1 errors, 3 warnings
- `src/utils.py` - 1 errors, 2 warnings

### Issue Breakdown

- ✗ **ERROR**: 2
- ! **WARNING**: 10

---
*Inline comments have been posted on relevant lines.*
*Generated at 2025-01-15 10:30:00 UTC*
```

## Configuration

### Review Event Types

- **COMMENT**: General review without approval/changes
- **APPROVE**: Approve the PR
- **REQUEST_CHANGES**: Request changes before merging

The reporter can auto-determine the event:
- Errors present → REQUEST_CHANGES
- Warnings only → COMMENT
- No issues → APPROVE

### Comment Prioritization

Comments are automatically prioritized:
1. ERROR (highest priority)
2. WARNING
3. INFO
4. SUGGESTION (lowest priority)

### Batching

Large reviews are batched to avoid rate limits:
- Default batch size: 30 comments
- Configurable via `max_comments` parameter

## Best Practices

### 1. Use Dry Run First

```bash
ai-pr-review github review owner/repo 123 --dry-run
```

### 2. Limit Comments for Large PRs

```bash
ai-pr-review github review owner/repo 123 --post --max-comments 20
```

### 3. Use Appropriate Review Events

```bash
# For informational review
--event COMMENT

# For blocking issues
--event REQUEST_CHANGES

# For approval
--event APPROVE
```

### 4. Post Summary for Quick Overview

```bash
ai-pr-review github post-summary owner/repo 123
```

## Examples

### Example 1: Full Review Workflow

```python
from ai_pr_agent.adapters import AdapterFactory
from ai_pr_agent.reporters import GitHubReporter
from ai_pr_agent.core.engine import AnalysisEngine
from ai_pr_agent.analyzers import StaticAnalyzer

# Setup
adapter = AdapterFactory.create_github_adapter(token="token")
reporter = GitHubReporter(adapter)
engine = AnalysisEngine()
engine.register_analyzer(StaticAnalyzer())

# Get PR and analyze
pr = adapter.get_pull_request("owner/repo", 123)
summary = engine.analyze_pull_request(pr)

# Post review
review_id = reporter.post_review(
    "owner/repo",
    123,
    summary,
    event="COMMENT",
    max_comments=25
)

print(f"Review posted: {review_id}")
```

### Example 2: Summary Comment Only

```python
# Quick summary without inline comments
comment_id = reporter.post_summary_comment(
    "owner/repo",
    123,
    summary
)
```

### Example 3: Custom Formatting

```python
from ai_pr_agent.reporters import MarkdownFormatter

formatter = MarkdownFormatter()

# Format custom comment
comment = Comment(
    body="Custom issue",
    severity=SeverityLevel.WARNING,
    line=42,
    path="file.py"
)

formatted = formatter.format_comment(comment)
print(formatted)
```

## Troubleshooting

### Rate Limiting

If you hit rate limits:
- Reduce `max_comments`
- Use batching
- Check rate limit: `adapter.get_rate_limit()`

### Permission Errors

Ensure your token has:
- `repo` scope (for private repos)
- Write access to repository

### Comment Not Appearing

- Check that file/line exists in PR
- Verify comment format
- Check GitHub logs

## API Reference

### GitHubReporter

```python
class GitHubReporter:
    def __init__(self, adapter: BaseAdapter)
    
    def post_review(
        self,
        repository: str,
        pr_number: int,
        summary: ReviewSummary,
        event: str = "COMMENT",
        max_comments: Optional[int] = None
    ) -> str
    
    def post_summary_comment(
        self,
        repository: str,
        pr_number: int,
        summary: ReviewSummary
    ) -> str
    
    def post_inline_comments(
        self,
        repository: str,
        pr_number: int,
        comments: List[Comment],
        batch_size: int = 10
    ) -> List[str]
```

### MarkdownFormatter

```python
class MarkdownFormatter:
    def format_comment(self, comment: Comment) -> str
    
    def format_review_summary(self, summary: ReviewSummary) -> str
    
    def format_summary_comment(self, summary: ReviewSummary) -> str
    
    def format_file_summary(self, result: AnalysisResult) -> str
```

## See Also

- [GitHub Integration Guide](github_integration.md)
- [CLI Reference](cli_reference.md)
- [API Documentation](api_reference.md)
