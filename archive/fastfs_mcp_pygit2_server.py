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
from pygit2_integration import PyGit2MCP

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if os.environ.get("FASTFS_DEBUG", "").lower() in ("true", "1", "yes") else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fastfs-mcp-pygit2")

# Create FastMCP server
mcp = fastmcp.FastMCP(name="fastfs-mcp-pygit2", version="1.0.0")

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

@mcp.tool()
async def commit(message: str, author_name: Optional[str] = None, 
                author_email: Optional[str] = None, path: str = None,
                amend: bool = False) -> Dict[str, Any]:
    """
    Commit changes to the Git repository.
    
    Args:
        message: Commit message
        author_name: Author name (default: from config)
        author_email: Author email (default: from config)
        path: Path to the repository (default: current directory)
        amend: Whether to amend the previous commit
    
    Returns:
        Dictionary with commit operation results
    """
    request = {
        "method": "commit",
        "params": {
            "message": message,
            "author_name": author_name,
            "author_email": author_email,
            "path": path,
            "amend": amend
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute commit command"})

@mcp.tool()
async def log(path: str = None, max_count: int = 10, skip: int = 0, 
            ref: Optional[str] = None, path_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Show commit logs.
    
    Args:
        path: Path to the repository (default: current directory)
        max_count: Maximum number of commits to show
        skip: Number of commits to skip
        ref: Reference to start from (default: HEAD)
        path_filter: Only show commits affecting this path
    
    Returns:
        Dictionary with log information
    """
    request = {
        "method": "log",
        "params": {
            "path": path,
            "max_count": max_count,
            "skip": skip,
            "ref": ref,
            "path_filter": path_filter
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute log command"})

@mcp.tool()
async def branch(name: Optional[str] = None, path: str = None, 
                start_point: Optional[str] = None, delete: bool = False, 
                force: bool = False) -> Dict[str, Any]:
    """
    List, create, or delete branches.
    
    Args:
        name: Branch name (default: list branches)
        path: Path to the repository (default: current directory)
        start_point: Reference to start branch from (default: HEAD)
        delete: Whether to delete the branch
        force: Whether to force branch creation/deletion
    
    Returns:
        Dictionary with branch operation results
    """
    request = {
        "method": "branch",
        "params": {
            "name": name,
            "path": path,
            "start_point": start_point,
            "delete": delete,
            "force": force
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute branch command"})

@mcp.tool()
async def checkout(revision: str, path: str = None, 
                 create_branch: bool = False, force: bool = False) -> Dict[str, Any]:
    """
    Switch branches or restore working tree files.
    
    Args:
        revision: Branch, tag, or commit to checkout
        path: Path to the repository (default: current directory)
        create_branch: Whether to create the branch if it doesn't exist
        force: Whether to force checkout (discard changes)
    
    Returns:
        Dictionary with checkout operation results
    """
    request = {
        "method": "checkout",
        "params": {
            "revision": revision,
            "path": path,
            "create_branch": create_branch,
            "force": force
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute checkout command"})

@mcp.tool()
async def remote(path: str = None, command: str = "list", 
               name: Optional[str] = None, url: Optional[str] = None) -> Dict[str, Any]:
    """
    Manage remote repositories.
    
    Args:
        path: Path to the repository (default: current directory)
        command: Remote command (list, add, remove, set-url)
        name: Remote name
        url: Remote URL
    
    Returns:
        Dictionary with remote operation results
    """
    request = {
        "method": "remote",
        "params": {
            "path": path,
            "command": command,
            "name": name,
            "url": url
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute remote command"})

@mcp.tool()
async def push(path: str = None, remote: str = "origin", 
             refspecs: Optional[List[str]] = None, force: bool = False,
             token: Optional[str] = None) -> Dict[str, Any]:
    """
    Push changes to a remote repository.
    
    Args:
        path: Path to the repository (default: current directory)
        remote: Remote name (default: origin)
        refspecs: Refspecs to push (default: current branch)
        force: Whether to force push
        token: Optional token for authentication
    
    Returns:
        Dictionary with push operation results
    """
    request = {
        "method": "push",
        "params": {
            "path": path,
            "remote": remote,
            "refspecs": refspecs,
            "force": force,
            "token": token
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute push command"})

@mcp.tool()
async def pull(path: str = None, remote: str = "origin", 
             branch: Optional[str] = None, fast_forward_only: bool = False,
             token: Optional[str] = None) -> Dict[str, Any]:
    """
    Pull changes from a remote repository.
    
    Args:
        path: Path to the repository (default: current directory)
        remote: Remote name (default: origin)
        branch: Remote branch to pull (default: current branch)
        fast_forward_only: Whether to only allow fast-forward merges
        token: Optional token for authentication
    
    Returns:
        Dictionary with pull operation results
    """
    request = {
        "method": "pull",
        "params": {
            "path": path,
            "remote": remote,
            "branch": branch,
            "fast_forward_only": fast_forward_only,
            "token": token
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute pull command"})

@mcp.tool()
async def fetch(path: str = None, remote: str = "origin", 
              refspec: Optional[str] = None, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Download objects and refs from another repository.
    
    Args:
        path: Path to the repository (default: current directory)
        remote: Remote name (default: origin)
        refspec: Refspec to fetch (default: all refs)
        token: Optional token for authentication
    
    Returns:
        Dictionary with fetch operation results
    """
    request = {
        "method": "fetch",
        "params": {
            "path": path,
            "remote": remote,
            "refspec": refspec,
            "token": token
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute fetch command"})

@mcp.tool()
async def diff(path: str = None, from_ref: Optional[str] = None, 
             to_ref: Optional[str] = None, staged: bool = False,
             path_filter: Optional[str] = None, context_lines: int = 3) -> Dict[str, Any]:
    """
    Show changes between commits, commit and working tree, etc.
    
    Args:
        path: Path to the repository (default: current directory)
        from_ref: From reference (default: HEAD for staged, parent of HEAD otherwise)
        to_ref: To reference (default: None for staged, HEAD otherwise)
        staged: Whether to show staged changes
        path_filter: Filter by path
        context_lines: Number of context lines to show
    
    Returns:
        Dictionary with diff information
    """
    request = {
        "method": "diff",
        "params": {
            "path": path,
            "from_ref": from_ref,
            "to_ref": to_ref,
            "staged": staged,
            "path_filter": path_filter,
            "context_lines": context_lines
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute diff command"})

@mcp.tool()
async def merge(path: str = None, branch: str = None, 
              commit_message: Optional[str] = None, no_commit: bool = False,
              no_ff: bool = False) -> Dict[str, Any]:
    """
    Join two or more development histories together.
    
    Args:
        path: Path to the repository (default: current directory)
        branch: Branch to merge
        commit_message: Custom commit message for the merge
        no_commit: Don't automatically commit the merge
        no_ff: Don't fast-forward merge
    
    Returns:
        Dictionary with merge operation results
    """
    request = {
        "method": "merge",
        "params": {
            "path": path,
            "branch": branch,
            "commit_message": commit_message,
            "no_commit": no_commit,
            "no_ff": no_ff
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute merge command"})

@mcp.tool()
async def show(path: str = None, object_name: str = "HEAD") -> Dict[str, Any]:
    """
    Show various types of Git objects.
    
    Args:
        path: Path to the repository (default: current directory)
        object_name: Object to show (default: HEAD)
    
    Returns:
        Dictionary with object information
    """
    request = {
        "method": "show",
        "params": {
            "path": path,
            "object_name": object_name
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute show command"})

@mcp.tool()
async def reset(path: str = None, mode: str = "mixed", 
              target: str = "HEAD", paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Reset current HEAD to the specified state.
    
    Args:
        path: Path to the repository (default: current directory)
        mode: Reset mode (soft, mixed, hard)
        target: Target commit to reset to
        paths: Optional list of paths to reset (for mixed and soft modes)
    
    Returns:
        Dictionary with reset operation results
    """
    request = {
        "method": "reset",
        "params": {
            "path": path,
            "mode": mode,
            "target": target,
            "paths": paths
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute reset command"})

@mcp.tool()
async def stash(path: str = None, command: str = "push", 
              message: Optional[str] = None, include_untracked: bool = False,
              stash_index: Optional[int] = None) -> Dict[str, Any]:
    """
    Stash changes in the working directory.
    
    Args:
        path: Path to the repository (default: current directory)
        command: Stash command (push, pop, apply, list, drop, clear)
        message: Optional message for stash push
        include_untracked: Include untracked files in stash
        stash_index: Index of stash for pop, apply, drop commands
    
    Returns:
        Dictionary with stash operation results
    """
    request = {
        "method": "stash",
        "params": {
            "path": path,
            "command": command,
            "message": message,
            "include_untracked": include_untracked,
            "stash_index": stash_index
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute stash command"})

@mcp.tool()
async def tag(path: str = None, name: Optional[str] = None, 
            target: str = "HEAD", message: Optional[str] = None,
            delete: bool = False, force: bool = False) -> Dict[str, Any]:
    """
    Create, list, delete or verify a tag object.
    
    Args:
        path: Path to the repository (default: current directory)
        name: Name of the tag
        target: Target to tag (default: HEAD)
        message: Optional message for annotated tag
        delete: Whether to delete the tag
        force: Whether to force tag creation or deletion
    
    Returns:
        Dictionary with tag operation results
    """
    request = {
        "method": "tag",
        "params": {
            "path": path,
            "name": name,
            "target": target,
            "message": message,
            "delete": delete,
            "force": force
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute tag command"})

@mcp.tool()
async def blame(path: str = None, file_path: str = None, 
              rev: str = "HEAD") -> Dict[str, Any]:
    """
    Show what revision and author last modified each line of a file.
    
    Args:
        path: Path to the repository (default: current directory)
        file_path: Path to the file to blame
        rev: Revision to blame (default: HEAD)
    
    Returns:
        Dictionary with blame information
    """
    request = {
        "method": "blame",
        "params": {
            "path": path,
            "file_path": file_path,
            "rev": rev
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute blame command"})

@mcp.tool()
async def grep(path: str = None, pattern: str = None, 
             revision: str = "HEAD", ignore_case: bool = False,
             word_regexp: bool = False, paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Search for a pattern in tracked files.
    
    Args:
        path: Path to the repository (default: current directory)
        pattern: Pattern to search for
        revision: Revision to search in (default: HEAD)
        ignore_case: Whether to ignore case
        word_regexp: Whether to match whole words
        paths: Optional list of paths to search
    
    Returns:
        Dictionary with grep results
    """
    request = {
        "method": "git_grep",  # Note the difference in method name
        "params": {
            "path": path,
            "pattern": pattern,
            "revision": revision,
            "ignore_case": ignore_case,
            "word_regexp": word_regexp,
            "paths": paths
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute grep command"})

@mcp.tool()
async def context(path: str = None, details: str = "all") -> Dict[str, Any]:
    """
    Get comprehensive context about the current Git repository.
    
    Args:
        path: Path to the repository (default: current directory)
        details: Level of detail to include ("basic", "standard", "all")
    
    Returns:
        Dictionary with repository context information
    """
    request = {
        "method": "context",
        "params": {
            "path": path,
            "details": details
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute context command"})

@mcp.tool()
async def validate(path: str = None) -> Dict[str, Any]:
    """
    Validate the Git repository for common issues.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with validation results
    """
    request = {
        "method": "validate",
        "params": {
            "path": path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute validate command"})

@mcp.tool()
async def suggest_commit(path: str = None) -> Dict[str, Any]:
    """
    Analyze changes and suggest a commit message.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with suggestion information
    """
    request = {
        "method": "suggest_commit",
        "params": {
            "path": path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute suggest_commit command"})

# Advanced Git operations
@mcp.tool()
async def rebase(path: str = None, upstream: str = None, 
               branch: Optional[str] = None, onto: Optional[str] = None, 
               interactive: bool = False) -> Dict[str, Any]:
    """
    Reapply commits on top of another base tip.
    
    Args:
        path: Path to the repository (default: current directory)
        upstream: Upstream branch to rebase onto
        branch: Branch to rebase (default: current branch)
        onto: Starting point for reapplying commits (default: upstream)
        interactive: Whether to perform an interactive rebase
    
    Returns:
        Dictionary with rebase operation results
    """
    request = {
        "method": "rebase",
        "params": {
            "path": path,
            "upstream": upstream,
            "branch": branch,
            "onto": onto,
            "interactive": interactive
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute rebase command"})

@mcp.tool()
async def rebase_continue(path: str = None) -> Dict[str, Any]:
    """
    Continue a rebase operation after resolving conflicts.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with rebase continuation results
    """
    request = {
        "method": "rebase_continue",
        "params": {
            "path": path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute rebase_continue command"})

@mcp.tool()
async def rebase_abort(path: str = None) -> Dict[str, Any]:
    """
    Abort a rebase operation and return to the original state.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with rebase abort results
    """
    request = {
        "method": "rebase_abort",
        "params": {
            "path": path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute rebase_abort command"})

@mcp.tool()
async def cherry_pick(path: str = None, commit: str = None, 
                    no_commit: bool = False) -> Dict[str, Any]:
    """
    Apply the changes introduced by existing commits.
    
    Args:
        path: Path to the repository (default: current directory)
        commit: Commit to cherry-pick
        no_commit: Whether to apply changes without creating a commit
    
    Returns:
        Dictionary with cherry-pick operation results
    """
    request = {
        "method": "cherry_pick",
        "params": {
            "path": path,
            "commit": commit,
            "no_commit": no_commit
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute cherry_pick command"})

@mcp.tool()
async def worktree_add(path: str = None, worktree_path: str = None, 
                     branch: str = None, create_branch: bool = False) -> Dict[str, Any]:
    """
    Add a new working tree.
    
    Args:
        path: Path to the repository (default: current directory)
        worktree_path: Path to the new working tree
        branch: Branch to checkout
        create_branch: Whether to create a new branch
    
    Returns:
        Dictionary with worktree add operation results
    """
    request = {
        "method": "worktree_add",
        "params": {
            "path": path,
            "worktree_path": worktree_path,
            "branch": branch,
            "create_branch": create_branch
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute worktree_add command"})

@mcp.tool()
async def worktree_list(path: str = None) -> Dict[str, Any]:
    """
    List working trees.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with worktree list results
    """
    request = {
        "method": "worktree_list",
        "params": {
            "path": path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute worktree_list command"})

@mcp.tool()
async def worktree_remove(path: str = None, worktree_path: str = None, 
                        force: bool = False) -> Dict[str, Any]:
    """
    Remove a working tree.
    
    Args:
        path: Path to the repository (default: current directory)
        worktree_path: Path to the working tree to remove
        force: Whether to force removal
    
    Returns:
        Dictionary with worktree remove operation results
    """
    request = {
        "method": "worktree_remove",
        "params": {
            "path": path,
            "worktree_path": worktree_path,
            "force": force
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute worktree_remove command"})

@mcp.tool()
async def submodule_add(path: str = None, repo_url: str = None, 
                      target_path: Optional[str] = None, 
                      branch: Optional[str] = None) -> Dict[str, Any]:
    """
    Add a submodule.
    
    Args:
        path: Path to the repository (default: current directory)
        repo_url: URL of the repository to add as a submodule
        target_path: Path where the submodule will be added (default: repo name)
        branch: Branch to checkout
    
    Returns:
        Dictionary with submodule add operation results
    """
    request = {
        "method": "submodule_add",
        "params": {
            "path": path,
            "repo_url": repo_url,
            "target_path": target_path,
            "branch": branch
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute submodule_add command"})

@mcp.tool()
async def submodule_update(path: str = None, submodule_path: Optional[str] = None, 
                         init: bool = True, recursive: bool = False) -> Dict[str, Any]:
    """
    Update submodules.
    
    Args:
        path: Path to the repository (default: current directory)
        submodule_path: Path to the submodule to update (default: all submodules)
        init: Whether to initialize new submodules
        recursive: Whether to update recursively
    
    Returns:
        Dictionary with submodule update operation results
    """
    request = {
        "method": "submodule_update",
        "params": {
            "path": path,
            "submodule_path": submodule_path,
            "init": init,
            "recursive": recursive
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute submodule_update command"})

@mcp.tool()
async def submodule_list(path: str = None) -> Dict[str, Any]:
    """
    List submodules.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with submodule list results
    """
    request = {
        "method": "submodule_list",
        "params": {
            "path": path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute submodule_list command"})

@mcp.tool()
async def check_repository(path: str = None) -> Dict[str, Any]:
    """
    Perform comprehensive health check on repository.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with health check results
    """
    request = {
        "method": "check_repository",
        "params": {
            "path": path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute check_repository command"})

@mcp.tool()
async def suggest_optimization(path: str = None) -> Dict[str, Any]:
    """
    Suggest repository optimizations.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with optimization suggestions
    """
    request = {
        "method": "suggest_optimization",
        "params": {
            "path": path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute suggest_optimization command"})

@mcp.tool()
async def list_conflicts(path: str = None) -> Dict[str, Any]:
    """
    List all conflicts in the repository.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with conflict information
    """
    request = {
        "method": "list_conflicts",
        "params": {
            "path": path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute list_conflicts command"})

@mcp.tool()
async def resolve_conflict(path: str = None, file_path: str = None, 
                         resolution: str = None, content: Optional[str] = None) -> Dict[str, Any]:
    """
    Resolve a conflict for a specific file.
    
    Args:
        path: Path to the repository (default: current directory)
        file_path: Path to the conflicted file
        resolution: Resolution type (ours, theirs, custom)
        content: Custom content if resolution is 'custom'
    
    Returns:
        Dictionary with resolution result
    """
    request = {
        "method": "resolve_conflict",
        "params": {
            "path": path,
            "file_path": file_path,
            "resolution": resolution,
            "content": content
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute resolve_conflict command"})

@mcp.tool()
async def repair_repository(path: str = None) -> Dict[str, Any]:
    """
    Attempt to repair a Git repository.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with repair results
    """
    request = {
        "method": "repair_repository",
        "params": {
            "path": path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute repair_repository command"})

@mcp.tool()
async def restore_backup(path: str = None, backup_path: str = None) -> Dict[str, Any]:
    """
    Restore a backup of a Git repository.
    
    Args:
        path: Path to the repository (default: current directory)
        backup_path: Path to the backup
    
    Returns:
        Dictionary with restore results
    """
    request = {
        "method": "restore_backup",
        "params": {
            "path": path,
            "backup_path": backup_path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute restore_backup command"})

@mcp.tool()
async def fix_corrupted_index(path: str = None) -> Dict[str, Any]:
    """
    Fix a corrupted Git index.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with fix results
    """
    request = {
        "method": "fix_corrupted_index",
        "params": {
            "path": path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute fix_corrupted_index command"})

@mcp.tool()
async def fix_detached_head(path: str = None, branch: Optional[str] = None) -> Dict[str, Any]:
    """
    Fix a detached HEAD state by pointing it to a branch.
    
    Args:
        path: Path to the repository (default: current directory)
        branch: Branch to point HEAD to (default: create a new branch)
    
    Returns:
        Dictionary with fix results
    """
    request = {
        "method": "fix_detached_head",
        "params": {
            "path": path,
            "branch": branch
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute fix_detached_head command"})

@mcp.tool()
async def fix_missing_refs(path: str = None) -> Dict[str, Any]:
    """
    Fix missing references in a Git repository.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with fix results
    """
    request = {
        "method": "fix_missing_refs",
        "params": {
            "path": path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute fix_missing_refs command"})

@mcp.tool()
async def recover_lost_commits(path: str = None) -> Dict[str, Any]:
    """
    Recover lost commits in a Git repository using reflog.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with recovery results
    """
    request = {
        "method": "recover_lost_commits",
        "params": {
            "path": path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute recover_lost_commits command"})

@mcp.tool()
async def generate_ssh_key(key_type: str = "rsa", bits: int = 4096, 
                         comment: str = "PyGit2 SSH Key", passphrase: str = "",
                         output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a new SSH key pair.
    
    Args:
        key_type: SSH key type (rsa, ed25519, ecdsa)
        bits: Key size in bits (for RSA and ECDSA)
        comment: Key comment
        passphrase: Key passphrase
        output_dir: Output directory
    
    Returns:
        Dictionary with key information
    """
    request = {
        "method": "generate_ssh_key",
        "params": {
            "key_type": key_type,
            "bits": bits,
            "comment": comment,
            "passphrase": passphrase,
            "output_dir": output_dir
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute generate_ssh_key command"})

@mcp.tool()
async def import_ssh_key(private_key: str, public_key: Optional[str] = None,
                       output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Import SSH key pair.
    
    Args:
        private_key: Private key content or file path
        public_key: Public key content or file path
        output_dir: Output directory
    
    Returns:
        Dictionary with key information
    """
    request = {
        "method": "import_ssh_key",
        "params": {
            "private_key": private_key,
            "public_key": public_key,
            "output_dir": output_dir
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute import_ssh_key command"})

@mcp.tool()
async def verify_ssh_key(private_key_path: str, 
                       public_key_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify SSH key pair.
    
    Args:
        private_key_path: Path to private key file
        public_key_path: Path to public key file
    
    Returns:
        Dictionary with verification results
    """
    request = {
        "method": "verify_ssh_key",
        "params": {
            "private_key_path": private_key_path,
            "public_key_path": public_key_path
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute verify_ssh_key command"})

@mcp.tool()
async def test_ssh_connection(host: str, port: int = 22, username: str = "git",
                            private_key_path: Optional[str] = None,
                            timeout: int = 10) -> Dict[str, Any]:
    """
    Test SSH connection.
    
    Args:
        host: Host to connect to
        port: Port to connect to
        username: Username to use
        private_key_path: Path to private key file
        timeout: Connection timeout in seconds
    
    Returns:
        Dictionary with test results
    """
    request = {
        "method": "test_ssh_connection",
        "params": {
            "host": host,
            "port": port,
            "username": username,
            "private_key_path": private_key_path,
            "timeout": timeout
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute test_ssh_connection command"})

@mcp.tool()
async def configure_auth(auth_type: str, **kwargs) -> Dict[str, Any]:
    """
    Configure authentication.
    
    Args:
        auth_type: Authentication type (token, ssh, username_password)
        **kwargs: Authentication parameters
    
    Returns:
        Dictionary with configuration result
    """
    request = {
        "method": "configure_auth",
        "params": {
            "auth_type": auth_type,
            **kwargs
        }
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute configure_auth command"})

@mcp.tool()
async def get_api_documentation() -> Dict[str, Any]:
    """
    Get API documentation for all Git operations.
    
    Returns:
        Dictionary with API documentation
    """
    request = {
        "method": "get_api_documentation",
        "params": {}
    }
    
    response = pygit2_mcp.handle_request(request)
    return response.get("result", {"success": False, "message": "Failed to execute get_api_documentation command"})

if __name__ == "__main__":
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
