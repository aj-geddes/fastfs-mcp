#!/usr/bin/env python3
"""
Test script to check the FastFS-MCP package structure.

This script ensures that the package and its modules can be imported successfully.
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def test_package_imports():
    """Test importing the package and its modules."""
    logger.info("Testing package imports...")
    
    try:
        import fastfs_mcp
        logger.info("✅ Imported fastfs_mcp successfully")
        
        from fastfs_mcp import server
        logger.info("✅ Imported fastfs_mcp.server successfully")
        
        from fastfs_mcp.git import base
        logger.info("✅ Imported fastfs_mcp.git.base successfully")
        
        from fastfs_mcp.git import integration
        logger.info("✅ Imported fastfs_mcp.git.integration successfully")
        
        from fastfs_mcp.git.integration import PyGit2MCP
        logger.info("✅ Imported PyGit2MCP class successfully")
        
        from fastfs_mcp.git.base import git_init, git_clone, git_status
        logger.info("✅ Imported git functions successfully")
        
        logger.info("\n✅ All package imports successful!")
        return True
    except ImportError as e:
        logger.error(f"❌ Import error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Main function."""
    logger.info("=== Testing FastFS-MCP Package Structure ===")
    
    if not test_package_imports():
        logger.error("\n❌ Package structure test failed!")
        sys.exit(1)
    
    logger.info("\n✅ Package structure test passed!")

if __name__ == "__main__":
    main()
