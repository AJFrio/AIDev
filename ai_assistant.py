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
                 branch_name: Optional[str] = None, objective: Optional[str] = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        
        # Initialize OpenAI client (Azure or regular)
        if Config.use_azure_openai():
            print("🔷 Using Azure OpenAI")
            self.openai_client = AzureOpenAI(
                api_key=Config.AZURE_OPENAI_API_KEY,
                azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
                api_version=Config.AZURE_OPENAI_API_VERSION
            )
            self.model_name = Config.AZURE_OPENAI_DEPLOYMENT
        else:
            print("🟢 Using OpenAI")
            if not Config.OPENAI_API_KEY:
                raise ValueError("No OpenAI configuration found. Please set AZURE_OPENAI_* or OPENAI_API_KEY environment variables.")
            self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
            self.model_name = Config.OPENAI_MODEL
        
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
        Generate the system prompt for the AI assistant
        """
        tools_info = json.dumps(self.ai_tools.get_tool_schemas(), indent=2)
        structure_info = json.dumps(repo_structure, indent=2)
        
        return f"""You are an AI coding assistant that helps complete programming tasks by analyzing and modifying code repositories through GitHub.

OBJECTIVE: {objective}

WORKING BRANCH: {self.branch_name}
You are working on a dedicated branch, so all changes will be isolated from the main branch.

REPOSITORY STRUCTURE:
{structure_info}

AVAILABLE TOOLS:
You have access to the following tools to interact with the repository:
{tools_info}

INSTRUCTIONS:
1. Start by exploring the repository structure using get_directory
2. Read relevant files to understand the codebase
3. Make necessary changes to complete the objective
4. Use change_dir to navigate between directories
5. Always use update_file to save your changes (they will be committed to the branch: {self.branch_name})
6. Think step by step and explain your reasoning
7. When you're finished, clearly state that the task is complete

TOOL USAGE:
To use a tool, respond with JSON in this format:
{{"tool": "tool_name", "parameters": {{"param": "value"}}}}

Continue working until the objective is completed. Be thorough and methodical in your approach."""

    def call_openai(self, messages: List[Dict[str, str]]) -> str:
        """
        Make a call to OpenAI API
        """
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling OpenAI API: {str(e)}"
    
    def parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse tool call from AI response
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
        Execute the given objective using the AI assistant
        """
        print(f"Starting AI Assistant for repository: {self.repo_owner}/{self.repo_name}")
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
            print(f"AI Response: {ai_response}")
            
            # Add AI response to history
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            # Check if AI thinks task is complete
            if any(phrase in ai_response.lower() for phrase in [
                "task is complete", "objective is complete", "finished", "done"
            ]):
                print("\n🎉 AI Assistant has completed the task!")
                
                # Create pull request if requested and we created a branch
                pr_url = None
                if create_pr and branch_created:
                    print("Creating pull request...")
                    default_branch = self.github_client.get_default_branch(
                        self.repo_owner, self.repo_name
                    )
                    pr_title = f"AI Assistant: {objective}"
                    pr_body = f"""This pull request was created by the AI Assistant.

**Objective:** {objective}

**Branch:** {working_branch}
**Iterations:** {iteration}

**AI Summary:**
{ai_response}

Please review the changes before merging."""
                    
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
                    "final_response": ai_response,
                    "iterations": iteration,
                    "branch": working_branch,
                    "pull_request_url": pr_url,
                    "used_main_branch": not branch_created
                }
            
            # Parse and execute tool call
            tool_call = self.parse_tool_call(ai_response)
            
            if tool_call:
                tool_name = tool_call.get("tool")
                parameters = tool_call.get("parameters", {})
                
                print(f"Executing tool: {tool_name} with parameters: {parameters}")
                
                # Execute the tool
                result = self.ai_tools.execute_tool(tool_name, parameters)
                print(f"Tool result: {result}")
                
                # Add tool result to conversation
                result_message = f"Tool execution result: {json.dumps(result, indent=2)}"
                self.conversation_history.append({"role": "user", "content": result_message})
                
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