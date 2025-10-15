"""Tests for cache manager."""

import pytest
import tempfile
import time
import gc
from pathlib import Path

from ai_pr_agent.cache import CacheManager
from ai_pr_agent.core import AnalysisResult, AnalysisType, SeverityLevel


class TestCacheManager:
    """Test CacheManager functionality."""
    
    @pytest.fixture
    def temp_cache(self):
        """Create temporary cache database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        cache = CacheManager(db_path)
        yield cache
        
        # Cleanup - Windows-compatible version
        try:
            # Close any open connections
            del cache
            gc.collect()  # Force garbage collection
            time.sleep(0.1)  # Give Windows time to release file handles
            
            # Now try to delete
            db_file = Path(db_path)
            if db_file.exists():
                db_file.unlink()
        except PermissionError:
            # If still locked, try again after a short delay
            time.sleep(0.5)
            try:
                Path(db_path).unlink(missing_ok=True)
            except:
                pass  # Ignore if we still can't delete
    
    def test_cache_initialization(self, temp_cache):
        """Test cache initialization."""
        assert temp_cache.db_path is not None
        assert Path(temp_cache.db_path).exists()
    
    def test_store_and_retrieve_result(self, temp_cache):
        """Test storing and retrieving results."""
        # Create a result
        result = AnalysisResult(
            filename="test.py",
            analysis_type=AnalysisType.STATIC
        )
        result.add_comment("Test issue", line=10, severity=SeverityLevel.WARNING)
        
        # Store in cache
        content = "def hello():\n    pass"
        temp_cache.store_result("test.py", content, "static", result)
        
        # Retrieve from cache
        cached = temp_cache.get_cached_result("test.py", content, "static")
        
        assert cached is not None
        assert cached.filename == "test.py"
        assert len(cached.comments) == 1
        assert cached.comments[0].body == "Test issue"
    
    def test_cache_miss(self, temp_cache):
        """Test cache miss with different content."""
        # Store result
        result = AnalysisResult(filename="test.py", analysis_type=AnalysisType.STATIC)
        content1 = "def hello():\n    pass"
        temp_cache.store_result("test.py", content1, "static", result)
        
        # Try to retrieve with different content
        content2 = "def goodbye():\n    pass"
        cached = temp_cache.get_cached_result("test.py", content2, "static")
        
        assert cached is None
    
    def test_different_analyzer_types(self, temp_cache):
        """Test caching with different analyzer types."""
        result1 = AnalysisResult(filename="test.py", analysis_type=AnalysisType.STATIC)
        result2 = AnalysisResult(filename="test.py", analysis_type=AnalysisType.AI)
        
        content = "def hello():\n    pass"
        
        temp_cache.store_result("test.py", content, "static", result1)
        temp_cache.store_result("test.py", content, "ai", result2)
        
        # Should retrieve correct results for each analyzer
        cached_static = temp_cache.get_cached_result("test.py", content, "static")
        cached_ai = temp_cache.get_cached_result("test.py", content, "ai")
        
        assert cached_static is not None
        assert cached_ai is not None
        assert cached_static.analysis_type == AnalysisType.STATIC
        assert cached_ai.analysis_type == AnalysisType.AI
    
    def test_cache_stats(self, temp_cache):
        """Test getting cache statistics."""
        # Add some entries with DIFFERENT content (so they have different hashes)
        result = AnalysisResult(filename="test.py", analysis_type=AnalysisType.STATIC)
        
        content1 = "def hello():\n    pass"
        content2 = "def goodbye():\n    pass"
        content3 = "def farewell():\n    pass"
        
        temp_cache.store_result("test1.py", content1, "static", result)
        temp_cache.store_result("test2.py", content2, "static", result)
        temp_cache.store_result("test3.py", content3, "ai", result)
        
        # Get stats
        stats = temp_cache.get_cache_stats()
        
        assert stats['total_entries'] == 3
        assert 'static' in stats['by_analyzer']
        assert stats['by_analyzer']['static'] == 2
        assert stats['database_size_bytes'] > 0
    
    def test_clear_cache(self, temp_cache):
        """Test clearing cache."""
        # Add entry
        result = AnalysisResult(filename="test.py", analysis_type=AnalysisType.STATIC)
        content = "def hello():\n    pass"
        temp_cache.store_result("test.py", content, "static", result)
        
        # Verify entry exists
        stats_before = temp_cache.get_cache_stats()
        assert stats_before['total_entries'] > 0
        
        # Clear cache
        temp_cache.clear_cache()
        
        # Verify cache is empty
        stats_after = temp_cache.get_cache_stats()
        assert stats_after['total_entries'] == 0
    
    def test_cleanup_old_entries(self, temp_cache):
        """Test cleaning up old entries."""
        # This test would require mocking timestamps
        # For now, just verify the method doesn't crash
        temp_cache.cleanup_old_entries(days=7)
        
        # Should not raise exception
        assert True
    
    def test_hash_consistency(self, temp_cache):
        """Test that same content produces same hash."""
        content = "def test():\n    return True"
        
        hash1 = temp_cache._calculate_file_hash(content)
        hash2 = temp_cache._calculate_file_hash(content)
        
        assert hash1 == hash2
    
    def test_hash_difference(self, temp_cache):
        """Test that different content produces different hash."""
        content1 = "def test():\n    return True"
        content2 = "def test():\n    return False"
        
        hash1 = temp_cache._calculate_file_hash(content1)
        hash2 = temp_cache._calculate_file_hash(content2)
        
        assert hash1 != hash2