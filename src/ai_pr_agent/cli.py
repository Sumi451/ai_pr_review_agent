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
from datetime import datetime

from ai_pr_agent.config import get_settings, reload_settings
from ai_pr_agent.core import (
    PullRequest,
    FileChange,
    FileStatus,
    SeverityLevel,
)
from ai_pr_agent.core.engine import AnalysisEngine
from ai_pr_agent.analyzers import StaticAnalyzer
from ai_pr_agent.utils import get_logger

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


if __name__ == "__main__":
    main()