#!/usr/bin/env python3
"""
PyGit2 implementation of Git tools for FastFS-MCP.

This module provides Git operations using PyGit2 instead of shell commands,
resulting in better performance and more structured responses.
"""

import os
import re
import sys
import json
import glob
import shutil
import tempfile
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional, Union

try:
    import pygit2
except ImportError:
    print("Error: PyGit2 is not installed. Please install it with 'pip install pygit2'", file=sys.stderr)
    sys.exit(1)

# Logging helper functions
def log_debug(message: str) -> None:
    """Log debug message."""
    if os.environ.get("FASTFS_DEBUG", "").lower() in ("true", "1", "yes"):
        print(f"[DEBUG] {message}", file=sys.stderr, flush=True)

def log_error(message: str) -> None:
    """Log error message."""
    print(f"[ERROR] {message}", file=sys.stderr, flush=True)

# Helper functions
def find_repository(path: Optional[str] = None) -> Optional[pygit2.Repository]:
    """Find a Git repository at the given path or its parents."""
    try:
        if path is None:
            path = os.getcwd()
        path = os.path.abspath(path)
        log_debug(f"Looking for Git repository at {path}")
        
        # Check if path itself is a repository
        if os.path.isdir(os.path.join(path, ".git")):
            return pygit2.Repository(path)
        elif os.path.exists(path) and path.endswith(".git") and os.path.isdir(path):
            return pygit2.Repository(path)
        
        # Try to discover the repository
        return pygit2.discover_repository(path)
    except pygit2.GitError:
        # Try to walk up the directory tree
        parent = os.path.dirname(path)
        if parent and parent != path:
            return find_repository(parent)
        return None
    except Exception as e:
        log_error(f"Error finding repository: {str(e)}")
        return None

def format_commit(commit: pygit2.Commit) -> Dict[str, Any]:
    """Format a commit object into a dictionary."""
    try:
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
            "parents": [str(p) for p in commit.parent_ids]
        }
        
        return result
    except Exception as e:
        log_error(f"Error formatting commit {commit.id if commit else 'None'}: {str(e)}")
        return {
            "id": str(commit.id) if commit else "unknown",
            "error": str(e)
        }

def format_status(status_flags: int) -> str:
    """Convert pygit2 status flags to a readable string."""
    if status_flags & pygit2.GIT_STATUS_IGNORED:
        return "ignored"
    
    result = []
    
    # Index status
    if status_flags & pygit2.GIT_STATUS_INDEX_NEW:
        result.append("new in index")
    elif status_flags & pygit2.GIT_STATUS_INDEX_MODIFIED:
        result.append("modified in index")
    elif status_flags & pygit2.GIT_STATUS_INDEX_DELETED:
        result.append("deleted in index")
    elif status_flags & pygit2.GIT_STATUS_INDEX_RENAMED:
        result.append("renamed in index")
    elif status_flags & pygit2.GIT_STATUS_INDEX_TYPECHANGE:
        result.append("typechange in index")
    
    # Working tree status
    if status_flags & pygit2.GIT_STATUS_WT_NEW:
        result.append("untracked")
    elif status_flags & pygit2.GIT_STATUS_WT_MODIFIED:
        result.append("modified in worktree")
    elif status_flags & pygit2.GIT_STATUS_WT_DELETED:
        result.append("deleted in worktree")
    elif status_flags & pygit2.GIT_STATUS_WT_RENAMED:
        result.append("renamed in worktree")
    elif status_flags & pygit2.GIT_STATUS_WT_TYPECHANGE:
        result.append("typechange in worktree")
    
    if not result:
        return "unchanged"
    
    return ", ".join(result)

def format_diff_line(line: Dict[str, Any]) -> Dict[str, Any]:
    """Format a diff line into a dictionary."""
    return {
        "content": line.content,
        "origin": chr(line.origin),
        "old_lineno": line.old_lineno,
        "new_lineno": line.new_lineno
    }

