"""Command-line interface for AI PR Review Agent."""

import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from ai_pr_agent.config import get_settings


console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """AI Pull Request Review Agent CLI."""
    pass


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
                raise click.ClickException("Configuration validation failed")
            else:
                rprint("[green]✅ Configuration is valid![/green]")
                return
        
        # Display configuration
        rprint("[bold blue]🔧 AI PR Review Agent Configuration[/bold blue]\n")
        
        # Create table for configuration display
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan", width=30)
        table.add_column("Value", style="green")
        
        config_dict = settings.to_dict()
        
        def add_section(section_name: str, section_data: dict, prefix: str = ""):
            for key, value in section_data.items():
                if isinstance(value, dict):
                    add_section(f"{section_name}.{key}", value, prefix + "  ")
                else:
                    table.add_row(f"{prefix}{section_name}.{key}", str(value))
        
        for section_name, section_data in config_dict.items():
            add_section(section_name, section_data)
        
        console.print(table)
        
    except Exception as e:
        raise click.ClickException(f"Configuration error: {e}")


if __name__ == "__main__":
    main()