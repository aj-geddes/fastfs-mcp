#!/usr/bin/env python3
"""
Module: fastfs_mcp/git/base.py
Purpose: Git operation tools powered by PyGit2 for fastfs-mcp MCP server.

Sections:
- Repository management: find_repository, git_init, git_clone
- Status & Information: git_status, git_log, git_show
- File operations: git_add, git_commit, git_reset
- Branch operations: git_branch, git_checkout, git_merge
- Remote operations: git_remote, git_push, git_pull, git_fetch
- Diff & Compare: git_diff, git_blame
- Utility functions: format_commit, format_diff, logging utilities

All Git operations return structured responses with success status and detailed information.
"""

import os
import re
import logging
import glob
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple

import pygit2

# Logging setup
logger = logging.getLogger("fastfs-mcp-git")

def log_debug(message: str) -> None:
    """Log a debug message."""
    logger.debug(message)

def log_error(message: str) -> None:
    """Log an error message."""
    logger.error(message)

def find_repository(path: Optional[str] = None) -> Optional[pygit2.Repository]:
    """
    Find a Git repository at the given path or current directory.
    
    Args:
        path: Path to look for repository (default: current directory)
    
    Returns:
        Repository object or None if not found
    """
    try:
        if path:
            return pygit2.Repository(path)
        else:
            # Start from current directory and search upward
            current_dir = os.getcwd()
            return pygit2.Repository(pygit2.discover_repository(current_dir))
    except pygit2.GitError:
        return None

def format_commit(commit: pygit2.Commit) -> Dict[str, Any]:
    """
    Format a commit object into a dictionary.
    
    Args:
        commit: Commit object to format
    
    Returns:
        Dictionary with commit information
    """
    parents = [str(parent) for parent in commit.parent_ids]
    
    result = {
        "id": str(commit.id),
        "short_id": str(commit.id)[:7],
        "message": commit.message,
        "summary": commit.message.split('\n', 1)[0] if commit.message else "",
        "author": {
            "name": commit.author.name,
            "email": commit.author.email,
            "time": datetime.fromtimestamp(commit.author.time).isoformat()
        },
        "committer": {
            "name": commit.committer.name,
            "email": commit.committer.email,
            "time": datetime.fromtimestamp(commit.committer.time).isoformat()
        },
        "parents": parents,
        "is_merge": len(parents) > 1
    }
    
    return result

def format_diff(diff: pygit2.Diff) -> Dict[str, Any]:
    """
    Format a diff object into a dictionary.
    
    Args:
        diff: Diff object to format
    
    Returns:
        Dictionary with diff information
    """
    # Get stats
    stats = {
        "files_changed": diff.stats.files_changed,
        "insertions": diff.stats.insertions,
        "deletions": diff.stats.deletions
    }
    
    # Format each change
    changes = []
    for patch in diff:
        change = {
            "old_file_path": patch.delta.old_file.path,
            "new_file_path": patch.delta.new_file.path,
            "status": _get_status_from_delta(patch.delta.status),
            "additions": 0,
            "deletions": 0,
            "is_binary": patch.delta.is_binary,
            "hunks": []
        }
        
        # If not binary, format hunks
        if not patch.delta.is_binary:
            for hunk in patch.hunks:
                hunk_data = {
                    "old_start": hunk.old_start,
                    "old_lines": hunk.old_lines,
                    "new_start": hunk.new_start,
                    "new_lines": hunk.new_lines,
                    "lines": []
                }
                
                for line in hunk.lines:
                    origin = line.origin
                    if origin == '+':
                        change["additions"] += 1
                    elif origin == '-':
                        change["deletions"] += 1
                    
                    line_data = {
                        "origin": origin,
                        "content": line.content,
                        "old_lineno": line.old_lineno,
                        "new_lineno": line.new_lineno
                    }
                    
                    hunk_data["lines"].append(line_data)
                
                change["hunks"].append(hunk_data)
        
        changes.append(change)
    
    return {
        "stats": stats,
        "changes": changes
    }

