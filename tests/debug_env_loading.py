#!/usr/bin/env python3
"""
Debug Environment Loading Script

This script helps debug issues with loading environment variables from .env file.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

def debug_env_loading():
    """Debug environment variable loading"""
    
    print("🔍 Environment Variable Debug")
    print("=" * 50)
    
    # Check if .env file exists
    env_file_path = '.env'
    if os.path.exists(env_file_path):
        print(f"✅ Found .env file at: {os.path.abspath(env_file_path)}")
        
        # Read the raw file content
        print(f"\n📄 Raw .env file content:")
        print("-" * 30)
        try:
            with open(env_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    # Show line numbers and raw content
                    print(f"{i:2d}: {repr(line)}")
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
            return
        print("-" * 30)
    else:
        print(f"❌ .env file not found at: {os.path.abspath(env_file_path)}")
        return
    
    # Test loading environment variables
    print(f"\n🔄 Loading environment variables...")
    
    # Load without dotenv first
    print(f"\nBefore load_dotenv():")
    jira_vars_before = {
        'JIRA_URL': os.getenv('JIRA_URL'),
        'JIRA_USERNAME': os.getenv('JIRA_USERNAME'),
        'JIRA_TOKEN': os.getenv('JIRA_TOKEN')
    }
    
    for var, value in jira_vars_before.items():
        if value:
            display_value = value if var != 'JIRA_TOKEN' else f"*{'*' * (len(value) - 2)}*"
            print(f"  {var}: {display_value}")
        else:
            print(f"  {var}: None")
    
    # Load with dotenv
    load_result = load_dotenv()
    print(f"\nload_dotenv() result: {load_result}")
    
    print(f"\nAfter load_dotenv():")
    jira_vars_after = {
        'JIRA_URL': os.getenv('JIRA_URL'),
        'JIRA_USERNAME': os.getenv('JIRA_USERNAME'),
        'JIRA_TOKEN': os.getenv('JIRA_TOKEN')
    }
    
    for var, value in jira_vars_after.items():
        if value:
            display_value = value if var != 'JIRA_TOKEN' else f"*{'*' * (len(value) - 2)}*"
            print(f"  {var}: {display_value}")
            print(f"    Length: {len(value)} characters")
            print(f"    Raw: {repr(value)}")
        else:
            print(f"  {var}: None")
    
    # Test manual parsing
    print(f"\n🔧 Manual .env parsing test:")
    print("-" * 30)
    
    try:
        with open(env_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value_unquoted = value[1:-1]
                        print(f"Line {line_num}: {key}")
                        print(f"  Raw value: {repr(value)}")
                        print(f"  Unquoted: {repr(value_unquoted)}")
                        print(f"  Length: {len(value_unquoted)}")
                    else:
                        print(f"Line {line_num}: {key}")
                        print(f"  Value: {repr(value)}")
                        print(f"  Length: {len(value)}")
                    print()
    except Exception as e:
        print(f"❌ Error in manual parsing: {e}")
    
    # Recommendations
    print("💡 Recommendations:")
    print("-" * 30)
    
    if not jira_vars_after['JIRA_TOKEN']:
        print("❌ JIRA_TOKEN is still not loaded. Possible issues:")
        print("  1. Remove quotes around the token value in .env")
        print("  2. Ensure no extra spaces around the = sign")
        print("  3. Make sure the line doesn't have Windows line endings (\\r\\n)")
        print("  4. Try putting the JIRA_TOKEN line at the end of the .env file")
        print("\n📝 Correct format:")
        print("JIRA_TOKEN=your_actual_token_without_quotes")
    else:
        print("✅ JIRA_TOKEN loaded successfully!")
        
    # Show recommended .env format
    print(f"\n📋 Recommended .env format:")
    print("# No quotes around values")
    print("JIRA_URL=https://your-company.atlassian.net")
    print("JIRA_USERNAME=your_email@company.com")
    print("JIRA_TOKEN=your_jira_api_token_here")

def main():
    debug_env_loading()

if __name__ == "__main__":
    main() 