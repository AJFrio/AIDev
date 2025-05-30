import requests
import base64
from typing import List, Dict, Any, Optional
from config import Config

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or Config.GITHUB_TOKEN
        self.base_url = Config.GITHUB_API_BASE
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
    def get_repository_structure(self, repo_owner: str, repo_name: str, path: str = "", branch: str = "main") -> List[Dict[str, Any]]:
        """
        Get the directory structure of a repository
        Returns a list of files and directories with their metadata
        """
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/contents/{path}"
        params = {"ref": branch} if branch != "main" else {}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            contents = response.json()
            
            # Filter and format the data as requested
            filtered_contents = []
            for item in contents:
                filtered_item = {
                    'name': item['name'],
                    'path': item['path'],
                    'type': item['type']  # 'file' or 'dir'
                }
                filtered_contents.append(filtered_item)
                
            return filtered_contents
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repository structure: {e}")
            return []
    
    def get_file_content(self, repo_owner: str, repo_name: str, file_path: str, branch: str = "main") -> Optional[str]:
        """
        Get the content of a specific file from the repository
        """
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/contents/{file_path}"
        params = {"ref": branch} if branch != "main" else {}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            file_data = response.json()
            
            # Decode base64 content
            if file_data.get('encoding') == 'base64':
                content = base64.b64decode(file_data['content']).decode('utf-8')
                return content
            else:
                return file_data.get('content', '')
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching file content: {e}")
            return None
    
    def get_default_branch(self, repo_owner: str, repo_name: str) -> str:
        """
        Get the default branch of the repository
        """
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            repo_data = response.json()
            return repo_data.get('default_branch', 'main')
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repository info: {e}")
            print(f"Repository URL: {url}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                if e.response.status_code == 404:
                    print(f"❌ Repository {repo_owner}/{repo_name} not found or not accessible")
                    print("Possible issues:")
                    print("  - Repository doesn't exist")
                    print("  - Repository is private and token lacks access")
                    print("  - Incorrect repository owner/name")
                    print("  - GitHub token doesn't have 'repo' permissions")
                elif e.response.status_code == 401:
                    print("❌ Authentication failed - check your GitHub token")
            return 'main'
    
    def get_branch_sha(self, repo_owner: str, repo_name: str, branch: str) -> Optional[str]:
        """
        Get the SHA of the latest commit on a branch
        """
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/git/refs/heads/{branch}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            ref_data = response.json()
            return ref_data['object']['sha']
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching branch SHA for '{branch}': {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                if e.response.status_code == 404:
                    print(f"Branch '{branch}' not found. Available branches:")
                    # Try to list available branches
                    try:
                        branches_url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/branches"
                        branches_response = requests.get(branches_url, headers=self.headers)
                        if branches_response.status_code == 200:
                            branches = branches_response.json()
                            for b in branches:
                                print(f"  - {b['name']}")
                        else:
                            print("  Could not list branches")
                    except:
                        print("  Could not list branches")
            return None
    
    def create_branch(self, repo_owner: str, repo_name: str, new_branch: str, base_branch: str = None) -> bool:
        """
        Create a new branch from the base branch
        """
        print(f"Creating branch '{new_branch}' in {repo_owner}/{repo_name}")
        
        # First, verify repository access
        repo_url = f"{self.base_url}/repos/{repo_owner}/{repo_name}"
        try:
            repo_response = requests.get(repo_url, headers=self.headers)
            repo_response.raise_for_status()
            print(f"✅ Repository access confirmed")
            
            # Check if we have push permissions
            repo_data = repo_response.json()
            permissions = repo_data.get('permissions', {})
            if not permissions.get('push', False):
                print("❌ No push permissions to this repository")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot access repository: {e}")
            return False
        
        # Check token scopes
        try:
            user_response = requests.get(f"{self.base_url}/user", headers=self.headers)
            if user_response.status_code == 200:
                scopes = user_response.headers.get('X-OAuth-Scopes', '')
                print(f"Token scopes: {scopes}")
                
                # Check if we have repo scope
                if 'repo' not in scopes and 'public_repo' not in scopes:
                    print("❌ GitHub token lacks 'repo' or 'public_repo' scope needed for branch creation")
                    print("Please update your GitHub token with proper scopes:")
                    print("  1. Go to GitHub Settings → Developer settings → Personal access tokens")
                    print("  2. Generate a new token with 'repo' scope")
                    print("  3. Update your .env file with the new token")
                    return False
            else:
                print("⚠️ Could not verify token scopes")
        except Exception as e:
            print(f"⚠️ Error checking token scopes: {e}")
        
        if not base_branch:
            base_branch = self.get_default_branch(repo_owner, repo_name)
        
        print(f"Using base branch: {base_branch}")
        
        # Get the SHA of the base branch
        base_sha = self.get_branch_sha(repo_owner, repo_name, base_branch)
        if not base_sha:
            print(f"Could not get SHA for base branch: {base_branch}")
            return False
        
        print(f"Base branch SHA: {base_sha}")
        
        # Create the new branch
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/git/refs"
        
        data = {
            'ref': f'refs/heads/{new_branch}',
            'sha': base_sha
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code == 201:
                print(f"✅ Created new branch: {new_branch}")
                return True
            elif response.status_code == 422:
                # Branch already exists
                print(f"⚠️  Branch {new_branch} already exists")
                return True
            else:
                response.raise_for_status()
                return True
                
        except requests.exceptions.RequestException as e:
            print(f"Error creating branch: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                try:
                    error_detail = e.response.json()
                    print(f"Error details: {error_detail}")
                except:
                    pass
            return False
    
    def update_file_content(self, repo_owner: str, repo_name: str, file_path: str, 
                          content: str, commit_message: str, sha: str, branch: str = "main") -> bool:
        """
        Update a file in the repository
        """
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/contents/{file_path}"
        
        # Encode content to base64
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        data = {
            'message': commit_message,
            'content': encoded_content,
            'sha': sha,
            'branch': branch
        }
        
        try:
            response = requests.put(url, headers=self.headers, json=data)
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Error updating file: {e}")
            return False
    
    def get_file_sha(self, repo_owner: str, repo_name: str, file_path: str, branch: str = "main") -> Optional[str]:
        """
        Get the SHA hash of a file (needed for updates)
        """
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/contents/{file_path}"
        params = {"ref": branch} if branch != "main" else {}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            file_data = response.json()
            return file_data.get('sha')
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching file SHA: {e}")
            return None
    
    def create_pull_request(self, repo_owner: str, repo_name: str, head_branch: str, 
                          base_branch: str, title: str, body: str = "") -> Optional[str]:
        """
        Create a pull request from head_branch to base_branch
        Returns the PR URL if successful
        """
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/pulls"
        
        data = {
            'title': title,
            'head': head_branch,
            'base': base_branch,
            'body': body
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            pr_data = response.json()
            return pr_data.get('html_url')
            
        except requests.exceptions.RequestException as e:
            print(f"Error creating pull request: {e}")
            return None 