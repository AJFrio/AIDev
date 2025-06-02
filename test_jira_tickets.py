#!/usr/bin/env python3
"""
Jira Ticket Test Script

This script tests the Jira connection and displays all tickets with the UseAI label
in a detailed, readable format.
"""

import sys
import logging
from datetime import datetime
from config import Config
from jira_client import JiraClient

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n🔹 {title}")
    print("-" * 40)

def format_date(date_str):
    """Format ISO date string to readable format"""
    try:
        if date_str:
            # Parse ISO format and convert to readable format
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        pass
    return date_str or "N/A"

def print_ticket_details(ticket, index):
    """Print detailed ticket information"""
    print(f"\n📋 Ticket #{index}: {ticket['key']}")
    print("─" * 50)
    print(f"Title:       {ticket['title']}")
    print(f"Status:      {ticket['status']}")
    print(f"Type:        {ticket['issue_type']}")
    print(f"Assignee:    {ticket['assignee'] or 'Unassigned'}")
    print(f"Reporter:    {ticket['reporter'] or 'Unknown'}")
    print(f"Created:     {format_date(ticket['created'])}")
    print(f"Updated:     {format_date(ticket['updated'])}")
    
    # Epic information
    if ticket['epic_name']:
        print(f"Epic:        {ticket['epic_name']} ({ticket['epic_key']})")
    else:
        print(f"Epic:        Not linked to any epic")
    
    # Labels
    if ticket['labels']:
        labels_str = ", ".join(ticket['labels'])
        print(f"Labels:      {labels_str}")
    else:
        print(f"Labels:      None")
    
    # Description
    if ticket['description'] and ticket['description'].strip():
        desc = ticket['description'].strip()
        # Show first 200 characters
        if len(desc) > 200:
            desc_preview = desc[:200] + "..."
        else:
            desc_preview = desc
        print(f"Description: {desc_preview}")
    else:
        print(f"Description: No description provided")
    
    print(f"URL:         {ticket['url']}")

def test_jira_connection_and_tickets():
    """Main function to test Jira and display tickets"""
    
    print_header("🔗 JIRA CONNECTION & TICKETS TEST")
    
    # Check configuration
    print_section("Configuration Check")
    
    config_items = [
        ("JIRA_URL", Config.JIRA_URL),
        ("JIRA_USERNAME", Config.JIRA_USERNAME),
        ("JIRA_TOKEN", Config.JIRA_TOKEN)
    ]
    
    missing_config = []
    for name, value in config_items:
        if value:
            # Mask the token for security
            display_value = value if name != "JIRA_TOKEN" else "*" * len(value)
            print(f"✅ {name}: {display_value}")
        else:
            print(f"❌ {name}: Not configured")
            missing_config.append(name)
    
    if missing_config:
        print(f"\n❌ Missing configuration: {', '.join(missing_config)}")
        print("\nPlease add these to your .env file:")
        print("JIRA_URL=https://your-company.atlassian.net")
        print("JIRA_USERNAME=your_email@company.com")
        print("JIRA_TOKEN=your_jira_api_token")
        return False
    
    # Test connection
    print_section("Connection Test")
    
    try:
        jira_client = JiraClient()
        
        if jira_client.test_connection():
            print("✅ Successfully connected to Jira!")
        else:
            print("❌ Failed to connect to Jira")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False
    
    # Get user information
    try:
        user_info = jira_client.jira.myself()
        print(f"👤 Logged in as: {user_info['displayName']} ({user_info['emailAddress']})")
    except Exception as e:
        print(f"⚠️  Could not get user info: {str(e)}")
    
    # Search for UseAI tickets
    print_section("Searching for UseAI Tickets")
    
    try:
        tickets = jira_client.get_tickets_with_label("UseAI")
        
        if not tickets:
            print("ℹ️  No tickets found with 'UseAI' label")
            print("\n💡 To test this functionality:")
            print("1. Go to your Jira instance")
            print("2. Create a new ticket (any type)")
            print("3. Add the label 'UseAI' to the ticket")
            print("4. Optionally link it to an Epic")
            print("5. Run this script again")
            return True
        
        print(f"🎉 Found {len(tickets)} tickets with 'UseAI' label!")
        
        # Display summary first
        print_section("Tickets Summary")
        for i, ticket in enumerate(tickets, 1):
            epic_info = f" → {ticket['epic_name']}" if ticket['epic_name'] else " → No Epic"
            print(f"{i:2d}. {ticket['key']} - {ticket['status']}{epic_info}")
        
        # Display detailed information for each ticket
        print_section("Detailed Ticket Information")
        for i, ticket in enumerate(tickets, 1):
            print_ticket_details(ticket, i)
        
        # Test processing functionality
        print_section("AI Processing Test")
        
        processed_tickets = jira_client.process_useai_tickets()
        
        if processed_tickets:
            print(f"✅ Successfully processed {len(processed_tickets)} tickets for AI automation")
            print("\n🎯 Processed tickets ready for AI:")
            
            for i, ticket in enumerate(processed_tickets, 1):
                print(f"\n{i}. {ticket['jira_key']}")
                
                # Show repository with owner
                repo_owner = Config.get_owner_for_repo(ticket['repo'])
                print(f"   Repository: {repo_owner}/{ticket['repo']}")
                print(f"   Epic Key: {ticket['epic_key'] or 'None'}")
                
                # Show branch name that would be generated
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                branch_name = f"ai-dev-{ticket['jira_key']}-{timestamp}"
                print(f"   Branch: {branch_name}")
                
                print(f"   Objective Length: {len(ticket['objective'])} characters")
                
                # Show objective preview
                objective_preview = ticket['objective'][:150]
                if len(ticket['objective']) > 150:
                    objective_preview += "..."
                print(f"   Objective Preview: {objective_preview}")
        else:
            print("ℹ️  No tickets ready for AI processing")
        
                 # Show epics information and mapping
        print_section("Epic to Repository Mapping")
        
        print("📋 Current epic-to-repo mappings:")
        for epic_name, repo_name in Config.EPIC_TO_REPO_MAP.items():
            print(f"  • '{epic_name}' → {repo_name}")
        print(f"  • [Default for unmapped epics] → {Config.DEFAULT_REPO_NAME}")
        
        print_section("Available Epics")
        
        try:
            epics = jira_client.get_all_epics()
            if epics:
                print(f"📊 Found {len(epics)} epics in the project:")
                for i, epic in enumerate(epics, 1):
                    mapped_repo = Config.get_repo_for_epic(epic['name'])
                    mapping_info = f" → {mapped_repo}"
                    print(f"{i:2d}. {epic['key']}: {epic['name']} ({epic['status']}){mapping_info}")
            else:
                print("ℹ️  No epics found in the project")
        except Exception as e:
            print(f"⚠️  Could not fetch epics: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error searching for tickets: {str(e)}")
        logging.exception("Full error details:")
        return False

def main():
    """Main entry point"""
    
    # Set up logging for debugging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        success = test_jira_connection_and_tickets()
        
        print_header("🏁 TEST COMPLETE")
        
        if success:
            print("🎉 All tests completed successfully!")
            print("\nNext steps:")
            print("• Use 'python main.py --jira-mode' to process UseAI tickets")
            print("• Use 'python main.py --test-jira' for a quick connection test")
        else:
            print("❌ Some tests failed. Please check the error messages above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        logging.exception("Full error details:")
        sys.exit(1)

if __name__ == "__main__":
    main() 