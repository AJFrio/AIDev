#!/usr/bin/env python3
"""
Test Jira Comment Functionality

This script tests the ability to add comments to Jira tickets.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from jira_client import JiraClient

def test_jira_comments():
    """Test adding comments to Jira tickets"""
    
    print("💬 Jira Comment Functionality Test")
    print("=" * 50)
    
    # Check if Jira is configured
    if not all([Config.JIRA_URL, Config.JIRA_USERNAME, Config.JIRA_TOKEN]):
        print("❌ Jira not configured. Please set up your .env file.")
        return False
    
    try:
        # Initialize Jira client
        jira_client = JiraClient()
        
        # Test connection first
        if not jira_client.test_connection():
            print("❌ Failed to connect to Jira")
            return False
        
        print("✅ Connected to Jira successfully!")
        
        # Get some tickets to test with
        print("\n🔍 Looking for existing tickets to test comments...")
        tickets = jira_client.get_tickets_with_label("UseAI")
        
        if not tickets:
            print("ℹ️  No tickets with 'UseAI' label found for testing")
            print("\n💡 To test comment functionality:")
            print("1. Create a ticket in Jira")
            print("2. Add the 'UseAI' label")
            print("3. Run this test again")
            return True
        
        # Show available tickets
        print(f"📋 Found {len(tickets)} tickets with 'UseAI' label:")
        for i, ticket in enumerate(tickets, 1):
            print(f"{i:2d}. {ticket['key']}: {ticket['title']}")
        
        # Test comment formatting
        print(f"\n📝 Example comment that would be added:")
        print("-" * 40)
        
        sample_comment = f"""🤖 *AI Dev Update*

✅ *Pull Request Created*
• Repository: repfitness/threejs-builder
• Branch: ai-dev-REP-123-20241201-143022
• Pull Request: https://github.com/repfitness/threejs-builder/pull/42

The AI Dev has completed the automated work for this ticket. Please review the pull request and merge when ready."""
        
        print(sample_comment)
        print("-" * 40)
        
        # Ask if user wants to test adding a comment
        print(f"\n🧪 Test Options:")
        print("1. Run this with --test-comment TICKET-KEY to actually add a test comment")
        print("2. Or use the real Jira processing with: python main.py --jira-mode")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Jira comments: {str(e)}")
        return False

def add_test_comment(ticket_key: str):
    """Add a test comment to a specific ticket"""
    
    print(f"💬 Adding Test Comment to {ticket_key}")
    print("=" * 50)
    
    try:
        jira_client = JiraClient()
        
        # Add a test comment
        test_comment = f"""🧪 *Test Comment from AI Dev*

This is a test comment to verify the commenting functionality is working correctly.

Timestamp: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If you can see this comment, the integration is working! 🎉"""

        success = jira_client.add_comment_to_ticket(ticket_key, test_comment)
        
        if success:
            print(f"✅ Test comment successfully added to {ticket_key}")
            print(f"🔗 Check the ticket: {Config.JIRA_URL}/browse/{ticket_key}")
        else:
            print(f"❌ Failed to add test comment to {ticket_key}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error adding test comment: {str(e)}")
        return False

def main():
    """Main function"""
    
    # Check for test comment mode
    if len(sys.argv) == 3 and sys.argv[1] == "--test-comment":
        ticket_key = sys.argv[2]
        add_test_comment(ticket_key)
    else:
        test_jira_comments()
        
        if len(sys.argv) > 1:
            print(f"\n❓ Usage for testing comments:")
            print(f"  python test_jira_comments.py --test-comment TICKET-KEY")
            print(f"  Example: python test_jira_comments.py --test-comment REP-123")

if __name__ == "__main__":
    main() 