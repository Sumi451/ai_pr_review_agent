"""
Command-line interface for AI PR Review Agent.
"""
import click
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from datetime import datetime

from ai_pr_agent.config import get_settings, reload_settings
from ai_pr_agent.core import (
    PullRequest,
    FileChange,
    FileStatus,
    SeverityLevel,
)
from ai_pr_agent.utils.git_parser import DiffParser, GitRepository
from ai_pr_agent.core.engine import AnalysisEngine
from ai_pr_agent.analyzers import StaticAnalyzer
from ai_pr_agent.utils import get_logger
from ai_pr_agent.cache import CacheManager
from ai_pr_agent.adapters import AdapterFactory, PlatformType
from ai_pr_agent.core.exceptions import NotFoundError, APIError, RateLimitError
from ai_pr_agent.core.exceptions import AccessPermissionError as CustomPermissionError
import os

console = Console()
logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.1.0")
@click.option('--debug', is_flag=True, help='Enable debug mode')
def main(debug):
    """AI Pull Request Review Agent CLI."""
    if debug:
        import logging
        logger.setLevel(logging.DEBUG)


@main.command()
@click.option(
    "--config",
    "-c",
    help="Path to configuration file",
    type=click.Path(exists=True)
)
@click.option(
    "--validate",
    "-v",
    is_flag=True,
    help="Validate configuration"
)
def config(config: str, validate: bool):
    """Show and validate configuration."""
    try:
        settings = get_settings(config)
        
        if validate:
            errors = settings.validate()
            if errors:
                rprint("[red]❌ Configuration validation failed:[/red]")
                for error in errors:
                    rprint(f"  • {error}")
                sys.exit(1)
            else:
                rprint("[green]✅ Configuration is valid![/green]")
                return
        
        # Display configuration
        rprint(Panel.fit(
            "[bold blue]AI PR Review Agent Configuration[/bold blue]",
            border_style="blue"
        ))
        
        # Create table for configuration display
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan", width=40)
        table.add_column("Value", style="green")
        
        config_dict = settings.to_dict()
        
        def add_section(section_name: str, section_data: dict, prefix: str = ""):
            for key, value in section_data.items():
                if isinstance(value, dict):
                    add_section(f"{section_name}.{key}", value, prefix + "  ")
                elif isinstance(value, list):
                    table.add_row(
                        f"{prefix}{section_name}.{key}",
                        ", ".join(str(v) for v in value[:3]) + ("..." if len(value) > 3 else "")
                    )
                else:
                    table.add_row(f"{prefix}{section_name}.{key}", str(value))
        
        for section_name, section_data in config_dict.items():
            add_section(section_name, section_data)
        
        console.print(table)
        
    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--pr-id', default=1, help='Pull request ID for testing')
@click.option('--title', default='Test PR', help='Pull request title')
@click.option('--author', default='developer', help='PR author name')
@click.option('--output', '-o', type=click.Choice(['text', 'json', 'markdown']), default='text')
@click.option('--no-static', is_flag=True, help='Disable static analysis')
def analyze(files, pr_id, title, author, output, no_static):
    """Analyze local files as if they were in a pull request."""
    
    if not files:
        rprint("[yellow]No files specified. Use: ai-pr-review analyze <file1> <file2>...[/yellow]")
        sys.exit(1)
    
    rprint(Panel.fit(
        f"[bold blue]Analyzing {len(files)} file(s)[/bold blue]",
        border_style="blue"
    ))
    
    # Create file changes from local files
    file_changes = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Reading files...", total=len(files))
        
        for file_path in files:
            try:
                path = Path(file_path)
                
                # Read file content
                content = path.read_text(encoding='utf-8')
                
                # Create a mock patch (for analysis)
                patch = f"@@ -0,0 +1,{len(content.splitlines())} @@\n"
                patch += '\n'.join(f"+{line}" for line in content.splitlines())
                
                file_change = FileChange(
                    filename=str(path),
                    status=FileStatus.MODIFIED,
                    additions=len(content.splitlines()),
                    deletions=0,
                    patch=patch
                )
                
                file_changes.append(file_change)
                progress.advance(task)
                
            except Exception as e:
                rprint(f"[red]Error reading {file_path}: {e}[/red]")
    
    if not file_changes:
        rprint("[red]No valid files to analyze[/red]")
        sys.exit(1)
    
    # Create a mock PR
    pr = PullRequest(
        id=pr_id,
        title=title,
        description="Local analysis via CLI",
        author=author,
        source_branch="local",
        target_branch="main",
        files_changed=file_changes,
        created_at=datetime.now()
    )
    
    # Set up analysis engine
    engine = AnalysisEngine()
    
    if not no_static:
        engine.register_analyzer(StaticAnalyzer())
        rprint("[green] Static analyzer registered[/green]")
    
    # Run analysis
    rprint("\n[bold]Running analysis...[/bold]")
    
    try:
        summary = engine.analyze_pull_request(pr)
        
        # Display results based on output format
        if output == 'text':
            _display_text_results(summary)
        elif output == 'json':
            _display_json_results(summary)
        elif output == 'markdown':
            _display_markdown_results(summary)
        
    except Exception as e:
        rprint(f"[red]Analysis failed: {e}[/red]")
        logger.exception("Analysis error")
        sys.exit(1)


