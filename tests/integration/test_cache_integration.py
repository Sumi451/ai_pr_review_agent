"""Integration tests for cache with analyzer."""

import gc
import pytest
import tempfile
import time
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
        
        # Cleanup: delete the database file
        # Note: Tests must close any CacheManager instances before teardown
        # Force garbage collection to ensure all SQLite connections are closed
        gc.collect()
        # Give Windows a moment to release file handles
        time.sleep(0.1)
        try:
            Path(db_path).unlink(missing_ok=True)
        except PermissionError:
            # On Windows, sometimes the file is still locked
            # Try one more time after forcing another GC and longer delay
            gc.collect()
            time.sleep(0.5)
            Path(db_path).unlink(missing_ok=True)
    
    def test_analyzer_uses_cache(self, temp_cache_db):
        """Test that analyzer uses cache."""
        # Create analyzer with cache
        analyzer = StaticAnalyzer()
        cache_manager = CacheManager(temp_cache_db)
        analyzer.cache = cache_manager
        
        try:
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
        finally:
            # Always close the cache connection
            cache_manager.close()