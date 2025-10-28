"""
Demonstration of GitHub reporter functionality.
"""
import os
from ai_pr_agent.adapters import AdapterFactory
from ai_pr_agent.reporters import GitHubReporter, MarkdownFormatter
from ai_pr_agent.core import (
    ReviewSummary,
    PullRequest,
    AnalysisResult,
    Comment,
    SeverityLevel,
    AnalysisType,
    FileChange,
    FileStatus,
)
from rich import print as rprint
from datetime import datetime


def main():
    """Demonstrate reporter functionality."""
    
    rprint("[bold blue]🤖 GitHub Reporter Demo[/bold blue]\n")
    
    # Create sample data
    rprint("[cyan]1. Creating sample review data...[/cyan]")
    
    pr = PullRequest(
        id=999,
        title="Demo PR for Reporter Testing",
        description="This is a demo PR",
        author="demo-user",
        source_branch="demo-feature",
        target_branch="main",
        platform="github",
        repository="demo/repo"
    )
    
    # Create analysis results
    result1 = AnalysisResult(
        filename="src/main.py",
        analysis_type=AnalysisType.STATIC
    )
    result1.add_comment(
        "Function complexity too high",
        line=42,
        severity=SeverityLevel.WARNING
    )
    result1.add_comment(
        "Missing docstring",
        line=35,
        severity=SeverityLevel.INFO
    )
    
    result2 = AnalysisResult(
        filename="src/utils.py",
        analysis_type=AnalysisType.STATIC
    )
    result2.add_comment(
        "Potential SQL injection",
        line=15,
        severity=SeverityLevel.ERROR
    )
    
    summary = ReviewSummary(
        pull_request=pr,
        analysis_results=[result1, result2],
        timestamp=datetime.now()
    )
    
    rprint(f"[green]✓ Created summary with {summary.total_comments} comments[/green]\n")
    
    # Demonstrate formatter
    rprint("[cyan]2. Formatting review summary...[/cyan]")
    formatter = MarkdownFormatter()
    
    review_body = formatter.format_review_summary(summary)
    rprint("\n[dim]" + "="*60 + "[/dim]")
    rprint(review_body)
    rprint("[dim]" + "="*60 + "[/dim]\n")
    
    # Demonstrate comment formatting
    rprint("[cyan]3. Formatting individual comment...[/cyan]")
    
    sample_comment = Comment(
        body="This function should be refactored",
        line=42,
        severity=SeverityLevel.WARNING,
        path="src/main.py",
        suggestion="def refactored_function():\n    pass",
        analysis_type=AnalysisType.STATIC
    )
    
    formatted_comment = formatter.format_comment(sample_comment)
    rprint("\n[dim]" + "-"*60 + "[/dim]")
    rprint(formatted_comment)
    rprint("[dim]" + "-"*60 + "[/dim]\n")
    
    # Optional: Post to real GitHub (if token available)
    token = os.getenv('GITHUB_TOKEN')
    if token:
        rprint("[cyan]4. Testing GitHub connection...[/cyan]")
        
        try:
            adapter = AdapterFactory.create_github_adapter(token=token)
            reporter = GitHubReporter(adapter)
            
            rprint("[green]✓ Reporter initialized with GitHub adapter[/green]")
            rprint("[yellow]💡 Ready to post reviews to GitHub PRs[/yellow]")
            
        except Exception as e:
            rprint(f"[red]❌ GitHub connection failed: {e}[/red]")
    else:
        rprint("[yellow]⚠️  GITHUB_TOKEN not set - skipping live test[/yellow]")
    
    rprint("\n[green]✓ Demo complete![/green]")


if __name__ == "__main__":
    main()