def format_diff_hunk(hunk: pygit2.DiffHunk) -> Dict[str, Any]:
    """Format a diff hunk into a dictionary."""
    return {
        "header": hunk.header,
        "old_start": hunk.old_start,
        "old_lines": hunk.old_lines,
        "new_start": hunk.new_start,
        "new_lines": hunk.new_lines,
        "lines": [format_diff_line(line) for line in hunk.lines]
    }

def format_diff_file(patch: pygit2.Patch) -> Dict[str, Any]:
    """Format a diff file into a dictionary."""
    result = {
        "old_file_path": patch.delta.old_file.path,
        "new_file_path": patch.delta.new_file.path,
        "status": patch.delta.status_char(),
        "additions": patch.line_stats[1],
        "deletions": patch.line_stats[2],
        "is_binary": patch.delta.is_binary,
        "hunks": []
    }
    
    if not patch.delta.is_binary:
        result["hunks"] = [format_diff_hunk(hunk) for hunk in patch.hunks]
    
    return result

def format_diff(diff: pygit2.Diff) -> Dict[str, Any]:
    """Format a diff into a dictionary."""
    stats = diff.stats
    
    result = {
        "stats": {
            "files_changed": stats.files_changed,
            "insertions": stats.insertions,
            "deletions": stats.deletions
        },
        "changes": []
    }
    
    for patch in diff:
        result["changes"].append(format_diff_file(patch))
    
    return result

