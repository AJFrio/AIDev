#!/usr/bin/env python3
"""
Example test script for the AI Coding Assistant

This script demonstrates how to use the AI assistant programmatically
and provides a simple test case.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_assistant import AIAssistant
from config import Config

def test_repository_connection():
    """Test basic repository connection"""
    print("Testing GitHub repository connection...")
    
    # You can test with any public repository
    test_repo_owner = "AJFrio"  # GitHub's mascot account
    test_repo_name = "Wholesale-Builder"  # Simple test repository
    
    try:
        assistant = AIAssistant(test_repo_owner, test_repo_name)
        
        # Test getting repository structure
        repo_structure = assistant.github_client.get_repository_structure(
            test_repo_owner, test_repo_name
        )
        
        if repo_structure:
            print("✅ Successfully connected to GitHub!")
            print(f"Found {len(repo_structure)} items in the repository:")
            for item in repo_structure:  # Show first 5 items
                print(f"  - {item['name']} ({item['type']})")
            return True
        else:
            print("❌ Failed to fetch repository structure")
            return False
            
    except Exception as e:
        print(f"❌ Error testing repository connection: {e}")
        return False

def test_file_reading():
    """Test reading a file from repository"""
    print("\nTesting file reading...")
    
    test_repo_owner = "AJFrio"
    test_repo_name = "Wholesale-Builder"
    
    try:
        assistant = AIAssistant(test_repo_owner, test_repo_name)
        
        # Try to read README file
        content = assistant.github_client.get_file_content(
            test_repo_owner, test_repo_name, "README.md"
        )
        
        if content:
            print("✅ Successfully read file!")
            print("File content preview:")
            print("-" * 30)
            print(content[:200] + "..." if len(content) > 200 else content)
            print("-" * 30)
            return True
        else:
            print("❌ Failed to read file")
            return False
            
    except Exception as e:
        print(f"❌ Error testing file reading: {e}")
        return False

def run_simple_objective():
    """Run a simple objective on a test repository"""
    print("\nRunning simple objective test...")
    
    # Note: This would only work on a repository you have write access to
    # For testing purposes, we'll just simulate the planning phase
    
    test_repo_owner = "AJFrio"  # Change this to your username
    test_repo_name = "Wholesale-Builder"  # Change this to a test repository you own
    objective = "Analyze the repository structure and provide a summary"
    
    try:
        assistant = AIAssistant(test_repo_owner, test_repo_name)
        
        print(f"Repository: {test_repo_owner}/{test_repo_name}")
        print(f"Objective: {objective}")
        
        # Get repository structure for analysis
        repo_structure = assistant.github_client.get_repository_structure(
            test_repo_owner, test_repo_name
        )
        
        if repo_structure:
            print("✅ Repository analysis successful!")
            print(f"Repository contains {len(repo_structure)} items")
            
            # Categorize items
            files = [item for item in repo_structure if item['type'] == 'file']
            dirs = [item for item in repo_structure if item['type'] == 'dir']
            
            print(f"  - Files: {len(files)}")
            print(f"  - Directories: {len(dirs)}")
            
            if files:
                print("  File types found:")
                extensions = {}
                for file_item in files:
                    name = file_item['name']
                    if '.' in name:
                        ext = name.split('.')[-1].lower()
                        extensions[ext] = extensions.get(ext, 0) + 1
                
                for ext, count in extensions.items():
                    print(f"    .{ext}: {count} files")
            
            return True
        else:
            print("❌ Could not access repository")
            return False
            
    except Exception as e:
        print(f"❌ Error running objective test: {e}")
        return False

def main():
    """Run all tests"""
    print("🤖 AI Coding Assistant - Test Suite")
    print("=" * 50)
    
    # Check configuration
    if not Config.GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN not found in environment variables")
        print("Please set up your .env file with your GitHub token")
        return
    
    if not Config.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set up your .env file with your OpenAI API key")
        return
    
    print("✅ Configuration loaded successfully")
    
    # Run tests
    tests = [
        ("Repository Connection", test_repository_connection),
        ("File Reading", test_file_reading),
        ("Simple Objective", run_simple_objective)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running test: {test_name}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    # Summary
    print(f"\n🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The AI assistant is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check your configuration and network connection.")

if __name__ == "__main__":
    main() 