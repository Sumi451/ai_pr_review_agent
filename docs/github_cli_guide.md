# GitHub CLI Commands Guide

## Setup

### 1. Generate GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name (e.g., "AI PR Review Agent")
4. Select scopes:
   - `repo` (Full control of private repositories)
   - `read:org` (Read org and team membership)
5. Click "Generate token"
6. Copy the token (you won't see it again!)

### 2. Set Environment Variable
```bash
# Linux/Mac
export GITHUB_TOKEN=ghp_your_token_here

# Windows (PowerShell)
$env:GITHUB_TOKEN="ghp_your_token_here"

# Or add to .env file
echo "GITHUB_TOKEN=ghp_your_token_here" >> .env
```

## Commands

### Test Connection

Test your GitHub token and see rate limit info:
```bash
ai-pr-review github test-connection
```

### Repository Info

Get information about a repository:
```bash
ai-pr-review github repo-info owner/repo
```

### List Pull Requests

List PRs in a repository:
```bash
# List open PRs
ai-pr-review github list-prs owner/repo

# List closed PRs
ai-pr-review github list-prs owner/repo --state closed

# Limit number of results
ai-pr-review github list-prs owner/repo --limit 20
```

### Analyze Pull Request

Analyze a PR without posting to GitHub:
```bash
# Basic analysis
ai-pr-review github analyze-pr owner/repo 123

# JSON output
ai-pr-review github analyze-pr owner/repo 123 --output json

# Markdown report
ai-pr-review github analyze-pr owner/repo 123 --output markdown > report.md
```

### Review Pull Request

Analyze and post review to GitHub:
```bash
# Dry run (see what would be posted)
ai-pr-review github review-pr owner/repo 123 --dry-run

# Actually post review
ai-pr-review github review-pr owner/repo 123 --post
```

## Examples

### Complete Workflow
```bash
# 1. Test connection
ai-pr-review github test-connection

# 2. List open PRs
ai-pr-review github list-prs your-username/your-repo

# 3. Analyze a specific PR
ai-pr-review github analyze-pr your-username/your-repo 123

# 4. Review with dry run first
ai-pr-review github review-pr your-username/your-repo 123 --dry-run

# 5. Post the review
ai-pr-review github review-pr your-username/your-repo 123 --post
```

### CI/CD Integration
```yaml
# .github/workflows/ai-review.yml
name: AI Code Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install
        run: pip install -e .
      
      - name: Analyze PR
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          ai-pr-review github analyze-pr \
            ${{ github.repository }} \
            ${{ github.event.pull_request.number }} \
            --output json > analysis.json
      
      - name: Check for errors
        run: |
          errors=$(jq '.summary.total_errors' analysis.json)
          if [ $errors -gt 0 ]; then
            echo "Found $errors error(s)"
            exit 1
          fi
```

## Troubleshooting

### Token Issues

**Error:** "GitHub token not found"
**Solution:** Set GITHUB_TOKEN environment variable

**Error:** "Bad credentials"
**Solution:** Regenerate token with correct scopes

### Permission Issues

**Error:** "Access denied" or 403
**Solution:** Ensure token has `repo` scope for private repos

### Rate Limit

**Error:** "Rate limit exceeded"
**Solution:** Wait for reset time shown in error, or use authenticated requests

## Best Practices

1. **Never commit tokens** - Use environment variables
2. **Use dry-run first** - Test before posting
3. **Check rate limits** - Monitor API usage
4. **Specific repositories** - Grant access only to needed repos
5. **Token rotation** - Regenerate tokens periodically