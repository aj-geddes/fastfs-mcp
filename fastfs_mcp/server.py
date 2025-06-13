#!/usr/bin/env python3
"""
FastFS-MCP Server with PyGit2 Integration.

This server integrates the PyGit2 implementation with FastFS-MCP to provide
improved Git operations with better performance and structured responses.
"""

import os
import sys
import json
import time
import logging
import signal
from typing import Dict, Any, Optional, List, Union

try:
    import fastmcp
except ImportError:
    print("Error: FastMCP is not installed. Please install it with 'pip install fastmcp'", file=sys.stderr)
    sys.exit(1)

try:
    import pygit2
except ImportError:
    print("Error: PyGit2 is not installed. Please install it with 'pip install pygit2'", file=sys.stderr)
    sys.exit(1)

# Import PyGit2 integration
from fastfs_mcp.git.integration import PyGit2MCP

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if os.environ.get("FASTFS_DEBUG", "").lower() in ("true", "1", "yes") else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fastfs-mcp-pygit2")

# Create FastMCP server - we removed the version parameter
mcp = fastmcp.FastMCP(name="fastfs-mcp-pygit2")

# Create PyGit2 integration
pygit2_mcp = PyGit2MCP()

# Define MCP tools using PyGit2 implementation

@mcp.tool()
async def init(directory: str = ".", bare: bool = False, initial_commit: bool = False) -> Dict[str, Any]:
    """
    Initialize a new Git repository.
    
    Args:
        directory: Directory to initialize the repository in
        bare: Whether to create a bare repository
        initial_commit: Whether to create an initial commit
    
    Returns:
        Dictionary with initialization results
    """
    request = {
        "method": "init",
        "params": {
            "directory": directory,
            "bare": bare,
            "initial_commit": initial_commit
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute init command"})

@mcp.tool()
async def clone(repo_url: str, target_dir: Optional[str] = None, 
               options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Clone a Git repository.
    
    Args:
        repo_url: URL of the repository to clone
        target_dir: Target directory (default: repository name)
        options: Dictionary of options like depth, branch, etc.
    
    Returns:
        Dictionary with clone operation results
    """
    request = {
        "method": "clone",
        "params": {
            "repo_url": repo_url,
            "target_dir": target_dir,
            "options": options or {}
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute clone command"})

@mcp.tool()
async def status(path: str = None) -> Dict[str, Any]:
    """
    Show the working tree status.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with status information
    """
    request = {
        "method": "status",
        "params": {
            "path": path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute status command"})

@mcp.tool()
async def add(paths: Union[str, List[str]], path: str = None) -> Dict[str, Any]:
    """
    Add file(s) to the Git staging area.
    
    Args:
        paths: Path(s) to add
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with add operation results
    """
    request = {
        "method": "add",
        "params": {
            "paths": paths,
            "path": path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute add command"})

# ... (all other tool definitions remain the same)

def main():
    """Main function to run the server."""
    try:
        # Register signal handlers for graceful shutdown
        def handle_signal(signum, frame):
            print(f"[fastfs-mcp-pygit2] Received signal {signum}, shutting down...", file=sys.stderr, flush=True)
            sys.exit(0)
            
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        
        # Run MCP server
        print("[fastfs-mcp-pygit2] Server running, waiting for requests...", file=sys.stderr, flush=True)
        
        # Start the server
        mcp.run()
        
    except Exception as e:
        print(f"[fastfs-mcp-pygit2] Fatal error: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
