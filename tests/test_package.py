#!/usr/bin/env python3
"""
Test script to verify the FastFS-MCP package structure.
"""

import os
import sys
import importlib


def check_package_structure():
    """Check if the FastFS-MCP package is properly structured."""
    try:
        # Import the package
        try:
            import fastfs_mcp
            print(f"✅ Successfully imported fastfs_mcp package (version: {fastfs_mcp.__version__})")
        except (ImportError, AttributeError) as e:
            print(f"⚠️ Import note: {str(e)}")
            print("Attempting to add package to path...")
            # Try to add the package to the path
            sys.path.insert(0, '/app')
            import fastfs_mcp
            print(f"✅ Successfully imported fastfs_mcp package after path adjustment")
        
        # Import git module
        try:
            from fastfs_mcp import git
            print("✅ Successfully imported git module")
        except ImportError as e:
            print(f"❌ Failed to import git module: {str(e)}")
            return False
        
        # Import prompt module
        try:
            from fastfs_mcp import prompt
            print("✅ Successfully imported prompt module")
        except ImportError as e:
            print(f"❌ Failed to import prompt module: {str(e)}")
            return False
        
        # Try to import specific modules
        try:
            from fastfs_mcp.git.integration import PyGit2MCP
            print("✅ Successfully imported PyGit2MCP class")
        except ImportError as e:
            print(f"❌ Failed to import PyGit2MCP class: {str(e)}")
            return False
        
        # Check if the necessary modules exist
        required_files = [
            "fastfs_mcp/__init__.py",
            "fastfs_mcp/server.py",
            "fastfs_mcp/git/__init__.py",
            "fastfs_mcp/git/base.py",
            "fastfs_mcp/git/advanced.py",
            "fastfs_mcp/git/enhanced.py",
            "fastfs_mcp/git/error_handler.py",
            "fastfs_mcp/git/integration.py",
            "fastfs_mcp/git/ssh.py",
            "fastfs_mcp/prompt/__init__.py",
            "fastfs_mcp/prompt/helpers.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(os.path.join("/app", file_path)):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing files: {', '.join(missing_files)}")
            return False
        else:
            print("✅ All required files exist")
            return True
    
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    print("Testing FastFS-MCP package structure...")
    if check_package_structure():
        print("\n✅ Package structure is valid!")
        sys.exit(0)
    else:
        print("\n❌ Package structure is invalid!")
        sys.exit(1)
