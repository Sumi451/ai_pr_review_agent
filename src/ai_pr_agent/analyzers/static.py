"""
Static code analysis module using flake8, bandit, and mypy.
"""
import subprocess
import tempfile
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

from ai_pr_agent.cache import CacheManager
from ai_pr_agent.utils import get_logger
from ai_pr_agent.config import get_settings
from ai_pr_agent.core.models import (
    FileChange,
    AnalysisResult,
    AnalysisType,
    SeverityLevel,
)
from .base import BaseAnalyzer


logger = get_logger(__name__)


class StaticAnalyzer(BaseAnalyzer):
    """
    Static code analysis using flake8, bandit, and mypy.
    
    This analyzer runs multiple static analysis tools on Python files
    and consolidates their findings into structured comments.
    """
    
    def __init__(self):
        """Initialize the static analyzer."""
        self.settings = get_settings()
        self.config = self.settings.analysis.static_analysis
        self.cache = CacheManager() if self.settings.cache.enabled else None
        logger.info("StaticAnalyzer initialized")
    
    def can_analyze(self, file_change: FileChange) -> bool:
        """
        Check if this analyzer can analyze the given file.
        
        Args:
            file_change: File to check
        
        Returns:
            True if file is a Python file
        """
        return file_change.language == "python"
    
    def analyze(self, file_change: FileChange) -> Optional[AnalysisResult]:
        """
        Analyze a Python file with static analysis tools.
        
        Args:
            file_change: The file change to analyze
        
        Returns:
            AnalysisResult with findings
        """
        
        if not self.can_analyze(file_change):
            logger.debug("Skipping non-Python file: %s", file_change.filename)
            return None
        
        if not self.config.enabled:
            logger.debug("Static analysis is disabled in config")
            return None
        
        logger.info(f"Running static analysis on {file_change.filename}")
        
         # Create new result
        result = AnalysisResult(
            filename=file_change.filename,
            analysis_type=AnalysisType.STATIC
        )
        # Extract code from patch
        if not file_change.patch:
            logger.warning(f"No patch available for {file_change.filename}, skipping")
            return result
        
        code_content = self._extract_code_from_patch(file_change.patch)
        
        if not code_content:
            logger.debug(f"No code content extracted from {file_change.filename}")
            return None
        
        # Check cache first
        if self.cache:
            cached_result = self.cache.get_cached_result(
                filename=file_change.filename,
                content=code_content,
                analyzer_type='static'
            )
            if cached_result:
                logger.info(f"Using cached result for {file_change.filename}")
                return cached_result
        
       
        
        try:
            # Run analysis tools
            if "flake8" in self.config.tools:
                self._run_flake8(code_content, result)
            
            if "bandit" in self.config.tools:
                self._run_bandit(code_content, result)
            
            if "mypy" in self.config.tools:
                self._run_mypy(code_content, result)
            
            logger.info(
                f"Static analysis complete for {file_change.filename}: "
                f"{len(result.comments)} issues found"
            )
            
            # Store in cache
            if self.cache:
                self.cache.store_result(
                    filename=file_change.filename,
                    content=code_content,
                    analyzer_type='static',
                    result=result
                )
            
        except Exception as e:
            logger.error(f"Static analysis failed for {file_change.filename}: {e}")
            result.success = False
            result.error_message = str(e)
        
        return result
    
    def _extract_code_from_patch(self, patch: str) -> str:
        """
        Extract code lines from a git patch.
        
        Args:
            patch: Git diff patch
        
        Returns:
            Extracted code content
        """
        lines = []
        for line in patch.split('\n'):
            # Skip patch metadata lines
            if line.startswith('@@') or line.startswith('---') or line.startswith('+++'):
                continue
            # Keep added and context lines
            if line.startswith('+'):
                lines.append(line[1:])  # Remove the '+' prefix
            elif not line.startswith('-'):
                lines.append(line)
        
        return '\n'.join(lines)
    
    def _run_flake8(self, code: str, result: AnalysisResult) -> None:
        """
        Run flake8 on code and add findings to result.
        
        Args:
            code: Python code to analyze
            result: AnalysisResult to add findings to
        """
        logger.debug("Running flake8...")
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                encoding='utf-8'
            ) as tmp_file:
                tmp_file.write(code)
                tmp_path = tmp_file.name
            
            try:
                # Build flake8 command
                cmd = ['flake8', tmp_path]
                
                # Add configuration options
                if self.config.flake8.get('max_line_length'):
                    cmd.extend(['--max-line-length', str(self.config.flake8['max_line_length'])])
                
                if self.config.flake8.get('ignore_errors'):
                    ignore_str = ','.join(self.config.flake8['ignore_errors'])
                    cmd.extend(['--ignore', ignore_str])
                
                # Run flake8
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Parse output
                if process.stdout:
                    self._parse_flake8_output(process.stdout, result)
                
            finally:
                # Clean up temp file
                Path(tmp_path).unlink(missing_ok=True)
                
        except subprocess.TimeoutExpired:
            logger.error("flake8 execution timed out")
        except Exception as e:
            logger.error(f"flake8 execution failed: {e}")
    
    def _parse_flake8_output(self, output: str, result: AnalysisResult) -> None:
        """
        Parse flake8 output and create comments.
        
        Args:
            output: flake8 output text
            result: AnalysisResult to add comments to
        """
        # flake8 output format: filename:line:column: code message
        pattern = r'.*?:(\d+):(\d+):\s+([A-Z]\d+)\s+(.+)'
        
        for line in output.split('\n'):
            match = re.match(pattern, line)
            if match:
                line_num = int(match.group(1))
                code = match.group(3)
                message = match.group(4)
                
                # Determine severity based on error code
                severity = self._get_flake8_severity(code)
                
                result.add_comment(
                    body=f"[flake8 {code}] {message}",
                    line=line_num,
                    severity=severity
                )
    
    def _get_flake8_severity(self, code: str) -> SeverityLevel:
        """
        Determine severity level from flake8 error code.
        
        Args:
            code: flake8 error code (e.g., E501, W503)
        
        Returns:
            Appropriate severity level
        """
        # E: Error, W: Warning, C: Complexity, F: Fatal
        if code.startswith('E'):
            return SeverityLevel.ERROR
        elif code.startswith('W'):
            return SeverityLevel.WARNING
        elif code.startswith('C'):
            return SeverityLevel.WARNING
        elif code.startswith('F'):
            return SeverityLevel.ERROR
        else:
            return SeverityLevel.INFO
    
    def _run_bandit(self, code: str, result: AnalysisResult) -> None:
        """
        Run bandit security scanner on code.
        
        Args:
            code: Python code to analyze
            result: AnalysisResult to add findings to
        """
        logger.debug("Running bandit...")
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                encoding='utf-8'
            ) as tmp_file:
                tmp_file.write(code)
                tmp_path = tmp_file.name
            
            try:
                # Build bandit command
                cmd = ['bandit', '-f', 'json', tmp_path]
                
                # Add skip tests if configured
                if self.config.bandit.get('skip_tests'):
                    skip_str = ','.join(self.config.bandit['skip_tests'])
                    cmd.extend(['-s', skip_str])
                
                # Run bandit
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Parse JSON output
                if process.stdout:
                    self._parse_bandit_output(process.stdout, result)
                
            finally:
                # Clean up temp file
                Path(tmp_path).unlink(missing_ok=True)
                
        except subprocess.TimeoutExpired:
            logger.error("bandit execution timed out")
        except Exception as e:
            logger.error(f"bandit execution failed: {e}")
    
    def _parse_bandit_output(self, output: str, result: AnalysisResult) -> None:
        """
        Parse bandit JSON output and create comments.
        
        Args:
            output: bandit JSON output
            result: AnalysisResult to add comments to
        """
        try:
            data = json.loads(output)
            
            for issue in data.get('results', []):
                line_num = issue.get('line_number')
                issue_text = issue.get('issue_text', '')
                issue_severity = issue.get('issue_severity', 'MEDIUM')
                test_id = issue.get('test_id', '')
                
                # Map bandit severity to our severity
                severity = self._get_bandit_severity(issue_severity)
                
                result.add_comment(
                    body=f"[bandit {test_id}] {issue_text}",
                    line=line_num,
                    severity=severity
                )
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse bandit JSON output: {e}")
    
    def _get_bandit_severity(self, bandit_severity: str) -> SeverityLevel:
        """
        Map bandit severity to our severity level.
        
        Args:
            bandit_severity: Bandit severity (LOW, MEDIUM, HIGH)
        
        Returns:
            Appropriate severity level
        """
        severity_map = {
            'LOW': SeverityLevel.INFO,
            'MEDIUM': SeverityLevel.WARNING,
            'HIGH': SeverityLevel.ERROR,
        }
        return severity_map.get(bandit_severity.upper(), SeverityLevel.WARNING)
    
    def _run_mypy(self, code: str, result: AnalysisResult) -> None:
        """
        Run mypy type checker on code.
        
        Args:
            code: Python code to analyze
            result: AnalysisResult to add findings to
        """
        logger.debug("Running mypy...")
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                encoding='utf-8'
            ) as tmp_file:
                tmp_file.write(code)
                tmp_path = tmp_file.name
            
            try:
                # Build mypy command
                cmd = ['mypy', tmp_path]
                
                # Add configuration options
                if not self.config.mypy.get('strict'):
                    cmd.append('--no-strict')
                
                if self.config.mypy.get('ignore_missing_imports'):
                    cmd.append('--ignore-missing-imports')
                
                # Run mypy
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Parse output
                if process.stdout:
                    self._parse_mypy_output(process.stdout, result)
                
            finally:
                # Clean up temp file
                Path(tmp_path).unlink(missing_ok=True)
                
        except subprocess.TimeoutExpired:
            logger.error("mypy execution timed out")
        except Exception as e:
            logger.error(f"mypy execution failed: {e}")
    
    def _parse_mypy_output(self, output: str, result: AnalysisResult) -> None:
        """
        Parse mypy output and create comments.
        
        Args:
            output: mypy output text
            result: AnalysisResult to add comments to
        """
        # mypy output format: filename:line: error: message
        pattern = r'.*?:(\d+):\s+(error|warning|note):\s+(.+)'
        
        for line in output.split('\n'):
            match = re.match(pattern, line)
            if match:
                line_num = int(match.group(1))
                level = match.group(2)
                message = match.group(3)
                
                # Map mypy level to severity
                severity_map = {
                    'error': SeverityLevel.ERROR,
                    'warning': SeverityLevel.WARNING,
                    'note': SeverityLevel.INFO,
                }
                severity = severity_map.get(level, SeverityLevel.INFO)
                
                result.add_comment(
                    body=f"[mypy] {message}",
                    line=line_num,
                    severity=severity
                )