"""Quick test of GitHub integration."""

import os
from ai_pr_agent.adapters import AdapterFactory

def main():
    """Test GitHub adapter with real API."""
    
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ GITHUB_TOKEN not set!")
        print("Set it with: $env:GITHUB_TOKEN='your_token'")
        return
    
    print("🔍 Testing GitHub Integration...\n")
    
    # Create adapter
    adapter = AdapterFactory.create_github_adapter(token=token)
    
    # Test 1: Validate connection
    print("1. Testing connection...")
    try:
        adapter.validate_connection()
        print("   ✅ Connection successful!\n")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}\n")
        return
    
    # Test 2: Get rate limit
    print("2. Checking rate limit...")
    try:
        rate_info = adapter.get_rate_limit()
        print(f"   ✅ Limit: {rate_info.limit}")
        print(f"   ✅ Remaining: {rate_info.remaining}\n")
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
    
    # Test 3: Get repository info
    print("3. Fetching repository info (microsoft/vscode)...")
    try:
        repo_info = adapter.get_repository_info("microsoft/vscode")
        print(f"   ✅ Owner: {repo_info.owner}")
        print(f"   ✅ Name: {repo_info.name}")
        print(f"   ✅ Default branch: {repo_info.default_branch}\n")
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
    
    # Test 4: List PRs
    print("4. Listing recent closed PRs...")
    try:
        prs = adapter.list_pull_requests("microsoft/vscode", state="closed", limit=3)
        print(f"   ✅ Found {len(prs)} PRs:")
        for pr in prs[:3]:
            print(f"      - PR #{pr.id}: {pr.title[:50]}...")
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()