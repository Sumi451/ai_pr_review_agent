"""
Helper functions for CLI operations.
"""
from pathlib import Path
from typing import List
from rich.console import Console
from rich.syntax import Syntax

console = Console()


def display_code_snippet(code: str, language: str = "python", line_numbers: bool = True):
    """
    Display a code snippet with syntax highlighting.
    
    Args:
        code: Code to display
        language: Programming language
        line_numbers: Whether to show line numbers
    """
    syntax = Syntax(code, language, line_numbers=line_numbers, theme="monokai")
    console.print(syntax)


def find_python_files(directory: Path, exclude_patterns: List[str] = None) -> List[Path]:
    """
    Find all Python files in a directory.
    
    Args:
        directory: Directory to search
        exclude_patterns: Patterns to exclude
    
    Returns:
        List of Python file paths
    """
    if exclude_patterns is None:
        exclude_patterns = ['__pycache__', '.venv', 'venv', 'build', 'dist']
    
    python_files = []
    
    for py_file in directory.rglob("*.py"):
        # Check if file should be excluded
        should_exclude = any(pattern in str(py_file) for pattern in exclude_patterns)
        
        if not should_exclude:
            python_files.append(py_file)
    
    return python_files


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"