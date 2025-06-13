#!/usr/bin/env python3
"""
Test script to verify the FastFS-MCP package structure.
"""

import os
import sys


def check_package_structure():
    """Check if the FastFS-MCP package is properly structured."""
    try:
        # Import the package
        import fastfs_mcp
        print(f"✅ Successfully imported fastfs_mcp package (version: {fastfs_mcp.__version__})")
        
        # Import git module
        from fastfs_mcp import git
        print("✅ Successfully imported git module")
        
        # Import prompt module
        from fastfs_mcp import prompt
        print("✅ Successfully imported prompt module")
        
        # Try to import specific modules
        from fastfs_mcp.git.integration import PyGit2MCP
        print("✅ Successfully imported PyGit2MCP class")
        
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
