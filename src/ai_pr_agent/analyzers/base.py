"""
Base analyzer interface.
"""
from abc import ABC, abstractmethod
from typing import Optional

from ai_pr_agent.core.models import FileChange, AnalysisResult


class BaseAnalyzer(ABC):
    """
    Base class for all analyzers.
    
    All analyzer modules must inherit from this class and
    implement the analyze() method.
    """
    
    @abstractmethod
    def analyze(self, file_change: FileChange) -> Optional[AnalysisResult]:
        """
        Analyze a file change and return results.
        
        Args:
            file_change: The file change to analyze
        
        Returns:
            AnalysisResult with findings, or None if file should be skipped
        """
        pass
    
    def can_analyze(self, file_change: FileChange) -> bool:
        """
        Check if this analyzer can analyze the given file.
        
        Args:
            file_change: File to check
        
        Returns:
            True if analyzer supports this file type
        """
        return True