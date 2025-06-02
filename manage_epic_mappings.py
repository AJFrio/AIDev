#!/usr/bin/env python3
"""
Epic to Repository Mapping Manager

This script helps you manage and test epic-to-repository mappings.
"""

from config import Config
from jira_client import JiraClient

def show_current_mappings():
    """Display current epic-to-repo mappings"""
    print("📋 Current Epic-to-Repository Mappings")
    print("=" * 50)
    
    if Config.EPIC_TO_REPO_MAP:
        for i, (epic_name, repo_name) in enumerate(Config.EPIC_TO_REPO_MAP.items(), 1):
            repo_owner = Config.get_owner_for_repo(repo_name)
            print(f"{i:2d}. '{epic_name}' → {repo_owner}/{repo_name}")
    else:
        print("  No mappings configured")
    
    print(f"\n🔧 Default repository for unmapped epics: {Config.get_owner_for_repo(Config.DEFAULT_REPO_NAME)}/{Config.DEFAULT_REPO_NAME}")
    
    print(f"\n📋 Repository-to-Owner Mappings")
    print("-" * 30)
    if Config.REPO_TO_OWNER_MAP:
        for repo_name, owner in Config.REPO_TO_OWNER_MAP.items():
            print(f"  • {repo_name} → {owner}")
    else:
        print("  No custom owner mappings configured")
    print(f"  • [Default] → {Config.DEFAULT_REPO_OWNER}")

def test_epic_mapping(epic_name: str):
    """Test how an epic name would be mapped"""
    repo = Config.get_repo_for_epic(epic_name)
    owner = Config.get_owner_for_repo(repo)
    print(f"\n🎯 Mapping test:")
    print(f"  Epic: '{epic_name}'")
    print(f"  Repository: {owner}/{repo}")
    
    # Show why this mapping was chosen
    if not epic_name:
        print(f"  Reason: Empty epic name, using default")
    elif epic_name in Config.EPIC_TO_REPO_MAP:
        print(f"  Reason: Exact match found")
    else:
        # Check for case-insensitive match
        epic_lower = epic_name.lower()
        for mapped_epic, mapped_repo in Config.EPIC_TO_REPO_MAP.items():
            if mapped_epic.lower() == epic_lower:
                print(f"  Reason: Case-insensitive match with '{mapped_epic}'")
                return
            elif mapped_epic.lower() in epic_lower or epic_lower in mapped_epic.lower():
                print(f"  Reason: Partial match with '{mapped_epic}'")
                return
        
        print(f"  Reason: No match found, using default")

def show_jira_epics_with_mappings():
    """Show actual Jira epics and their current mappings"""
    print("\n🔗 Jira Epics and Their Mappings")
    print("=" * 50)
    
    try:
        # Check if Jira is configured
        if not all([Config.JIRA_URL, Config.JIRA_USERNAME, Config.JIRA_TOKEN]):
            print("❌ Jira not configured. Cannot fetch epic information.")
            return
        
        jira_client = JiraClient()
        epics = jira_client.get_all_epics()
        
        if not epics:
            print("ℹ️  No epics found in Jira")
            return
        
        print(f"Found {len(epics)} epics in Jira:")
        print()
        
        for i, epic in enumerate(epics, 1):
            mapped_repo = Config.get_repo_for_epic(epic['name'])
            mapped_owner = Config.get_owner_for_repo(mapped_repo)
            
            # Show if it's mapped or using default
            if epic['name'] in Config.EPIC_TO_REPO_MAP:
                status = "✅ Mapped"
            elif mapped_repo != Config.DEFAULT_REPO_NAME:
                status = "🔄 Partial match"
            else:
                status = "⚠️  Using default"
            
            print(f"{i:2d}. {status}")
            print(f"    Epic: {epic['key']} - {epic['name']}")
            print(f"    Status: {epic['status']}")
            print(f"    Repository: {mapped_owner}/{mapped_repo}")
            print()
        
    except Exception as e:
        print(f"❌ Error fetching Jira epics: {str(e)}")

def suggest_mappings():
    """Suggest epic mappings based on Jira data"""
    print("\n💡 Mapping Suggestions")
    print("=" * 50)
    
    try:
        if not all([Config.JIRA_URL, Config.JIRA_USERNAME, Config.JIRA_TOKEN]):
            print("❌ Jira not configured. Cannot provide suggestions.")
            return
        
        jira_client = JiraClient()
        epics = jira_client.get_all_epics()
        
        unmapped_epics = []
        for epic in epics:
            if epic['name'] not in Config.EPIC_TO_REPO_MAP:
                unmapped_epics.append(epic)
        
        if not unmapped_epics:
            print("✅ All epics are already mapped!")
            return
        
        print("📝 Add these mappings to config.py:")
        print()
        print("# Add to EPIC_TO_REPO_MAP in config.py:")
        for epic in unmapped_epics:
            # Suggest a repository name based on epic name
            suggested_repo = epic['name'].lower().replace(' ', '-').replace('_', '-')
            print(f"'{epic['name']}': '{suggested_repo}',")
        
    except Exception as e:
        print(f"❌ Error generating suggestions: {str(e)}")

def main():
    """Main function"""
    print("🎯 Epic-to-Repository Mapping Manager")
    print("=" * 60)
    
    # Show current mappings
    show_current_mappings()
    
    # Test some example mappings
    print("\n🧪 Testing Example Mappings")
    print("-" * 30)
    
    test_cases = [
        "User Management System",  # Should match exactly
        "user management system",  # Should match case-insensitive
        "E-commerce",              # Should partial match "E-commerce Platform"
        "Unknown Epic",            # Should use default
        "",                        # Should use default
    ]
    
    for test_case in test_cases:
        test_epic_mapping(test_case)
    
    # Show actual Jira epics if possible
    show_jira_epics_with_mappings()
    
    # Suggest new mappings
    suggest_mappings()
    
    print("\n📝 How to Add New Mappings:")
    print("=" * 40)
    print("1. Edit config.py")
    print("2. Add entries to the EPIC_TO_REPO_MAP dictionary:")
    print("   'Your Epic Name': 'your-repository-name',")
    print("3. Save the file")
    print("4. Run this script again to verify")

if __name__ == "__main__":
    main() 