def _display_text_results(summary):
    """Display analysis results in text format."""
    
    # Summary panel
    status_color = {
        "success": "green",
        "partial_failure": "yellow",
        "failure": "red"
    }.get(summary.overall_status, "white")
    
    rprint(f"\n[bold {status_color}]Analysis Status: {summary.overall_status.upper()}[/bold {status_color}]")
    rprint(f"Files analyzed: {len(summary.analysis_results)}")
    rprint(f"Total comments: {summary.total_comments}")
    rprint(f"Errors: {summary.total_errors}")
    rprint(f"Warnings: {summary.total_warnings}")
    rprint(f"Execution time: {summary.total_execution_time:.2f}s\n")
    
    # Results by file
    for result in summary.analysis_results:
        if not result.comments:
            continue
        
        rprint(f"\n[bold cyan]📄 {result.filename}[/bold cyan]")
        rprint(f"   Issues: {len(result.comments)} (Errors: {result.error_count}, Warnings: {result.warning_count})")
        
        # Group by severity
        for severity in [SeverityLevel.ERROR, SeverityLevel.WARNING, SeverityLevel.INFO, SeverityLevel.SUGGESTION]:
            comments = result.get_comments_by_severity(severity)
            if not comments:
                continue
            
            icon = {
                SeverityLevel.ERROR: "❌",
                SeverityLevel.WARNING: "⚠️",
                SeverityLevel.INFO: "ℹ️",
                SeverityLevel.SUGGESTION: "💡"
            }[severity]
            
            for comment in comments:
                location = f"Line {comment.line}" if comment.line else "File"
                rprint(f"   {icon} [{location}] {comment.body}")


def _display_json_results(summary):
    """Display analysis results in JSON format."""
    import json
    summary_dict = summary.to_dict()
    print(json.dumps(summary_dict, indent=2, default=str))


def _display_markdown_results(summary):
    """Display analysis results in Markdown format."""
    
    md = f"# Analysis Report\n\n"
    md += f"**Status:** {summary.overall_status}\n\n"
    md += f"**Summary:**\n"
    md += f"- Files analyzed: {len(summary.analysis_results)}\n"
    md += f"- Total comments: {summary.total_comments}\n"
    md += f"- Errors: {summary.total_errors}\n"
    md += f"- Warnings: {summary.total_warnings}\n"
    md += f"- Execution time: {summary.total_execution_time:.2f}s\n\n"
    
    md += "## Issues by File\n\n"
    
    for result in summary.analysis_results:
        if not result.comments:
            continue
        
        md += f"### {result.filename}\n\n"
        
        for severity in [SeverityLevel.ERROR, SeverityLevel.WARNING, SeverityLevel.INFO, SeverityLevel.SUGGESTION]:
            comments = result.get_comments_by_severity(severity)
            if not comments:
                continue
            
            md += f"#### {severity.value.capitalize()}\n\n"
            
            for comment in comments:
                location = f"Line {comment.line}" if comment.line else "File level"
                md += f"- **[{location}]** {comment.body}\n"
            
            md += "\n"
    
    print(md)


