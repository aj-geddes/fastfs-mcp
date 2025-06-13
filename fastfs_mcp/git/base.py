#!/usr/bin/env python3
"""
Basic Git operations for FastFS-MCP using PyGit2.

This module provides the core Git operations for FastFS-MCP using PyGit2.
"""

import os
import re
import logging
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
                import glob
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

def git_log(path: str = None, max_count: int = 10, skip: int = 0,
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
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        if repo.is_empty:
            return {
                "success": True,
                "message": "Repository is empty",
                "commits": []
            }
        
        # Resolve the reference
        start = repo.head.target
        if ref:
            try:
                ref_obj = repo.revparse_single(ref)
                if isinstance(ref_obj, pygit2.Reference):
                    start = ref_obj.target
                elif isinstance(ref_obj, pygit2.Commit):
                    start = ref_obj.id
                else:
                    start = ref_obj.peel(pygit2.Commit).id
            except KeyError:
                return {
                    "success": False,
                    "message": f"Reference '{ref}' not found"
                }
        
        # Create walker
        walker = repo.walk(start, pygit2.GIT_SORT_TIME)
        
        # Apply path filter if provided
        if path_filter:
            walker.push_glob(path_filter)
        
        # Skip commits
        if skip > 0:
            for _ in range(skip):
                try:
                    next(walker)
                except StopIteration:
                    break
        
        # Get commits
        commits = []
        count = 0
        
        for commit in walker:
            if count >= max_count:
                break
            
            commits.append(format_commit(commit))
            count += 1
        
        return {
            "success": True,
            "commits": commits,
            "count": len(commits)
        }
    except Exception as e:
        log_error(f"Error getting log: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_branch(name: Optional[str] = None, path: str = None,
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
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # List branches if no name provided
        if not name:
            branches = []
            head_ref = None
            
            if not repo.is_empty:
                try:
                    head_ref = repo.head.shorthand
                except pygit2.GitError:
                    # Detached HEAD or other issue
                    pass
            
            for branch_ref in repo.branches:
                branch_name = branch_ref
                if branch_name.startswith("refs/heads/"):
                    branch_name = branch_name[11:]  # Strip "refs/heads/"
                
                branch_info = {
                    "name": branch_name,
                    "is_head": head_ref == branch_name
                }
                
                try:
                    ref = repo.branches[branch_name]
                    commit = ref.peel(pygit2.Commit)
                    branch_info["commit"] = {
                        "id": str(commit.id),
                        "message": commit.message.split('\n', 1)[0] if commit.message else ""
                    }
                except (KeyError, ValueError):
                    pass
                
                branches.append(branch_info)
            
            return {
                "success": True,
                "branches": branches,
                "count": len(branches)
            }
        
        # Delete branch
        if delete:
            branch_ref = f"refs/heads/{name}"
            if branch_ref not in repo.references:
                return {
                    "success": False,
                    "message": f"Branch '{name}' not found"
                }
            
            # Check if it's the current branch
            if not repo.head_is_detached and repo.head.shorthand == name:
                return {
                    "success": False,
                    "message": f"Cannot delete branch '{name}' as it is the current branch"
                }
            
            # Check if the branch is merged
            if not force:
                # Check if the branch is merged into HEAD
                head_commit = repo.head.peel(pygit2.Commit)
                branch_commit = repo.branches[name].peel(pygit2.Commit)
                
                # Check if the branch commit is an ancestor of HEAD
                is_merged = repo.descendant_of(head_commit.id, branch_commit.id)
                
                if not is_merged:
                    return {
                        "success": False,
                        "message": f"Branch '{name}' is not fully merged. Use force=True to delete anyway."
                    }
            
            # Delete the branch
            repo.branches.delete(name)
            
            return {
                "success": True,
                "message": f"Deleted branch '{name}'"
            }
        
        # Create branch
        if f"refs/heads/{name}" in repo.references:
            return {
                "success": False,
                "message": f"Branch '{name}' already exists"
            }
        
        # Resolve start_point
        if start_point:
            try:
                start_obj = repo.revparse_single(start_point)
                if not isinstance(start_obj, pygit2.Commit):
                    start_obj = start_obj.peel(pygit2.Commit)
            except KeyError:
                return {
                    "success": False,
                    "message": f"Start point '{start_point}' not found"
                }
        else:
            # Use HEAD as start point
            if repo.is_empty:
                return {
                    "success": False,
                    "message": "Cannot create branch in empty repository without start_point"
                }
            
            start_obj = repo.head.peel(pygit2.Commit)
        
        # Create the branch
        repo.branches.create(name, start_obj)
        
        return {
            "success": True,
            "message": f"Created branch '{name}' at {str(start_obj.id)[:7]}",
            "branch": {
                "name": name,
                "commit": {
                    "id": str(start_obj.id),
                    "message": start_obj.message.split('\n', 1)[0] if start_obj.message else ""
                }
            }
        }
    except Exception as e:
        log_error(f"Error in branch operation: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_checkout(revision: str, path: str = None, 
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
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Check if revision exists
        branch_exists = f"refs/heads/{revision}" in repo.references
        
        # Create branch if requested
        if not branch_exists and create_branch:
            # Use HEAD as start point
            if repo.is_empty:
                return {
                    "success": False,
                    "message": "Cannot create branch in empty repository"
                }
            
            head_commit = repo.head.peel(pygit2.Commit)
            repo.branches.create(revision, head_commit)
            branch_exists = True
        
        # Check if the branch exists now
        if not branch_exists:
            try:
                target_obj = repo.revparse_single(revision)
            except KeyError:
                return {
                    "success": False,
                    "message": f"Revision '{revision}' not found"
                }
        
        # Checkout options
        checkout_strategy = pygit2.GIT_CHECKOUT_SAFE
        if force:
            checkout_strategy = pygit2.GIT_CHECKOUT_FORCE
        
        # Checkout the branch or revision
        if branch_exists:
            # Checkout branch
            branch = repo.branches[revision]
            repo.checkout(branch, strategy=checkout_strategy)
            
            # Get branch tip commit
            commit = branch.peel(pygit2.Commit)
            
            return {
                "success": True,
                "message": f"Switched to branch '{revision}'",
                "branch": revision,
                "commit": {
                    "id": str(commit.id),
                    "message": commit.message.split('\n', 1)[0] if commit.message else ""
                }
            }
        else:
            # Checkout revision
            repo.checkout_tree(target_obj, strategy=checkout_strategy)
            
            # Detach HEAD
            repo.set_head(target_obj.id)
            
            if isinstance(target_obj, pygit2.Commit):
                commit = target_obj
            else:
                commit = target_obj.peel(pygit2.Commit)
            
            return {
                "success": True,
                "message": f"Detached HEAD at {str(commit.id)[:7]}",
                "branch": None,
                "commit": {
                    "id": str(commit.id),
                    "message": commit.message.split('\n', 1)[0] if commit.message else ""
                }
            }
    except Exception as e:
        log_error(f"Error checking out {revision}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_remote(path: str = None, command: str = "list", 
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
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # List remotes
        if command == "list":
            remotes = []
            for remote_name in repo.remotes:
                remote = repo.remotes[remote_name]
                remotes.append({
                    "name": remote_name,
                    "url": remote.url
                })
            
            return {
                "success": True,
                "remotes": remotes,
                "count": len(remotes)
            }
        
        # Add remote
        elif command == "add":
            if not name:
                return {
                    "success": False,
                    "message": "Remote name is required"
                }
            
            if not url:
                return {
                    "success": False,
                    "message": "Remote URL is required"
                }
            
            # Check if remote already exists
            if name in repo.remotes:
                return {
                    "success": False,
                    "message": f"Remote '{name}' already exists"
                }
            
            # Add remote
            repo.remotes.create(name, url)
            
            return {
                "success": True,
                "message": f"Added remote '{name}' with URL '{url}'",
                "remote": {
                    "name": name,
                    "url": url
                }
            }
        
        # Remove remote
        elif command == "remove":
            if not name:
                return {
                    "success": False,
                    "message": "Remote name is required"
                }
            
            # Check if remote exists
            if name not in repo.remotes:
                return {
                    "success": False,
                    "message": f"Remote '{name}' not found"
                }
            
            # Get URL before removing
            remote_url = repo.remotes[name].url
            
            # Remove remote
            repo.remotes.delete(name)
            
            return {
                "success": True,
                "message": f"Removed remote '{name}'",
                "remote": {
                    "name": name,
                    "url": remote_url
                }
            }
        
        # Set URL
        elif command == "set-url":
            if not name:
                return {
                    "success": False,
                    "message": "Remote name is required"
                }
            
            if not url:
                return {
                    "success": False,
                    "message": "Remote URL is required"
                }
            
            # Check if remote exists
            if name not in repo.remotes:
                return {
                    "success": False,
                    "message": f"Remote '{name}' not found"
                }
            
            # Get old URL
            old_url = repo.remotes[name].url
            
            # Set URL
            repo.remotes.set_url(name, url)
            
            return {
                "success": True,
                "message": f"Set URL for remote '{name}'",
                "remote": {
                    "name": name,
                    "old_url": old_url,
                    "new_url": url
                }
            }
        
        else:
            return {
                "success": False,
                "message": f"Unknown remote command: {command}"
            }
    except Exception as e:
        log_error(f"Error in remote operation: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_push(path: str = None, remote: str = "origin", 
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
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Check if remote exists
        if remote not in repo.remotes:
            return {
                "success": False,
                "message": f"Remote '{remote}' not found"
            }
        
        # Determine refspecs if not provided
        if not refspecs:
            if repo.head_is_detached:
                return {
                    "success": False,
                    "message": "Cannot push when HEAD is detached without specifying refspecs"
                }
            
            current_branch = repo.head.shorthand
            refspecs = [f"refs/heads/{current_branch}:refs/heads/{current_branch}"]
        
        # Fallback to git command for pushing (pygit2 push can be limited)
        repo_dir = os.path.dirname(repo.path)
        cmd = ["git", "push", remote]
        
        if force:
            cmd.append("--force")
        
        # Add refspecs
        cmd.extend(refspecs)
        
        # Add token if provided
        env = os.environ.copy()
        if token:
            remote_url = repo.remotes[remote].url
            if remote_url.startswith("https://"):
                # Add token to URL
                if "@" in remote_url:
                    # URL already has credentials
                    return {
                        "success": False,
                        "message": f"Remote URL already contains credentials"
                    }
                
                # Extract domain part
                domain_part = remote_url[8:]  # Remove "https://"
                
                # Build new URL with token
                new_url = f"https://x-access-token:{token}@{domain_part}"
                
                # Set URL temporarily
                repo.remotes.set_url(remote, new_url)
        
        # Execute push command
        process = subprocess.run(
            cmd,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            env=env
        )
        
        # Restore original URL if token was used
        if token:
            repo.remotes.set_url(remote, remote_url)
        
        if process.returncode == 0:
            return {
                "success": True,
                "message": f"Pushed to {remote}",
                "refspecs": refspecs,
                "output": process.stdout.strip()
            }
        else:
            return {
                "success": False,
                "message": f"Push failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
    except Exception as e:
        log_error(f"Error pushing to {remote}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_pull(path: str = None, remote: str = "origin", 
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
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Check if remote exists
        if remote not in repo.remotes:
            return {
                "success": False,
                "message": f"Remote '{remote}' not found"
            }
        
        # Determine branch if not provided
        if not branch:
            if repo.head_is_detached:
                return {
                    "success": False,
                    "message": "Cannot pull when HEAD is detached without specifying branch"
                }
            
            branch = repo.head.shorthand
        
        # Fallback to git command for pulling (pygit2 pull is not directly available)
        repo_dir = os.path.dirname(repo.path)
        cmd = ["git", "pull", remote, branch]
        
        if fast_forward_only:
            cmd.append("--ff-only")
        
        # Add token if provided
        env = os.environ.copy()
        remote_url = None
        if token:
            remote_url = repo.remotes[remote].url
            if remote_url.startswith("https://"):
                # Add token to URL
                if "@" in remote_url:
                    # URL already has credentials
                    return {
                        "success": False,
                        "message": f"Remote URL already contains credentials"
                    }
                
                # Extract domain part
                domain_part = remote_url[8:]  # Remove "https://"
                
                # Build new URL with token
                new_url = f"https://x-access-token:{token}@{domain_part}"
                
                # Set URL temporarily
                repo.remotes.set_url(remote, new_url)
        
        # Execute pull command
        process = subprocess.run(
            cmd,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            env=env
        )
        
        # Restore original URL if token was used
        if token and remote_url:
            repo.remotes.set_url(remote, remote_url)
        
        if process.returncode == 0:
            return {
                "success": True,
                "message": f"Pulled from {remote}/{branch}",
                "output": process.stdout.strip()
            }
        else:
            return {
                "success": False,
                "message": f"Pull failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
    except Exception as e:
        log_error(f"Error pulling from {remote}/{branch}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_fetch(path: str = None, remote: str = "origin", 
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
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Check if remote exists
        if remote not in repo.remotes:
            return {
                "success": False,
                "message": f"Remote '{remote}' not found"
            }
        
        # Get remote
        remote_obj = repo.remotes[remote]
        remote_url = remote_obj.url
        
        # Configure authentication
        callbacks = None
        if token and remote_url.startswith("https://"):
            # Add token to URL
            if "@" in remote_url:
                # URL already has credentials
                return {
                    "success": False,
                    "message": f"Remote URL already contains credentials"
                }
            
            # Extract domain part
            domain_part = remote_url[8:]  # Remove "https://"
            
            # Build new URL with token
            new_url = f"https://x-access-token:{token}@{domain_part}"
            
            # Set URL temporarily
            repo.remotes.set_url(remote, new_url)
        
        # Fetch
        try:
            remote_obj.fetch(refspec)
            
            # Restore original URL if token was used
            if token and remote_url.startswith("https://"):
                repo.remotes.set_url(remote, remote_url)
            
            return {
                "success": True,
                "message": f"Fetched from {remote}" + (f" ({refspec})" if refspec else ""),
                "remote": remote,
                "refspec": refspec
            }
        except Exception as e:
            # Restore original URL if token was used
            if token and remote_url.startswith("https://"):
                repo.remotes.set_url(remote, remote_url)
            
            raise e
    except Exception as e:
        log_error(f"Error fetching from {remote}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_diff(path: str = None, from_ref: Optional[str] = None, 
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
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        if repo.is_empty:
            return {
                "success": False,
                "message": "Repository is empty"
            }
        
        diff = None
        
        if staged:
            # Diff between HEAD and index
            if from_ref:
                # Custom from_ref for staged changes
                try:
                    from_obj = repo.revparse_single(from_ref)
                    if not isinstance(from_obj, pygit2.Tree):
                        from_obj = from_obj.peel(pygit2.Tree)
                except KeyError:
                    return {
                        "success": False,
                        "message": f"Reference '{from_ref}' not found"
                    }
                
                diff = from_obj.diff_to_index(repo.index)
            else:
                # Default: HEAD vs index
                head_tree = repo.head.peel(pygit2.Tree)
                diff = head_tree.diff_to_index(repo.index)
        else:
            # Resolve from_ref
            if from_ref:
                try:
                    from_obj = repo.revparse_single(from_ref)
                    if not isinstance(from_obj, pygit2.Tree):
                        from_obj = from_obj.peel(pygit2.Tree)
                except KeyError:
                    return {
                        "success": False,
                        "message": f"Reference '{from_ref}' not found"
                    }
            else:
                # Default: parent of HEAD or empty tree for initial commit
                head_commit = repo.head.peel(pygit2.Commit)
                if head_commit.parents:
                    from_obj = head_commit.parents[0].tree
                else:
                    # Empty tree for initial commit
                    empty_tree_id = pygit2.Oid(hex="4b825dc642cb6eb9a060e54bf8d69288fbee4904")
                    try:
                        from_obj = repo.get(empty_tree_id)
                    except KeyError:
                        # Create empty tree if it doesn't exist
                        builder = repo.TreeBuilder()
                        empty_tree_id = builder.write()
                        from_obj = repo.get(empty_tree_id)
            
            # Resolve to_ref
            if to_ref:
                try:
                    to_obj = repo.revparse_single(to_ref)
                    if not isinstance(to_obj, pygit2.Tree):
                        to_obj = to_obj.peel(pygit2.Tree)
                except KeyError:
                    return {
                        "success": False,
                        "message": f"Reference '{to_ref}' not found"
                    }
            else:
                # Default: HEAD
                to_obj = repo.head.peel(pygit2.Tree)
            
            # Create diff
            diff = from_obj.diff_to_tree(to_obj)
        
        # Apply path filter
        if path_filter:
            # Cannot filter directly with PyGit2, so filter the results
            filtered_diff = pygit2.Diff()
            for patch in diff:
                if (patch.delta.old_file.path.startswith(path_filter) or
                    patch.delta.new_file.path.startswith(path_filter)):
                    filtered_diff.append(patch)
            
            diff = filtered_diff
        
        # Format diff
        return {
            "success": True,
            "diff": format_diff(diff)
        }
    except Exception as e:
        log_error(f"Error getting diff: {str(e)}")
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

# Additional functions and remaining implementations...
