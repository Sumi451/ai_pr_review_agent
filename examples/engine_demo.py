"""
Demonstration of the Analysis Engine.
"""

from ai_pr_agent.core import PullRequest, FileChange, FileStatus
from ai_pr_agent.core.engine import AnalysisEngine
from ai_pr_agent.analyzers import MockAnalyzer


def main():
    """Demonstrate the analysis engine."""
    
    print("=" * 70)
    print("AI PR Review Agent - Analysis Engine Demo")
    print("=" * 70)
    print()
    
    # Create a sample PR
    print("1. Creating sample Pull Request...")
    files = [
        FileChange(
            filename="src/main.py",
            status=FileStatus.MODIFIED,
            additions=45,
            deletions=10
        ),
        FileChange(
            filename="src/utils.py",
            status=FileStatus.MODIFIED,
            additions=20,
            deletions=5
        ),
        FileChange(
            filename="tests/test_main.py",
            status=FileStatus.ADDED,
            additions=60,
            deletions=0
        ),
    ]
    
    pr = PullRequest(
        id=42,
        title="Add new feature with tests",
        description="This PR implements feature XYZ",
        author="developer",
        source_branch="feature/xyz",
        target_branch="main",
        files_changed=files
    )
    
    print(f"   PR #{pr.id}: {pr.title}")
    print(f"   Files changed: {len(pr.files_changed)}")
    print()
    
    # Create and configure engine
    print("2. Setting up Analysis Engine...")
    engine = AnalysisEngine()
    
    # Register analyzers
    engine.register_analyzer(MockAnalyzer("StaticAnalyzer"))
    engine.register_analyzer(MockAnalyzer("SecurityAnalyzer"))
    
    print(f"   Registered {len(engine.analyzers)} analyzers")
    print()
    
    # Analyze the PR
    print("3. Analyzing Pull Request...")
    summary = engine.analyze_pull_request(pr)
    
    print(f"   ✓ Analysis complete!")
    print(f"   Status: {summary.overall_status}")
    print(f"   Files analyzed: {len(summary.analysis_results)}")
    print(f"   Total comments: {summary.total_comments}")
    print(f"   Execution time: {summary.total_execution_time:.2f}s")
    print()
    
    # Show results
    print("4. Analysis Results:")
    print()
    
    for result in summary.analysis_results:
        print(f"   📄 {result.filename}")
        print(f"      Comments: {len(result.comments)}")
        
        if result.comments:
            for comment in result.comments:
                severity_icon = {
                    "error": "❌",
                    "warning": "⚠️",
                    "info": "ℹ️",
                    "suggestion": "💡"
                }.get(comment.severity.value, "•")
                
                print(f"      {severity_icon} {comment.body}")
        print()
    
    # Show summary
    print("5. Summary:")
    print(f"   Total errors: {summary.total_errors}")
    print(f"   Total warnings: {summary.total_warnings}")
    print(f"   Files with issues: {len(summary.files_with_issues)}")
    print()
    
    print("=" * 70)
    print("Demo completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()