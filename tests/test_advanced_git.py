#!/usr/bin/env python3
"""
Test suite for advanced PyGit2 features.

This script tests the advanced features of the PyGit2 implementation,
including advanced Git operations, SSH support, and error handling.
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
        git_branch, git_checkout, git_diff, git_context
    )
except ImportError:
    print("Error: pygit2_tools module not found. Please run this script from the FastFS-MCP directory.")
    sys.exit(1)

# Try to import advanced PyGit2 tools
try:
    from advanced_pygit2 import (
        git_rebase, git_cherry_pick, git_worktree_add, git_worktree_list,
        git_worktree_remove, git_submodule_add, git_submodule_update,
        git_submodule_list, git_bisect_start, git_bisect_good,
        git_bisect_bad, git_bisect_reset, git_reflog, git_clean,
        git_archive, git_gc
    )
    has_advanced = True
except ImportError:
    print("Warning: advanced_pygit2 module not found. Some tests will be skipped.")
    has_advanced = False

# Try to import SSH support
try:
    from ssh_support import (
        SSHCredential, SSHConfig, SSHKeyManager
    )
    has_ssh = True
except ImportError:
    print("Warning: ssh_support module not found. Some tests will be skipped.")
    has_ssh = False

# Try to import error handling
try:
    from git_error_handler import (
        GitErrorHandler, GitRetry, GitRepair
    )
    has_error_handler = True
except ImportError:
    print("Warning: git_error_handler module not found. Some tests will be skipped.")
    has_error_handler = False

class AdvancedPyGit2TestCase(unittest.TestCase):
    """Test case for advanced PyGit2 features."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        if not has_advanced:
            raise unittest.SkipTest("Advanced PyGit2 module not found")
    
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
    
    def test_worktree(self):
        """Test Git worktree operations."""
        # Create a test file and commit it
        test_file = "test.txt"
        file_path = self.create_test_file(test_file, "This is a test file.\n")
        git_add(test_file, self.repo_dir)
        git_commit("Add test file", path=self.repo_dir)
        
        # Create a branch
        branch_result = git_branch("test-branch", self.repo_dir)
        self.assertTrue(branch_result["success"])
        
        # Add worktree
        worktree_path = os.path.join(self.temp_dir, "worktree")
        worktree_result = git_worktree_add(
            path=self.repo_dir,
            worktree_path=worktree_path,
            branch="test-branch"
        )
        self.assertTrue(worktree_result["success"])
        
        # List worktrees
        list_result = git_worktree_list(self.repo_dir)
        self.assertTrue(list_result["success"])
        self.assertEqual(list_result["count"], 2)  # Main + worktree
        
        # Create a file in the worktree
        worktree_file = os.path.join(worktree_path, "worktree.txt")
        with open(worktree_file, 'w') as f:
            f.write("This file is in the worktree.\n")
        
        # Add and commit the file in the worktree
        git_add("worktree.txt", worktree_path)
        git_commit("Add worktree file", path=worktree_path)
        
        # Check log in worktree
        log_result = git_log(worktree_path)
        self.assertTrue(log_result["success"])
        self.assertEqual(log_result["count"], 3)  # Initial commit + test file + worktree file
        
        # Remove worktree
        remove_result = git_worktree_remove(self.repo_dir, worktree_path)
        self.assertTrue(remove_result["success"])
        
        # List worktrees again
        list_result = git_worktree_list(self.repo_dir)
        self.assertTrue(list_result["success"])
        self.assertEqual(list_result["count"], 1)  # Only main
    
    def test_submodule(self):
        """Test Git submodule operations."""
        # Create another repository for submodule
        submodule_dir = os.path.join(self.temp_dir, "submodule")
        os.makedirs(submodule_dir)
        
        # Initialize submodule repository
        init_result = git_init(submodule_dir, initial_commit=True)
        self.assertTrue(init_result["success"])
        
        # Create a test file in the submodule
        submodule_file = os.path.join(submodule_dir, "submodule.txt")
        with open(submodule_file, 'w') as f:
            f.write("This is a submodule file.\n")
        
        # Add and commit the file in the submodule
        git_add("submodule.txt", submodule_dir)
        git_commit("Add submodule file", path=submodule_dir)
        
        # Add submodule to main repository
        submodule_result = git_submodule_add(
            path=self.repo_dir,
            repo_url=submodule_dir,
            target_path="sub"
        )
        self.assertTrue(submodule_result["success"])
        
        # List submodules
        list_result = git_submodule_list(self.repo_dir)
        self.assertTrue(list_result["success"])
        self.assertEqual(list_result["count"], 1)
        
        # Update submodule
        update_result = git_submodule_update(
            path=self.repo_dir,
            init=True,
            recursive=False
        )
        self.assertTrue(update_result["success"])
    
    def test_reflog(self):
        """Test Git reflog operations."""
        # Create a test file and commit it
        test_file = "test.txt"
        file_path = self.create_test_file(test_file, "This is a test file.\n")
        git_add(test_file, self.repo_dir)
        git_commit("Add test file", path=self.repo_dir)
        
        # Create a branch and switch to it
        git_branch("test-branch", self.repo_dir)
        git_checkout("test-branch", self.repo_dir)
        
        # Modify the file and commit
        with open(file_path, 'a') as f:
            f.write("This is a modification.\n")
        git_add(test_file, self.repo_dir)
        git_commit("Modify test file", path=self.repo_dir)
        
        # Switch back to main
        git_checkout("main", self.repo_dir)
        
        # Get reflog
        reflog_result = git_reflog(self.repo_dir)
        self.assertTrue(reflog_result["success"])
        self.assertGreater(reflog_result["count"], 0)
    
    def test_clean(self):
        """Test Git clean operations."""
        # Create a test file and commit it
        test_file = "test.txt"
        file_path = self.create_test_file(test_file, "This is a test file.\n")
        git_add(test_file, self.repo_dir)
        git_commit("Add test file", path=self.repo_dir)
        
        # Create untracked files
        untracked1 = self.create_test_file("untracked1.txt", "Untracked file 1\n")
        untracked2 = self.create_test_file("untracked2.txt", "Untracked file 2\n")
        
        # Create untracked directory
        untracked_dir = os.path.join(self.repo_dir, "untracked_dir")
        os.makedirs(untracked_dir)
        untracked3 = os.path.join(untracked_dir, "untracked3.txt")
        with open(untracked3, 'w') as f:
            f.write("Untracked file 3\n")
        
        # Check status
        status_result = git_status(self.repo_dir)
        self.assertTrue(status_result["success"])
        self.assertEqual(status_result["counts"]["untracked"], 3)
        
        # Clean with dry run
        clean_result = git_clean(
            path=self.repo_dir,
            directories=True,
            force=True,
            dry_run=True
        )
        self.assertTrue(clean_result["success"])
        self.assertEqual(clean_result["count"], 3)
        
        # Files should still exist
        self.assertTrue(os.path.exists(untracked1))
        self.assertTrue(os.path.exists(untracked2))
        self.assertTrue(os.path.exists(untracked3))
        
        # Clean for real
        clean_result = git_clean(
            path=self.repo_dir,
            directories=True,
            force=True,
            dry_run=False
        )
        self.assertTrue(clean_result["success"])
        
        # Files should be gone
        self.assertFalse(os.path.exists(untracked1))
        self.assertFalse(os.path.exists(untracked2))
        self.assertFalse(os.path.exists(untracked_dir))
    
    def test_archive(self):
        """Test Git archive operations."""
        # Create a test file and commit it
        test_file = "test.txt"
        file_path = self.create_test_file(test_file, "This is a test file.\n")
        git_add(test_file, self.repo_dir)
        git_commit("Add test file", path=self.repo_dir)
        
        # Create archive
        archive_path = os.path.join(self.temp_dir, "archive.tar")
        archive_result = git_archive(
            path=self.repo_dir,
            output_file=archive_path,
            format="tar",
            ref="HEAD"
        )
        self.assertTrue(archive_result["success"])
        self.assertTrue(os.path.exists(archive_path))
    
    def test_gc(self):
        """Test Git garbage collection."""
        # Create a test file and commit it
        test_file = "test.txt"
        file_path = self.create_test_file(test_file, "This is a test file.\n")
        git_add(test_file, self.repo_dir)
        git_commit("Add test file", path=self.repo_dir)
        
        # Run garbage collection
        gc_result = git_gc(self.repo_dir)
        self.assertTrue(gc_result["success"])


