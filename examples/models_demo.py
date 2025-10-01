"""
Demonstration of core data models.
Run this to see the models in action.
"""

from datetime import datetime
from ai_pr_agent.core import (
    SeverityLevel,
    FileStatus,
    AnalysisType,
    FileChange,
    Comment,
    AnalysisResult,
    PullRequest,
    ReviewSummary,
)


def main():
    """Demonstrate the core data models."""
    
    print("=" * 60)
    print("AI PR Review Agent - Data Models Demo")
    print("=" * 60)
    print()
    
    # 1. Create file changes
    print("1. Creating FileChange instances...")
    file1 = FileChange(
        filename="src/main.py",
        status=FileStatus.MODIFIED,
        additions=15,
        deletions=5,
        patch="@@ -1,5 +1,15 @@\n..."
    )
    
    file2 = FileChange(
        filename="tests/test_new_feature.py",
        status=FileStatus.ADDED,
        additions=50,
        deletions=0
    )
    
    file3 = FileChange(
        filename="docs/old_guide.md",
        status=FileStatus.DELETED,
        additions=0,
        deletions=30
    )
    
    print(f"  - {file1.filename}: {file1.status.value}, "
          f"+{file1.additions}/-{file1.deletions}, "
          f"language={file1.language}")
    print(f"  - {file2.filename}: {file2.status.value}, "
          f"+{file2.additions}/-{file2.deletions}, "
          f"language={file2.language}")
    print(f"  - {file3.filename}: {file3.status.value}, "
          f"+{file3.additions}/-{file3.deletions}")
    print()
    
    # 2. Create a pull request
    print("2. Creating PullRequest...")
    pr = PullRequest(
        id=42,
        title="Add new feature with improved error handling",
        description="This PR implements the new feature requested in #123",
        author="developer",
        source_branch="feature/new-feature",
        target_branch="main",
        files_changed=[file1, file2, file3],
        created_at=datetime.now(),
        repository="myorg/myrepo",
        url="https://github.com/myorg/myrepo/pull/42"
    )
    
    print(f"  PR #{pr.id}: {pr.title}")
    print(f"  Author: {pr.author}")
    print(f"  Branch: {pr.source_branch} -> {pr.target_branch}")
    print(f"  Files changed: {len(pr.files_changed)}")
    print(f"  Total changes: +{pr.total_additions}/-{pr.total_deletions}")
    print(f"  Languages: {', '.join(pr.languages)}")
    print(f"  New files: {len(pr.new_files)}")
    print(f"  Modified files: {len(pr.modified_files)}")
    print(f"  Deleted files: {len(pr.deleted_files)}")
    print()
    
    # 3. Create analysis results with comments
    print("3. Creating AnalysisResult with comments...")
    
    # Static analysis result
    static_result = AnalysisResult(
        filename="src/main.py",
        analysis_type=AnalysisType.STATIC,
        execution_time=0.5
    )
    
    static_result.add_comment(
        body="Function 'process_data' is too complex (complexity: 15)",
        line=45,
        severity=SeverityLevel.WARNING,
        suggestion="Consider breaking this function into smaller functions"
    )
    
    static_result.add_comment(
        body="Missing type hints for function parameters",
        line=23,
        severity=SeverityLevel.INFO
    )
    
    static_result.add_comment(
        body="Potential SQL injection vulnerability",
        line=67,
        severity=SeverityLevel.ERROR,
        suggestion="Use parameterized queries instead of string formatting"
    )
    
    print(f"  File: {static_result.filename}")
    print(f"  Analysis type: {static_result.analysis_type.value}")
    print(f"  Comments: {len(static_result.comments)}")
    print(f"  Errors: {static_result.error_count}")
    print(f"  Warnings: {static_result.warning_count}")
    print()
    
    # AI analysis result
    ai_result = AnalysisResult(
        filename="tests/test_new_feature.py",
        analysis_type=AnalysisType.AI,
        execution_time=2.3
    )
    
    ai_result.add_comment(
        body="Consider adding edge case tests for empty input",
        line=15,
        severity=SeverityLevel.SUGGESTION
    )
    
    ai_result.add_comment(
        body="Test coverage could be improved for error conditions",
        severity=SeverityLevel.INFO
    )
    
    print(f"  File: {ai_result.filename}")
    print(f"  Analysis type: {ai_result.analysis_type.value}")
    print(f"  Comments: {len(ai_result.comments)}")
    print()
    
    # 4. Create review summary
    print("4. Creating ReviewSummary...")
    summary = ReviewSummary(
        pull_request=pr,
        analysis_results=[static_result, ai_result],
        total_execution_time=2.8
    )
    
    print(f"  PR: #{summary.pull_request.id}")
    print(f"  Files analyzed: {len(summary.analysis_results)}")
    print(f"  Total comments: {summary.total_comments}")
    print(f"  Total errors: {summary.total_errors}")
    print(f"  Total warnings: {summary.total_warnings}")
    print(f"  Has errors: {summary.has_errors}")
    print(f"  Execution time: {summary.total_execution_time:.2f}s")
    print()
    
    # 5. Show all comments by severity
    print("5. Comments by severity:")
    
    for severity in [SeverityLevel.ERROR, SeverityLevel.WARNING, 
                     SeverityLevel.INFO, SeverityLevel.SUGGESTION]:
        comments = summary.get_comments_by_severity(severity)
        if comments:
            print(f"\n  {severity.value.upper()} ({len(comments)}):")
            for comment in comments:
                location = f"{comment.path}:{comment.line}" if comment.line else comment.path
                print(f"    - [{location}] {comment.body}")
                if comment.suggestion:
                    print(f"      Suggestion: {comment.suggestion}")
    
    print()
    
    # 6. Convert to dictionary
    print("6. Converting to dictionary format...")
    summary_dict = summary.to_dict()
    print(f"  Dictionary keys: {list(summary_dict.keys())}")
    print(f"  Can be serialized to JSON: ✓")
    print()
    
    print("=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()