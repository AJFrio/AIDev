#!/usr/bin/env python3
"""
AI Coding Assistant - GitHub Integration

This script provides an AI-powered coding assistant that can connect to GitHub repositories
and help complete coding tasks using OpenAI's language models.
"""

import argparse
import sys
from config import Config
from ai_assistant import AIAssistant

def main():
    parser = argparse.ArgumentParser(
        description="AI Coding Assistant with GitHub Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py my-repo "Add error handling to the API endpoints"
  python main.py my-repo "Refactor the database connection code" --owner AnotherUser
  python main.py my-repo "Fix the failing tests in test_utils.py" --max-iterations 30
  python main.py my-repo "Add logging" --branch feature/logging --no-pr
        """
    )
    
    parser.add_argument(
        "repo_name",
        help="Name of the GitHub repository"
    )
    
    parser.add_argument(
        "objective",
        help="The objective or task for the AI assistant to complete"
    )
    
    parser.add_argument(
        "--owner",
        default=Config.DEFAULT_REPO_OWNER,
        help=f"Repository owner (default: {Config.DEFAULT_REPO_OWNER})"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=20,
        help="Maximum number of iterations for the AI assistant (default: 20)"
    )
    
    parser.add_argument(
        "--github-token",
        help="GitHub personal access token (overrides environment variable)"
    )
    
    parser.add_argument(
        "--branch",
        help="Custom branch name (default: auto-generated with timestamp)"
    )
    
    parser.add_argument(
        "--no-pr",
        action="store_true",
        help="Skip creating a pull request when finished"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Validate required environment variables
    if not Config.GITHUB_TOKEN and not args.github_token:
        print("Error: GitHub token is required. Set GITHUB_TOKEN environment variable or use --github-token")
        sys.exit(1)
    
    if not Config.OPENAI_API_KEY:
        print("Error: OpenAI API key is required. Set OPENAI_API_KEY environment variable")
        sys.exit(1)
    
    # Initialize the AI assistant
    try:
        assistant = AIAssistant(
            repo_owner=args.owner,
            repo_name=args.repo_name,
            github_token=args.github_token,
            branch_name=args.branch
        )
        
        print("🤖 AI Coding Assistant")
        print("=" * 50)
        print(f"Repository: {args.owner}/{args.repo_name}")
        print(f"Objective: {args.objective}")
        print(f"Branch: {assistant.branch_name}")
        print(f"Max Iterations: {args.max_iterations}")
        print(f"Create PR: {'No' if args.no_pr else 'Yes'}")
        print("=" * 50)
        
        # Execute the objective
        result = assistant.execute_objective(
            objective=args.objective,
            max_iterations=args.max_iterations,
            create_pr=not args.no_pr
        )
        
        # Print results
        if result["success"]:
            print("\n✅ SUCCESS!")
            print(f"Task completed in {result['iterations']} iterations")
            print(f"Branch: {result['branch']}")
            
            if result.get('pull_request_url'):
                print(f"Pull Request: {result['pull_request_url']}")
            
            if args.verbose:
                print("\nFinal Response:")
                print(result["final_response"])
        else:
            print("\n❌ FAILED!")
            print(f"Error: {result['error']}")
            if result.get('branch'):
                print(f"Work was saved on branch: {result['branch']}")
            
        # Show conversation summary if verbose
        if args.verbose:
            print("\n" + assistant.get_conversation_summary())
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 