@main.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--extensions', '-e', multiple=True, help='File extensions to analyze (e.g., .py)')
@click.option('--exclude', '-x', multiple=True, help='Patterns to exclude')
def scan(directory, extensions, exclude):
    """Scan a directory for files to analyze."""
    
    from pathlib import Path
    
    dir_path = Path(directory)
    
    if not extensions:
        settings = get_settings()
        extensions = settings.file_filter.included_extensions
    
    rprint(f"[bold]Scanning {directory}...[/bold]")
    
    files_found = []
    
    for ext in extensions:
        for file_path in dir_path.rglob(f"*{ext}"):
            # Check exclusions
            should_exclude = False
            for pattern in exclude:
                if pattern in str(file_path):
                    should_exclude = True
                    break
            
            if not should_exclude:
                files_found.append(file_path)
    
    if files_found:
        rprint(f"\n[green]Found {len(files_found)} file(s):[/green]")
        for f in files_found[:20]:  # Show first 20
            rprint(f"  • {f}")
        
        if len(files_found) > 20:
            rprint(f"  ... and {len(files_found) - 20} more")
        
        rprint(f"\n[cyan]To analyze these files, run:[/cyan]")
        rprint(f"  ai-pr-review analyze {' '.join(str(f) for f in files_found[:5])} ...")
    else:
        rprint("[yellow]No files found matching criteria[/yellow]")


@main.command()
def demo():
    """Run a demonstration of the analysis engine."""
    
    rprint(Panel.fit(
        "[bold blue]AI PR Review Agent Demo[/bold blue]",
        border_style="blue"
    ))
    
    # Create sample code with issues
    sample_code = '''
def badly_formatted(x,y):
    result=x+y
    password="hardcoded"
    return result
'''
    
    rprint("\n[bold]Creating sample PR with intentional issues...[/bold]")
    
    patch = f"@@ -0,0 +1,{len(sample_code.splitlines())} @@\n"
    patch += '\n'.join(f"+{line}" for line in sample_code.splitlines())
    
    file_change = FileChange(
        filename="demo.py",
        status=FileStatus.ADDED,
        additions=len(sample_code.splitlines()),
        deletions=0,
        patch=patch
    )
    
    pr = PullRequest(
        id=999,
        title="Demo PR",
        description="Demonstration of analysis capabilities",
        author="demo-user",
        source_branch="demo",
        target_branch="main",
        files_changed=[file_change]
    )
    
    # Run analysis
    engine = AnalysisEngine()
    engine.register_analyzer(StaticAnalyzer())
    
    rprint("\n[bold]Analyzing...[/bold]")
    summary = engine.analyze_pull_request(pr)
    
    _display_text_results(summary)
    
    rprint(f"\n[green]✓ Demo complete![/green]")


@main.command()
@click.option('--show-stats', is_flag=True, help='Show analyzer statistics')
def info(show_stats):
    """Show information about the AI PR Review Agent."""
    
    settings = get_settings()
    
    info_text = f"""[bold blue]AI PR Review Agent v0.1.0[/bold blue]

[bold]Configuration:[/bold]
  Config file: config/config.yaml
  Log file: {settings.logging.file}
  Debug mode: {settings.app.debug}

[bold]Enabled Features:[/bold]
  Static Analysis: {settings.analysis.static_analysis.enabled}
  AI Feedback: {settings.analysis.ai_feedback.enabled}

[bold]Supported Languages:[/bold]
  {', '.join(settings.file_filter.included_extensions)}
"""
    
    rprint(Panel(info_text, border_style="blue"))
    
    if show_stats:
        engine = AnalysisEngine()
        engine.register_analyzer(StaticAnalyzer())
        
        stats = engine.get_statistics()
        rprint(f"\n[bold]Engine Statistics:[/bold]")
        rprint(f"  Total analyzers: {stats['total_analyzers']}")
        rprint(f"  Analyzer types: {', '.join(stats['analyzer_types'])}")

