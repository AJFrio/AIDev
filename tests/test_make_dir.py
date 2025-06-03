#!/usr/bin/env python3
"""
Test the make_dir functionality of AITools

This test creates a mock GitHub client and tests the make_dir function
to ensure it works correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import Mock, MagicMock
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


class TestMakeDir(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_github_client = MockGitHubClient()
        self.ai_tools = AITools(
            repo_owner="test-owner",
            repo_name="test-repo", 
            github_client=self.mock_github_client,
            branch="test-branch"
        )
    
    def test_make_dir_success(self):
        """Test successful directory creation"""
        result = self.ai_tools.make_dir("new-directory")
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertIn("Successfully created directory new-directory", result["message"])
        self.assertEqual(result["directory_path"], "new-directory")
        self.assertEqual(result["gitkeep_file"], "new-directory/.gitkeep")
        self.assertEqual(result["branch"], "test-branch")
        
        # Check that .gitkeep file was created
        expected_key = "test-owner/test-repo/test-branch/new-directory/.gitkeep"
        self.assertIn(expected_key, self.mock_github_client.created_files)
        
        # Check .gitkeep content
        gitkeep_data = self.mock_github_client.created_files[expected_key]
        self.assertIn("This file keeps the directory in Git", gitkeep_data['content'])
        self.assertEqual(gitkeep_data['commit_message'], "AI Dev: Create directory new-directory")
        
        # Check modified files tracking
        self.assertEqual(len(self.ai_tools.modified_files), 1)
        self.assertEqual(self.ai_tools.modified_files[0]["file_path"], "new-directory/.gitkeep")
        self.assertEqual(self.ai_tools.modified_files[0]["action"], "created")
    
    def test_make_dir_with_current_directory(self):
        """Test directory creation with current directory context"""
        # Set current directory
        self.ai_tools.current_directory = "existing-dir"
        
        result = self.ai_tools.make_dir("sub-directory")
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual(result["directory_path"], "existing-dir/sub-directory")
        self.assertEqual(result["gitkeep_file"], "existing-dir/sub-directory/.gitkeep")
        
        # Check that .gitkeep file was created in the right location
        expected_key = "test-owner/test-repo/test-branch/existing-dir/sub-directory/.gitkeep"
        self.assertIn(expected_key, self.mock_github_client.created_files)
    
    def test_make_dir_already_exists(self):
        """Test directory creation when directory already exists"""
        # Simulate existing directory
        existing_structure = [{"name": "file.txt", "type": "file"}]
        structure_key = "test-owner/test-repo/test-branch/existing-directory"
        self.mock_github_client.repository_structure[structure_key] = existing_structure
        
        result = self.ai_tools.make_dir("existing-directory")
        
        # Check the result
        self.assertFalse(result["success"])
        self.assertIn("Directory already exists: existing-directory", result["error"])
        
        # Check that no files were created
        self.assertEqual(len(self.mock_github_client.created_files), 0)
        self.assertEqual(len(self.ai_tools.modified_files), 0)
    
    def test_make_dir_nested_path(self):
        """Test creating nested directory structure"""
        result = self.ai_tools.make_dir("level1/level2/level3")
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual(result["directory_path"], "level1/level2/level3")
        self.assertEqual(result["gitkeep_file"], "level1/level2/level3/.gitkeep")
        
        # Check that .gitkeep file was created
        expected_key = "test-owner/test-repo/test-branch/level1/level2/level3/.gitkeep"
        self.assertIn(expected_key, self.mock_github_client.created_files)
    
    def test_make_dir_absolute_path(self):
        """Test directory creation with absolute path"""
        self.ai_tools.current_directory = "some-dir"
        
        result = self.ai_tools.make_dir("/absolute/path")
        
        # Check the result - absolute paths should strip leading slash
        self.assertTrue(result["success"])
        self.assertEqual(result["directory_path"], "absolute/path")
        self.assertEqual(result["gitkeep_file"], "absolute/path/.gitkeep")
    
    def test_make_dir_github_client_failure(self):
        """Test handling of GitHub client failure"""
        # Make the mock client fail
        self.mock_github_client.update_file_content = Mock(return_value=False)
        
        result = self.ai_tools.make_dir("fail-directory")
        
        # Check the result
        self.assertFalse(result["success"])
        self.assertIn("Failed to create directory fail-directory", result["error"])
        self.assertEqual(len(self.ai_tools.modified_files), 0)
    
    def test_make_dir_exception_handling(self):
        """Test exception handling in make_dir"""
        # Make the mock client throw an exception
        def failing_method(*args, **kwargs):
            raise Exception("GitHub API error")
        
        self.mock_github_client.get_repository_structure = failing_method
        
        result = self.ai_tools.make_dir("exception-directory")
        
        # Check the result
        self.assertFalse(result["success"])
        self.assertIn("GitHub API error", result["error"])
    
    def test_make_dir_tool_execution(self):
        """Test make_dir through the execute_tool interface"""
        parameters = {"directory_path": "tool-test-dir"}
        result = self.ai_tools.execute_tool("make_dir", parameters)
        
        # Check the result
        self.assertTrue(result["success"])
        self.assertEqual(result["directory_path"], "tool-test-dir")
        
        # Check that .gitkeep file was created
        expected_key = "test-owner/test-repo/test-branch/tool-test-dir/.gitkeep"
        self.assertIn(expected_key, self.mock_github_client.created_files)
    
    def test_make_dir_tool_schema(self):
        """Test that make_dir is included in tool schemas"""
        schemas = self.ai_tools.get_tool_schemas()
        
        # Find the make_dir schema
        make_dir_schema = None
        for schema in schemas:
            if schema["name"] == "make_dir":
                make_dir_schema = schema
                break
        
        # Check schema exists and is correct
        self.assertIsNotNone(make_dir_schema)
        self.assertEqual(make_dir_schema["name"], "make_dir")
        self.assertIn("Create a new directory", make_dir_schema["description"])
        self.assertIn("directory_path", make_dir_schema["input_schema"]["properties"])
        self.assertIn("directory_path", make_dir_schema["input_schema"]["required"])


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMakeDir)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"TEST SUMMARY")
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
        print(f"\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n❌ SOME TESTS FAILED!")
    
    return success


if __name__ == "__main__":
    print("🧪 Testing make_dir functionality...")
    print("="*50)
    
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        sys.exit(1) 