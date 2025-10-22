# Quick Start: GitHub Integration

## 5-Minute Setup

### 1. Generate Token (2 minutes)

1. Visit: https://github.com/settings/tokens/new
2. Name: "AI PR Review"
3. Scopes: Check `repo`
4. Click "Generate token"
5. Copy token: `ghp_xxxxx...`

### 2. Set Token (30 seconds)
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

### 3. Test Connection (30 seconds)
```bash
ai-pr-review github test-connection
```

### 4. Analyze Your First PR (2 minutes)
```bash
# List PRs
ai-pr-review github list-prs your-username/your-repo

# Analyze one
ai-pr-review github analyze-pr your-username/your-repo 1
```

## What's Next?

- Try `--dry-run` to see what would be posted
- Use `--post` to actually post reviews
- Integrate with CI/CD pipeline
- Create more test PRs for practice

## Getting Help
```bash
# Help for all commands
ai-pr-review github --help

# Help for specific command
ai-pr-review github analyze-pr --help
```