@main.command()
@click.option('--base', '-b', default='main', help='Base branch')
@click.option('--compare', '-c', help='Branch to compare (defaults to current)')
@click.option('--output', '-o', type=click.Choice(['text', 'json', 'markdown']), default='text')
@click.option('--no-static', is_flag=True, help='Disable static analysis')
@click.option('--repo-path', default='.', help='Path to git repository')
def analyze_branch(base, compare, output, no_static, repo_path):
    """Analyze changes between git branches."""
    
    try:
        # Initialize git repository
        git_repo = GitRepository(repo_path)
        
        # Get compare branch (default to current)
        if not compare:
            compare = git_repo.get_current_branch()
            rprint(f"[cyan]Using current branch: {compare}[/cyan]")
        
        # Check if branches exist
        if not git_repo.branch_exists(base):
            rprint(f"[red]❌ Base branch '{base}' not found[/red]")
            sys.exit(1)
        
        if not git_repo.branch_exists(compare):
            rprint(f"[red]❌ Compare branch '{compare}' not found[/red]")
            sys.exit(1)
        
        rprint(Panel.fit(
            f"[bold blue]📊 Analyzing {compare} vs {base}[/bold blue]",
            border_style="blue"
        ))
        
        # Get diff
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Getting git diff...", total=None)
            diff_text = git_repo.get_branch_diff(base, compare)
            progress.update(task, completed=True)
        
        if not diff_text or not diff_text.strip():
            rprint("[yellow]⚠️  No differences found between branches[/yellow]")
            return
        
        # Parse diff into file changes
        parser = DiffParser()
        file_changes = parser.parse_diff(diff_text)
        
        if not file_changes:
            rprint("[yellow]⚠️  No file changes to analyze[/yellow]")
            return
        
        rprint(f"[green]✓ Found {len(file_changes)} changed file(s)[/green]")
        
        # Get commit info for PR metadata
        commit_info = git_repo.get_commit_info(compare)
        
        # Create PR object
        pr = PullRequest(
            id=1,
            title=f"Changes in {compare}",
            description=commit_info['message'],
            author=commit_info['author'],
            source_branch=compare,
            target_branch=base,
            files_changed=file_changes,
            created_at=datetime.now()
        )
        
        # Run analysis
        _run_analysis_and_display(pr, output, no_static)
        
    except Exception as e:
        rprint(f"[red]❌ Error: {e}[/red]")
        logger.exception("Branch analysis failed")
        sys.exit(1)


@main.command()
@click.argument('commit', default='HEAD')
@click.option('--output', '-o', type=click.Choice(['text', 'json', 'markdown']), default='text')
@click.option('--no-static', is_flag=True, help='Disable static analysis')
@click.option('--repo-path', default='.', help='Path to git repository')
def analyze_commit(commit, output, no_static, repo_path):
    """Analyze changes in a specific commit."""
    
    try:
        # Initialize git repository
        git_repo = GitRepository(repo_path)
        
        # Get commit info
        commit_info = git_repo.get_commit_info(commit)
        
        rprint(Panel.fit(
            f"[bold blue]📊 Analyzing commit {commit_info['short_hash']}[/bold blue]\n"
            f"[cyan]{commit_info['message']}[/cyan]",
            border_style="blue"
        ))
        
        # Get diff
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Getting commit diff...", total=None)
            diff_text = git_repo.get_commit_diff(commit)
            progress.update(task, completed=True)
        
        if not diff_text or not diff_text.strip():
            rprint("[yellow]⚠️  No changes in this commit[/yellow]")
            return
        
        # Parse diff
        parser = DiffParser()
        file_changes = parser.parse_diff(diff_text)
        
        if not file_changes:
            rprint("[yellow]⚠️  No file changes to analyze[/yellow]")
            return
        
        rprint(f"[green]✓ Found {len(file_changes)} changed file(s)[/green]")
        
        # Create PR object
        pr = PullRequest(
            id=1,
            title=commit_info['message'].split('\n')[0],  # First line
            description=commit_info['message'],
            author=commit_info['author'],
            source_branch=commit_info['short_hash'],
            target_branch='base',
            files_changed=file_changes,
            created_at=datetime.now()
        )
        
        # Run analysis
        _run_analysis_and_display(pr, output, no_static)
        
    except Exception as e:
        rprint(f"[red]❌ Error: {e}[/red]")
        logger.exception("Commit analysis failed")
        sys.exit(1)