def _get_status_from_delta(status: int) -> str:
    """
    Convert a delta status code to a string.
    
    Args:
        status: Delta status code
    
    Returns:
        Status string
    """
    if status == pygit2.GIT_DELTA_ADDED:
        return "added"
    elif status == pygit2.GIT_DELTA_DELETED:
        return "deleted"
    elif status == pygit2.GIT_DELTA_MODIFIED:
        return "modified"
    elif status == pygit2.GIT_DELTA_RENAMED:
        return "renamed"
    elif status == pygit2.GIT_DELTA_COPIED:
        return "copied"
    elif status == pygit2.GIT_DELTA_UNMODIFIED:
        return "unmodified"
    elif status == pygit2.GIT_DELTA_UNTRACKED:
        return "untracked"
    elif status == pygit2.GIT_DELTA_TYPECHANGE:
        return "typechange"
    elif status == pygit2.GIT_DELTA_UNREADABLE:
        return "unreadable"
    elif status == pygit2.GIT_DELTA_CONFLICTED:
        return "conflicted"
    else:
        return "unknown"

def _is_binary_blob(blob: pygit2.Blob) -> bool:
    """Check if a blob is binary by looking for null bytes and text encoding."""
    # Check for null bytes in the first chunk of data
    chunk_size = min(8000, blob.size)
    data = blob.data[:chunk_size]
    
    # If there are null bytes, it's likely binary
    if b'\x00' in data:
        return True
    
    # Try to decode as UTF-8
    try:
        data.decode('utf-8')
        return False
    except UnicodeDecodeError:
        return True

def _get_tree_entry_type(type_id: int) -> str:
    """Convert a tree entry type code to a string."""
    if type_id == pygit2.GIT_OBJ_BLOB:
        return "blob"
    elif type_id == pygit2.GIT_OBJ_TREE:
        return "tree"
    elif type_id == pygit2.GIT_OBJ_COMMIT:
        return "commit"
    elif type_id == pygit2.GIT_OBJ_TAG:
        return "tag"
    else:
        return "unknown"

