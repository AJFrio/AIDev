#!/usr/bin/env python3
"""
Test Branch Naming for Jira Mode

This script demonstrates how branch names are generated in Jira mode.
"""

from datetime import datetime

def test_branch_naming():
    """Test the branch naming logic for Jira tickets"""
    
    print("🌿 Branch Naming Test for Jira Mode")
    print("=" * 50)
    
    # Sample Jira tickets
    sample_tickets = [
        {'jira_key': 'REP-123', 'title': 'Fix login bug'},
        {'jira_key': 'REP-456', 'title': 'Add new feature'},
        {'jira_key': 'ERP-789', 'title': 'Update database schema'},
    ]
    
    print("🎯 Auto-generated branch names (default behavior):")
    print("-" * 30)
    
    for i, ticket in enumerate(sample_tickets, 1):
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        branch_name = f"ai-dev-{ticket['jira_key']}-{timestamp}"
        print(f"{i}. Ticket: {ticket['jira_key']}")
        print(f"   Title: {ticket['title']}")
        print(f"   Branch: {branch_name}")
        print()
    
    print("🎯 Custom branch name (when using --branch flag):")
    print("-" * 30)
    custom_branch = "feature/jira-automation"
    print(f"All tickets would use: {custom_branch}")
    print()
    
    print("💡 Benefits of ticket-specific branch names:")
    print("-" * 30)
    print("✅ Easy to identify which branch belongs to which ticket")
    print("✅ Better traceability between Jira and GitHub")
    print("✅ Prevents branch name conflicts when processing multiple tickets")
    print("✅ Includes timestamp for uniqueness")
    print()
    
    print("📝 Branch naming format:")
    print("-" * 30)
    print("Format: ai-dev-{TICKET-KEY}-{YYYYMMDD-HHMMSS}")
    print("Example: ai-dev-REP-123-20241201-143022")

if __name__ == "__main__":
    test_branch_naming() 