"""
Demonstration of logging functionality.
Run this to see logging in action.
"""

import time
from ai_pr_agent.utils import get_logger, log_function_call
from ai_pr_agent.core.exceptions import ConfigurationError

# Get loggers for different modules
main_logger = get_logger("demo.main")
analyzer_logger = get_logger("demo.analyzer")
github_logger = get_logger("demo.github")


@log_function_call
def simulate_analysis(file_count: int) -> dict:
    """Simulate code analysis with logging."""
    analyzer_logger.info(f"Starting analysis of {file_count} files")
    
    results = {"files_analyzed": 0, "issues_found": 0}
    
    for i in range(file_count):
        analyzer_logger.debug(f"Analyzing file {i+1}/{file_count}")
        
        # Simulate some processing time
        time.sleep(0.1)
        
        # Simulate finding issues
        if i % 3 == 0:
            results["issues_found"] += 1
            analyzer_logger.warning(f"Issue found in file {i+1}")
        
        results["files_analyzed"] += 1
    
    analyzer_logger.info(f"Analysis complete: {results}")
    return results


def simulate_github_api():
    """Simulate GitHub API interaction."""
    github_logger.info("Connecting to GitHub API")
    
    try:
        # Simulate API call
        github_logger.debug("Fetching PR data...")
        time.sleep(0.2)
        
        # Simulate occasional API error
        import random
        if random.random() < 0.3:
            raise ConfigurationError("GitHub token not found")
            
        github_logger.info("Successfully fetched PR data")
        return {"pr_id": 123, "files_changed": 5}
        
    except ConfigurationError as e:
        github_logger.error(f"GitHub API error: {e}")
        return None


def main():
    """Main demo function."""
    main_logger.info("=== AI PR Review Agent Logging Demo ===")
    
    try:
        # Test different log levels
        main_logger.debug("This is a debug message")
        main_logger.info("This is an info message")
        main_logger.warning("This is a warning message")
        main_logger.error("This is an error message")
        
        # Test function logging decorator
        analysis_results = simulate_analysis(file_count=5)
        
        # Test GitHub simulation
        github_data = simulate_github_api()
        
        if github_data:
            main_logger.info(f"Processing PR {github_data['pr_id']}")
        else:
            main_logger.warning("Skipping processing due to API error")
        
        main_logger.info("Demo completed successfully")
        
    except Exception as e:
        main_logger.exception("Demo failed with unexpected error")


if __name__ == "__main__":
    main()