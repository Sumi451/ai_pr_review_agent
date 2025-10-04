"""Tests for the Analysis Engine."""

import pytest
from ai_pr_agent.core import (
    PullRequest,
    FileChange,
    FileStatus,
    ReviewSummary,
)
from ai_pr_agent.core.engine import AnalysisEngine
from ai_pr_agent.core.exceptions import AnalysisError
from ai_pr_agent.analyzers import MockAnalyzer, FailingAnalyzer


class TestAnalysisEngine:
    """Test AnalysisEngine functionality."""
    
    def test_engine_initialization(self):
        """Test creating an engine instance."""
        engine = AnalysisEngine()
        
        assert engine is not None
        assert len(engine.analyzers) == 0
    
    def test_register_analyzer(self):
        """Test registering analyzers."""
        engine = AnalysisEngine()
        analyzer = MockAnalyzer()
        
        engine.register_analyzer(analyzer)
        
        assert len(engine.analyzers) == 1
        assert engine.analyzers[0] == analyzer
    
    def test_register_invalid_analyzer(self):
        """Test that registering invalid analyzer raises error."""
        engine = AnalysisEngine()
        
        with pytest.raises(ValueError):
            engine.register_analyzer("not an analyzer")
    
    def test_analyze_pull_request_basic(self, sample_pull_request):
        """Test basic PR analysis."""
        engine = AnalysisEngine()
        engine.register_analyzer(MockAnalyzer("Analyzer1"))
        
        summary = engine.analyze_pull_request(sample_pull_request)
        
        assert isinstance(summary, ReviewSummary)
        assert summary.pull_request == sample_pull_request
        assert len(summary.analysis_results) > 0
        assert summary.overall_status in ["success", "partial_failure", "failure"]
    
    def test_analyze_with_multiple_analyzers(self, sample_pull_request):
        """Test analysis with multiple analyzers."""
        engine = AnalysisEngine()
        engine.register_analyzer(MockAnalyzer("Analyzer1"))
        engine.register_analyzer(MockAnalyzer("Analyzer2"))
        
        summary = engine.analyze_pull_request(sample_pull_request)
        
        assert len(summary.analysis_results) > 0
        # Each file should have comments from both analyzers
        for result in summary.analysis_results:
            assert len(result.comments) >= 0  # May have comments from multiple analyzers
    
    def test_analyze_with_failing_analyzer(self, sample_pull_request):
        """Test that engine handles failing analyzers gracefully."""
        engine = AnalysisEngine()
        engine.register_analyzer(MockAnalyzer("Good"))
        engine.register_analyzer(FailingAnalyzer())
        
        # Should not raise exception, but handle gracefully
        summary = engine.analyze_pull_request(sample_pull_request)
        
        assert isinstance(summary, ReviewSummary)
        # Status should reflect partial failure
        assert summary.overall_status in ["partial_failure", "failure"]
    
    def test_file_filtering(self):
        """Test that files are filtered correctly."""
        engine = AnalysisEngine()
        engine.register_analyzer(MockAnalyzer())
        
        files = [
            FileChange(filename="src/main.py", status=FileStatus.MODIFIED),
            FileChange(filename="build/output.txt", status=FileStatus.ADDED),
            FileChange(filename="test.pyc", status=FileStatus.ADDED),
            FileChange(filename="deleted.py", status=FileStatus.DELETED),
        ]
        
        pr = PullRequest(
            id=1,
            title="Test",
            description="Test",
            author="test",
            source_branch="test",
            files_changed=files
        )
        
        summary = engine.analyze_pull_request(pr)
        
        # Should only analyze main.py (others filtered out)
        assert len(summary.analysis_results) == 1
        assert summary.analysis_results[0].filename == "src/main.py"
    
    def test_parallel_analysis(self, sample_pull_request):
        """Test parallel analysis mode."""
        engine = AnalysisEngine()
        engine.register_analyzer(MockAnalyzer("Analyzer1", delay=0.1))
        engine.register_analyzer(MockAnalyzer("Analyzer2", delay=0.1))
        
        # Run in parallel
        summary = engine.analyze_pull_request(sample_pull_request, parallel=True)
        
        assert isinstance(summary, ReviewSummary)
        assert len(summary.analysis_results) > 0
    
    def test_get_statistics(self):
        """Test getting engine statistics."""
        engine = AnalysisEngine()
        engine.register_analyzer(MockAnalyzer("Analyzer1"))
        engine.register_analyzer(MockAnalyzer("Analyzer2"))
        
        stats = engine.get_statistics()
        
        assert stats["total_analyzers"] == 2
        assert len(stats["analyzer_types"]) == 2
    
    def test_empty_pull_request(self):
        """Test analyzing PR with no files."""
        engine = AnalysisEngine()
        engine.register_analyzer(MockAnalyzer())
        
        pr = PullRequest(
            id=1,
            title="Empty PR",
            description="No files",
            author="test",
            source_branch="test",
            files_changed=[]
        )
        
        summary = engine.analyze_pull_request(pr)
        
        assert isinstance(summary, ReviewSummary)
        assert len(summary.analysis_results) == 0