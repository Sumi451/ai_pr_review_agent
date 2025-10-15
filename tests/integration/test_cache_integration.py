"""Integration tests for cache with analyzer."""

import pytest
import tempfile
from pathlib import Path

from ai_pr_agent.cache import CacheManager
from ai_pr_agent.analyzers import StaticAnalyzer
from ai_pr_agent.core import FileChange, FileStatus


@pytest.mark.integration
class TestCacheIntegration:
    """Test cache integration with analyzers."""
    
    @pytest.fixture
    def temp_cache_db(self):
        """Create temporary cache database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        yield db_path
        Path(db_path).unlink(missing_ok=True)
    
    def test_analyzer_uses_cache(self, temp_cache_db):
        """Test that analyzer uses cache."""
        # Create analyzer with cache
        analyzer = StaticAnalyzer()
        analyzer.cache = CacheManager(temp_cache_db)
        
        # Create file change
        code = "def hello():\n    print('Hello')\n"
        patch = f"@@ -0,0 +1,2 @@\n+{code}"
        
        file_change = FileChange(
            filename="test.py",
            status=FileStatus.ADDED,
            additions=2,
            deletions=0,
            patch=patch
        )
        
        # First analysis - should miss cache
        result1 = analyzer.analyze(file_change)
        assert result1 is not None
        
        # Second analysis - should hit cache
        result2 = analyzer.analyze(file_change)
        assert result2 is not None
        
        # Results should be similar
        assert result1.filename == result2.filename
        assert len(result1.comments) == len(result2.comments)