@main.command()
@click.option('--output', '-o', type=click.Choice(['text', 'json', 'markdown']), default='text')
@click.option('--no-static', is_flag=True, help='Disable static analysis')
@click.option('--repo-path', default='.', help='Path to git repository')
def analyze_uncommitted(output, no_static, repo_path):
    """Analyze uncommitted changes in the working directory."""
    
    try:
        # Initialize git repository
        git_repo = GitRepository(repo_path)
        
        current_branch = git_repo.get_current_branch()
        
        rprint(Panel.fit(
            f"[bold blue]📊 Analyzing uncommitted changes[/bold blue]\n"
            f"[cyan]Branch: {current_branch}[/cyan]",
            border_style="blue"
        ))
        
        # Get uncommitted changes
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Getting uncommitted changes...", total=None)
            diff_text = git_repo.get_uncommitted_changes()
            progress.update(task, completed=True)
        
        if not diff_text or not diff_text.strip():
            rprint("[yellow]⚠️  No uncommitted changes found[/yellow]")
            return
        
        # Parse diff
        parser = DiffParser()
        file_changes = parser.parse_diff(diff_text)
        
        if not file_changes:
            rprint("[yellow]⚠️  No file changes to analyze[/yellow]")
            return
        
        rprint(f"[green]✓ Found {len(file_changes)} changed file(s)[/green]")
        
        # Create PR object
        pr = PullRequest(
            id=1,
            title="Uncommitted changes",
            description="Analysis of uncommitted changes in working directory",
            author="local",
            source_branch=current_branch,
            target_branch="base",
            files_changed=file_changes,
            created_at=datetime.now()
        )
        
        # Run analysis
        _run_analysis_and_display(pr, output, no_static)
        
    except Exception as e:
        rprint(f"[red]❌ Error: {e}[/red]")
        logger.exception("Uncommitted changes analysis failed")
        sys.exit(1)


@main.command()
@click.option('--repo-path', default='.', help='Path to git repository')
def git_info(repo_path):
    """Show git repository information."""
    
    try:
        git_repo = GitRepository(repo_path)
        
        current_branch = git_repo.get_current_branch()
        branches = git_repo.list_branches()
        commit_info = git_repo.get_commit_info()
        
        info_text = f"""[bold]Git Repository Information[/bold]

[cyan]Current Branch:[/cyan] {current_branch}

[cyan]All Branches:[/cyan]
{chr(10).join(f"  • {branch}" for branch in branches[:10])}
{f"  [dim]... and {len(branches) - 10} more[/dim]" if len(branches) > 10 else ""}

[cyan]Latest Commit:[/cyan]
  Hash: {commit_info['short_hash']}
  Author: {commit_info['author']}
  Date: {commit_info['date'][:10]}
  Message: {commit_info['message'].split(chr(10))[0]}
"""
        
        rprint(Panel(info_text, border_style="blue", title="🔍 Git Info"))
        
    except Exception as e:
        rprint(f"[red]❌ Error: {e}[/red]")
        logger.exception("Git info failed")
        sys.exit(1)


# Helper function to consolidate analysis logic
def _run_analysis_and_display(pr, output_format, no_static):
    """Run analysis and display results."""
    
    # Set up analysis engine
    engine = AnalysisEngine()
    
    if not no_static:
        engine.register_analyzer(StaticAnalyzer())
        rprint("[green]✓ Static analyzer registered[/green]")
    
    # Run analysis
    rprint("\n[bold]🔍 Running analysis...[/bold]\n")
    
    try:
        summary = engine.analyze_pull_request(pr)
        
        # Display results based on output format
        if output_format == 'text':
            _display_text_results(summary)
        elif output_format == 'json':
            _display_json_results(summary)
        elif output_format == 'markdown':
            _display_markdown_results(summary)
        
    except Exception as e:
        rprint(f"[red]❌ Analysis failed: {e}[/red]")
        logger.exception("Analysis error")
        raise

@main.group()
def cache():
    """Manage analysis cache."""
    pass


