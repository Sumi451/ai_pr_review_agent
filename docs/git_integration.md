# Git Integration Guide

## Overview

The AI PR Review Agent can analyze git changes directly from your local repository without needing GitHub API access.

## Available Commands

### 1. Analyze Branch Differences

Compare changes between two branches:
```cmd
ai-pr-review analyze-branch --base main --compare feature/new-feature

# Compare current branch with main
ai-pr-review analyze-branch

# Compare specific branches
ai-pr-review analyze-branch -b develop -c feature/xyz

# Get JSON output
ai-pr-review analyze-branch -b main -c feature/xyz -o json

# Get markdown report
ai-pr-review analyze-branch -b main -c feature/xyz -o markdown > report.md

# Analyze latest commit
ai-pr-review analyze-commit

# Analyze specific commit by hash
ai-pr-review analyze-commit abc123

# Analyze commit with JSON output
ai-pr-review analyze-commit HEAD -o json

# Analyze uncommitted changes
ai-pr-review analyze-uncommitted

# Get markdown report of uncommitted changes
ai-pr-review analyze-uncommitted -o markdown > uncommitted-report.md

### Step 8: Testing and Verification
```cmd
# Install GitPython
pip install GitPython

# Test git parser
pytest tests\unit\test_git_parser.py -v

# Test git info command
ai-pr-review git-info

# Test analyzing uncommitted changes (if you have any)
ai-pr-review analyze-uncommitted

# Test analyzing a commit
ai-pr-review analyze-commit HEAD

# Test branch comparison (adjust branch names)
ai-pr-review analyze-branch -b main -c your-current-branch

# Run all tests
pytest tests\unit\ -v