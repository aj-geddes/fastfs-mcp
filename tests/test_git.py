#!/usr/bin/env python3
"""
Test script for PyGit2 implementation in FastFS-MCP.

This script tests the functionality of the PyGit2-based Git tools
to ensure they work correctly and provide the expected responses.
"""

import os
import sys
import json
import tempfile
import shutil
from typing import Dict, Any, List, Optional

# Import PyGit2 tools
try:
    from pygit2_tools import (
        git_init, git_status, git_add, git_commit, git_log,
        git_branch, git_checkout, git_diff, git_context
    )
except ImportError:
    print("Error: pygit2_tools module not found. Please run this script from the FastFS-MCP directory.")
    sys.exit(1)

def run_test(name: str, func, *args, **kwargs) -> None:
    """Run a test function and print the result."""
    print(f"\n=== Running test: {name} ===")
    try:
        result = func(*args, **kwargs)
        print(f"Result: {json.dumps(result, indent=2)}")
        if result.get('success', False):
            print(f"✅ Test {name} passed!")
        else:
            print(f"❌ Test {name} failed: {result.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Test {name} failed with exception: {str(e)}")

def setup_test_repo() -> str:
    """Create a temporary repository for testing."""
    temp_dir = tempfile.mkdtemp()
    print(f"Created temporary directory: {temp_dir}")
    
    # Initialize repository
    init_result = git_init(temp_dir, initial_commit=True)
    if not init_result.get('success', False):
        print(f"Failed to initialize repository: {init_result.get('message', 'Unknown error')}")
        sys.exit(1)
    
    # Create a test file
    test_file = os.path.join(temp_dir, 'test.txt')
    with open(test_file, 'w') as f:
        f.write("This is a test file.\n")
    
    return temp_dir

def test_basic_workflow() -> None:
    """Test a basic Git workflow with PyGit2 tools."""
    repo_dir = setup_test_repo()
    try:
        # Check status
        run_test("git_status", git_status, repo_dir)
        
        # Add a file
        run_test("git_add", git_add, 'test.txt', repo_dir)
        
        # Check status after add
        run_test("git_status_after_add", git_status, repo_dir)
        
        # Commit the file
        run_test("git_commit", git_commit, "Add test file", path=repo_dir)
        
        # Check log
        run_test("git_log", git_log, repo_dir)
        
        # Create a new branch
        run_test("git_branch_create", git_branch, "test-branch", repo_dir)
        
        # List branches
        run_test("git_branch_list", git_branch, path=repo_dir)
        
        # Checkout the new branch
        run_test("git_checkout", git_checkout, "test-branch", repo_dir)
        
        # Modify the file
        test_file = os.path.join(repo_dir, 'test.txt')
        with open(test_file, 'a') as f:
            f.write("This is a modification.\n")
        
        # Check diff
        run_test("git_diff", git_diff, repo_dir)
        
        # Add and commit the modification
        run_test("git_add_modified", git_add, 'test.txt', repo_dir)
        run_test("git_commit_modified", git_commit, "Modify test file", path=repo_dir)
        
        # Get repository context
        run_test("git_context", git_context, repo_dir)
        
        print("\n✅ All basic workflow tests completed!")
    finally:
        # Clean up
        shutil.rmtree(repo_dir)
        print(f"Removed temporary directory: {repo_dir}")

if __name__ == "__main__":
    print("Testing PyGit2 implementation for FastFS-MCP...")
    test_basic_workflow()
