#!/usr/bin/env python3
"""
Test script specifically for branch creation debugging
"""

import requests
import json
from config import Config

def test_branch_creation():
    repo_owner = "AJFrio"
    repo_name = "Wholesale-Builder"
    new_branch = "test-branch-debug"
    
    headers = {
        'Authorization': f'token {Config.GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    print(f"Testing branch creation for {repo_owner}/{repo_name}")
    print(f"New branch: {new_branch}")
    
    # Step 0: Check token scopes
    print("\n0. Checking token scopes...")
    try:
        response = requests.get("https://api.github.com/user", headers=headers)
        if response.status_code == 200:
            scopes = response.headers.get('X-OAuth-Scopes', 'No scopes header')
            print(f"Token scopes: {scopes}")
        else:
            print(f"Failed to check scopes: {response.status_code}")
    except Exception as e:
        print(f"Error checking scopes: {e}")
    
    # Step 1: Get the main branch SHA
    print("\n1. Getting main branch SHA...")
    ref_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/refs/heads/main"
    
    try:
        response = requests.get(ref_url, headers=headers)
        print(f"GET {ref_url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            ref_data = response.json()
            main_sha = ref_data['object']['sha']
            print(f"✅ Main branch SHA: {main_sha}")
        else:
            print(f"❌ Failed to get main branch SHA: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error getting main branch SHA: {e}")
        return
    
    # Step 2: Try different headers
    print("\n2. Testing with different Accept headers...")
    alt_headers = headers.copy()
    alt_headers['Accept'] = 'application/vnd.github+json'
    
    create_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/refs"
    data = {
        'ref': f'refs/heads/{new_branch}',
        'sha': main_sha
    }
    
    print(f"POST {create_url}")
    print(f"Headers: {alt_headers}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(create_url, headers=alt_headers, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Branch created successfully!")
            return
        elif response.status_code == 422:
            print("⚠️  Branch already exists")
            return
        else:
            print(f"❌ Failed to create branch")
            
    except Exception as e:
        print(f"❌ Error creating branch: {e}")
    
    # Step 3: Try using GitHub CLI-style headers
    print("\n3. Testing with GitHub CLI-style headers...")
    cli_headers = {
        'Authorization': f'token {Config.GITHUB_TOKEN}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    try:
        response = requests.post(create_url, headers=cli_headers, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Branch created successfully!")
            return
        elif response.status_code == 422:
            print("⚠️  Branch already exists")
            return
            
    except Exception as e:
        print(f"❌ Error creating branch: {e}")
    
    # Step 4: Try creating via commits API (alternative approach)
    print("\n4. Testing alternative approach - create commit first...")
    
    # Get the latest commit on main
    commits_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/main"
    try:
        response = requests.get(commits_url, headers=headers)
        if response.status_code == 200:
            commit_data = response.json()
            commit_sha = commit_data['sha']
            print(f"Latest commit SHA: {commit_sha}")
            
            # Now try to create branch reference
            branch_data = {
                'ref': f'refs/heads/{new_branch}',
                'sha': commit_sha
            }
            
            response = requests.post(create_url, headers=headers, json=branch_data)
            print(f"Create branch status: {response.status_code}")
            print(f"Response: {response.text}")
            
        else:
            print(f"Failed to get latest commit: {response.status_code}")
    except Exception as e:
        print(f"Error with alternative approach: {e}")

if __name__ == "__main__":
    test_branch_creation() 