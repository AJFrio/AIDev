#!/usr/bin/env python3
"""
Debug script to test repository access and identify issues
"""

import requests
from config import Config

def test_repository_access(repo_owner: str, repo_name: str):
    """Test basic repository access"""
    
    print(f"🔍 Testing access to repository: {repo_owner}/{repo_name}")
    print("-" * 50)
    
    # Check if we have a token
    if not Config.GITHUB_TOKEN:
        print("❌ No GitHub token found!")
        print("Please set GITHUB_TOKEN in your .env file")
        return False
    
    print(f"✅ GitHub token found (length: {len(Config.GITHUB_TOKEN)})")
    
    # Test basic GitHub API access
    headers = {
        'Authorization': f'token {Config.GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Test 1: Check if we can access GitHub API at all
    print("\n1. Testing GitHub API access...")
    try:
        response = requests.get('https://api.github.com/user', headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ GitHub API access successful")
            print(f"   Authenticated as: {user_data.get('login', 'Unknown')}")
        else:
            print(f"❌ GitHub API access failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error accessing GitHub API: {e}")
        return False
    
    # Test 2: Check specific repository access
    print(f"\n2. Testing repository access: {repo_owner}/{repo_name}")
    repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    
    try:
        response = requests.get(repo_url, headers=headers)
        if response.status_code == 200:
            repo_data = response.json()
            print(f"✅ Repository access successful")
            print(f"   Repository: {repo_data.get('full_name')}")
            print(f"   Private: {repo_data.get('private', False)}")
            print(f"   Default branch: {repo_data.get('default_branch')}")
            print(f"   Permissions: {repo_data.get('permissions', {})}")
        elif response.status_code == 404:
            print(f"❌ Repository not found or not accessible")
            print("   Possible causes:")
            print("   - Repository doesn't exist")
            print("   - Repository is private and token lacks access")
            print("   - Incorrect repository owner/name")
            print("   - Token doesn't have 'repo' scope")
            return False
        else:
            print(f"❌ Repository access failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error accessing repository: {e}")
        return False
    
    # Test 3: Check branch access
    print(f"\n3. Testing branch listing...")
    branches_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/branches"
    
    try:
        response = requests.get(branches_url, headers=headers)
        if response.status_code == 200:
            branches = response.json()
            print(f"✅ Branch access successful")
            print(f"   Found {len(branches)} branches:")
            for branch in branches[:5]:  # Show first 5 branches
                print(f"   - {branch['name']}")
            if len(branches) > 5:
                print(f"   ... and {len(branches) - 5} more")
        else:
            print(f"❌ Branch access failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing branches: {e}")
        return False
    
    print("\n🎉 All tests passed! Repository access is working correctly.")
    return True

def main():
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python debug_repo_access.py <owner> <repo>")
        print("Example: python debug_repo_access.py AJFrio Wholesale-Builder")
        sys.exit(1)
    
    repo_owner = sys.argv[1]
    repo_name = sys.argv[2]
    
    test_repository_access(repo_owner, repo_name)

if __name__ == "__main__":
    main() 