# Main Git operations
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
    if options is None:
        options = {}
    
    try:
        # Determine target directory if not provided
        if not target_dir:
            target_dir = os.path.basename(repo_url)
            if target_dir.endswith('.git'):
                target_dir = target_dir[:-4]
        
        target_path = os.path.abspath(target_dir)
        log_debug(f"Cloning {repo_url} to {target_path}")
        
        # Check if target directory exists
        if os.path.exists(target_path):
            if os.path.isdir(target_path) and os.listdir(target_path):
                return {
                    "success": False,
                    "message": f"Target directory '{target_path}' already exists and is not empty"
                }
        
        # Prepare clone options
        clone_options = {}
        
        # Handle authentication if provided
        callbacks = None
        if 'token' in options:
            # Use token authentication
            token = options['token']
            callbacks = pygit2.RemoteCallbacks(
                credentials=lambda url, username_from_url, allowed_types: pygit2.UserPass(
                    "x-access-token", token
                )
            )
        
        if callbacks:
            clone_options['callbacks'] = callbacks
        
        # Handle shallow cloning
        if 'depth' in options:
            try:
                depth = int(options['depth'])
                clone_options['fetch_opts'] = {
                    'depth': depth
                }
            except (ValueError, TypeError):
                pass
        
        # Handle branch selection
        if 'branch' in options:
            clone_options['checkout_branch'] = options['branch']
        
        # Perform the clone
        # Note: pygit2 clone API doesn't support all options, so we might need to use subprocess for some cases
        if len(clone_options) > 0 and not (len(clone_options) == 1 and 'checkout_branch' in clone_options):
            # Use git command for advanced options
            cmd = ["git", "clone"]
            
            if 'depth' in options:
                cmd.extend(["--depth", str(options['depth'])])
            
            if 'branch' in options:
                cmd.extend(["--branch", options['branch']])
            
            if 'single-branch' in options and options['single-branch']:
                cmd.append("--single-branch")
            
            # Add token if needed
            clone_url = repo_url
            if 'token' in options:
                # Format: https://x-access-token:<token>@github.com/owner/repo.git
                clone_url = re.sub(r'https://', f'https://x-access-token:{options["token"]}@', clone_url)
            
            cmd.extend([clone_url, target_path])
            
            # Execute git clone
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "message": f"Clone failed: {process.stderr.strip()}",
                    "error": process.stderr.strip()
                }
        else:
            # Use pygit2 for simple cloning
            repo = pygit2.clone_repository(repo_url, target_path, checkout_branch=clone_options.get('checkout_branch'))
        
        # Return success result with repository information
        repo = pygit2.Repository(target_path)
        
        result = {
            "success": True,
            "message": f"Successfully cloned {repo_url} to {target_dir}",
            "repository": {
                "path": target_path,
                "is_bare": repo.is_bare,
                "is_empty": repo.is_empty
            }
        }
        
        # Add HEAD information if not empty
        if not repo.is_empty:
            if not repo.head_is_detached:
                result["repository"]["head"] = {
                    "type": "branch",
                    "name": repo.head.shorthand,
                    "commit": str(repo.head.target)
                }
            else:
                result["repository"]["head"] = {
                    "type": "detached",
                    "commit": str(repo.head.target)
                }
        
        return result
    except Exception as e:
        log_error(f"Error cloning repository {repo_url}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_init(directory: str = ".", bare: bool = False, 
            initial_commit: bool = False) -> Dict[str, Any]:
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
        path = os.path.abspath(directory)
        log_debug(f"Initializing Git repository at {path}")
        
        # Create directory if it doesn't exist
        if not os.path.exists(path):
            os.makedirs(path)
        
        # Initialize repository
        repo = pygit2.init_repository(path, bare=bare)
        
        result = {
            "success": True,
            "message": f"Initialized {'bare ' if bare else ''}Git repository in {path}",
            "repository": {
                "path": path,
                "is_bare": repo.is_bare,
                "is_empty": repo.is_empty
            }
        }
        
        # Create initial commit if requested
        if initial_commit and not bare:
            # Create a .gitignore file
            gitignore_path = os.path.join(path, '.gitignore')
            with open(gitignore_path, 'w') as f:
                f.write("# Auto-generated .gitignore file\n")
                f.write("*.log\n")
                f.write("*.tmp\n")
                f.write("*.swp\n")
                f.write("*.swo\n")
                f.write(".DS_Store\n")
                f.write("Thumbs.db\n")
            
            # Create a README.md file
            readme_path = os.path.join(path, 'README.md')
            with open(readme_path, 'w') as f:
                f.write("# Git Repository\n\n")
                f.write(f"This repository was initialized by PyGit2 at {datetime.now().isoformat()}\n")
            
            # Add files to index
            index = repo.index
            index.add('.gitignore')
            index.add('README.md')
            
            # Create initial commit
            tree_id = index.write_tree()
            
            # Create signature
            author = pygit2.Signature('FastFS-MCP', 'mcp@fastfs.com')
            committer = author
            
            # Create commit
            commit_id = repo.create_commit(
                'HEAD',
                author,
                committer,
                'Initial commit',
                tree_id,
                []
            )
            
            result["initial_commit"] = {
                "id": str(commit_id),
                "message": "Initial commit"
            }
            
            result["repository"]["is_empty"] = False
        
        return result
    except Exception as e:
        log_error(f"Error initializing repository in {directory}: {str(e)}")
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
        
        # Get repository status
        status = repo.status()
        
        # Categorize files
        staged = {}
        unstaged = {}
        untracked = {}
        ignored = {}
        
        for file_path, status_flags in status.items():
            status_str = format_status(status_flags)
            
            if status_flags & pygit2.GIT_STATUS_IGNORED:
                ignored[file_path] = status_str
            elif status_flags & pygit2.GIT_STATUS_WT_NEW:
                untracked[file_path] = status_str
            else:
                # Check if changes in index
                if (status_flags & pygit2.GIT_STATUS_INDEX_NEW or 
                    status_flags & pygit2.GIT_STATUS_INDEX_MODIFIED or 
                    status_flags & pygit2.GIT_STATUS_INDEX_DELETED or 
                    status_flags & pygit2.GIT_STATUS_INDEX_RENAMED or 
                    status_flags & pygit2.GIT_STATUS_INDEX_TYPECHANGE):
                    staged[file_path] = status_str
                
                # Check if changes in working tree
                if (status_flags & pygit2.GIT_STATUS_WT_MODIFIED or 
                    status_flags & pygit2.GIT_STATUS_WT_DELETED or 
                    status_flags & pygit2.GIT_STATUS_WT_RENAMED or 
                    status_flags & pygit2.GIT_STATUS_WT_TYPECHANGE):
                    unstaged[file_path] = status_str
        
        # Get current branch name
        branch = None
        if not repo.head_is_detached:
            branch = repo.head.shorthand
        
        # Create result dictionary
        result = {
            "success": True,
            "branch": branch,
            "detached": repo.head_is_detached,
            "is_clean": len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0,
            "counts": {
                "staged": len(staged),
                "unstaged": len(unstaged),
                "untracked": len(untracked),
                "ignored": len(ignored),
                "total": len(staged) + len(unstaged) + len(untracked)
            },
            "files": {}
        }
        
        # Merge all files into a single dictionary
        result["files"].update(staged)
        result["files"].update(unstaged)
        result["files"].update(untracked)
        
        return result
    except Exception as e:
        log_error(f"Error getting repository status: {str(e)}")
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
        
        # Convert single path to list
        if isinstance(paths, str):
            paths = [paths]
        
        # Add files to index
        index = repo.index
        
        # Track added files
        added_files = []
        failed_files = []
        
        for file_path in paths:
            try:
                # Check if path contains wildcards
                if '*' in file_path or '?' in file_path:
                    # Get the repository root
                    repo_root = os.path.dirname(repo.path) if repo.path.endswith('/.git/') else repo.path
                    
                    # Get list of matching files
                    matching_files = glob.glob(os.path.join(repo_root, file_path))
                    
                    if not matching_files:
                        failed_files.append({"path": file_path, "error": "No matching files found"})
                        continue
                    
                    # Add each matching file
                    for match in matching_files:
                        # Get relative path to repository root
                        rel_path = os.path.relpath(match, repo_root)
                        try:
                            index.add(rel_path)
                            added_files.append(rel_path)
                        except Exception as e:
                            failed_files.append({"path": rel_path, "error": str(e)})
                else:
                    # Add the file directly
                    index.add(file_path)
                    added_files.append(file_path)
            except Exception as e:
                failed_files.append({"path": file_path, "error": str(e)})
        
        # Write the index
        index.write()
        
        return {
            "success": len(added_files) > 0 or len(failed_files) == 0,
            "message": f"Added {len(added_files)} file(s) to the staging area",
            "added": added_files,
            "failed": failed_files
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
        
        # Get index
        index = repo.index
        
        # Check if there are staged changes
        if not amend:
            diff = index.diff_to_tree(repo.head.peel(pygit2.Tree))
            if len(diff) == 0:
                return {
                    "success": False,
                    "message": "No changes staged for commit"
                }
        
        # Get author signature
        if author_name and author_email:
            author = pygit2.Signature(author_name, author_email)
        else:
            try:
                author = pygit2.Signature(
                    repo.config['user.name'],
                    repo.config['user.email']
                )
            except KeyError:
                return {
                    "success": False,
                    "message": "Author identity unknown. Please configure user.name and user.email in git config."
                }
        
        # Committer is same as author
        committer = author
        
        # Create tree
        tree_id = index.write_tree()
        
        # Get parents
        parents = []
        if amend:
            # For amend, get parents of HEAD
            try:
                head_commit = repo.head.peel(pygit2.Commit)
                parents = [parent.id for parent in head_commit.parents]
                
                # If no parents and not a merge commit, use current HEAD as parent
                if not parents and len(head_commit.parent_ids) == 0:
                    parents = []
            except (pygit2.GitError, KeyError):
                # Repository might be empty
                parents = []
        else:
            # Normal commit
            try:
                parents = [repo.head.target]
            except (pygit2.GitError, KeyError):
                # Repository might be empty
                parents = []
        
        # Create commit
        commit_id = repo.create_commit(
            'HEAD',
            author,
            committer,
            message,
            tree_id,
            parents
        )
        
        # Get the commit
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
        
        # Check if repository is empty
        if repo.is_empty:
            return {
                "success": True,
                "message": "Repository is empty, no commits to show",
                "commits": [],
                "count": 0,
                "total_count": 0
            }
        
        # Resolve reference
        if ref is None:
            ref = repo.head.target
        else:
            try:
                ref_obj = repo.revparse_single(ref)
                if not isinstance(ref_obj, pygit2.Commit):
                    ref_obj = ref_obj.peel(pygit2.Commit)
                ref = ref_obj.id
            except KeyError:
                return {
                    "success": False,
                    "message": f"Reference '{ref}' not found"
                }
        
        # Create walker
        walker = repo.walk(ref, pygit2.GIT_SORT_TIME)
        
        # Apply path filter if provided
        if path_filter:
            walker.push_hide(path_filter)
        
        # Skip commits if needed
        if skip > 0:
            for _ in range(skip):
                try:
                    next(walker)
                except StopIteration:
                    break
        
        # Get commits
        commits = []
        try:
            for i, commit in enumerate(walker):
                if i >= max_count:
                    break
                commits.append(format_commit(commit))
        except StopIteration:
            pass
        
        # Count total commits
        total_count = 0
        try:
            walker = repo.walk(ref, pygit2.GIT_SORT_TIME)
            total_count = sum(1 for _ in walker)
        except:
            pass
        
        return {
            "success": True,
            "commits": commits,
            "count": len(commits),
            "total_count": total_count,
            "has_more": total_count > (skip + len(commits))
        }
    except Exception as e:
        log_error(f"Error getting commit logs: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_branch(name: Optional[str] = None, path: str = None, start_point: Optional[str] = None,
              delete: bool = False, force: bool = False) -> Dict[str, Any]:
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
            for ref in repo.references:
                if ref.startswith('refs/heads/'):
                    branch_name = ref[11:]  # Strip 'refs/heads/'
                    branch_ref = repo.references[ref]
                    target_commit = branch_ref.peel(pygit2.Commit)
                    
                    # Check if this is the current branch
                    is_current = False
                    if not repo.head_is_detached and repo.head.shorthand == branch_name:
                        is_current = True
                    
                    # Get tracking branch
                    try:
                        tracking_branch = None
                        remote = None
                        
                        config_key = f"branch.{branch_name}.remote"
                        if config_key in repo.config:
                            remote = repo.config[config_key]
                            
                            config_key = f"branch.{branch_name}.merge"
                            if config_key in repo.config:
                                remote_ref = repo.config[config_key]
                                tracking_branch = remote_ref.replace('refs/heads/', '')
                    except:
                        tracking_branch = None
                        remote = None
                    
                    branch_info = {
                        "name": branch_name,
                        "is_current": is_current,
                        "commit": str(branch_ref.target),
                        "commit_message": target_commit.message.split('\n', 1)[0] if target_commit.message else "",
                        "commit_date": datetime.fromtimestamp(target_commit.commit_time).isoformat(),
                        "tracking": {
                            "remote": remote,
                            "branch": tracking_branch
                        } if remote and tracking_branch else None
                    }
                    
                    branches.append(branch_info)
            
            return {
                "success": True,
                "branches": branches,
                "count": len(branches)
            }
        
        # Check if branch exists
        branch_ref = f"refs/heads/{name}"
        branch_exists = branch_ref in repo.references
        
        # Delete branch
        if delete:
            if not branch_exists:
                return {
                    "success": False,
                    "message": f"Branch '{name}' not found"
                }
            
            # Check if this is the current branch
            if not repo.head_is_detached and repo.head.shorthand == name:
                return {
                    "success": False,
                    "message": f"Cannot delete the current branch '{name}'"
                }
            
            # Get branch reference
            ref = repo.references[branch_ref]
            target = str(ref.target)
            
            # Delete branch
            repo.references.delete(branch_ref)
            
            return {
                "success": True,
                "message": f"Deleted branch '{name}'",
                "branch": {
                    "name": name,
                    "commit": target
                }
            }
        
        # Create branch
        if branch_exists and not force:
            return {
                "success": False,
                "message": f"Branch '{name}' already exists. Use force=True to overwrite."
            }
        
        # Resolve start point
        if start_point is None:
            start_point = repo.head.target
        else:
            try:
                start_obj = repo.revparse_single(start_point)
                if not isinstance(start_obj, pygit2.Commit):
                    start_obj = start_obj.peel(pygit2.Commit)
                start_point = start_obj.id
            except KeyError:
                return {
                    "success": False,
                    "message": f"Start point '{start_point}' not found"
                }
        
        # Create or update branch
        if branch_exists:
            ref = repo.references[branch_ref]
            ref.set_target(start_point)
        else:
            ref = repo.create_reference(branch_ref, start_point)
        
        return {
            "success": True,
            "message": f"{'Updated' if branch_exists else 'Created'} branch '{name}'",
            "branch": {
                "name": name,
                "commit": str(ref.target)
            }
        }
    except Exception as e:
        log_error(f"Error creating branch {name}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_checkout(revision: str, path: str = None, create_branch: bool = False,
                force: bool = False) -> Dict[str, Any]:
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
        
        # Check if working directory is clean unless force checkout
        if not force:
            status = git_status(path)
            if not status["success"] or not status["is_clean"]:
                return {
                    "success": False,
                    "message": f"Working directory not clean. Use force=True to discard changes."
                }
        
        # Check if branch exists
        is_branch = False
        branch_ref = f"refs/heads/{revision}"
        if branch_ref in repo.references:
            is_branch = True
        
        # Create branch if requested
        if not is_branch and create_branch:
            branch_result = git_branch(revision, path)
            if not branch_result["success"]:
                return branch_result
            is_branch = True
        
        # Resolve revision
        try:
            obj = repo.revparse_single(revision)
            if not isinstance(obj, pygit2.Commit):
                obj = obj.peel(pygit2.Commit)
            commit_id = obj.id
        except KeyError:
            return {
                "success": False,
                "message": f"Revision '{revision}' not found"
            }
        
        # Checkout the tree
        repo.checkout_tree(obj)
        
        # Update HEAD
        if is_branch:
            # Point HEAD to branch
            repo.set_head(branch_ref)
        else:
            # Detached HEAD
            repo.set_head(commit_id)
        
        return {
            "success": True,
            "message": f"Switched to {'branch' if is_branch else 'detached HEAD'} '{revision}'",
            "type": "branch" if is_branch else "detached",
            "commit": str(commit_id)
        }
    except Exception as e:
        log_error(f"Error checking out {revision}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_remote(path: str = None, command: str = "list", name: Optional[str] = None,
             url: Optional[str] = None) -> Dict[str, Any]:
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
                
                # Get fetch refspecs
                fetch_refspecs = []
                try:
                    for refspec in remote.fetch_refspecs:
                        fetch_refspecs.append(refspec)
                except:
                    pass
                
                # Get push refspecs
                push_refspecs = []
                try:
                    for refspec in remote.push_refspecs:
                        push_refspecs.append(refspec)
                except:
                    pass
                
                remote_info = {
                    "name": remote_name,
                    "url": remote.url,
                    "fetch_refspecs": fetch_refspecs,
                    "push_refspecs": push_refspecs
                }
                
                remotes.append(remote_info)
            
            return {
                "success": True,
                "remotes": remotes,
                "count": len(remotes)
            }
        
        # Check if name is provided for other commands
        if not name:
            return {
                "success": False,
                "message": "Remote name is required"
            }
        
        # Add remote
        if command == "add":
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
            remote = repo.remotes.create(name, url)
            
            return {
                "success": True,
                "message": f"Added remote '{name}' with URL '{url}'",
                "remote": {
                    "name": name,
                    "url": url
                }
            }
        
        # Remove remote
        if command == "remove":
            # Check if remote exists
            if name not in repo.remotes:
                return {
                    "success": False,
                    "message": f"Remote '{name}' not found"
                }
            
            # Get remote URL
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
        if command == "set-url":
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
            
            # Get current URL
            old_url = repo.remotes[name].url
            
            # Set URL
            remote = repo.remotes.set_url(name, url)
            
            return {
                "success": True,
                "message": f"Updated URL for remote '{name}'",
                "remote": {
                    "name": name,
                    "old_url": old_url,
                    "new_url": url
                }
            }
        
        return {
            "success": False,
            "message": f"Unknown remote command: {command}"
        }
    except Exception as e:
        log_error(f"Error managing remote {name}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_diff(path: str = None, from_ref: Optional[str] = None, to_ref: Optional[str] = None,
            staged: bool = False, path_filter: Optional[str] = None, 
            context_lines: int = 3) -> Dict[str, Any]:
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
        
        # Check if repository is empty
        if repo.is_empty:
            return {
                "success": False,
                "message": "Repository is empty, no commits to diff"
            }
        
        # Set diff options
        diff_opts = {
            'context_lines': context_lines,
            'flags': pygit2.GIT_DIFF_NORMAL
        }
        
        # Create diff based on parameters
        if staged:
            # Diff between index and HEAD
            head_tree = repo.head.peel(pygit2.Tree)
            diff = repo.diff_tree_to_index(head_tree, flags=diff_opts['flags'], context_lines=diff_opts['context_lines'])
        elif from_ref is not None and to_ref is not None:
            # Diff between two references
            try:
                from_obj = repo.revparse_single(from_ref)
                if not isinstance(from_obj, pygit2.Tree):
                    from_obj = from_obj.peel(pygit2.Tree)
                
                to_obj = repo.revparse_single(to_ref)
                if not isinstance(to_obj, pygit2.Tree):
                    to_obj = to_obj.peel(pygit2.Tree)
                
                diff = repo.diff_tree_to_tree(from_obj, to_obj, flags=diff_opts['flags'], context_lines=diff_opts['context_lines'])
            except KeyError as e:
                return {
                    "success": False,
                    "message": f"Reference not found: {str(e)}"
                }
        elif from_ref is not None:
            # Diff between reference and working directory
            try:
                from_obj = repo.revparse_single(from_ref)
                if not isinstance(from_obj, pygit2.Tree):
                    from_obj = from_obj.peel(pygit2.Tree)
                
                diff = repo.diff_tree_to_workdir(from_obj, flags=diff_opts['flags'], context_lines=diff_opts['context_lines'])
            except KeyError:
                return {
                    "success": False,
                    "message": f"Reference '{from_ref}' not found"
                }
        else:
            # Diff between HEAD and working directory
            head_tree = repo.head.peel(pygit2.Tree)
            diff = repo.diff_tree_to_workdir(head_tree, flags=diff_opts['flags'], context_lines=diff_opts['context_lines'])
        
        # Apply path filter if provided
        if path_filter:
            diff.find_similar()
            
            # Create a filtered diff
            new_diff = []
            for patch in diff:
                if (patch.delta.old_file.path == path_filter or 
                    patch.delta.new_file.path == path_filter or 
                    (path_filter.endswith('/') and 
                     (patch.delta.old_file.path.startswith(path_filter) or 
                      patch.delta.new_file.path.startswith(path_filter)))):
                    new_diff.append(patch)
            
            # Replace the diff
            if len(new_diff) == 0:
                return {
                    "success": False,
                    "message": f"No changes found in path '{path_filter}'"
                }
        
        # Format diff
        formatted_diff = format_diff(diff)
        
        return {
            "success": True,
            "diff": formatted_diff
        }
    except Exception as e:
        log_error(f"Error getting diff: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_pull(path: str = None, remote: str = "origin", branch: Optional[str] = None,
            fast_forward_only: bool = False, token: Optional[str] = None) -> Dict[str, Any]:
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
        
        # Check if working directory is clean
        status = git_status(path)
        if not status["success"] or not status["is_clean"]:
            return {
                "success": False,
                "message": "Working directory not clean. Commit or stash changes first."
            }
        
        # Check if remote exists
        if remote not in repo.remotes:
            return {
                "success": False,
                "message": f"Remote '{remote}' not found"
            }
        
        # Check if on a branch
        if repo.head_is_detached:
            return {
                "success": False,
                "message": "Cannot pull when HEAD is detached"
            }
        
        # Get current branch
        current_branch = repo.head.shorthand
        
        # Determine remote branch
        remote_branch = branch
        if not remote_branch:
            # Try to get tracking branch
            try:
                config_key = f"branch.{current_branch}.merge"
                if config_key in repo.config:
                    remote_ref = repo.config[config_key]
                    remote_branch = remote_ref.replace('refs/heads/', '')
            except:
                remote_branch = current_branch
        
        # Use git command for pull
        cmd = ["git", "pull"]
        
        if fast_forward_only:
            cmd.append("--ff-only")
        
        cmd.extend([remote, remote_branch])
        
        # Execute git pull
        env = os.environ.copy()
        if token:
            # Setup credential helper to use the token
            env["GIT_ASKPASS"] = "echo"
            env["GIT_USERNAME"] = "x-access-token"
            env["GIT_PASSWORD"] = token
        
        process = subprocess.run(
            cmd,
            cwd=os.path.dirname(repo.path),
            capture_output=True,
            text=True,
            env=env
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Pull failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        # Get the current HEAD commit
        head_commit = repo.head.peel(pygit2.Commit)
        
        return {
            "success": True,
            "message": f"Successfully pulled changes from {remote}/{remote_branch}",
            "head_commit": format_commit(head_commit),
            "output": process.stdout.strip()
        }
    except Exception as e:
        log_error(f"Error pulling changes: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_push(path: str = None, remote: str = "origin", refspecs: Optional[List[str]] = None,
            force: bool = False, token: Optional[str] = None) -> Dict[str, Any]:
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
        
        # Determine refspecs
        if not refspecs:
            if repo.head_is_detached:
                return {
                    "success": False,
                    "message": "Cannot push when HEAD is detached"
                }
            
            # Get current branch
            current_branch = repo.head.shorthand
            refspecs = [f"refs/heads/{current_branch}:refs/heads/{current_branch}"]
        
        # Use git command for push
        cmd = ["git", "push"]
        
        if force:
            cmd.append("--force")
        
        cmd.append(remote)
        cmd.extend(refspecs)
        
        # Execute git push
        env = os.environ.copy()
        if token:
            # Setup credential helper to use the token
            env["GIT_ASKPASS"] = "echo"
            env["GIT_USERNAME"] = "x-access-token"
            env["GIT_PASSWORD"] = token
        
        process = subprocess.run(
            cmd,
            cwd=os.path.dirname(repo.path),
            capture_output=True,
            text=True,
            env=env
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Push failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        return {
            "success": True,
            "message": f"Successfully pushed to {remote}",
            "refspecs": refspecs,
            "output": process.stdout.strip()
        }
    except Exception as e:
        log_error(f"Error pushing changes: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_fetch(path: str = None, remote: str = "origin", refspec: Optional[str] = None,
            token: Optional[str] = None) -> Dict[str, Any]:
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
        
        # Use git command for fetch
        cmd = ["git", "fetch"]
        
        cmd.append(remote)
        if refspec:
            cmd.append(refspec)
        
        # Execute git fetch
        env = os.environ.copy()
        if token:
            # Setup credential helper to use the token
            env["GIT_ASKPASS"] = "echo"
            env["GIT_USERNAME"] = "x-access-token"
            env["GIT_PASSWORD"] = token
        
        process = subprocess.run(
            cmd,
            cwd=os.path.dirname(repo.path),
            capture_output=True,
            text=True,
            env=env
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Fetch failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        return {
            "success": True,
            "message": f"Successfully fetched from {remote}",
            "output": process.stdout.strip()
        }
    except Exception as e:
        log_error(f"Error fetching changes: {str(e)}")
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
        
        # Resolve object
        try:
            obj = repo.revparse_single(object_name)
            
            # Handle different object types
            if isinstance(obj, pygit2.Commit):
                # Show commit
                commit = obj
                
                # Get diff
                if commit.parents:
                    parent = commit.parents[0]
                    diff = repo.diff(parent, commit)
                else:
                    diff = commit.tree.diff_to_tree()
                
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
                        "type": entry.type_str,
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
                # Unknown object type
                return {
                    "success": True,
                    "type": obj.type_str,
