#!/usr/bin/env python3
"""
Comprehensive test script for PyGit2 implementation.

This script tests the PyGit2-based Git tools implementation, including
basic and advanced operations, authentication, conflict resolution, and
repository health checks.
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from typing import Dict, Any, List, Optional

# Try to import PyGit2 tools
try:
    from pygit2_tools import (
        git_init, git_status, git_add, git_commit, git_log,
        git_branch, git_checkout, git_diff, git_context,
        git_tag, git_merge, git_reset, git_stash, git_show
    )
except ImportError:
    print("Error: pygit2_tools module not found. Please run this script from the FastFS-MCP directory.")
    sys.exit(1)

# Try to import enhanced PyGit2 tools
try:
    from enhanced_pygit2 import (
        RepositoryHealth, ConflictResolver, DocumentationGenerator,
        AuthenticationManager, timing_decorator
    )
    has_enhanced = True
except ImportError:
    print("Warning: enhanced_pygit2 module not found. Some tests will be skipped.")
    has_enhanced = False

class PyGit2TestCase(unittest.TestCase):
    """Test case for PyGit2 implementation."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        print(f"Created temporary directory: {self.temp_dir}")
        
        # Initialize repository
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)
        
        # Initialize git repository
        init_result = git_init(self.repo_dir, initial_commit=True)
        self.assertTrue(init_result["success"])
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
        print(f"Removed temporary directory: {self.temp_dir}")
    
    def create_test_file(self, filename: str, content: str) -> str:
        """
        Create a test file in the repository.
        
        Args:
            filename: Filename
            content: File content
        
        Returns:
            Path to the file
        """
        file_path = os.path.join(self.repo_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def test_basic_workflow(self):
        """Test basic Git workflow."""
        # Create a test file
        test_file = "test.txt"
        file_path = self.create_test_file(test_file, "This is a test file.\n")
        
        # Check status
        status_result = git_status(self.repo_dir)
        self.assertTrue(status_result["success"])
        self.assertFalse(status_result["is_clean"])
        self.assertEqual(status_result["counts"]["untracked"], 1)
        
        # Add file
        add_result = git_add(test_file, self.repo_dir)
        self.assertTrue(add_result["success"])
        self.assertEqual(len(add_result["added"]), 1)
        
        # Check status after add
        status_result = git_status(self.repo_dir)
        self.assertTrue(status_result["success"])
        self.assertFalse(status_result["is_clean"])
        self.assertEqual(status_result["counts"]["staged"], 1)
        
        # Commit file
        commit_result = git_commit("Add test file", path=self.repo_dir)
        self.assertTrue(commit_result["success"])
        
        # Check status after commit
        status_result = git_status(self.repo_dir)
        self.assertTrue(status_result["success"])
        self.assertTrue(status_result["is_clean"])
        
        # Check log
        log_result = git_log(self.repo_dir)
        self.assertTrue(log_result["success"])
        self.assertEqual(log_result["count"], 2)  # Initial commit + our commit
    
    def test_branching(self):
        """Test Git branching."""
        # Create a test file and commit it
        test_file = "test.txt"
        file_path = self.create_test_file(test_file, "This is a test file.\n")
        git_add(test_file, self.repo_dir)
        git_commit("Add test file", path=self.repo_dir)
        
        # Create a branch
        branch_result = git_branch("test-branch", self.repo_dir)
        self.assertTrue(branch_result["success"])
        
        # List branches
        branch_list_result = git_branch(path=self.repo_dir)
        self.assertTrue(branch_list_result["success"])
        self.assertEqual(branch_list_result["count"], 2)
        
        # Checkout the branch
        checkout_result = git_checkout("test-branch", self.repo_dir)
        self.assertTrue(checkout_result["success"])
        
        # Modify the file
        with open(file_path, 'a') as f:
            f.write("This is a modification.\n")
        
        # Add and commit the modification
        git_add(test_file, self.repo_dir)
        commit_result = git_commit("Modify test file", path=self.repo_dir)
        self.assertTrue(commit_result["success"])
        
        # Checkout main branch
        checkout_result = git_checkout("main", self.repo_dir)
        self.assertTrue(checkout_result["success"])
        
        # Check the file content (should not have the modification)
        with open(file_path, 'r') as f:
            content = f.read()
        self.assertNotIn("This is a modification.", content)
        
        # Merge the branch
        merge_result = git_merge(self.repo_dir, "test-branch")
        self.assertTrue(merge_result["success"])
        
        # Check the file content (should have the modification now)
        with open(file_path, 'r') as f:
            content = f.read()
        self.assertIn("This is a modification.", content)
    
    def test_tagging(self):
        """Test Git tagging."""
        # Create a test file and commit it
        test_file = "test.txt"
        file_path = self.create_test_file(test_file, "This is a test file.\n")
        git_add(test_file, self.repo_dir)
        git_commit("Add test file", path=self.repo_dir)
        
        # Create a lightweight tag
        tag_result = git_tag(self.repo_dir, "v1.0", "HEAD")
        self.assertTrue(tag_result["success"])
        
        # Create an annotated tag
        tag_result = git_tag(self.repo_dir, "v1.1", "HEAD", "Version 1.1")
        self.assertTrue(tag_result["success"])
        
        # List tags
        tag_list_result = git_tag(self.repo_dir)
        self.assertTrue(tag_list_result["success"])
        self.assertEqual(tag_list_result["count"], 2)
        
        # Delete a tag
        tag_result = git_tag(self.repo_dir, "v1.0", delete=True)
        self.assertTrue(tag_result["success"])
        
        # List tags again
        tag_list_result = git_tag(self.repo_dir)
        self.assertTrue(tag_list_result["success"])
        self.assertEqual(tag_list_result["count"], 1)
    
    def test_diff(self):
        """Test Git diff."""
        # Create a test file and commit it
        test_file = "test.txt"
        file_path = self.create_test_file(test_file, "Line 1\nLine 2\nLine 3\n")
        git_add(test_file, self.repo_dir)
        git_commit("Add test file", path=self.repo_dir)
        
        # Modify the file
        with open(file_path, 'w') as f:
            f.write("Line 1\nModified Line 2\nLine 3\nLine 4\n")
        
        # Get diff
        diff_result = git_diff(self.repo_dir)
        self.assertTrue(diff_result["success"])
        self.assertEqual(diff_result["diff"]["stats"]["files_changed"], 1)
        self.assertEqual(diff_result["diff"]["stats"]["insertions"], 2)
        self.assertEqual(diff_result["diff"]["stats"]["deletions"], 1)
    
    def test_reset(self):
        """Test Git reset."""
        # Create a test file and commit it
        test_file = "test.txt"
        file_path = self.create_test_file(test_file, "Line 1\nLine 2\nLine 3\n")
        git_add(test_file, self.repo_dir)
        commit_result = git_commit("Add test file", path=self.repo_dir)
        commit_id = commit_result["commit"]["id"]
        
        # Modify the file and stage it
        with open(file_path, 'w') as f:
            f.write("Line 1\nModified Line 2\nLine 3\nLine 4\n")
        git_add(test_file, self.repo_dir)
        
        # Check status
        status_result = git_status(self.repo_dir)
        self.assertTrue(status_result["success"])
        self.assertFalse(status_result["is_clean"])
        self.assertEqual(status_result["counts"]["staged"], 1)
        
        # Reset (mixed)
        reset_result = git_reset(self.repo_dir, "mixed", "HEAD")
        self.assertTrue(reset_result["success"])
        
        # Check status after reset
        status_result = git_status(self.repo_dir)
        self.assertTrue(status_result["success"])
        self.assertFalse(status_result["is_clean"])
        self.assertEqual(status_result["counts"]["staged"], 0)
        self.assertEqual(status_result["counts"]["unstaged"], 1)
        
        # Reset (hard)
        reset_result = git_reset(self.repo_dir, "hard", "HEAD")
        self.assertTrue(reset_result["success"])
        
        # Check status after hard reset
        status_result = git_status(self.repo_dir)
        self.assertTrue(status_result["success"])
        self.assertTrue(status_result["is_clean"])
    
    def test_show(self):
        """Test Git show."""
        # Create a test file and commit it
        test_file = "test.txt"
        file_path = self.create_test_file(test_file, "This is a test file.\n")
        git_add(test_file, self.repo_dir)
        commit_result = git_commit("Add test file", path=self.repo_dir)
        commit_id = commit_result["commit"]["id"]
        
        # Show commit
        show_result = git_show(self.repo_dir, commit_id)
        self.assertTrue(show_result["success"])
        self.assertEqual(show_result["type"], "commit")
        self.assertEqual(show_result["commit"]["id"], commit_id)
    
    def test_context(self):
        """Test Git context."""
        # Create a test file and commit it
        test_file = "test.txt"
        file_path = self.create_test_file(test_file, "This is a test file.\n")
        git_add(test_file, self.repo_dir)
        git_commit("Add test file", path=self.repo_dir)
        
        # Get context
        context_result = git_context(self.repo_dir)
        self.assertTrue(context_result["success"])
        self.assertFalse(context_result["repository"]["is_bare"])
        self.assertFalse(context_result["repository"]["is_empty"])
        self.assertEqual(context_result["head"]["type"], "branch")
        self.assertEqual(context_result["head"]["name"], "main")


class EnhancedPyGit2TestCase(unittest.TestCase):
    """Test case for enhanced PyGit2 implementation."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        if not has_enhanced:
            raise unittest.SkipTest("Enhanced PyGit2 module not found")
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        print(f"Created temporary directory: {self.temp_dir}")
        
        # Initialize repository
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)
        
        # Initialize git repository
        init_result = git_init(self.repo_dir, initial_commit=True)
        self.assertTrue(init_result["success"])
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
        print(f"Removed temporary directory: {self.temp_dir}")
    
    def create_test_file(self, filename: str, content: str) -> str:
        """
        Create a test file in the repository.
        
        Args:
            filename: Filename
            content: File content
        
        Returns:
            Path to the file
        """
        file_path = os.path.join(self.repo_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def test_repository_health(self):
        """Test repository health checks."""
        # Create test files and commits
        for i in range(5):
            file_path = self.create_test_file(f"test{i}.txt", f"Test file {i}\n")
            git_add(f"test{i}.txt", self.repo_dir)
            git_commit(f"Add test file {i}", path=self.repo_dir)
        
        # Check repository health
        health_result = RepositoryHealth.check_repository(self.repo_dir)
        self.assertTrue(health_result["success"])
        self.assertFalse(health_result["repository"]["is_bare"])
        self.assertFalse(health_result["repository"]["is_empty"])
    
    def test_documentation_generator(self):
        """Test documentation generator."""
        # Generate documentation
        docs_result = DocumentationGenerator.generate_function_docs("pygit2_tools.py")
        self.assertTrue(docs_result["success"])
        self.assertGreater(docs_result["count"], 0)
        
        # Generate markdown docs
        markdown_docs = DocumentationGenerator.generate_markdown_docs("pygit2_tools.py")
        self.assertIsInstance(markdown_docs, str)
        self.assertGreater(len(markdown_docs), 0)
    
    def test_timing_decorator(self):
        """Test timing decorator."""
        # Apply timing decorator to a function
        @timing_decorator
        def test_function():
            return {"success": True}
        
        # Enable timing
        os.environ["PYGIT2_TIMING"] = "true"
        
        # Call function
        result = test_function()
        self.assertTrue(result["success"])
        self.assertIn("timing", result)
        self.assertIn("execution_time_ms", result["timing"])
        
        # Disable timing
        os.environ["PYGIT2_TIMING"] = "false"
    
    def test_conflict_resolver(self):
        """Test conflict resolver."""
        # Create a file and commit it
        test_file = "test.txt"
        file_path = self.create_test_file(test_file, "Line 1\nLine 2\nLine 3\n")
        git_add(test_file, self.repo_dir)
        git_commit("Add test file", path=self.repo_dir)
        
        # Create a branch
        git_branch("test-branch", self.repo_dir)
        
        # Modify the file on main branch
        with open(file_path, 'w') as f:
            f.write("Line 1\nMain Line 2\nLine 3\n")
        git_add(test_file, self.repo_dir)
        git_commit("Modify test file on main", path=self.repo_dir)
        
        # Checkout the branch
        git_checkout("test-branch", self.repo_dir)
        
        # Modify the file on the branch
        with open(file_path, 'w') as f:
            f.write("Line 1\nBranch Line 2\nLine 3\n")
        git_add(test_file, self.repo_dir)
        git_commit("Modify test file on branch", path=self.repo_dir)
        
        # Try to merge (should result in conflict)
        git_checkout("main", self.repo_dir)
        
        # Using subprocess directly to create a merge with conflict
        import subprocess
        subprocess.run(
            ["git", "merge", "--no-commit", "test-branch"],
            cwd=self.repo_dir,
            capture_output=True
        )
        
        # Check for conflicts
        conflict_result = ConflictResolver.list_conflicts(self.repo_dir)
        if conflict_result["success"] and conflict_result["count"] > 0:
            # Resolve conflict
            resolve_result = ConflictResolver.resolve_conflict(
                self.repo_dir, test_file, "custom", 
                "Line 1\nResolved Line 2\nLine 3\n"
            )
            self.assertTrue(resolve_result["success"])
            self.assertEqual(resolve_result["file"], test_file)
            self.assertEqual(resolve_result["resolution"], "custom")


def run_tests():
    """Run all tests."""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add PyGit2 tests
    suite.addTest(unittest.makeSuite(PyGit2TestCase))
    
    # Add enhanced PyGit2 tests if available
    if has_enhanced:
        suite.addTest(unittest.makeSuite(EnhancedPyGit2TestCase))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\nTest Summary:")
    print(f"  Ran {result.testsRun} tests")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    
    # Return success/failure
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
