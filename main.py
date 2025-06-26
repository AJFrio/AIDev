#!/usr/bin/env python3
"""
AI Coding Assistant - GitHub Integration

This script provides an AI-powered coding assistant that can connect to GitHub repositories
and help complete coding tasks using OpenAI's language models.
"""

import argparse
import sys
import logging
from config import Config
from ai_assistant import AIAssistant
from jira_client import JiraClient

def main():
    parser = argparse.ArgumentParser(
        description="AI Coding Assistant with GitHub and Jira Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process specific repository with objective
  python main.py my-repo "Add error handling to the API endpoints"
  python main.py my-repo "Refactor the database connection code" --owner AnotherUser
  python main.py my-repo "Fix the failing tests in test_utils.py" --max-iterations 30
  python main.py my-repo "Add logging" --branch feature/logging --no-pr
  
  # Process all Jira tickets with UseAI label
  python main.py --jira-mode
  
  # Process all Jira tickets with UseAI label without adding comments
  python main.py --jira-mode --no-comments
  
  # Process specific Jira ticket regardless of UseAI label
  python main.py --ticket REP-123
  python main.py --ticket REP-123 --no-comments --no-pr
  
  # Test Jira connection
  python main.py --test-jira
        """
    )
    
    parser.add_argument(
        "repo_name",
        nargs='?',
        help="Name of the GitHub repository (required unless using --jira-mode or --test-jira)"
    )
    
    parser.add_argument(
        "objective",
        nargs='?',
        help="The objective or task for the AI Dev to complete (required unless using --jira-mode or --test-jira)"
    )
    
    parser.add_argument(
        "--owner",
        default=Config.DEFAULT_REPO_OWNER,
        help=f"Repository owner (default: {Config.DEFAULT_REPO_OWNER})"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=100,
        help="Maximum number of iterations for the AI Dev (default: 20)"
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
    
    parser.add_argument(
        "--jira-mode",
        action="store_true",
        help="Process all Jira tickets with UseAI label"
    )
    
    parser.add_argument(
        "--test-jira",
        action="store_true",
        help="Test Jira connection and exit"
    )
    
    parser.add_argument(
        "--azure-tier",
        choices=['auto', 'low', 'high'],
        default='auto',
        help="Select Azure OpenAI tier: 'auto' (prefer high, fallback to low), 'low', or 'high' (default: auto)"
    )
    
    parser.add_argument(
        "--no-comments",
        action="store_true",
        help="Skip adding comments to Jira tickets when in Jira mode"
    )
    
    parser.add_argument(
        "--ticket",
        help="Process specific Jira ticket by key (e.g., REP-123) regardless of UseAI label"
    )
    
    parser.add_argument(
        "--model-provider",
        choices=['openai', 'azure', 'openrouter'],
        default='openai',
        help="Select the model provider: 'openai', 'azure', or 'openrouter' (default: openai)"
    )
    
    parser.add_argument(
        "--openrouter-model",
        help="Specify the model to use with OpenRouter (e.g., 'anthropic/claude-3-opus')"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Handle Jira test mode
    if args.test_jira:
        return test_jira_connection()
    
    # Handle Jira processing mode
    if args.jira_mode:
        return process_jira_tickets(args)
    
    # Handle specific ticket processing mode
    if args.ticket:
        return process_specific_ticket(args)
    
    # Validate required arguments for GitHub mode
    if not args.repo_name or not args.objective:
        print("Error: repo_name and objective are required unless using --jira-mode, --test-jira, or --ticket")
        parser.print_help()
        sys.exit(1)
    
    # Validate required environment variables
    if not Config.GITHUB_TOKEN and not args.github_token:
        print("Error: GitHub token is required. Set GITHUB_TOKEN environment variable or use --github-token")
        sys.exit(1)
    
    # Check for OpenAI configuration with new provider system
    if args.model_provider == 'azure':
        azure_config = Config.get_azure_config(args.azure_tier)
        if azure_config:
            tier_name = azure_config['tier'].upper()
            print(f"✅ Azure OpenAI configured ({tier_name} tier)")
            print(f"   Endpoint: {azure_config['endpoint']}")
            print(f"   Deployment: {azure_config['deployment']}")
        else:
            print("Error: Azure OpenAI configuration not found for the specified tier.")
            sys.exit(1)
    elif args.model_provider == 'openrouter':
        if Config.OPENROUTER_API_KEY:
            print("✅ OpenRouter configured")
            if args.openrouter_model:
                print(f"   Model: {args.openrouter_model}")
            else:
                print("   Model: anthropic/claude-3-haiku (default)")
        else:
            print("Error: OpenRouter configuration not found. Please set OPENROUTER_API_KEY.")
            sys.exit(1)
    else: # Default to OpenAI
        if Config.OPENAI_API_KEY:
            print("✅ OpenAI configured")
        else:
            print("Error: No OpenAI configuration found. Please set OPENAI_API_KEY.")
            sys.exit(1)
    
    # Initialize the AI Dev
    try:
        assistant = AIAssistant(
            repo_owner=args.owner,
            repo_name=args.repo_name,
            github_token=args.github_token,
            branch_name=args.branch,
            objective=args.objective,
            azure_tier=args.azure_tier,
            model_provider=args.model_provider,
            openrouter_model=args.openrouter_model
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

def test_jira_connection():
    """Test Jira connection and display information"""
    try:
        print("🔗 Testing Jira Connection")
        print("=" * 40)
        
        # Check if Jira credentials are configured
        if not all([Config.JIRA_URL, Config.JIRA_USERNAME, Config.JIRA_TOKEN]):
            print("❌ Jira credentials not configured!")
            print("Please set JIRA_URL, JIRA_USERNAME, and JIRA_TOKEN in your .env file")
            return False
        
        # Test connection
        jira_client = JiraClient()
        if jira_client.test_connection():
            print("✅ Jira connection successful!")
            
            # Show some basic info
            tickets = jira_client.get_tickets_with_label("UseAI")
            print(f"📋 Found {len(tickets)} tickets with UseAI label")
            
            if tickets:
                print("\nTickets with UseAI label:")
                for ticket in tickets[:5]:  # Show first 5
                    epic_info = f" (Epic: {ticket['epic_name']})" if ticket['epic_name'] else ""
                    print(f"  • {ticket['key']}: {ticket['title'][:60]}...{epic_info}")
                
                if len(tickets) > 5:
                    print(f"  ... and {len(tickets) - 5} more")
            
            return True
        else:
            print("❌ Jira connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Jira connection: {str(e)}")
        return False

def process_jira_tickets(args):
    """Process all Jira tickets with UseAI label"""
    try:
        print("🤖 Processing Jira Tickets with UseAI Label")
        print("=" * 50)
        
        # Check if Jira credentials are configured
        if not all([Config.JIRA_URL, Config.JIRA_USERNAME, Config.JIRA_TOKEN]):
            print("❌ Jira credentials not configured!")
            print("Please set JIRA_URL, JIRA_USERNAME, and JIRA_TOKEN in your .env file")
            sys.exit(1)
        
        # Check GitHub credentials
        if not Config.GITHUB_TOKEN and not args.github_token:
            print("❌ GitHub token is required for processing tickets")
            print("Set GITHUB_TOKEN environment variable or use --github-token")
            sys.exit(1)
        
        # Check for OpenAI configuration with new provider system
        if args.model_provider == 'azure':
            azure_config = Config.get_azure_config(args.azure_tier)
            if azure_config:
                tier_name = azure_config['tier'].upper()
                print(f"✅ Using Azure OpenAI ({tier_name} tier) for Jira processing")
            else:
                print("Error: Azure OpenAI configuration not found for the specified tier.")
                sys.exit(1)
        elif args.model_provider == 'openrouter':
            if not Config.OPENROUTER_API_KEY:
                print("Error: OpenRouter configuration not found. Please set OPENROUTER_API_KEY.")
                sys.exit(1)
            print("✅ Using OpenRouter for Jira processing")
        else: # Default to OpenAI
            if not Config.OPENAI_API_KEY:
                print("❌ No OpenAI configuration found.")
                sys.exit(1)
            print("✅ Using OpenAI for Jira processing")
        
        # Initialize Jira client
        jira_client = JiraClient()
        
        # Get tickets to process
        processed_tickets = jira_client.process_useai_tickets()
        
        if not processed_tickets:
            print("✅ No tickets with UseAI label found")
            return True
        
        print(f"📋 Found {len(processed_tickets)} tickets to process")
        
        # Process each ticket
        results = []
        for i, ticket in enumerate(processed_tickets, 1):
            print(f"\n🎯 Processing ticket {i}/{len(processed_tickets)}: {ticket['jira_key']}")
            
            # Get the appropriate owner for this repository
            repo_owner = Config.get_owner_for_repo(ticket['repo'])
            print(f"   Repository: {repo_owner}/{ticket['repo']}")
            
            # Show branch name that will be used
            if args.branch:
                branch_name = args.branch
                print(f"   Branch: {branch_name} (custom)")
            else:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                branch_name = f"ai-dev-{ticket['jira_key']}-{timestamp}"
                print(f"   Branch: {branch_name}")
            
            print(f"   Jira URL: {ticket['jira_url']}")
            
            try:
                # Get the appropriate owner for this repository
                repo_owner = Config.get_owner_for_repo(ticket['repo'])
                
                # Generate branch name with ticket number for Jira mode
                if args.branch:
                    # Use custom branch name if specified
                    branch_name = args.branch
                else:
                    # Generate branch name with ticket key
                    from datetime import datetime
                    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                    branch_name = f"ai-dev-{ticket['jira_key']}-{timestamp}"
                
                # Initialize AI Dev for this ticket
                assistant = AIAssistant(
                    repo_owner=repo_owner,
                    repo_name=ticket['repo'],
                    github_token=args.github_token,
                    branch_name=branch_name,
                    objective=ticket['objective'],
                    azure_tier=args.azure_tier,
                    model_provider=args.model_provider,
                    openrouter_model=args.openrouter_model
                )
                
                # Execute the objective
                result = assistant.execute_objective(
                    objective=ticket['objective'],
                    max_iterations=args.max_iterations,
                    create_pr=not args.no_pr
                )
                
                # Add Jira info to result
                result['jira_key'] = ticket['jira_key']
                result['jira_url'] = ticket['jira_url']
                results.append(result)
                
                # Print result for this ticket
                if result["success"]:
                    print(f"   ✅ SUCCESS! Completed in {result['iterations']} iterations")
                    if result.get('pull_request_url'):
                        print(f"   🔗 Pull Request: {result['pull_request_url']}")
                        
                        # Add comment to Jira ticket with PR link (unless --no-comments is specified)
                        if not args.no_pr and not args.no_comments:  # Only add comment if PR was actually created and comments not disabled
                            print(f"   💬 Adding comment to Jira ticket...")
                            comment_success = jira_client.add_pr_link_comment(
                                ticket_key=ticket['jira_key'],
                                pr_url=result['pull_request_url'],
                                branch_name=branch_name,
                                repo_name=f"{repo_owner}/{ticket['repo']}"
                            )
                            if comment_success:
                                print(f"   ✅ Comment added to Jira ticket")
                            else:
                                print(f"   ⚠️  Failed to add comment to Jira ticket")
                        elif args.no_comments:
                            print(f"   💬 Skipping Jira comment (--no-comments flag)")
                else:
                    print(f"   ❌ FAILED: {result['error']}")
                
            except Exception as e:
                print(f"   ❌ Error processing ticket: {str(e)}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'jira_key': ticket['jira_key'],
                    'jira_url': ticket['jira_url']
                })
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 PROCESSING SUMMARY")
        print("=" * 50)
        
        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]
        
        print(f"Total tickets processed: {len(results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        
        if successful:
            print("\n✅ Successful tickets:")
            for result in successful:
                pr_info = ""
                if result.get('pull_request_url'):
                    pr_info = f" -> {result.get('pull_request_url')}"
                    if not args.no_pr and not args.no_comments:
                        pr_info += " (comment added to Jira)"
                    elif not args.no_pr and args.no_comments:
                        pr_info += " (comment skipped)"
                print(f"  • {result['jira_key']}{pr_info}")
        
        if failed:
            print("\n❌ Failed tickets:")
            for result in failed:
                print(f"  • {result['jira_key']}: {result.get('error', 'Unknown error')}")
        
        return len(failed) == 0  # Return True if all succeeded
        
    except Exception as e:
        print(f"\n❌ Unexpected error processing Jira tickets: {str(e)}")
        return False

def process_specific_ticket(args):
    """Process a specific Jira ticket by key regardless of UseAI label"""
    try:
        print(f"🎯 Processing Specific Jira Ticket: {args.ticket}")
        print("=" * 50)
        
        # Check if Jira credentials are configured
        if not all([Config.JIRA_URL, Config.JIRA_USERNAME, Config.JIRA_TOKEN]):
            print("❌ Jira credentials not configured!")
            print("Please set JIRA_URL, JIRA_USERNAME, and JIRA_TOKEN in your .env file")
            sys.exit(1)
        
        # Check GitHub credentials
        if not Config.GITHUB_TOKEN and not args.github_token:
            print("❌ GitHub token is required for processing tickets")
            print("Set GITHUB_TOKEN environment variable or use --github-token")
            sys.exit(1)
        
        # Check for OpenAI configuration with new provider system
        if args.model_provider == 'azure':
            azure_config = Config.get_azure_config(args.azure_tier)
            if azure_config:
                tier_name = azure_config['tier'].upper()
                print(f"✅ Using Azure OpenAI ({tier_name} tier) for ticket processing")
            else:
                print("Error: Azure OpenAI configuration not found for the specified tier.")
                sys.exit(1)
        elif args.model_provider == 'openrouter':
            if not Config.OPENROUTER_API_KEY:
                print("Error: OpenRouter configuration not found. Please set OPENROUTER_API_KEY.")
                sys.exit(1)
            print("✅ Using OpenRouter for ticket processing")
        else: # Default to OpenAI
            if not Config.OPENAI_API_KEY:
                print("❌ No OpenAI configuration found.")
                sys.exit(1)
            print("✅ Using OpenAI for ticket processing")
        
        # Initialize Jira client
        jira_client = JiraClient()
        
        # Get the specific ticket
        ticket_data = jira_client.get_ticket_by_key(args.ticket)
        
        if not ticket_data:
            print(f"❌ Ticket {args.ticket} not found or not accessible")
            return False
        
        print(f"📋 Found ticket: {ticket_data['key']} - {ticket_data['title']}")
        
        # Create objective from title and description
        objective = f"Title: {ticket_data['title']}"
        if ticket_data['description']:
            objective += f"\n\nDescription: {ticket_data['description']}"
        
        # Get repository name using epic mapping
        repo = Config.get_repo_for_epic(ticket_data['epic_name'])
        
        # Get the appropriate owner for this repository
        repo_owner = Config.get_owner_for_repo(repo)
        print(f"   Repository: {repo_owner}/{repo}")
        
        # Show branch name that will be used
        if args.branch:
            branch_name = args.branch
            print(f"   Branch: {branch_name} (custom)")
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            branch_name = f"ai-dev-{args.ticket}-{timestamp}"
            print(f"   Branch: {branch_name}")
        
        print(f"   Jira URL: {ticket_data['url']}")
        print(f"   Epic: {ticket_data['epic_name'] or 'None'}")
        
        try:
            # Initialize AI Dev for this ticket
            assistant = AIAssistant(
                repo_owner=repo_owner,
                repo_name=repo,
                github_token=args.github_token,
                branch_name=branch_name,
                objective=objective,
                azure_tier=args.azure_tier,
                model_provider=args.model_provider,
                openrouter_model=args.openrouter_model
            )
            
            # Execute the objective
            result = assistant.execute_objective(
                objective=objective,
                max_iterations=args.max_iterations,
                create_pr=not args.no_pr
            )
            
            # Print result
            if result["success"]:
                print(f"\n✅ SUCCESS! Completed in {result['iterations']} iterations")
                if result.get('pull_request_url'):
                    print(f"🔗 Pull Request: {result['pull_request_url']}")
                    
                    # Add comment to Jira ticket with PR link (unless --no-comments is specified)
                    if not args.no_pr and not args.no_comments:
                        print(f"💬 Adding comment to Jira ticket...")
                        comment_success = jira_client.add_pr_link_comment(
                            ticket_key=args.ticket,
                            pr_url=result['pull_request_url'],
                            branch_name=branch_name,
                            repo_name=f"{repo_owner}/{repo}"
                        )
                        if comment_success:
                            print(f"✅ Comment added to Jira ticket")
                        else:
                            print(f"⚠️  Failed to add comment to Jira ticket")
                    elif args.no_comments:
                        print("💬 Skipping Jira comment (--no-comments flag)")
                        
                return True
            else:
                print(f"\n❌ FAILED: {result['error']}")
                return False
                
        except Exception as e:
            print(f"❌ Error processing ticket: {str(e)}")
            return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error processing ticket: {str(e)}")
        return False

if __name__ == "__main__":
    main() 