@cache.command()
def stats():
    """Show cache statistics."""
    try:
        cache_mgr = CacheManager()
        stats = cache_mgr.get_cache_stats()
        
        rprint(Panel.fit(
            "[bold blue]📊 Cache Statistics[/bold blue]",
            border_style="blue"
        ))
        
        rprint(f"\n[cyan]Total Entries:[/cyan] {stats.get('total_entries', 0)}")
        rprint(f"[cyan]Database Size:[/cyan] {stats.get('database_size_mb', 0)} MB")
        
        by_analyzer = stats.get('by_analyzer', {})
        if by_analyzer:
            rprint(f"\n[cyan]Entries by Analyzer:[/cyan]")
            for analyzer, count in by_analyzer.items():
                rprint(f"  • {analyzer}: {count}")
        
    except Exception as e:
        rprint(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cache.command()
@click.option('--days', default=7, help='Keep entries from last N days')
def cleanup(days):
    """Clean up old cache entries."""
    try:
        cache_mgr = CacheManager()
        
        rprint(f"[yellow]Cleaning up entries older than {days} days...[/yellow]")
        cache_mgr.cleanup_old_entries(days)
        
        rprint("[green]✓ Cache cleanup complete[/green]")
        
    except Exception as e:
        rprint(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cache.command()
@click.confirmation_option(prompt='Are you sure you want to clear all cache?')
def clear():
    """Clear all cache entries."""
    try:
        cache_mgr = CacheManager()
        cache_mgr.clear_cache()
        
        rprint("[green]✓ Cache cleared[/green]")
        
    except Exception as e:
        rprint(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cache.command('info')
def cache_info():
    """Show cache configuration and location."""
    settings = get_settings()
    
    cache_dir = Path('.cache')
    db_path = cache_dir / 'analysis_cache.db'
    
    info_text = f"""[bold]Cache Configuration[/bold]

[cyan]Status:[/cyan] {'✅ Enabled' if settings.cache.enabled else '❌ Disabled'}
[cyan]TTL:[/cyan] {settings.cache.ttl_hours} hours
[cyan]Max Size:[/cyan] {settings.cache.max_size_mb} MB
[cyan]Database:[/cyan] {db_path}
[cyan]Exists:[/cyan] {'Yes' if db_path.exists() else 'No'}
"""
    
    rprint(Panel(info_text, border_style="blue"))

@main.group()
def github():
    """GitHub integration commands."""
    pass


@github.command()
@click.argument('repository')
@click.argument('pr_number', type=int)
@click.option('--output', '-o', type=click.Choice(['text', 'json', 'markdown']), default='text')
@click.option('--no-static', is_flag=True, help='Disable static analysis')
@click.option('--token', envvar='GITHUB_TOKEN', help='GitHub token (or set GITHUB_TOKEN env var)')
def analyze_pr(repository, pr_number, output, no_static, token):
    """Analyze a GitHub pull request.
    
    Examples:
        ai-pr-review github analyze-pr microsoft/vscode 12345
        ai-pr-review github analyze-pr owner/repo 123 --output json
    """
    if not token:
        rprint("[red]❌ GitHub token not found[/red]")
        rprint("[yellow]Set GITHUB_TOKEN environment variable or use --token option[/yellow]")
        sys.exit(1)
    
    try:
        rprint(Panel.fit(
            f"[bold blue]📊 Analyzing GitHub PR[/bold blue]\n"
            f"[cyan]Repository: {repository}[/cyan]\n"
            f"[cyan]PR Number: #{pr_number}[/cyan]",
            border_style="blue"
        ))
        
        # Create adapter
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Connecting to GitHub...", total=None)
            
            adapter = AdapterFactory.create_github_adapter(token=token)
            
            # Validate connection
            if not adapter.validate_connection():
                rprint("[red]❌ Failed to connect to GitHub[/red]")
                sys.exit(1)
            
            progress.update(task, description="Fetching pull request...")
            
            # Get PR
            pr = adapter.get_pull_request(repository, pr_number)
            
            progress.update(task, completed=True)
        
        rprint(f"[green]✓ PR fetched successfully[/green]")
        rprint(f"  Title: {pr.title}")
        rprint(f"  Author: {pr.author}")
        rprint(f"  Files changed: {len(pr.files_changed)}")
        rprint(f"  State: {pr.state}")
        
        # Run analysis
        _run_analysis_and_display(pr, output, no_static)
        
    except NotFoundError as e:
        rprint(f"[red]❌ Not found: {e}[/red]")
        sys.exit(1)
    except CustomPermissionError as e:
        rprint(f"[red]❌ Permission denied: {e}[/red]")
        sys.exit(1)
    except RateLimitError as e:
        rprint(f"[red]❌ Rate limit exceeded: {e}[/red]")
        sys.exit(1)
    except APIError as e:
        rprint(f"[red]❌ API error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        rprint(f"[red]❌ Unexpected error: {e}[/red]")
        logger.exception("Failed to analyze GitHub PR")
        sys.exit(1)


@github.command()
@click.argument('repository')
@click.argument('pr_number', type=int)
@click.option('--post', is_flag=True, help='Actually post review to GitHub')
@click.option('--dry-run', is_flag=True, help='Show what would be posted without posting')
@click.option('--no-static', is_flag=True, help='Disable static analysis')
@click.option('--token', envvar='GITHUB_TOKEN', help='GitHub token')
def review_pr(repository, pr_number, post, dry_run, no_static, token):
    """Analyze and optionally post review to GitHub PR.
    
    Examples:
        ai-pr-review github review-pr owner/repo 123 --dry-run
        ai-pr-review github review-pr owner/repo 123 --post
    """
    if not token:
        rprint("[red]❌ GitHub token not found[/red]")
        sys.exit(1)
    
    try:
        # Create adapter
        adapter = AdapterFactory.create_github_adapter(token=token)
        
        # Get PR
        rprint(f"[yellow]Fetching PR #{pr_number} from {repository}...[/yellow]")
        pr = adapter.get_pull_request(repository, pr_number)
        
        rprint(f"[green]✓ PR fetched: {pr.title}[/green]\n")
        
        # Run analysis
        engine = AnalysisEngine()
        if not no_static:
            from ai_pr_agent.analyzers import StaticAnalyzer
            engine.register_analyzer(StaticAnalyzer())
        
        rprint("[bold]🔍 Running analysis...[/bold]\n")
        summary = engine.analyze_pull_request(pr)
        
        # Display results
        _display_text_results(summary)
        
        if summary.total_comments == 0:
            rprint("\n[green]✨ No issues found! PR looks good.[/green]")
            return
        
        # Prepare comments for posting
        all_comments = summary.get_all_comments()
        
        if dry_run:
            rprint(f"\n[cyan]📝 Dry run - Would post {len(all_comments)} comment(s):[/cyan]")
            for comment in all_comments[:5]:
                rprint(f"  • [{comment.path}:{comment.line}] {comment.body[:50]}...")
            if len(all_comments) > 5:
                rprint(f"  ... and {len(all_comments) - 5} more")
            return
        
        if post:
            if not Confirm.ask(f"\n[yellow]Post {len(all_comments)} comment(s) to GitHub?[/yellow]"):
                rprint("[yellow]Cancelled[/yellow]")
                return
            
            rprint("\n[yellow]Posting review to GitHub...[/yellow]")
            
            # Post as a review
            review_body = f"""## 🤖 AI Code Review

**Summary:**
- Files analyzed: {len(summary.analysis_results)}
- Total comments: {summary.total_comments}
- Errors: {summary.total_errors}
- Warnings: {summary.total_warnings}

This is an automated review. Please verify all suggestions.
"""
            
            try:
                review_id = adapter.post_review(
                    repository,
                    pr_number,
                    all_comments,
                    review_body,
                    event="COMMENT"
                )
                
                rprint(f"[green]✓ Review posted successfully! (ID: {review_id})[/green]")
                rprint(f"[cyan]View at: {pr.html_url}[/cyan]")
                
            except Exception as e:
                rprint(f"[red]❌ Failed to post review: {e}[/red]")
                sys.exit(1)
        
    except Exception as e:
        rprint(f"[red]❌ Error: {e}[/red]")
        logger.exception("Failed to review PR")
        sys.exit(1)


@github.command()
@click.argument('repository')
@click.option('--state', type=click.Choice(['open', 'closed', 'all']), default='open')
@click.option('--limit', type=int, default=10, help='Maximum number of PRs to list')
@click.option('--token', envvar='GITHUB_TOKEN', help='GitHub token')
def list_prs(repository, state, limit, token):
    """List pull requests in a GitHub repository.
    
    Examples:
        ai-pr-review github list-prs owner/repo
        ai-pr-review github list-prs owner/repo --state closed --limit 20
    """
    if not token:
        rprint("[red]❌ GitHub token not found[/red]")
        sys.exit(1)
    
    try:
        adapter = AdapterFactory.create_github_adapter(token=token)
        
        rprint(f"[yellow]Fetching {state} PRs from {repository}...[/yellow]\n")
        
        prs = adapter.list_pull_requests(repository, state=state, limit=limit)
        
        if not prs:
            rprint(f"[yellow]No {state} pull requests found[/yellow]")
            return
        
        rprint(f"[bold cyan]Found {len(prs)} pull request(s):[/bold cyan]\n")
        
        for pr in prs:
            state_icon = "🟢" if pr.state == "open" else "🔴"
            rprint(f"{state_icon} [bold]#{pr.id}[/bold]: {pr.title}")
            rprint(f"   By: {pr.author} | Branch: {pr.source_branch} → {pr.target_branch}")
            rprint(f"   Files: {len(pr.files_changed)} | +{pr.total_additions}/-{pr.total_deletions}")
            rprint(f"   URL: {pr.html_url}")
            rprint()
        
    except Exception as e:
        rprint(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@github.command()
@click.option('--token', envvar='GITHUB_TOKEN', help='GitHub token')
def test_connection(token):
    """Test GitHub API connection and show user info."""
    if not token:
        rprint("[red]❌ GitHub token not found[/red]")
        rprint("\n[cyan]To set up your token:[/cyan]")
        rprint("1. Go to https://github.com/settings/tokens")
        rprint("2. Generate a new token with 'repo' scope")
        rprint("3. Set it: export GITHUB_TOKEN=your_token")
        sys.exit(1)
    
    try:
        rprint("[yellow]Testing GitHub connection...[/yellow]\n")
        
        adapter = AdapterFactory.create_github_adapter(token=token)
        
        if adapter.validate_connection():
            rprint("[green]✓ Connected to GitHub successfully![/green]\n")
            
            # Get rate limit info
            rate_info = adapter.get_rate_limit()
            rprint("[bold cyan]Rate Limit Info:[/bold cyan]")
            rprint(f"  Limit: {rate_info.limit}")
            rprint(f"  Remaining: {rate_info.remaining}")
            rprint(f"  Resets at: {datetime.fromtimestamp(rate_info.reset_at)}")
            
            # Calculate percentage
            usage_pct = ((rate_info.limit - rate_info.remaining) / rate_info.limit) * 100
            if usage_pct > 80:
                rprint(f"  [red]⚠️  Usage: {usage_pct:.1f}% (high)[/red]")
            else:
                rprint(f"  [green]Usage: {usage_pct:.1f}%[/green]")
        
    except Exception as e:
        rprint(f"[red]❌ Connection failed: {e}[/red]")
        sys.exit(1)


@github.command()
@click.argument('repository')
@click.option('--token', envvar='GITHUB_TOKEN', help='GitHub token')
def repo_info(repository, token):
    """Get information about a GitHub repository.
    
    Example:
        ai-pr-review github repo-info microsoft/vscode
    """
    if not token:
        rprint("[red]❌ GitHub token not found[/red]")
        sys.exit(1)
    
    try:
        adapter = AdapterFactory.create_github_adapter(token=token)
        
        rprint(f"[yellow]Fetching repository info...[/yellow]\n")
        
        repo_info = adapter.get_repository_info(repository)
        
        info_text = f"""[bold]Repository Information[/bold]

[cyan]Name:[/cyan] {repo_info.full_name}
[cyan]Owner:[/cyan] {repo_info.owner}
[cyan]Default Branch:[/cyan] {repo_info.default_branch}
[cyan]Private:[/cyan] {repo_info.is_private}
[cyan]URL:[/cyan] {repo_info.url}
"""
        
        rprint(Panel(info_text, border_style="blue", title="📦 Repository"))
        
    except Exception as e:
        rprint(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()