"""
Analysis Engine - Orchestrates the code review process.
"""
from typing import List, Optional, Dict, Any
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from ai_pr_agent.utils import get_logger
from ai_pr_agent.config import get_settings
from .models import (
    PullRequest,
    FileChange,
    AnalysisResult,
    ReviewSummary,
    AnalysisType,
)
from .exceptions import AnalysisError


logger = get_logger(__name__)


class AnalysisEngine:
    """
    Main engine for orchestrating code analysis.
    
    The engine coordinates multiple analysis modules and consolidates
    their results into a comprehensive review summary.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the analysis engine.
        
        Args:
            config: Optional configuration override
        """
        self.settings = get_settings()
        self.config = config or {}
        self.analyzers = []
        
        logger.info("AnalysisEngine initialized")
    
    def register_analyzer(self, analyzer: Any) -> None:
        """
        Register an analyzer module.
        
        Args:
            analyzer: Analyzer instance (must have analyze() method)
        """
        if not hasattr(analyzer, 'analyze'):
            raise ValueError(f"Analyzer {analyzer} must have an 'analyze' method")
        
        self.analyzers.append(analyzer)
        logger.info(f"Registered analyzer: {analyzer.__class__.__name__}")
    
    def analyze_pull_request(
        self, 
        pull_request: PullRequest,
        parallel: bool = False
    ) -> ReviewSummary:
        """
        Analyze a pull request and generate a comprehensive review.
        
        Args:
            pull_request: The pull request to analyze
            parallel: Whether to run analyzers in parallel (default: False)
        
        Returns:
            ReviewSummary with all analysis results
        
        Raises:
            AnalysisError: If the analysis process fails
        """
        logger.info(
            f"Starting analysis of PR #{pull_request.id}: '{pull_request.title}'"
        )
        
        start_time = time.time()
        
        try:
            # Filter files to analyze
            files_to_analyze = self._filter_files(pull_request.files_changed)
            logger.info(f"Analyzing {len(files_to_analyze)} files")
            
            # Run analysis
            if parallel and len(self.analyzers) > 1:
                analysis_results = self._analyze_parallel(files_to_analyze)
            else:
                analysis_results = self._analyze_sequential(files_to_analyze)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Determine overall status
            overall_status = self._determine_status(analysis_results)
            
            # Create summary
            summary = ReviewSummary(
                pull_request=pull_request,
                analysis_results=analysis_results,
                overall_status=overall_status,
                total_execution_time=execution_time
            )
            
            logger.info(
                f"Analysis complete - {len(analysis_results)} files analyzed, "
                f"{summary.total_comments} comments generated, "
                f"status: {overall_status}"
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            raise AnalysisError(
                f"Failed to analyze PR #{pull_request.id}",
                details=str(e)
            )
    
    def _filter_files(self, files: List[FileChange]) -> List[FileChange]:
        """
        Filter files based on configuration rules.
        
        Args:
            files: List of file changes
        
        Returns:
            Filtered list of files to analyze
        """
        filtered = []
        file_filter_config = self.settings.file_filter
        
        for file in files:
            # Skip deleted files
            if file.is_deleted_file:
                logger.debug(f"Skipping deleted file: {file.filename}")
                continue
            
            # Check if file extension is included
            included = any(
                file.filename.endswith(ext) 
                for ext in file_filter_config.included_extensions
            )
            
            if not included:
                logger.debug(
                    f"Skipping file with non-included extension: {file.filename}"
                )
                continue
            
            # Check if file is in ignored directory
            ignored = any(
                ignored_dir in file.filename 
                for ignored_dir in file_filter_config.ignored_directories
            )
            
            if ignored:
                logger.debug(
                    f"Skipping file in ignored directory: {file.filename}"
                )
                continue
            
            # Check if file matches ignored patterns
            ignored_pattern = any(
                self._matches_pattern(file.filename, pattern)
                for pattern in file_filter_config.ignored_files
            )
            
            if ignored_pattern:
                logger.debug(
                    f"Skipping file matching ignored pattern: {file.filename}"
                )
                continue
            
            filtered.append(file)
        
        logger.info(
            f"Filtered {len(files)} files to {len(filtered)} for analysis"
        )
        return filtered
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """
        Check if filename matches a pattern (simple glob-style).
        
        Args:
            filename: Filename to check
            pattern: Pattern to match (supports * wildcard)
        
        Returns:
            True if filename matches pattern
        """
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
    def _analyze_sequential(
        self, 
        files: List[FileChange]
    ) -> List[AnalysisResult]:
        """
        Analyze files sequentially with all registered analyzers.
        
        Args:
            files: Files to analyze
        
        Returns:
            List of analysis results
        """
        results = []
        
        for file in files:
            logger.debug(f"Analyzing file: {file.filename}")
            
            # Collect results from all analyzers for this file
            file_results = []
            
            for analyzer in self.analyzers:
                try:
                    result = self._run_analyzer(analyzer, file)
                    if result:
                        file_results.append(result)
                except Exception as e:
                    logger.error(
                        f"Analyzer {analyzer.__class__.__name__} failed "
                        f"for {file.filename}: {e}"
                    )
                    # Create error result
                    error_result = AnalysisResult(
                        filename=file.filename,
                        success=False,
                        error_message=str(e)
                    )
                    file_results.append(error_result)
            
            # Merge results for this file
            if file_results:
                merged = self._merge_results(file.filename, file_results)
                results.append(merged)
        
        return results
    
    def _analyze_parallel(
        self, 
        files: List[FileChange]
    ) -> List[AnalysisResult]:
        """
        Analyze files in parallel using thread pool.
        
        Args:
            files: Files to analyze
        
        Returns:
            List of analysis results
        """
        results = []
        max_workers = min(4, len(files))  # Limit concurrent workers
        
        logger.debug(f"Using {max_workers} parallel workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all file analysis tasks
            future_to_file = {
                executor.submit(self._analyze_file_with_all, file): file
                for file in files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(
                        f"Parallel analysis failed for {file.filename}: {e}"
                    )
                    results.append(
                        AnalysisResult(
                            filename=file.filename,
                            success=False,
                            error_message=str(e)
                        )
                    )
        
        return results
    
    def _analyze_file_with_all(
        self, 
        file: FileChange
    ) -> Optional[AnalysisResult]:
        """
        Analyze a single file with all registered analyzers.
        
        Args:
            file: File to analyze
        
        Returns:
            Merged analysis result or None
        """
        logger.debug(f"Analyzing file with all analyzers: {file.filename}")
        
        file_results = []
        
        for analyzer in self.analyzers:
            try:
                result = self._run_analyzer(analyzer, file)
                if result:
                    file_results.append(result)
            except Exception as e:
                logger.error(
                    f"Analyzer {analyzer.__class__.__name__} failed: {e}"
                )
                file_results.append(
                    AnalysisResult(
                        filename=file.filename,
                        success=False,
                        error_message=str(e)
                    )
                )
        
        if file_results:
            return self._merge_results(file.filename, file_results)
        
        return None
    
    def _run_analyzer(
        self, 
        analyzer: Any, 
        file: FileChange
    ) -> Optional[AnalysisResult]:
        """
        Run a single analyzer on a file with error handling.
        
        Args:
            analyzer: Analyzer instance
            file: File to analyze
        
        Returns:
            Analysis result or None
        """
        analyzer_name = analyzer.__class__.__name__
        
        try:
            start_time = time.time()
            result = analyzer.analyze(file)
            execution_time = time.time() - start_time
            
            if result:
                result.execution_time = execution_time
                logger.debug(
                    f"{analyzer_name} analyzed {file.filename} "
                    f"in {execution_time:.2f}s"
                )
            
            return result
            
        except Exception as e:
            logger.error(
                f"{analyzer_name} failed for {file.filename}: {e}",
                exc_info=True
            )
            raise
    
    def _merge_results(
        self, 
        filename: str, 
        results: List[AnalysisResult]
    ) -> AnalysisResult:
        """
        Merge multiple analysis results for the same file.
        
        Args:
            filename: Filename being analyzed
            results: List of results to merge
        
        Returns:
            Merged analysis result
        """
        merged = AnalysisResult(filename=filename)
        
        for result in results:
            # Combine comments
            merged.comments.extend(result.comments)
            
            # Combine metadata
            merged.metadata.update(result.metadata)
            
            # Sum execution times
            merged.execution_time += result.execution_time
            
            # If any analyzer failed, mark as failed
            if not result.success:
                merged.success = False
                if result.error_message:
                    if merged.error_message:
                        merged.error_message += f"; {result.error_message}"
                    else:
                        merged.error_message = result.error_message
        
        logger.debug(
            f"Merged {len(results)} results for {filename}: "
            f"{len(merged.comments)} total comments"
        )
        
        return merged
    
    def _determine_status(
        self, 
        results: List[AnalysisResult]
    ) -> str:
        """
        Determine overall analysis status based on results.
        
        Args:
            results: List of analysis results
        
        Returns:
            Status string: "success", "partial_failure", or "failure"
        """
        if not results:
            return "failure"
        
        failed_count = sum(1 for r in results if not r.success)
        error_count = sum(r.error_count for r in results)
        
        if failed_count == len(results):
            return "failure"
        elif failed_count > 0 or error_count > 0:
            return "partial_failure"
        else:
            return "success"
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about registered analyzers.
        
        Returns:
            Dictionary with analyzer statistics
        """
        return {
            "total_analyzers": len(self.analyzers),
            "analyzer_types": [
                analyzer.__class__.__name__ 
                for analyzer in self.analyzers
            ],
        }