def git_init(directory: str = ".", bare: bool = False, initial_commit: bool = False) -> Dict[str, Any]:
    """
    Initialize a new Git repository.
    
    Args:
        directory: Directory to initialize the repository in
        bare: Whether to create a bare repository
        initial_commit: Whether to create an initial commit
    
    Returns:
        Dictionary with initialization results
    """
    try:
        # Create directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # Initialize repository
        repo_path = pygit2.init_repository(directory, bare=bare)
        repo = pygit2.Repository(repo_path)
        
        result = {
            "success": True,
            "message": f"Initialized {'bare ' if bare else ''}repository in {os.path.abspath(directory)}",
            "path": os.path.abspath(directory)
        }
        
        # Create initial commit if requested
        if initial_commit and not bare:
            # Create a file
            readme_path = os.path.join(directory, "README.md")
            with open(readme_path, "w") as f:
                f.write("# Git Repository\n\nInitialized with FastFS-MCP.\n")
            
            # Add the file
            repo.index.add("README.md")
            repo.index.write()
            
            # Create the commit
            author = None
            try:
                author = pygit2.Signature(
                    repo.config['user.name'],
                    repo.config['user.email']
                )
            except KeyError:
                author = pygit2.Signature('FastFS-MCP', 'mcp@fastfs.com')
            
            tree = repo.index.write_tree()
            commit_id = repo.create_commit(
                'HEAD',
                author,
                author,
                'Initial commit',
                tree,
                []
            )
            
            result["initial_commit"] = {
                "id": str(commit_id),
                "message": "Initial commit"
            }
        
        return result
    except Exception as e:
        log_error(f"Error initializing repository: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_clone(repo_url: str, target_dir: Optional[str] = None, 
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
    try:
        # Set default options
        if options is None:
            options = {}
        
        # Determine target directory
        if not target_dir:
            # Use repository name as target directory
            repo_name = repo_url.rstrip('/').split('/')[-1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            target_dir = repo_name
        
        # Check if target directory exists
        if os.path.exists(target_dir):
            if os.path.isdir(target_dir) and os.listdir(target_dir):
                return {
                    "success": False,
                    "message": f"Target directory '{target_dir}' already exists and is not empty"
                }
        
        # Prepare clone options
        clone_options = {}
        
        # Callbacks for authentication
        if 'callbacks' in options:
            clone_options['callbacks'] = options['callbacks']
        
        # Branch to clone
        if 'branch' in options:
            clone_options['checkout_branch'] = options['branch']
        
        # Depth for shallow clone
        if 'depth' in options:
            clone_options['fetch_opts'] = {
                'depth': options['depth']
            }
        
        # Clone the repository
        repo_path = pygit2.clone_repository(repo_url, target_dir, **clone_options)
        repo = pygit2.Repository(repo_path)
        
        # Get repository information
        head_ref = repo.head
        head_commit = head_ref.peel(pygit2.Commit)
        
        return {
            "success": True,
            "message": f"Cloned repository to {os.path.abspath(target_dir)}",
            "path": os.path.abspath(target_dir),
            "head": {
                "branch": head_ref.shorthand if not repo.head_is_detached else None,
                "commit": str(head_commit.id),
                "message": head_commit.message.split('\n', 1)[0] if head_commit.message else ""
            }
        }
    except Exception as e:
        log_error(f"Error cloning repository: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_status(path: str = None) -> Dict[str, Any]:
    """
    Show the working tree status.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with status information
    """
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Get status
        status = repo.status()
        
        # Process status
        files = []
        counts = {
            "staged": 0,
            "unstaged": 0,
            "untracked": 0,
            "total": 0
        }
        
        for filepath, flags in status.items():
            file_status = {
                "path": filepath,
                "staged": False,
                "unstaged": False,
                "untracked": False,
                "status": []
            }
            
            # Check status flags
            if flags & pygit2.GIT_STATUS_INDEX_NEW:
                file_status["staged"] = True
                file_status["status"].append("new")
                counts["staged"] += 1
            elif flags & pygit2.GIT_STATUS_INDEX_MODIFIED:
                file_status["staged"] = True
                file_status["status"].append("modified")
                counts["staged"] += 1
            elif flags & pygit2.GIT_STATUS_INDEX_DELETED:
                file_status["staged"] = True
                file_status["status"].append("deleted")
                counts["staged"] += 1
            elif flags & pygit2.GIT_STATUS_INDEX_RENAMED:
                file_status["staged"] = True
                file_status["status"].append("renamed")
                counts["staged"] += 1
            elif flags & pygit2.GIT_STATUS_INDEX_TYPECHANGE:
                file_status["staged"] = True
                file_status["status"].append("typechange")
                counts["staged"] += 1
            
            if flags & pygit2.GIT_STATUS_WT_NEW:
                file_status["untracked"] = True
                file_status["status"].append("untracked")
                counts["untracked"] += 1
            elif flags & pygit2.GIT_STATUS_WT_MODIFIED:
                file_status["unstaged"] = True
                file_status["status"].append("modified")
                counts["unstaged"] += 1
            elif flags & pygit2.GIT_STATUS_WT_DELETED:
                file_status["unstaged"] = True
                file_status["status"].append("deleted")
                counts["unstaged"] += 1
            elif flags & pygit2.GIT_STATUS_WT_RENAMED:
                file_status["unstaged"] = True
                file_status["status"].append("renamed")
                counts["unstaged"] += 1
            elif flags & pygit2.GIT_STATUS_WT_TYPECHANGE:
                file_status["unstaged"] = True
                file_status["status"].append("typechange")
                counts["unstaged"] += 1
            
            files.append(file_status)
        
        # Update total count
        counts["total"] = len(files)
        
        # Determine if repository is clean
        is_clean = counts["total"] == 0
        
        # Determine current branch
        branch = None
        if not repo.head_is_detached:
            branch = repo.head.shorthand
        
        return {
            "success": True,
            "is_clean": is_clean,
            "branch": branch,
            "files": files,
            "counts": counts
        }
    except Exception as e:
        log_error(f"Error getting status: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_add(paths: Union[str, List[str]], path: str = None) -> Dict[str, Any]:
    """
    Add file(s) to the Git staging area.
    
    Args:
        paths: Path(s) to add
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with add operation results
    """
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Ensure paths is a list
        if isinstance(paths, str):
            paths = [paths]
        
        # Add files to the index
        index = repo.index
        added_files = []
        
        for file_path in paths:
            # Handle wildcards with glob
            if '*' in file_path or '?' in file_path:
                repo_dir = os.path.dirname(repo.path)
                glob_paths = glob.glob(os.path.join(repo_dir, file_path))
                for gp in glob_paths:
                    rel_path = os.path.relpath(gp, repo_dir)
                    if not os.path.isdir(gp):
                        index.add(rel_path)
                        added_files.append(rel_path)
            else:
                # Check if path is a directory
                full_path = os.path.join(os.path.dirname(repo.path), file_path)
                if os.path.isdir(full_path):
                    # Add all files in the directory
                    for root, _, files in os.walk(full_path):
                        for f in files:
                            file_full_path = os.path.join(root, f)
                            rel_path = os.path.relpath(file_full_path, os.path.dirname(repo.path))
                            index.add(rel_path)
                            added_files.append(rel_path)
                else:
                    index.add(file_path)
                    added_files.append(file_path)
        
        # Write the index
        index.write()
        
        return {
            "success": True,
            "message": f"Added {len(added_files)} file(s) to the staging area",
            "added_files": added_files
        }
    except Exception as e:
        log_error(f"Error adding files: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_reset(path: str = None, mode: str = "mixed", target: str = "HEAD", 
             paths: Optional[List[str]] = None) -> Dict[str, Any]:
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
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Resolve the target
        try:
            target_obj = repo.revparse_single(target)
            if not isinstance(target_obj, pygit2.Commit):
                target_obj = target_obj.peel(pygit2.Commit)
        except KeyError:
            return {
                "success": False,
                "message": f"Target '{target}' not found"
            }
        
        # Path-specific reset (index only)
        if paths:
            # Only reset specific paths
            index = repo.index
            tree = target_obj.tree
            
            for path_pattern in paths:
                # Handle wildcards with glob
                if '*' in path_pattern or '?' in path_pattern:
                    import glob
                    repo_dir = os.path.dirname(repo.path)
                    glob_paths = glob.glob(os.path.join(repo_dir, path_pattern))
                    for gp in glob_paths:
                        rel_path = os.path.relpath(gp, repo_dir)
                        try:
                            # Find the tree entry for this path
                            entry = tree[rel_path]
                            index.add(entry.id, rel_path)
                        except KeyError:
                            # If path doesn't exist in the target, remove it from index
                            try:
                                index.remove(rel_path)
                            except KeyError:
                                pass
                else:
                    try:
                        # Find the tree entry for this path
                        entry = tree[path_pattern]
                        index.add(entry.id, path_pattern)
                    except KeyError:
                        # If path doesn't exist in the target, remove it from index
                        try:
                            index.remove(path_pattern)
                        except KeyError:
                            pass
            
            index.write()
            
            return {
                "success": True,
                "message": f"Reset paths to {target}",
                "paths": paths
            }
        
        # Full reset
        if mode == "soft":
            # Just move HEAD to the target commit
            reference = repo.head
            reference.set_target(target_obj.id)
            
            return {
                "success": True,
                "message": f"Soft reset to {target}",
                "target": str(target_obj.id)
            }
            
        elif mode == "mixed":
            # Move HEAD and reset index
            reference = repo.head
            reference.set_target(target_obj.id)
            repo.reset(target_obj.id, pygit2.GIT_RESET_MIXED)
            
            return {
                "success": True,
                "message": f"Mixed reset to {target}",
                "target": str(target_obj.id)
            }
            
        elif mode == "hard":
            # Move HEAD, reset index, and checkout working directory
            repo.reset(target_obj.id, pygit2.GIT_RESET_HARD)
            
            return {
                "success": True,
                "message": f"Hard reset to {target}",
                "target": str(target_obj.id)
            }
            
        else:
            return {
                "success": False,
                "message": f"Unknown reset mode: {mode}"
            }
    except Exception as e:
        log_error(f"Error resetting to {target}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_commit(message: str, author_name: Optional[str] = None, 
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
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Check if there are staged changes
        status = repo.status()
        has_staged_changes = any(
            flags & (pygit2.GIT_STATUS_INDEX_NEW | 
                    pygit2.GIT_STATUS_INDEX_MODIFIED | 
                    pygit2.GIT_STATUS_INDEX_DELETED |
                    pygit2.GIT_STATUS_INDEX_RENAMED |
                    pygit2.GIT_STATUS_INDEX_TYPECHANGE)
            for flags in status.values()
        )
        
        if not has_staged_changes and not amend:
            return {
                "success": False,
                "message": "No changes added to commit"
            }
        
        # Get author signature
        author = None
        try:
            name = author_name or repo.config['user.name']
            email = author_email or repo.config['user.email']
            author = pygit2.Signature(name, email)
        except KeyError:
            if author_name and author_email:
                author = pygit2.Signature(author_name, author_email)
            else:
                return {
                    "success": False,
                    "message": "Author name and email are required"
                }
        
        # Create commit
        parents = []
        if not repo.is_empty:
            if amend:
                # For amend, use the parent(s) of the current HEAD
                head_commit = repo.head.peel(pygit2.Commit)
                parents = list(head_commit.parent_ids)
            else:
                # Normal commit uses HEAD as parent
                parents = [repo.head.target]
        
        tree = repo.index.write_tree()
        
        commit_id = repo.create_commit(
            'HEAD',
            author,
            author,
            message,
            tree,
            parents
        )
        
        commit = repo.get(commit_id)
        
        return {
            "success": True,
            "message": f"{'Amended' if amend else 'Created'} commit {str(commit_id)[:7]}",
            "commit": format_commit(commit)
        }
    except Exception as e:
        log_error(f"Error committing changes: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_merge(path: str = None, branch: str = None, commit_message: Optional[str] = None,
             no_commit: bool = False, no_ff: bool = False) -> Dict[str, Any]:
    """
    Merge a branch into the current branch.
    
    Args:
        path: Path to the repository (default: current directory)
        branch: Branch to merge
        commit_message: Custom commit message for the merge
        no_commit: Don't automatically commit the merge
        no_ff: Don't fast-forward merge
    
    Returns:
        Dictionary with merge operation results
    """
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        if not branch:
            return {
                "success": False,
                "message": "Branch to merge is required"
            }
        
        # Check if the branch exists
        if f"refs/heads/{branch}" not in repo.references:
            return {
                "success": False,
                "message": f"Branch '{branch}' not found"
            }
        
        # Get the branch reference
        branch_ref = repo.references[f"refs/heads/{branch}"]
        branch_commit = branch_ref.peel(pygit2.Commit)
        
        # Get current HEAD
        if repo.head_is_detached:
            return {
                "success": False,
                "message": "Cannot merge when HEAD is detached"
            }
        
        head_ref = repo.head
        head_commit = head_ref.peel(pygit2.Commit)
        
        # Check if this is a fast-forward merge
        is_ff = repo.merge_base(head_commit.id, branch_commit.id) == head_commit.id
        
        if is_ff and not no_ff:
            # Fast-forward merge
            repo.checkout_tree(branch_commit)
            head_ref.set_target(branch_commit.id)
            
            return {
                "success": True,
                "message": f"Fast-forward merge of '{branch}' into '{head_ref.shorthand}'",
                "merge_type": "fast-forward",
                "result_commit": str(branch_commit.id)
            }
        else:
            # Non-fast-forward merge
            repo.merge(branch_commit.id)
            
            # Check for conflicts
            index = repo.index
            if index.conflicts:
                conflicts = []
                for conflict in index.conflicts:
                    conflict_info = {
                        "ancestor": conflict[0].path if conflict[0] else None,
                        "ours": conflict[1].path if conflict[1] else None,
                        "theirs": conflict[2].path if conflict[2] else None
                    }
                    conflicts.append(conflict_info)
                
                # Abort the merge
                repo.state_cleanup()
                
                return {
                    "success": False,
                    "message": "Merge conflicts detected",
                    "conflicts": conflicts
                }
            
            # No conflicts, create the merge commit if requested
            if not no_commit:
                author = None
                try:
                    author = pygit2.Signature(
                        repo.config['user.name'],
                        repo.config['user.email']
                    )
                except KeyError:
                    author = pygit2.Signature('FastFS-MCP', 'mcp@fastfs.com')
                
                # Determine commit message
                if not commit_message:
                    commit_message = f"Merge branch '{branch}' into {head_ref.shorthand}"
                
                # Write the index as a tree
                tree_id = index.write_tree()
                
                # Create the merge commit
                commit_id = repo.create_commit(
                    'HEAD',
                    author,
                    author,
                    commit_message,
                    tree_id,
                    [head_commit.id, branch_commit.id]
                )
                
                # Clean up the merge state
                repo.state_cleanup()
                
                commit = repo.get(commit_id)
                
                return {
                    "success": True,
                    "message": f"Merged '{branch}' into '{head_ref.shorthand}'",
                    "merge_type": "merge",
                    "result_commit": str(commit_id),
                    "commit": format_commit(commit)
                }
            else:
                # No commit requested, just stage the changes
                
                return {
                    "success": True,
                    "message": f"Merged '{branch}' into '{head_ref.shorthand}' (staged, not committed)",
                    "merge_type": "no-commit"
                }
    except Exception as e:
        log_error(f"Error merging branch {branch}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_show(path: str = None, object_name: str = "HEAD") -> Dict[str, Any]:
    """
    Show various types of Git objects.
    
    Args:
        path: Path to the repository (default: current directory)
        object_name: Object to show (default: HEAD)
    
    Returns:
        Dictionary with object information
    """
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        try:
            obj = repo.revparse_single(object_name)
            
            if isinstance(obj, pygit2.Commit):
                # Show commit
                commit = obj
                
                # Get diff
                if commit.parents:
                    parent = commit.parents[0]
                    diff = parent.tree.diff_to_tree(commit.tree)
                else:
                    # Initial commit
                    diff = commit.tree.diff_to_tree(None)
                
                return {
                    "success": True,
                    "type": "commit",
                    "commit": format_commit(commit),
                    "diff": format_diff(diff)
                }
            
            elif isinstance(obj, pygit2.Tree):
                # Show tree
                tree = obj
                entries = []
                
                for entry in tree:
                    entry_info = {
                        "name": entry.name,
                        "id": str(entry.id),
                        "type": _get_tree_entry_type(entry.type),
                        "filemode": entry.filemode
                    }
                    
                    entries.append(entry_info)
                
                return {
                    "success": True,
                    "type": "tree",
                    "tree": {
                        "id": str(tree.id),
                        "entries": entries
                    }
                }
            
            elif isinstance(obj, pygit2.Blob):
                # Show blob
                blob = obj
                
                # Determine if blob is binary
                is_binary = _is_binary_blob(blob)
                
                result = {
                    "success": True,
                    "type": "blob",
                    "blob": {
                        "id": str(blob.id),
                        "size": blob.size,
                        "is_binary": is_binary
                    }
                }
                
                # Add content for text blobs
                if not is_binary:
                    try:
                        result["blob"]["content"] = blob.data.decode('utf-8')
                    except UnicodeDecodeError:
                        result["blob"]["is_binary"] = True
                
                return result
            
            elif isinstance(obj, pygit2.Tag):
                # Show tag
                tag = obj
                
                return {
                    "success": True,
                    "type": "tag",
                    "tag": {
                        "id": str(tag.id),
                        "name": tag.name,
                        "message": tag.message,
                        "tagger": {
                            "name": tag.tagger.name,
                            "email": tag.tagger.email,
                            "time": datetime.fromtimestamp(tag.tagger.time).isoformat()
                        },
                        "target": {
                            "id": str(tag.target.id),
                            "type": tag.target.type_str
                        }
                    }
                }
            
            else:
                # Other object type
                return {
                    "success": True,
                    "type": obj.type_str,
                    "object": {
                        "id": str(obj.id),
                        "type": obj.type_str
                    }
                }
            
        except KeyError:
            return {
                "success": False,
                "message": f"Object '{object_name}' not found"
            }
    except Exception as e:
        log_error(f"Error showing object {object_name}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

# Additional Git functions can be implemented as needed