class SSHSupportTestCase(unittest.TestCase):
    """Test case for SSH support."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        if not has_ssh:
            raise unittest.SkipTest("SSH support module not found")
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        print(f"Created temporary directory: {self.temp_dir}")
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
        print(f"Removed temporary directory: {self.temp_dir}")
    
    def test_ssh_key_generation(self):
        """Test SSH key generation."""
        # Generate SSH key
        key_result = SSHKeyManager.generate_key(
            key_type="rsa",
            bits=2048,
            comment="PyGit2 Test Key",
            passphrase="",
            output_dir=self.temp_dir
        )
        self.assertTrue(key_result["success"])
        self.assertTrue(os.path.exists(key_result["private_key_path"]))
        self.assertTrue(os.path.exists(key_result["public_key_path"]))
        
        # Verify key
        verify_result = SSHKeyManager.verify_key(
            private_key_path=key_result["private_key_path"],
            public_key_path=key_result["public_key_path"]
        )
        self.assertTrue(verify_result["success"])
    
    def test_ssh_credential(self):
        """Test SSH credential."""
        # Generate SSH key
        key_result = SSHKeyManager.generate_key(
            key_type="rsa",
            bits=2048,
            comment="PyGit2 Test Key",
            passphrase="",
            output_dir=self.temp_dir
        )
        self.assertTrue(key_result["success"])
        
        # Create SSH credential from key files
        credential = SSHCredential(
            username="git",
            private_key_path=key_result["private_key_path"],
            public_key_path=key_result["public_key_path"]
        )
        
        # Get credential callback
        callback = credential.get_credential_callback()
        self.assertIsNotNone(callback)
        
        # Create SSH credential from key content
        credential = SSHCredential.from_key_content(
            private_key_content=key_result["private_key"],
            public_key_content=key_result["public_key"]
        )
        
        # Get credential callback
        callback = credential.get_credential_callback()
        self.assertIsNotNone(callback)
        
        # Clean up
        credential.cleanup()
    
    def test_ssh_config(self):
        """Test SSH config."""
        # Create SSH config
        config = SSHConfig()
        
        # Create temporary config
        config_path = config.create_temp_config(
            host="github.com",
            options={
                "User": "git",
                "IdentityFile": "/path/to/key",
                "StrictHostKeyChecking": "no"
            }
        )
        self.assertTrue(os.path.exists(config_path))
        
        # Get SSH command
        ssh_command = config.get_ssh_command(config_path)
        self.assertTrue(ssh_command.startswith("ssh -F"))
        
        # Clean up
        config.cleanup()


class ErrorHandlingTestCase(unittest.TestCase):
    """Test case for error handling."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        if not has_error_handler:
            raise unittest.SkipTest("Error handling module not found")
    
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
    
    def test_error_handler(self):
        """Test error handler."""
        # Create a test error
        error = Exception("Test error")
        
        # Handle error
        result = GitErrorHandler.handle_error(
            error=error,
            operation="test_operation",
            repository_path=self.repo_dir
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["error"]["type"], "Exception")
        self.assertEqual(result["error"]["message"], "Test error")
    
    def test_retry(self):
        """Test retry mechanism."""
        # Create a function that fails the first time
        fail_count = [0]
        
        def test_func(**kwargs):
            fail_count[0] += 1
            if fail_count[0] == 1:
                return {"success": False, "error": "First attempt failed"}
            return {"success": True, "message": "Success"}
        
        # Retry the function
        result = GitRetry.retry(
            func=test_func,
            max_retries=3,
            delay=0.1,
            backoff_factor=1.0
        )
        self.assertTrue(result["success"])
        self.assertEqual(fail_count[0], 2)
    
    def test_repository_repair(self):
        """Test repository repair."""
        # Check if repository is valid
        repair_result = GitRepair.fix_corrupted_index(self.repo_dir)
        self.assertTrue(repair_result["success"])
        
        # Fix detached HEAD
        # First create a detached HEAD state
        git_branch("test-branch", self.repo_dir)
        git_checkout("test-branch", self.repo_dir)
        
        # Get the HEAD commit hash
        log_result = git_log(self.repo_dir, max_count=1)
        self.assertTrue(log_result["success"])
        head_commit = log_result["commits"][0]["id"]
        
        # Checkout the commit directly to create detached HEAD
        git_checkout(head_commit, self.repo_dir)
        
        # Fix detached HEAD
        fix_result = GitRepair.fix_detached_head(self.repo_dir, "main")
        self.assertTrue(fix_result["success"])
        
        # Check if HEAD is attached
        context_result = git_context(self.repo_dir)
        self.assertTrue(context_result["success"])
        self.assertEqual(context_result["head"]["type"], "branch")
        self.assertEqual(context_result["head"]["name"], "main")


def run_tests():
    """Run all tests."""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add advanced PyGit2 tests if available
    if has_advanced:
        suite.addTest(unittest.makeSuite(AdvancedPyGit2TestCase))
    
    # Add SSH support tests if available
    if has_ssh:
        suite.addTest(unittest.makeSuite(SSHSupportTestCase))
    
    # Add error handling tests if available
    if has_error_handler:
        suite.addTest(unittest.makeSuite(ErrorHandlingTestCase))
    
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
