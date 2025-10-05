"""
Demonstration of Static Analysis.
"""

from ai_pr_agent.core import PullRequest, FileChange, FileStatus
from ai_pr_agent.core.engine import AnalysisEngine
from ai_pr_agent.analyzers import StaticAnalyzer


def main():
    """Demonstrate static analysis."""
    
    print("=" * 70)
    print("AI PR Review Agent - Static Analysis Demo")
    print("=" * 70)
    print()
    
    # Create sample files with intentional issues
    print("1. Creating sample Python files with issues...")
    
    # File 1: Style issues
    bad_style_code = '''
def badly_formatted_function( x,y ):
    result=x+y
    return result
'''
    
    file1 = FileChange(
        filename="src/bad_style.py",
        status=FileStatus.ADDED,
        additions=4,
        deletions=0,
        patch=f"@@ -0,0 +1,4 @@\n+{bad_style_code}"
    )
    
    # File 2: Security issue
    security_issue_code = '''
import subprocess

def run_command(user_input):
    # Security issue: shell injection
    subprocess.call(user_input, shell=True)
'''
    
    file2 = FileChange(
        filename="src/security_issue.py",
        status=FileStatus.ADDED,
        additions=5,
        deletions=0,
        patch=f"@@ -0,0 +1,5 @@\n+{security_issue_code}"
    )
    
    pr = PullRequest(
        id=123,
        title="Example PR with code issues",
        description="This PR contains intentional issues for demo",
        author="developer",
        source_branch="feature/demo",
        target_branch="main",
        files_changed=[file1, file2]
    )
    
    print(f"   Created PR #{pr.id} with {len(pr.files_changed)} files")
    print()
    
    # Set up engine with static analyzer
    print("2. Setting up Analysis Engine with Static Analyzer...")
    engine = AnalysisEngine()
    engine.register_analyzer(StaticAnalyzer())
    
    print(f"   Registered {len(engine.analyzers)} analyzer(s)")
    print()
    
    # Run analysis
    print("3. Running Static Analysis...")
    summary = engine.analyze_pull_request(pr)
    
    print(f"   ✓ Analysis complete!")
    print(f"   Status: {summary.overall_status}")
    print(f"   Files analyzed: {len(summary.analysis_results)}")
    print(f"   Total issues found: {summary.total_comments}")
    print()
    
    # Show results
    print("4. Analysis Results:")
    print()
    
    for result in summary.analysis_results:
        print(f"   📄 {result.filename}")
        print(f"      Total issues: {len(result.comments)}")
        print(f"      Errors: {result.error_count}")
        print(f"      Warnings: {result.warning_count}")
        print()
        
        if result.comments:
            for comment in result.comments[:5]:  # Show first 5
                severity_icon = {
                    "error": "❌",
                    "warning": "⚠️",
                    "info": "ℹ️",
                    "suggestion": "💡"
                }.get(comment.severity.value, "•")
                
                location = f"Line {comment.line}" if comment.line else "File"
                print(f"      {severity_icon} [{location}] {comment.body}")
            
            if len(result.comments) > 5:
                print(f"      ... and {len(result.comments) - 5} more issues")
        print()
    
    # Summary
    print("5. Summary:")
    print(f"   Total issues: {summary.total_comments}")
    print(f"   Errors: {summary.total_errors}")
    print(f"   Warnings: {summary.total_warnings}")
    print(f"   Execution time: {summary.total_execution_time:.2f}s")
    print()
    
    print("=" * 70)
    print("Demo completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()