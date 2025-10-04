"""
Mock analyzer for testing purposes.
"""
from typing import Optional
import time

from ai_pr_agent.utils import get_logger
from ai_pr_agent.core.models import (
    FileChange,
    AnalysisResult,
    AnalysisType,
    SeverityLevel,
)
from .base import BaseAnalyzer


logger = get_logger(__name__)


class MockAnalyzer(BaseAnalyzer):
    """
    Mock analyzer that generates fake results for testing.
    """
    
    def __init__(self, name: str = "MockAnalyzer", delay: float = 0.0):
        """
        Initialize mock analyzer.
        
        Args:
            name: Name for this analyzer instance
            delay: Artificial delay in seconds (for testing)
        """
        self.name = name
        self.delay = delay
        logger.info(f"Initialized {name}")
    
    def analyze(self, file_change: FileChange) -> Optional[AnalysisResult]:
        """
        Perform mock analysis.
        
        Args:
            file_change: File to analyze
        
        Returns:
            Mock analysis result
        """
        logger.debug(f"{self.name} analyzing {file_change.filename}")
        
        # Simulate processing time
        if self.delay > 0:
            time.sleep(self.delay)
        
        # Create result
        result = AnalysisResult(
            filename=file_change.filename,
            analysis_type=AnalysisType.STATIC
        )
        
        # Add some mock comments based on file properties
        if file_change.additions > 50:
            result.add_comment(
                body=f"Large file change: {file_change.additions} lines added",
                severity=SeverityLevel.WARNING
            )
        
        if file_change.language == "python":
            result.add_comment(
                body="Python file detected - consider adding type hints",
                severity=SeverityLevel.SUGGESTION,
                line=1
            )
        
        logger.debug(
            f"{self.name} generated {len(result.comments)} comments "
            f"for {file_change.filename}"
        )
        
        return result


class FailingAnalyzer(BaseAnalyzer):
    """
    Analyzer that always fails (for testing error handling).
    """
    
    def analyze(self, file_change: FileChange) -> Optional[AnalysisResult]:
        """
        Always raises an exception.
        
        Args:
            file_change: File to analyze
        
        Raises:
            RuntimeError: Always
        """
        raise RuntimeError(f"FailingAnalyzer intentionally failed for {file_change.filename}")