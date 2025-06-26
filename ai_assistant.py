import json
from openai import OpenAI, AzureOpenAI
from typing import Dict, Any, List, Optional
from datetime import datetime
import re
from config import Config
from github_client import GitHubClient
from ai_tools import AITools

class AIAssistant:
    def __init__(self, repo_owner: str, repo_name: str, github_token: Optional[str] = None, 
                 branch_name: Optional[str] = None, objective: Optional[str] = None, 
                 azure_tier: str = 'auto', model_provider: str = 'openai', openrouter_model: Optional[str] = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        
        # Initialize OpenAI client based on the selected provider
        self.model_provider = model_provider
        
        if model_provider == 'azure':
            azure_config = Config.get_azure_config(azure_tier)
            if not azure_config:
                raise ValueError("Azure configuration not found for the specified tier.")
            
            tier_display = azure_config['tier']
            print(f"🔷 Using Azure OpenAI ({tier_display.upper()} tier)")
            self.openai_client = AzureOpenAI(
                api_key=azure_config['api_key'],
                azure_endpoint=azure_config['endpoint'],
                api_version=azure_config['api_version']
            )
            self.model_name = azure_config['deployment']
            self.azure_tier = tier_display
        
        elif model_provider == 'openrouter':
            if not Config.OPENROUTER_API_KEY:
                raise ValueError("OpenRouter API key not found. Please set OPENROUTER_API_KEY environment variable.")
            
            print("⚫️ Using OpenRouter")
            self.openai_client = OpenAI(
                api_key=Config.OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1"
            )
            self.model_name = openrouter_model or 'anthropic/claude-3-haiku'
            print(f"   Model: {self.model_name}")
            self.azure_tier = None
            
        else: # Default to OpenAI
            if not Config.OPENAI_API_KEY:
                raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
            
            print("🟢 Using OpenAI")
            self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
            self.model_name = Config.OPENAI_MODEL
            self.azure_tier = None
        
        # Initialize GitHub client
        self.github_client = GitHubClient(github_token)
        
        # Generate branch name if not provided
        if not branch_name:
            if objective:
                self.branch_name = self._generate_branch_name(objective)
            else:
                # Fallback to timestamp if no objective provided
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                self.branch_name = f"ai-dev/task-{timestamp}"
        else:
            self.branch_name = branch_name
        
        # Initialize tools with the branch
        self.ai_tools = AITools(repo_owner, repo_name, self.github_client, self.branch_name)
        
        # Conversation history
        self.conversation_history = []
        
    def _generate_branch_name(self, objective: str) -> str:
        """
        Generate a descriptive branch name from the objective
        Format: ai-dev/<5-word-summary>
        """
        # Remove common words and clean the objective
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
        
        # Clean and split the objective
        words = re.findall(r'\b[a-zA-Z]+\b', objective.lower())
        
        # Filter out common words and keep meaningful ones
        meaningful_words = [word for word in words if word not in common_words and len(word) > 2]
        
        # Take first 5 meaningful words
        summary_words = meaningful_words[:5]
        
        # If we don't have enough meaningful words, add some original words
        if len(summary_words) < 3:
            original_words = [word for word in words if word not in summary_words and len(word) > 1]
            summary_words.extend(original_words[:5-len(summary_words)])
        
        # Join with dashes and create branch name
        if summary_words:
            summary = '-'.join(summary_words)
            # Ensure it's not too long (Git branch names should be reasonable)
            if len(summary) > 50:
                summary = summary[:47] + "..."
            return f"ai-dev/{summary}"
        else:
            # Fallback if no good words found
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            return f"ai-dev/task-{timestamp}"

    def get_system_prompt(self, objective: str, repo_structure: List[Dict[str, Any]]) -> str:
        """
        Generate the system prompt for the AI Dev
        """
        structure_info = json.dumps(repo_structure, indent=2)
        
        return f"""You are an AI coding assistant that helps complete programming tasks by analyzing and modifying code repositories through GitHub.

OBJECTIVE: {objective}

WORKING BRANCH: {self.branch_name}
You are working on a dedicated branch, so all changes will be isolated from the main branch.

REPOSITORY STRUCTURE:
{structure_info}

AVAILABLE TOOLS:
You have access to the following tools to interact with the repository:
- get_directory: Retrieve directory contents (optional directory_path parameter)
- read_file: Read file contents (requires file_path parameter)  
- update_file: Update file contents (requires file_path and content parameters)
- add_file: Create new files (requires file_path and content parameters)
- make_dir: Create new directories (requires directory_path parameter)
- change_dir: Change current directory (requires directory_path parameter)
- finish_task: Call when objective is complete (requires summary and success parameters)

INSTRUCTIONS:
1. Start by exploring the repository structure using get_directory
2. Read relevant files to understand the codebase
3. Make necessary changes to complete the objective
4. Use change_dir to navigate between directories
5. Always use update_file to save your changes (they will be committed to the branch: {self.branch_name})
6. Think step by step and explain your reasoning
7. When you have completed the objective, call finish_task with a summary of what was accomplished

IMPORTANT: You must call finish_task when you are done. Do not just say the task is complete - use the finish_task function.

Continue working until the objective is completed. Be thorough and methodical in your approach."""

    def call_openai(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Make a call to OpenAI API with function calling support
        """
        try:
            # Convert tool schemas to OpenAI function format
            tools = []
            for tool_schema in self.ai_tools.get_tool_schemas():
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool_schema["name"],
                        "description": tool_schema["description"],
                        "parameters": tool_schema["input_schema"]
                    }
                })
            
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            return {
                "message": response.choices[0].message,
                "content": response.choices[0].message.content,
                "tool_calls": response.choices[0].message.tool_calls
            }
        except Exception as e:
            return {
                "error": f"Error calling OpenAI API: {str(e)}",
                "content": f"Error calling OpenAI API: {str(e)}",
                "tool_calls": None
            }
    
    def parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse tool call from AI response - DEPRECATED
        This method is kept for backward compatibility but is no longer used
        """
        try:
            # Look for JSON in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                tool_call = json.loads(json_str)
                
                if 'tool' in tool_call:
                    return tool_call
                    
        except json.JSONDecodeError:
            pass
            
        return None
    
    def execute_objective(self, objective: str, max_iterations: int = 20, 
                         create_pr: bool = True, fallback_to_main: bool = False) -> Dict[str, Any]:
        """
        Execute the given objective using the AI Dev
        """
        print(f"Starting AI Dev for repository: {self.repo_owner}/{self.repo_name}")
        print(f"Objective: {objective}")
        print(f"Working Branch: {self.branch_name}")
        print("-" * 50)
        
        # Try to create the new branch
        branch_created = False
        if not fallback_to_main:
            print("Creating new branch...")
            branch_created = self.github_client.create_branch(self.repo_owner, self.repo_name, self.branch_name)
        
        if not branch_created and not fallback_to_main:
            print("\n⚠️  Branch creation failed. Would you like to:")
            print("1. Fix your GitHub token scopes (recommended)")
            print("2. Work directly on main branch (NOT recommended for production)")
            print("\nFor now, the system will stop here for safety.")
            return {
                "success": False,
                "error": f"Could not create branch: {self.branch_name}. Please fix GitHub token scopes.",
                "instructions": [
                    "1. Go to GitHub Settings → Developer settings → Personal access tokens",
                    "2. Generate a new token with 'repo' scope", 
                    "3. Update your .env file with the new token"
                ]
            }
        
        # Determine which branch to use
        working_branch = self.branch_name if branch_created else "main"
        if not branch_created:
            print(f"⚠️  Working directly on main branch - changes will be immediate!")
            self.ai_tools.branch = "main"
        
        # Get initial repository structure from the working branch
        repo_structure = self.github_client.get_repository_structure(
            self.repo_owner, self.repo_name, branch=working_branch
        )
        
        if not repo_structure:
            return {
                "success": False,
                "error": "Could not fetch repository structure"
            }
        
        # Initialize conversation with system prompt
        system_prompt = self.get_system_prompt(objective, repo_structure)
        self.conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please help me complete this objective: {objective}"}
        ]
        
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")
            
            # Get AI response
            ai_response = self.call_openai(self.conversation_history)
            
            # Check for API errors
            if "error" in ai_response:
                print(f"❌ API Error: {ai_response['error']}")
                return {
                    "success": False,
                    "error": ai_response["error"],
                    "iterations": iteration
                }
            
            content = ai_response.get("content", "")
            tool_calls = ai_response.get("tool_calls")
            message = ai_response.get("message")
            
            # Print response - handle both text and tool calls
            if content:
                print(f"AI Response: {content}")
            elif tool_calls:
                print(f"AI Response: [Making {len(tool_calls)} tool call(s)]")
                for tool_call in tool_calls:
                    print(f"  - Calling {tool_call.function.name} with {tool_call.function.arguments}")
            else:
                print("AI Response: [No content or tool calls]")
            
            # Add AI response to history (handle None content properly)
            assistant_message = {
                "role": "assistant"
            }
            if content:
                assistant_message["content"] = content
            if tool_calls:
                assistant_message["tool_calls"] = tool_calls
            
            self.conversation_history.append(assistant_message)
            
            # Check if AI thinks task is complete (only check if there's actual content)
            if content and any(phrase in content.lower() for phrase in [
                "task is complete", "objective is complete", "finished", "done"
            ]):
                print("\n🎉 AI Dev has completed the task!")
                
                # Create pull request if requested and we created a branch
                pr_url = None
                if create_pr and branch_created:
                    print("Creating pull request...")
                    default_branch = self.github_client.get_default_branch(
                        self.repo_owner, self.repo_name
                    )
                    pr_title = f"AI Dev: {objective}"
                    
                    # Get list of modified files
                    modified_files = self.ai_tools.get_modified_files()
                    
                    # Create structured PR description
                    pr_body = self._create_pr_description(objective, working_branch, iteration, content, modified_files)
                    
                    pr_url = self.github_client.create_pull_request(
                        self.repo_owner, self.repo_name, 
                        working_branch, default_branch,
                        pr_title, pr_body
                    )
                    
                    if pr_url:
                        print(f"✅ Pull request created: {pr_url}")
                    else:
                        print("⚠️  Could not create pull request")
                elif not branch_created:
                    print("⚠️  Changes were made directly to main branch - no PR created")
                
                return {
                    "success": True,
                    "message": "Task completed successfully",
                    "final_response": content,
                    "iterations": iteration,
                    "branch": working_branch,
                    "pull_request_url": pr_url,
                    "used_main_branch": not branch_created
                }
            
            # Handle tool calls using proper OpenAI format
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        parameters = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        parameters = {}
                    
                    print(f"Executing tool: {tool_name} with parameters: {parameters}")
                    
                    # Execute the tool
                    result = self.ai_tools.execute_tool(tool_name, parameters)
                    print(f"Tool result: {result}")
                    
                    # Check if this is the finish_task tool call
                    if tool_name == "finish_task" and result.get("task_completed"):
                        print("\n🎉 AI Dev has completed the task using finish_task!")
                        
                        # Create pull request if requested and we created a branch
                        pr_url = None
                        if create_pr and branch_created:
                            print("Creating pull request...")
                            default_branch = self.github_client.get_default_branch(
                                self.repo_owner, self.repo_name
                            )
                            pr_title = f"AI Dev: {objective}"
                            
                            # Get list of modified files from the result
                            modified_files = result.get("modified_files", [])
                            ai_summary = result.get("summary", "Task completed successfully")
                            
                            # Create structured PR description
                            pr_body = self._create_pr_description(objective, working_branch, iteration, ai_summary, modified_files)
                            
                            pr_url = self.github_client.create_pull_request(
                                self.repo_owner, self.repo_name, 
                                working_branch, default_branch,
                                pr_title, pr_body
                            )
                            
                            if pr_url:
                                print(f"✅ Pull request created: {pr_url}")
                            else:
                                print("⚠️  Could not create pull request")
                        elif not branch_created:
                            print("⚠️  Changes were made directly to main branch - no PR created")
                        
                        return {
                            "success": result.get("objective_success", True),
                            "message": "Task completed successfully using finish_task",
                            "final_response": result.get("summary", "Task completed"),
                            "iterations": iteration,
                            "branch": working_branch,
                            "pull_request_url": pr_url,
                            "used_main_branch": not branch_created,
                            "modified_files": result.get("modified_files", [])
                        }
                    
                    # Add tool result to conversation using proper format
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, indent=2)
                    })
            else:
                # No tool call found, ask AI to continue
                continue_message = "Please continue with the next step or use a tool to proceed."
                self.conversation_history.append({"role": "user", "content": continue_message})
        
        return {
            "success": False,
            "error": f"Max iterations ({max_iterations}) reached without completion",
            "iterations": iteration,
            "branch": working_branch
        }
    
    def get_conversation_summary(self) -> str:
        """
        Get a summary of the conversation history
        """
        summary = "CONVERSATION SUMMARY:\n"
        summary += "=" * 50 + "\n"
        
        for i, message in enumerate(self.conversation_history):
            role = message["role"].upper()
            content = message["content"][:200] + "..." if len(message["content"]) > 200 else message["content"]
            summary += f"{i+1}. {role}: {content}\n\n"
        
        return summary 
    
    def _create_pr_description(self, objective: str, branch: str, iterations: int, 
                             ai_summary: str, modified_files: List[Dict[str, str]]) -> str:
        """
        Create a structured PR description with file changes and single summary
        """
        # Build file changes section
        file_changes_section = ""
        if modified_files:
            file_changes_section = "\n**Files Changed:**\n"
            for file_info in modified_files:
                file_path = file_info["file_path"]
                action = file_info["action"]
                file_changes_section += f"• `{file_path}` - {action}\n"
        else:
            file_changes_section = "\n**Files Changed:** None\n"
        
        # Use the AI summary as a single overall summary (no per-file breakdown)
        summary_section = ""
        if ai_summary:
            summary_section = f"\n**Summary:**\n{ai_summary}\n"
        
        # Build complete PR description
        pr_body = f"""This pull request was created by the AI Dev.

**Objective:** {objective}

**Branch:** {branch}
**Iterations:** {iterations}
{file_changes_section}{summary_section}
Please review the changes before merging."""
        
        return pr_body