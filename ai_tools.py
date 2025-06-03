from typing import Dict, Any, List, Optional
from github_client import GitHubClient
import os

class AITools:
    def __init__(self, repo_owner: str, repo_name: str, github_client: GitHubClient, branch: str = "main"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_client = github_client
        self.current_directory = ""
        self.branch = branch
        self.modified_files = []  # Track files that were modified
        
    def get_directory(self, directory_path: str = "") -> Dict[str, Any]:
        """
        Retrieve the contents of a directory
        If no directory_path is provided, shows the top level directory
        """
        try:
            # If no directory specified, use root directory
            target_directory = directory_path if directory_path else ""
            
            contents = self.github_client.get_repository_structure(
                self.repo_owner, 
                self.repo_name, 
                target_directory,
                self.branch
            )
            
            return {
                "success": True,
                "contents": contents,
                "current_path": target_directory,
                "branch": self.branch
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read the contents of a specified file
        """
        try:
            # Handle relative paths from current directory
            if self.current_directory and not file_path.startswith(self.current_directory):
                full_path = f"{self.current_directory}/{file_path}".strip("/")
            else:
                full_path = file_path
                
            content = self.github_client.get_file_content(
                self.repo_owner,
                self.repo_name,
                full_path,
                self.branch
            )
            
            if content is not None:
                return {
                    "success": True,
                    "content": content,
                    "file_path": full_path,
                    "branch": self.branch
                }
            else:
                return {
                    "success": False,
                    "error": f"Could not read file: {full_path}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Update the contents of a specified file
        """
        try:
            # Handle relative paths from current directory
            if self.current_directory and not file_path.startswith(self.current_directory):
                full_path = f"{self.current_directory}/{file_path}".strip("/")
            else:
                full_path = file_path
            
            # Get the current file SHA (required for updates)
            sha = self.github_client.get_file_sha(
                self.repo_owner,
                self.repo_name,
                full_path,
                self.branch
            )
            
            if not sha:
                return {
                    "success": False,
                    "error": f"Could not get SHA for file: {full_path}"
                }
            
            # Update the file
            commit_message = f"AI Dev: Update {full_path}"
            success = self.github_client.update_file_content(
                self.repo_owner,
                self.repo_name,
                full_path,
                content,
                commit_message,
                sha,
                self.branch
            )
            
            if success:
                # Track the file change
                self.modified_files.append({
                    "file_path": full_path,
                    "action": "updated",
                    "branch": self.branch
                })
                
                return {
                    "success": True,
                    "message": f"Successfully updated {full_path} on branch {self.branch}",
                    "branch": self.branch
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to update {full_path}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Create a new file with the specified content
        """
        try:
            # Handle relative paths from current directory
            if self.current_directory and not file_path.startswith(self.current_directory):
                full_path = f"{self.current_directory}/{file_path}".strip("/")
            else:
                full_path = file_path
            
            # Check if file already exists
            existing_sha = self.github_client.get_file_sha(
                self.repo_owner,
                self.repo_name,
                full_path,
                self.branch
            )
            
            if existing_sha:
                return {
                    "success": False,
                    "error": f"File already exists: {full_path}. Use update_file to modify existing files."
                }
            
            # Create the new file
            commit_message = f"AI Dev: Add {full_path}"
            success = self.github_client.update_file_content(
                self.repo_owner,
                self.repo_name,
                full_path,
                content,
                commit_message,
                None,  # No SHA needed for new files
                self.branch
            )
            
            if success:
                # Track the file creation
                self.modified_files.append({
                    "file_path": full_path,
                    "action": "created",
                    "branch": self.branch
                })
                
                return {
                    "success": True,
                    "message": f"Successfully created {full_path} on branch {self.branch}",
                    "branch": self.branch
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create {full_path}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def make_dir(self, directory_path: str) -> Dict[str, Any]:
        """
        Create a new directory by adding a .gitkeep file
        
        Note: GitHub doesn't allow empty directories, so we create a .gitkeep file
        to establish the directory structure. This is a common Git convention.
        """
        try:
            # Handle relative and absolute paths
            if directory_path.startswith("/"):
                # Absolute path - strip leading slash
                full_path = directory_path.strip("/")
            elif self.current_directory and not directory_path.startswith(self.current_directory):
                # Relative path from current directory
                full_path = f"{self.current_directory}/{directory_path}".strip("/")
            else:
                # Already a full path or no current directory
                full_path = directory_path
            
            # Check if directory already exists by trying to get its contents
            existing_contents = self.github_client.get_repository_structure(
                self.repo_owner,
                self.repo_name,
                full_path,
                self.branch
            )
            
            if existing_contents is not None:
                return {
                    "success": False,
                    "error": f"Directory already exists: {full_path}"
                }
            
            # Create the directory by adding a .gitkeep file
            gitkeep_path = f"{full_path}/.gitkeep"
            gitkeep_content = "# This file keeps the directory in Git\n# You can safely delete this file if the directory has other content\n"
            
            commit_message = f"AI Dev: Create directory {full_path}"
            success = self.github_client.update_file_content(
                self.repo_owner,
                self.repo_name,
                gitkeep_path,
                gitkeep_content,
                commit_message,
                None,  # No SHA needed for new files
                self.branch
            )
            
            if success:
                # Track the directory creation
                self.modified_files.append({
                    "file_path": gitkeep_path,
                    "action": "created",
                    "branch": self.branch
                })
                
                return {
                    "success": True,
                    "message": f"Successfully created directory {full_path} on branch {self.branch}",
                    "directory_path": full_path,
                    "gitkeep_file": gitkeep_path,
                    "branch": self.branch
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create directory {full_path}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def change_dir(self, directory_path: str) -> Dict[str, Any]:
        """
        Change the current working directory
        """
        try:
            # Handle relative and absolute paths
            if directory_path.startswith("/"):
                new_path = directory_path.strip("/")
            elif directory_path == "..":
                # Go up one directory
                if self.current_directory:
                    path_parts = self.current_directory.split("/")
                    if len(path_parts) > 1:
                        new_path = "/".join(path_parts[:-1])
                    else:
                        new_path = ""
                else:
                    new_path = ""
            elif directory_path == ".":
                new_path = self.current_directory
            else:
                # Relative path
                if self.current_directory:
                    new_path = f"{self.current_directory}/{directory_path}".strip("/")
                else:
                    new_path = directory_path
            
            # Verify the directory exists by trying to get its contents
            contents = self.github_client.get_repository_structure(
                self.repo_owner,
                self.repo_name,
                new_path,
                self.branch
            )
            
            if contents is not None:
                self.current_directory = new_path
                return {
                    "success": True,
                    "current_path": self.current_directory,
                    "contents": contents,
                    "branch": self.branch
                }
            else:
                return {
                    "success": False,
                    "error": f"Directory not found: {new_path}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get the schema definitions for all available tools
        """
        return [
            {
                "name": "get_directory",
                "description": "Retrieve the contents of a directory. If no directory_path is provided, shows the top level directory.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "Path to the directory to explore (optional - defaults to top level)"
                        }
                    }
                }
            },
            {
                "name": "read_file",
                "description": "Read the contents of a specified file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to be read"
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "update_file",
                "description": "Update the contents of a specified file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to be updated"
                        },
                        "content": {
                            "type": "string",
                            "description": "New content for the file"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            },
            {
                "name": "add_file",
                "description": "Create a new file with the specified content",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to be created"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content for the new file"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            },
            {
                "name": "make_dir",
                "description": "Create a new directory with a .gitkeep file to maintain the directory structure",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "Path to the directory to be created"
                        }
                    },
                    "required": ["directory_path"]
                }
            },
            {
                "name": "change_dir",
                "description": "Change the current working directory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "Path to the target directory"
                        }
                    },
                    "required": ["directory_path"]
                }
            },
            {
                "name": "finish_task",
                "description": "Call this function when you have completed the objective and are ready to finish. Provide a summary of what was accomplished.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "A brief summary of what was accomplished and any important notes"
                        },
                        "success": {
                            "type": "boolean",
                            "description": "Whether the objective was successfully completed"
                        }
                    },
                    "required": ["summary", "success"]
                }
            }
        ]
    
    def get_modified_files(self) -> List[Dict[str, str]]:
        """
        Get the list of files that were modified during this session
        """
        return self.modified_files.copy()
    
    def finish_task(self, summary: str, success: bool = True) -> Dict[str, Any]:
        """
        Signal that the task is complete
        """
        return {
            "success": True,
            "task_completed": True,
            "summary": summary,
            "objective_success": success,
            "modified_files": self.modified_files.copy()
        }
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with the given parameters
        """
        if tool_name == "get_directory":
            directory_path = parameters.get("directory_path", "")
            return self.get_directory(directory_path)
        elif tool_name == "read_file":
            return self.read_file(parameters["file_path"])
        elif tool_name == "update_file":
            return self.update_file(parameters["file_path"], parameters["content"])
        elif tool_name == "add_file":
            return self.add_file(parameters["file_path"], parameters["content"])
        elif tool_name == "make_dir":
            return self.make_dir(parameters["directory_path"])
        elif tool_name == "change_dir":
            return self.change_dir(parameters["directory_path"])
        elif tool_name == "finish_task":
            return self.finish_task(
                parameters["summary"], 
                parameters.get("success", True)
            )
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            } 