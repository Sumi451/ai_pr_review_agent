"""
Demonstration of git-based analysis.
"""
from ai_pr_agent.utils.git_parser import DiffParser, GitRepository
from rich import print as rprint


def main():
    """Demonstrate git analysis capabilities."""
    
    rprint("[bold blue]🔍 Git Analysis Demo[/bold blue]\n")
    
    try:
        # Initialize repository
        repo = GitRepository('.')
        
        # Show repository info
        rprint("[cyan]Repository Information:[/cyan]")
        current_branch = repo.get_current_branch()
        rprint(f"  Current branch: {current_branch}")
        
        branches = repo.list_branches()
        rprint(f"  Total branches: {len(branches)}")
        rprint(f"  Branches: {', '.join(branches[:5])}")
        
        # Get latest commit info
        commit_info = repo.get_commit_info()
        rprint(f"\n[cyan]Latest Commit:[/cyan]")
        rprint(f"  Hash: {commit_info['short_hash']}")
        rprint(f"  Author: {commit_info['author']}")
        rprint(f"  Message: {commit_info['message'].split(chr(10))[0]}")
        
        # Get uncommitted changes
        rprint(f"\n[cyan]Uncommitted Changes:[/cyan]")
        diff_text = repo.get_uncommitted_changes()
        
        if diff_text:
            parser = DiffParser()
            file_changes = parser.parse_diff(diff_text)
            
            rprint(f"  {len(file_changes)} file(s) with uncommitted changes")
            for fc in file_changes:
                rprint(f"    • {fc.filename} (+{fc.additions}/-{fc.deletions})")
        else:
            rprint("  No uncommitted changes")
        
        rprint("\n[green]✓ Demo complete![/green]")
        
    except Exception as e:
        rprint(f"[red]❌ Error: {e}[/red]")


if __name__ == "__main__":
    main()