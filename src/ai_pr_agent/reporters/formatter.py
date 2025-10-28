from typing import List, Dict, Any, Optional
from datetime import datetime

from ai_pr_agent.core.models import (
    ReviewSummary,
    AnalysisResult,
    Comment,
    SeverityLevel,
)


class MarkdownFormatter:
    """Format review content as GitHub-flavored Markdown."""
    
    # Symbol mapping for severity levels (cleaner, professional look)
    SEVERITY_EMOJI = {
        SeverityLevel.ERROR: "✗",
        SeverityLevel.WARNING: "!",
        SeverityLevel.INFO: "i",
        SeverityLevel.SUGGESTION: "→",
    }
    
    # Severity labels for GitHub markdown
    SEVERITY_LABELS = {
        SeverityLevel.ERROR: "[ERROR]",
        SeverityLevel.WARNING: "[WARNING]",
        SeverityLevel.INFO: "[INFO]",
        SeverityLevel.SUGGESTION: "[SUGGESTION]",
    }
    
    def format_comment(self, comment: Comment) -> str:
        """
        Format a single comment.
        
        Args:
            comment: Comment to format
        
        Returns:
            Formatted markdown string
        """
        parts = []
        
        # Severity indicator
        emoji = self.SEVERITY_EMOJI.get(comment.severity, "•")
        label = self.SEVERITY_LABELS.get(comment.severity, "NOTE")
        
        parts.append(f"{emoji} {label}")
        parts.append("")
        
        # Main comment body
        parts.append(comment.body)
        
        # Add suggestion if present
        if comment.suggestion:
            parts.append("")
            parts.append("**Suggestion:**")
            parts.append("```python")
            parts.append(comment.suggestion)
            parts.append("```")
        
        # Analysis type footer
        if comment.analysis_type:
            parts.append("")
            parts.append(f"*— {comment.analysis_type.value} analysis*")
        
        return "\n".join(parts)
    
    def format_review_summary(self, summary: ReviewSummary) -> str:
        """
        Format complete review summary.
        
        Args:
            summary: Review summary to format
        
        Returns:
            Formatted markdown string
        """
        lines = []
        
        # Header
        lines.append("## Code Review Report")
        lines.append("")
        
        # Status badge
        status_symbol = "✓" if summary.overall_status == "success" else "✗"
        lines.append(f"**Status:** {status_symbol} {summary.overall_status.replace('_', ' ').title()}")
        lines.append("")
        
        # Summary statistics
        lines.append("### Summary")
        lines.append("")
        lines.append(f"- **Files Analyzed:** {len(summary.analysis_results)}")
        lines.append(f"- **Total Comments:** {summary.total_comments}")
        lines.append(f"- **Errors:** {summary.total_errors}")
        lines.append(f"- **Warnings:** {summary.total_warnings}")
        lines.append(f"- **Execution Time:** {summary.total_execution_time:.2f}s")
        lines.append("")
        
        # Files with issues
        if summary.files_with_issues:
            lines.append("### Files with Issues")
            lines.append("")
            for filepath in summary.files_with_issues[:10]:
                result = next(
                    (r for r in summary.analysis_results if r.filename == filepath),
                    None
                )
                if result:
                    lines.append(
                        f"- `{filepath}` - "
                        f"{result.error_count} errors, "
                        f"{result.warning_count} warnings"
                    )
            
            if len(summary.files_with_issues) > 10:
                lines.append(f"- *... and {len(summary.files_with_issues) - 10} more files*")
            lines.append("")
        
        # Breakdown by severity
        lines.append("### Issue Breakdown")
        lines.append("")
        
        for severity in [SeverityLevel.ERROR, SeverityLevel.WARNING, 
                         SeverityLevel.INFO, SeverityLevel.SUGGESTION]:
            count = len(summary.get_comments_by_severity(severity))
            if count > 0:
                symbol = self.SEVERITY_EMOJI[severity]
                lines.append(f"- {symbol} **{severity.value.upper()}**: {count}")
        
        lines.append("")
        
        # Footer
        lines.append("---")
        lines.append("*Inline comments have been posted on relevant lines.*")
        lines.append(f"*Generated at {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC*")
        
        return "\n".join(lines)
    
    def format_summary_comment(self, summary: ReviewSummary) -> str:
        """
        Format a summary comment (shorter version).
        
        Args:
            summary: Review summary
        
        Returns:
            Formatted markdown string
        """
        lines = []
        
        # Header
        lines.append("## 🤖 Code Review Summary")
        lines.append("")
        
        # Quick stats
        status_emoji = "✅" if summary.overall_status == "success" else "⚠️"
        lines.append(f"{status_emoji} **Analysis Complete**")
        lines.append("")
        
        # Key metrics in table
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Files | {len(summary.analysis_results)} |")
        lines.append(f"| Comments | {summary.total_comments} |")
        lines.append(f"| Errors | {summary.total_errors} |")
        lines.append(f"| Warnings | {summary.total_warnings} |")
        lines.append("")
        
        # Quick recommendations
        if summary.total_errors > 0:
            lines.append("⚠️ **Action Required:** Please address the errors before merging.")
        elif summary.total_warnings > 0:
            lines.append("💡 **Suggestions Available:** Consider reviewing the warnings.")
        else:
            lines.append("✨ **Looks Good:** No issues found!")
        
        return "\n".join(lines)
    
    def format_file_summary(self, result: AnalysisResult) -> str:
        """
        Format summary for a single file.
        
        Args:
            result: Analysis result for file
        
        Returns:
            Formatted markdown string
        """
        lines = []
        
        # File header
        lines.append(f"### 📄 `{result.filename}`")
        lines.append("")
        
        # Stats
        lines.append(f"- **Comments:** {len(result.comments)}")
        lines.append(f"- **Errors:** {result.error_count}")
        lines.append(f"- **Warnings:** {result.warning_count}")
        lines.append(f"- **Time:** {result.execution_time:.2f}s")
        lines.append("")
        
        # Issues by severity
        if result.comments:
            lines.append("**Issues:**")
            lines.append("")
            
            for severity in [SeverityLevel.ERROR, SeverityLevel.WARNING]:
                comments = result.get_comments_by_severity(severity)
                if comments:
                    emoji = self.SEVERITY_EMOJI[severity]
                    lines.append(f"{emoji} **{severity.value.upper()}**")
                    for comment in comments[:5]:
                        location = f"L{comment.line}" if comment.line else "File"
                        lines.append(f"- [{location}] {comment.body[:80]}...")
                    
                    if len(comments) > 5:
                        lines.append(f"- *... and {len(comments) - 5} more*")
                    lines.append("")
        
        return "\n".join(lines)
    
    def format_comparison(
        self,
        old_summary: ReviewSummary,
        new_summary: ReviewSummary
    ) -> str:
        """
        Format a comparison between two reviews.
        
        Args:
            old_summary: Previous review summary
            new_summary: Current review summary
        
        Returns:
            Formatted markdown string
        """
        lines = []
        
        lines.append("## 📊 Review Comparison")
        lines.append("")
        
        # Calculate changes
        error_change = new_summary.total_errors - old_summary.total_errors
        warning_change = new_summary.total_warnings - old_summary.total_warnings
        
        # Format changes
        def format_change(value: int) -> str:
            if value > 0:
                return f"🔴 +{value}"
            elif value < 0:
                return f"🟢 {value}"
            else:
                return "➖ 0"
        
        lines.append("| Metric | Previous | Current | Change |")
        lines.append("|--------|----------|---------|--------|")
        lines.append(
            f"| Errors | {old_summary.total_errors} | "
            f"{new_summary.total_errors} | {format_change(error_change)} |"
        )
        lines.append(
            f"| Warnings | {old_summary.total_warnings} | "
            f"{new_summary.total_warnings} | {format_change(warning_change)} |"
        )
        lines.append("")
        
        # Overall assessment
        if error_change < 0 and warning_change <= 0:
            lines.append("✅ **Improvement!** Issues have been reduced.")
        elif error_change > 0 or warning_change > 0:
            lines.append("⚠️ **New Issues:** More issues found than before.")
        else:
            lines.append("➖ **No Change:** Same number of issues.")
        
        return "\n".join(lines)
    
    def format_code_block(
        self,
        code: str,
        language: str = "python",
        title: Optional[str] = None
    ) -> str:
        """
        Format code block with optional title.
        
        Args:
            code: Code content
            language: Programming language
            title: Optional title
        
        Returns:
            Formatted code block
        """
        lines = []
        
        if title:
            lines.append(f"**{title}**")
            lines.append("")
        
        lines.append(f"```{language}")
        lines.append(code)
        lines.append("```")
        
        return "\n".join(lines)
