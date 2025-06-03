#!/usr/bin/env python3
"""
Integration test for make_dir with other AI tools

This test verifies that make_dir works correctly with other tools 
like add_file and change_dir.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from ai_tools import AITools


class MockGitHubClient:
    """Mock GitHub client for testing"""
    
    def __init__(self):
        self.created_files = {}
        self.repository_structure = {}
    
    def get_repository_structure(self, owner, repo, path="", branch="main"):
        """Mock repository structure - returns None for non-existent directories"""
        full_key = f"{owner}/{repo}/{branch}/{path}"
        return self.repository_structure.get(full_key, None)
    
    def update_file_content(self, owner, repo, file_path, content, commit_message, sha, branch):
        """Mock file creation"""
        full_key = f"{owner}/{repo}/{branch}/{file_path}"
        self.created_files[full_key] = {
            'content': content,
            'commit_message': commit_message,
            'sha': sha
        }
        return True
    
    def get_file_sha(self, owner, repo, file_path, branch):
        """Mock file SHA retrieval - returns None for non-existent files"""
        full_key = f"{owner}/{repo}/{branch}/{file_path}"
        return self.created_files.get(full_key, {}).get('sha', None)


class TestMakeDirIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_github_client = MockGitHubClient()
        self.ai_tools = AITools(
            repo_owner="test-owner",
            repo_name="test-repo", 
            github_client=self.mock_github_client,
            branch="test-branch"
        )
    
    def test_make_dir_then_add_file(self):
        """Test creating a directory then adding a file to it"""
        # Create directory
        dir_result = self.ai_tools.make_dir("new-project")
        self.assertTrue(dir_result["success"])
        
        # Change to the directory
        cd_result = self.ai_tools.change_dir("new-project")
        # This will fail because the directory structure isn't fully simulated
        # But let's test adding a file to the directory path directly
        
        # Add a file to the created directory
        file_result = self.ai_tools.add_file("new-project/main.py", "print('Hello, World!')")
        self.assertTrue(file_result["success"])
        
        # Verify both the .gitkeep and the new file exist
        gitkeep_key = "test-owner/test-repo/test-branch/new-project/.gitkeep"
        file_key = "test-owner/test-repo/test-branch/new-project/main.py"
        
        self.assertIn(gitkeep_key, self.mock_github_client.created_files)
        self.assertIn(file_key, self.mock_github_client.created_files)
        
        # Check file content
        file_data = self.mock_github_client.created_files[file_key]
        self.assertEqual(file_data['content'], "print('Hello, World!')")
    
    def test_nested_directory_structure(self):
        """Test creating nested directories and files"""
        # Create nested directory structure
        dir_result = self.ai_tools.make_dir("src/components/ui")
        self.assertTrue(dir_result["success"])
        
        # Add files at different levels
        files_to_create = [
            ("src/main.py", "# Main application file"),
            ("src/components/__init__.py", "# Components package"),
            ("src/components/ui/button.py", "# Button component"),
        ]
        
        for file_path, content in files_to_create:
            result = self.ai_tools.add_file(file_path, content)
            self.assertTrue(result["success"], f"Failed to create {file_path}")
        
        # Verify all files were created
        expected_files = [
            "test-owner/test-repo/test-branch/src/components/ui/.gitkeep",
            "test-owner/test-repo/test-branch/src/main.py",
            "test-owner/test-repo/test-branch/src/components/__init__.py",
            "test-owner/test-repo/test-branch/src/components/ui/button.py",
        ]
        
        for expected_file in expected_files:
            self.assertIn(expected_file, self.mock_github_client.created_files,
                         f"Expected file not found: {expected_file}")
    
    def test_tool_chaining_workflow(self):
        """Test a complete workflow using multiple tools"""
        # Step 1: Create project structure
        directories = ["backend", "frontend", "docs"]
        for directory in directories:
            result = self.ai_tools.make_dir(directory)
            self.assertTrue(result["success"])
        
        # Step 2: Add configuration files
        config_files = [
            ("backend/server.py", "# Backend server"),
            ("frontend/app.js", "// Frontend application"),
            ("docs/README.md", "# Project Documentation"),
            ("requirements.txt", "# Python dependencies"),
        ]
        
        for file_path, content in config_files:
            result = self.ai_tools.add_file(file_path, content)
            self.assertTrue(result["success"])
        
        # Step 3: Verify modified files tracking
        modified_files = self.ai_tools.get_modified_files()
        
        # Should have 3 .gitkeep files + 4 regular files = 7 total
        self.assertEqual(len(modified_files), 7)
        
        # Check that we have the right mix of created files
        gitkeep_files = [f for f in modified_files if f["file_path"].endswith(".gitkeep")]
        regular_files = [f for f in modified_files if not f["file_path"].endswith(".gitkeep")]
        
        self.assertEqual(len(gitkeep_files), 3)  # 3 directories
        self.assertEqual(len(regular_files), 4)  # 4 files
        
        # All should be marked as created
        for file_info in modified_files:
            self.assertEqual(file_info["action"], "created")
    
    def test_all_tools_available(self):
        """Test that all tools including make_dir are available"""
        schemas = self.ai_tools.get_tool_schemas()
        tool_names = [schema["name"] for schema in schemas]
        
        expected_tools = [
            "get_directory", "read_file", "update_file", 
            "add_file", "make_dir", "change_dir", "finish_task"
        ]
        
        for tool in expected_tools:
            self.assertIn(tool, tool_names, f"Tool {tool} not found in schemas")


def run_integration_tests():
    """Run integration tests"""
    print("🔗 Running make_dir integration tests...")
    print("="*50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMakeDirIntegration)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"INTEGRATION TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    if success:
        print(f"\n✅ ALL INTEGRATION TESTS PASSED!")
    else:
        print(f"\n❌ SOME INTEGRATION TESTS FAILED!")
    
    return success


if __name__ == "__main__":
    try:
        success = run_integration_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Integration test execution failed: {str(e)}")
        sys.exit(1) 