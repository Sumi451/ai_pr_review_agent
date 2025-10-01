"""
Utility functions for testing.
"""

from typing import List, Dict, Any
from pathlib import Path
import json
import yaml


def load_fixture_file(filename: str) -> str:
    """
    Load content from a fixture file.
    
    Args:
        filename: Name of the fixture file
    
    Returns:
        File content as string
    """
    fixture_path = Path(__file__).parent / "fixtures" / filename
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return f.read()


def load_json_fixture(filename: str) -> Dict[str, Any]:
    """
    Load JSON fixture file.
    
    Args:
        filename: Name of the JSON fixture file
    
    Returns:
        Parsed JSON data
    """
    content = load_fixture_file(filename)
    return json.loads(content)


def load_yaml_fixture(filename: str) -> Dict[str, Any]:
    """
    Load YAML fixture file.
    
    Args:
        filename: Name of the YAML fixture file
    
    Returns:
        Parsed YAML data
    """
    content = load_fixture_file(filename)
    return yaml.safe_load(content)


def assert_contains_all(container: List, items: List) -> None:
    """
    Assert that container contains all items.
    
    Args:
        container: List to check
        items: Items that should be in container
    """
    for item in items:
        assert item in container, f"Expected {item} to be in {container}"


def assert_dict_subset(subset: Dict, superset: Dict) -> None:
    """
    Assert that subset is a subset of superset.
    
    Args:
        subset: Dictionary that should be subset
        superset: Dictionary that should be superset
    """
    for key, value in subset.items():
        assert key in superset, f"Key {key} not found in superset"
        assert superset[key] == value, f"Value mismatch for key {key}"


def create_mock_pr_data(**kwargs) -> Dict[str, Any]:
    """
    Create mock pull request data for testing.
    
    Args:
        **kwargs: Override default values
    
    Returns:
        Dictionary with PR data
    """
    default_data = {
        "id": 123,
        "title": "Test PR",
        "description": "Test description",
        "author": "testuser",
        "source_branch": "feature/test",
        "target_branch": "main",
        "files_changed": [],
    }
    default_data.update(kwargs)
    return default_data


def create_mock_file_data(**kwargs) -> Dict[str, Any]:
    """
    Create mock file change data for testing.
    
    Args:
        **kwargs: Override default values
    
    Returns:
        Dictionary with file change data
    """
    default_data = {
        "filename": "test.py",
        "status": "modified",
        "additions": 10,
        "deletions": 5,
        "patch": "@@ -1,5 +1,10 @@\n+ new line",
    }
    default_data.update(kwargs)
    return default_data