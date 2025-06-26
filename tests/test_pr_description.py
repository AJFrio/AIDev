#!/usr/bin/env python3
"""
Test the PR description generation to ensure it's simplified and not repetitive
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import Mock, MagicMock
from ai_assistant import AIAssistant


class TestPRDescription(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a mock AIAssistant without actually initializing OpenAI client
        self.assistant = Mock(spec=AIAssistant)
        
        # Bind the actual _create_pr_description method to our mock
        self.assistant._create_pr_description = AIAssistant._create_pr_description.__get__(self.assistant)
    
    def test_pr_description_with_files_and_summary(self):
        """Test PR description with files and AI summary"""
        objective = "Add validation to user input forms"
        branch = "ai-dev-validation-20241201"
        iterations = 5
        ai_summary = "Added comprehensive input validation including email format checking, password strength requirements, and form field validation with appropriate error messages."
        modified_files = [
            {"file_path": "src/components/LoginForm.js", "action": "updated"},
            {"file_path": "src/utils/validation.js", "action": "created"},
            {"file_path": "src/styles/forms.css", "action": "updated"}
        ]
        
        result = self.assistant._create_pr_description(
            objective, branch, iterations, ai_summary, modified_files
        )
        
        # Check that the description contains expected sections
        self.assertIn("This pull request was created by the AI Dev", result)
        self.assertIn("**Objective:** Add validation to user input forms", result)
        self.assertIn(f"**Branch:** {branch}", result)
        self.assertIn(f"**Iterations:** {iterations}", result)
        self.assertIn("**Files Changed:**", result)
        self.assertIn("**Summary:**", result)
        
        # Check that files are listed correctly
        self.assertIn("• `src/components/LoginForm.js` - updated", result)
        self.assertIn("• `src/utils/validation.js` - created", result)
        self.assertIn("• `src/styles/forms.css` - updated", result)
        
        # Check that the summary is included
        self.assertIn(ai_summary, result)
        
        # Check that there's NO "What Was Changed" section
        self.assertNotIn("**What Was Changed:**", result)
        
        # Ensure we don't have repetitive content
        summary_count = result.count(ai_summary)
        self.assertEqual(summary_count, 1, "AI summary should appear only once")
    
    def test_pr_description_with_no_files(self):
        """Test PR description when no files were modified"""
        objective = "Analyze code structure"
        branch = "ai-dev-analysis-20241201"
        iterations = 3
        ai_summary = "Completed analysis of the codebase structure and provided recommendations."
        modified_files = []
        
        result = self.assistant._create_pr_description(
            objective, branch, iterations, ai_summary, modified_files
        )
        
        # Check basic structure
        self.assertIn("**Objective:** Analyze code structure", result)
        self.assertIn("**Files Changed:** None", result)
        self.assertIn("**Summary:**", result)
        self.assertIn(ai_summary, result)
        
        # Should not have repetitive sections
        self.assertNotIn("**What Was Changed:**", result)
    
    def test_pr_description_with_no_summary(self):
        """Test PR description when AI summary is empty"""
        objective = "Update configuration files"
        branch = "ai-dev-config-20241201"
        iterations = 2
        ai_summary = ""
        modified_files = [
            {"file_path": "config/settings.json", "action": "updated"}
        ]
        
        result = self.assistant._create_pr_description(
            objective, branch, iterations, ai_summary, modified_files
        )
        
        # Check basic structure
        self.assertIn("**Objective:** Update configuration files", result)
        self.assertIn("**Files Changed:**", result)
        self.assertIn("• `config/settings.json` - updated", result)
        
        # Should not have summary section when summary is empty
        self.assertNotIn("**Summary:**", result)
        self.assertNotIn("**What Was Changed:**", result)
    
    def test_pr_description_format_consistency(self):
        """Test that PR description format is consistent and clean"""
        objective = "Implement user authentication"
        branch = "ai-dev-auth-feature"
        iterations = 8
        ai_summary = "Implemented JWT-based authentication with login, logout, and protected routes."
        modified_files = [
            {"file_path": "src/auth/login.js", "action": "created"},
            {"file_path": "src/auth/middleware.js", "action": "created"},
            {"file_path": "src/routes/protected.js", "action": "updated"},
            {"file_path": "package.json", "action": "updated"}
        ]
        
        result = self.assistant._create_pr_description(
            objective, branch, iterations, ai_summary, modified_files
        )
        
        # Check that each section appears only once
        sections = [
            "This pull request was created by the AI Dev",
            "**Objective:**",
            "**Branch:**", 
            "**Iterations:**",
            "**Files Changed:**",
            "**Summary:**",
            "Please review the changes before merging"
        ]
        
        for section in sections:
            count = result.count(section)
            self.assertEqual(count, 1, f"Section '{section}' should appear exactly once, found {count}")
        
        # Verify no repetitive "What Was Changed" sections
        self.assertEqual(result.count("**What Was Changed:**"), 0)
        
        # Check proper formatting
        lines = result.split('\n')
        
        # Should start with the intro line
        self.assertTrue(lines[0].startswith("This pull request was created"))
        
        # Should end with review message
        self.assertTrue(any("Please review the changes" in line for line in lines))


def run_pr_tests():
    """Run PR description tests"""
    print("📝 Testing PR description generation...")
    print("="*50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPRDescription)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"PR DESCRIPTION TEST SUMMARY")
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
        print(f"\n✅ ALL PR DESCRIPTION TESTS PASSED!")
    else:
        print(f"\n❌ SOME PR DESCRIPTION TESTS FAILED!")
    
    return success


if __name__ == "__main__":
    try:
        success = run_pr_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ PR description test execution failed: {str(e)}")
        sys.exit(1) 