"""
Cache manager for storing and retrieving analysis results.
"""
import sqlite3
import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ai_pr_agent.utils import get_logger
from ai_pr_agent.config import get_settings
from ai_pr_agent.core.models import AnalysisResult

logger = get_logger(__name__)


class CacheManager:
    """Manages caching of analysis results in SQLite."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize cache manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            settings = get_settings()
            # Use .cache directory in project root
            cache_dir = Path('.cache')
            cache_dir.mkdir(exist_ok=True)
            db_path = str(cache_dir / 'analysis_cache.db')
        
        self.db_path = db_path
        self.settings = get_settings()
        self.conn=None
        self._init_database()
        logger.info(f"Cache manager initialized with database: {db_path}")

    
    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_hash TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    analyzer_type TEXT NOT NULL,
                    result_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(file_hash, analyzer_type)
                )
            """)
            
            # Create index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_hash 
                ON analysis_cache(file_hash, analyzer_type)
            """)
            
            # Create index for cleanup queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_accessed_at 
                ON analysis_cache(accessed_at)
            """)
            
            conn.commit()
            logger.debug("Database schema initialized")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def _calculate_file_hash(self, content: str) -> str:
        """
        Calculate hash of file content.
        
        Args:
            content: File content
        
        Returns:
            SHA256 hash of content
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get_cached_result(
        self, 
        filename: str, 
        content: str, 
        analyzer_type: str
    ) -> Optional[AnalysisResult]:
        """
        Get cached analysis result if available.
        
        Args:
            filename: Name of the file
            content: File content (used for hash)
            analyzer_type: Type of analyzer
        
        Returns:
            Cached AnalysisResult or None if not found/expired
        """
        if not self.settings.cache.enabled:
            return None
        
        file_hash = self._calculate_file_hash(content)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT result_data, created_at 
                    FROM analysis_cache 
                    WHERE file_hash = ? AND analyzer_type = ?
                    """,
                    (file_hash, analyzer_type)
                )
                
                row = cursor.fetchone()
                
                if row is None:
                    logger.debug(f"Cache miss for {filename} ({analyzer_type})")
                    return None
                
                # Check if cache entry is expired
                created_at = datetime.fromisoformat(row['created_at'])
                ttl = timedelta(hours=self.settings.cache.ttl_hours)
                
                if datetime.now() - created_at > ttl:
                    logger.debug(f"Cache expired for {filename} ({analyzer_type})")
                    # Delete expired entry
                    conn.execute(
                        "DELETE FROM analysis_cache WHERE file_hash = ? AND analyzer_type = ?",
                        (file_hash, analyzer_type)
                    )
                    conn.commit()
                    return None
                
                # Update accessed_at
                conn.execute(
                    "UPDATE analysis_cache SET accessed_at = CURRENT_TIMESTAMP WHERE file_hash = ? AND analyzer_type = ?",
                    (file_hash, analyzer_type)
                )
                conn.commit()
                
                # Deserialize result
                result_dict = json.loads(row['result_data'])
                result = self._dict_to_analysis_result(result_dict)
                
                logger.info(f"Cache hit for {filename} ({analyzer_type})")
                return result
                
        except Exception as e:
            logger.error(f"Error retrieving cached result: {e}")
            return None
    
    def store_result(
        self, 
        filename: str, 
        content: str, 
        analyzer_type: str, 
        result: AnalysisResult
    ):
        """
        Store analysis result in cache.
        
        Args:
            filename: Name of the file
            content: File content (used for hash)
            analyzer_type: Type of analyzer
            result: Analysis result to store
        """
        if not self.settings.cache.enabled:
            return
        
        file_hash = self._calculate_file_hash(content)
        
        try:
            # Serialize result
            result_dict = result.to_dict()
            result_json = json.dumps(result_dict)
            
            with sqlite3.connect(self.db_path) as conn:
                # Use INSERT OR REPLACE to handle duplicates
                conn.execute(
                    """
                    INSERT OR REPLACE INTO analysis_cache 
                    (file_hash, filename, analyzer_type, result_data, created_at, accessed_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (file_hash, filename, analyzer_type, result_json)
                )
                conn.commit()
                
            logger.debug(f"Stored result in cache for {filename} ({analyzer_type})")
            
        except Exception as e:
            logger.error(f"Error storing result in cache: {e}")
    
    def _dict_to_analysis_result(self, data: Dict[str, Any]) -> AnalysisResult:
        """
        Convert dictionary to AnalysisResult object.
        
        Args:
            data: Dictionary representation of AnalysisResult
        
        Returns:
            AnalysisResult object
        """
        from ai_pr_agent.core.models import Comment, SeverityLevel, AnalysisType
        
        # Reconstruct comments
        comments = []
        for comment_dict in data.get('comments', []):
            comment = Comment(
                body=comment_dict['body'],
                line=comment_dict.get('line'),
                severity=SeverityLevel(comment_dict['severity']),
                path=comment_dict.get('path'),
                suggestion=comment_dict.get('suggestion'),
                analysis_type=AnalysisType(comment_dict['analysis_type']) if comment_dict.get('analysis_type') else None
            )
            comments.append(comment)
        
        # Create AnalysisResult
        result = AnalysisResult(
            filename=data['filename'],
            comments=comments,
            metadata=data.get('metadata', {}),
            analysis_type=AnalysisType(data['analysis_type']) if data.get('analysis_type') else None,
            execution_time=data.get('execution_time', 0.0),
            success=data.get('success', True),
            error_message=data.get('error_message')
        )
        
        return result
    
    def cleanup_old_entries(self, days: int = 7):
        """
        Remove cache entries older than specified days.
        
        Args:
            days: Number of days to keep entries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                
                cursor = conn.execute(
                    "DELETE FROM analysis_cache WHERE accessed_at < ?",
                    (cutoff_date.isoformat(),)
                )
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old cache entries")
                
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
    
    def clear_cache(self):
        """Clear all cache entries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM analysis_cache")
                conn.commit()
                logger.info("Cache cleared")
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total entries
                cursor = conn.execute("SELECT COUNT(*) FROM analysis_cache")
                total_entries = cursor.fetchone()[0]
                
                # Entries by analyzer type
                cursor = conn.execute(
                    """
                    SELECT analyzer_type, COUNT(*) as count 
                    FROM analysis_cache 
                    GROUP BY analyzer_type
                    """
                )
                by_analyzer = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Database size
                db_size = Path(self.db_path).stat().st_size
                
                return {
                    'total_entries': total_entries,
                    'by_analyzer': by_analyzer,
                    'database_size_bytes': db_size,
                    'database_size_mb': round(db_size / (1024 * 1024), 2),
                }
                
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}