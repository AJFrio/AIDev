#!/usr/bin/env python3
"""
Example script showing how to use the Jira integration
"""

from config import Config
from jira_client import JiraClient

def main():
    print("🔗 Jira Integration Example")
    print("=" * 40)
    
    try:
        # Check if Jira is configured
        if not all([Config.JIRA_URL, Config.JIRA_USERNAME, Config.JIRA_TOKEN]):
            print("❌ Jira not configured. Please set up your .env file with:")
            print("  JIRA_URL=https://your-company.atlassian.net")
            print("  JIRA_USERNAME=your_email@company.com")
            print("  JIRA_TOKEN=your_jira_api_token")
            return
        
        # Initialize Jira client
        jira_client = JiraClient()
        
        # Test connection
        print("Testing Jira connection...")
        if not jira_client.test_connection():
            print("❌ Failed to connect to Jira")
            return
        
        print("✅ Connected to Jira successfully!")
        
        # Get tickets with UseAI label
        print("\nSearching for tickets with 'UseAI' label...")
        tickets = jira_client.get_tickets_with_label("UseAI")
        
        if not tickets:
            print("No tickets found with 'UseAI' label")
            print("\nTo test this:")
            print("1. Create a ticket in Jira")
            print("2. Add the label 'UseAI' to it")
            print("3. Run this script again")
        else:
            print(f"Found {len(tickets)} tickets:")
            for ticket in tickets:
                print(f"\n📋 {ticket['key']}: {ticket['title']}")
                print(f"   Epic: {ticket['epic_name'] or 'None'}")
                print(f"   Status: {ticket['status']}")
                print(f"   URL: {ticket['url']}")
        
        # Process tickets for AI automation
        print("\n" + "=" * 40)
        print("Processing tickets for AI automation...")
        
        processed_tickets = jira_client.process_useai_tickets()
        
        if processed_tickets:
            print(f"✅ Processed {len(processed_tickets)} tickets:")
            for ticket in processed_tickets:
                print(f"\n🎯 {ticket['jira_key']}")
                print(f"   Repo: {ticket['repo']}")
                print(f"   Objective: {ticket['objective'][:100]}...")
        else:
            print("No tickets ready for processing")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main() 