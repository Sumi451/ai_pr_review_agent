# Adapter Pattern Documentation

## Overview

The adapter pattern allows the AI PR Review Agent to support multiple Git platforms (GitHub, GitLab, Bitbucket) through a common interface.

## Architecture
```
BaseAdapter (Abstract)
├── GitHubAdapter
├── GitLabAdapter (future)
└── BitbucketAdapter (future)
```

## Creating a New Adapter

### Step 1: Implement BaseAdapter
```python
from ai_pr_agent.adapters.base import BaseAdapter, AdapterConfig

class MyPlatformAdapter(BaseAdapter):
    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        # Initialize platform-specific client
    
    def validate_connection(self) -> bool:
        # Implement connection validation
        pass
    
    # Implement all abstract methods...
```

### Step 2: Register Adapter
```python
from ai_pr_agent.adapters import AdapterFactory, PlatformType

AdapterFactory.register_adapter(
    PlatformType.MY_PLATFORM,
    MyPlatformAdapter
)
```

### Step 3: Use Adapter
```python
adapter = AdapterFactory.create_adapter(
    PlatformType.MY_PLATFORM,
    token="my_token"
)

pr = adapter.get_pull_request("owner/repo", 123)
```

## Available Methods

### Core Methods
- `validate_connection()` - Test API connection
- `get_pull_request()` - Fetch PR details
- `get_pull_request_files()` - Get changed files
- `get_file_content()` - Fetch file content

### Review Methods
- `post_review_comment()` - Post single comment
- `post_review()` - Post complete review
- `update_comment()` - Update existing comment
- `delete_comment()` - Delete comment

### Query Methods
- `list_pull_requests()` - List PRs in repo
- `get_repository_info()` - Get repo details
- `get_rate_limit()` - Check rate limits

## Error Handling

Adapters should raise appropriate exceptions:
- `NotFoundError` - Resource not found
- `PermissionError` - Insufficient permissions
- `RateLimitError` - Rate limit exceeded
- `APIError` - General API errors

## Best Practices

1. **Always validate connections** before operations
2. **Handle rate limits** gracefully
3. **Use retries** for transient failures
4. **Log all API calls** for debugging
5. **Cache responses** when appropriate