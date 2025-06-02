#!/usr/bin/env python3
"""
Test Jira Connection Script

This script helps test the Jira connection and displays available tickets
with the UseAI label.
"""

import sys
import logging
from config import Config
from jira_client import JiraClient

def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🔗 Jira Connection Test")
    print("=" * 40)
    
    try:
        # Check if Jira credentials are configured
        print("Checking Jira configuration...")
        
        if not Config.JIRA_URL:
            print("❌ JIRA_URL not set in environment")
        else:
            print(f"✅ JIRA_URL: {Config.JIRA_URL}")
        
        if not Config.JIRA_USERNAME:
            print("❌ JIRA_USERNAME not set in environment")
        else:
            print(f"✅ JIRA_USERNAME: {Config.JIRA_USERNAME}")
        
        if not Config.JIRA_TOKEN:
            print("❌ JIRA_TOKEN not set in environment")
        else:
            print(f"✅ JIRA_TOKEN: {'*' * len(Config.JIRA_TOKEN)}")
        
        if not all([Config.JIRA_URL, Config.JIRA_USERNAME, Config.JIRA_TOKEN]):
            print("\n❌ Missing Jira credentials. Please check your .env file.")
            print("Required variables:")
            print("  - JIRA_URL=https://your-company.atlassian.net")
            print("  - JIRA_USERNAME=your_email@company.com")
            print("  - JIRA_TOKEN=your_jira_api_token")
            sys.exit(1)
        
        print("\n🔌 Testing connection...")
        
        # Initialize Jira client
        jira_client = JiraClient()
        
        # Test connection
        if jira_client.test_connection():
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
            sys.exit(1)
        
        print("\n📋 Searching for UseAI tickets...")
        
        # Get tickets with UseAI label
        tickets = jira_client.get_tickets_with_label("UseAI")
        
        if not tickets:
            print("ℹ️  No tickets found with 'UseAI' label")
            print("\nTo test this functionality:")
            print("1. Create a ticket in Jira")
            print("2. Add the label 'UseAI' to the ticket")
            print("3. Run this test again")
        else:
            print(f"✅ Found {len(tickets)} tickets with 'UseAI' label:")
            print()
            
            for i, ticket in enumerate(tickets, 1):
                print(f"{i}. {ticket['key']}: {ticket['title']}")
                print(f"   Status: {ticket['status']}")
                print(f"   Type: {ticket['issue_type']}")
                if ticket['epic_name']:
                    print(f"   Epic: {ticket['epic_name']} ({ticket['epic_key']})")
                else:
                    print(f"   Epic: Not linked")
                print(f"   URL: {ticket['url']}")
                if ticket['description']:
                    desc_preview = ticket['description'][:100]
                    if len(ticket['description']) > 100:
                        desc_preview += "..."
                    print(f"   Description: {desc_preview}")
                print()
        
        print("\n🎯 Testing ticket processing...")
        
        # Test the processing functionality
        processed_tickets = jira_client.process_useai_tickets()
        
        if processed_tickets:
            print(f"✅ Successfully processed {len(processed_tickets)} tickets for AI automation")
            print("\nProcessed tickets:")
            
            for i, ticket in enumerate(processed_tickets, 1):
                print(f"{i}. {ticket['jira_key']}")
                print(f"   Repo: {ticket['repo']}")
                print(f"   Objective: {ticket['objective'][:100]}{'...' if len(ticket['objective']) > 100 else ''}")
                print()
        else:
            print("ℹ️  No tickets ready for processing")
        
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        logging.exception("Full error details:")
        sys.exit(1)

if __name__ == "__main__":
    main() 