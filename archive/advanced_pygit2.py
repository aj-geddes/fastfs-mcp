#!/usr/bin/env python3
"""
Advanced Git operations for PyGit2 implementation.

This module provides advanced Git operations not covered by the basic
implementation, including rebasing, cherry-picking, worktree management,
and more comprehensive submodule support.
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

# Import base functionality
from pygit2_tools import (
    find_repository, log_debug, log_error, format_commit,
    format_diff, _is_binary_blob
)

def git_rebase(path: str = None, upstream: str = None, branch: Optional[str] = None,
              onto: Optional[str] = None, interactive: bool = False) -> Dict[str, Any]:
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
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Check if upstream is provided
        if not upstream:
            return {
                "success": False,
                "message": "Upstream branch is required for rebasing"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Check if repository is clean
        status = {}
        for file_path, status_flags in repo.status().items():
            status[file_path] = status_flags
        
        if status:
            return {
                "success": False,
                "message": "Cannot rebase with uncommitted changes. Commit or stash changes first."
            }
        
        # Build rebase command
        cmd = ["git", "rebase"]
        
        if interactive:
            cmd.append("-i")
        
        if onto:
            cmd.extend(["--onto", onto])
        
        cmd.append(upstream)
        
        if branch:
            cmd.append(branch)
        
        # Execute rebase
        process = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            # Check for conflicts
            if "CONFLICT" in process.stderr:
                return {
                    "success": False,
                    "message": "Rebase conflicts detected. Resolve conflicts and continue the rebase.",
                    "conflicts": True,
                    "error": process.stderr.strip()
                }
            else:
                return {
                    "success": False,
                    "message": f"Rebase failed: {process.stderr.strip()}",
                    "error": process.stderr.strip()
                }
        
        # Get current HEAD
        head_commit = repo.head.peel(pygit2.Commit)
        
        return {
            "success": True,
            "message": f"Successfully rebased onto {upstream}",
            "head_commit": format_commit(head_commit),
            "output": process.stdout.strip()
        }
    except Exception as e:
        log_error(f"Error rebasing: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_rebase_continue(path: str = None) -> Dict[str, Any]:
    """
    Continue a rebase operation after resolving conflicts.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with rebase continuation results
    """
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Check if repository is in rebase state
        git_dir = repo.path
        if not os.path.exists(os.path.join(git_dir, "rebase-merge")) and not os.path.exists(os.path.join(git_dir, "rebase-apply")):
            return {
                "success": False,
                "message": "No rebase in progress"
            }
        
        # Check for unresolved conflicts
        unresolved_conflicts = False
        for file_path, status_flags in repo.status().items():
            if status_flags & pygit2.GIT_STATUS_CONFLICTED:
                unresolved_conflicts = True
                break
        
        if unresolved_conflicts:
            return {
                "success": False,
                "message": "Cannot continue rebase with unresolved conflicts"
            }
        
        # Execute rebase continue
        process = subprocess.run(
            ["git", "rebase", "--continue"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            # Check for more conflicts
            if "CONFLICT" in process.stderr:
                return {
                    "success": False,
                    "message": "More rebase conflicts detected. Resolve conflicts and continue the rebase.",
                    "conflicts": True,
                    "error": process.stderr.strip()
                }
            else:
                return {
                    "success": False,
                    "message": f"Rebase continue failed: {process.stderr.strip()}",
                    "error": process.stderr.strip()
                }
        
        # Get current HEAD
        head_commit = repo.head.peel(pygit2.Commit)
        
        return {
            "success": True,
            "message": "Successfully continued rebase",
            "head_commit": format_commit(head_commit),
            "output": process.stdout.strip()
        }
    except Exception as e:
        log_error(f"Error continuing rebase: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_rebase_abort(path: str = None) -> Dict[str, Any]:
    """
    Abort a rebase operation and return to the original state.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with rebase abort results
    """
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Check if repository is in rebase state
        git_dir = repo.path
        if not os.path.exists(os.path.join(git_dir, "rebase-merge")) and not os.path.exists(os.path.join(git_dir, "rebase-apply")):
            return {
                "success": False,
                "message": "No rebase in progress"
            }
        
        # Execute rebase abort
        process = subprocess.run(
            ["git", "rebase", "--abort"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Rebase abort failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        # Get current HEAD
        head_commit = repo.head.peel(pygit2.Commit)
        
        return {
            "success": True,
            "message": "Successfully aborted rebase",
            "head_commit": format_commit(head_commit)
        }
    except Exception as e:
        log_error(f"Error aborting rebase: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_cherry_pick(path: str = None, commit: str = None, 
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
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Check if commit is provided
        if not commit:
            return {
                "success": False,
                "message": "Commit is required for cherry-picking"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Build cherry-pick command
        cmd = ["git", "cherry-pick"]
        
        if no_commit:
            cmd.append("--no-commit")
        
        cmd.append(commit)
        
        # Execute cherry-pick
        process = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            # Check for conflicts
            if "CONFLICT" in process.stderr:
                return {
                    "success": False,
                    "message": "Cherry-pick conflicts detected. Resolve conflicts and continue.",
                    "conflicts": True,
                    "error": process.stderr.strip()
                }
            else:
                return {
                    "success": False,
                    "message": f"Cherry-pick failed: {process.stderr.strip()}",
                    "error": process.stderr.strip()
                }
        
        # Get current HEAD
        head_commit = repo.head.peel(pygit2.Commit)
        
        return {
            "success": True,
            "message": f"Successfully cherry-picked {commit}",
            "head_commit": format_commit(head_commit),
            "output": process.stdout.strip()
        }
    except Exception as e:
        log_error(f"Error cherry-picking {commit}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_worktree_add(path: str = None, worktree_path: str = None, 
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
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Check if worktree path is provided
        if not worktree_path:
            return {
                "success": False,
                "message": "Worktree path is required"
            }
        
        # Check if branch is provided
        if not branch:
            return {
                "success": False,
                "message": "Branch is required for adding a worktree"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Build worktree add command
        cmd = ["git", "worktree", "add"]
        
        if create_branch:
            cmd.append("-b")
        
        cmd.extend([worktree_path, branch])
        
        # Execute worktree add
        process = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Worktree add failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        return {
            "success": True,
            "message": f"Successfully added worktree at {worktree_path} for branch {branch}",
            "worktree_path": worktree_path,
            "branch": branch
        }
    except Exception as e:
        log_error(f"Error adding worktree: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_worktree_list(path: str = None) -> Dict[str, Any]:
    """
    List working trees.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with worktree list results
    """
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Execute worktree list
        process = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Worktree list failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        # Parse output
        worktrees = []
        current_worktree = {}
        
        for line in process.stdout.strip().split('\n'):
            if not line:
                if current_worktree:
                    worktrees.append(current_worktree)
                    current_worktree = {}
                continue
            
            if line.startswith("worktree "):
                current_worktree["path"] = line[9:]
            elif line.startswith("HEAD "):
                current_worktree["head"] = line[5:]
            elif line.startswith("branch "):
                current_worktree["branch"] = line[7:]
                # Extract branch name from refs/heads/
                if current_worktree["branch"].startswith("refs/heads/"):
                    current_worktree["branch_name"] = current_worktree["branch"][11:]
            elif line.startswith("detached"):
                current_worktree["detached"] = True
            elif line.startswith("prunable"):
                current_worktree["prunable"] = True
                if " " in line:
                    current_worktree["prunable_reason"] = line.split(" ", 1)[1]
        
        # Add the last worktree
        if current_worktree:
            worktrees.append(current_worktree)
        
        return {
            "success": True,
            "worktrees": worktrees,
            "count": len(worktrees)
        }
    except Exception as e:
        log_error(f"Error listing worktrees: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_worktree_remove(path: str = None, worktree_path: str = None, 
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
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Check if worktree path is provided
        if not worktree_path:
            return {
                "success": False,
                "message": "Worktree path is required"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Build worktree remove command
        cmd = ["git", "worktree", "remove"]
        
        if force:
            cmd.append("--force")
        
        cmd.append(worktree_path)
        
        # Execute worktree remove
        process = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Worktree remove failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        return {
            "success": True,
            "message": f"Successfully removed worktree at {worktree_path}"
        }
    except Exception as e:
        log_error(f"Error removing worktree: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_submodule_add(path: str = None, repo_url: str = None, 
                     target_path: Optional[str] = None, branch: Optional[str] = None) -> Dict[str, Any]:
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
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Check if repo URL is provided
        if not repo_url:
            return {
                "success": False,
                "message": "Repository URL is required for adding a submodule"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Build submodule add command
        cmd = ["git", "submodule", "add"]
        
        if branch:
            cmd.extend(["-b", branch])
        
        cmd.append(repo_url)
        
        if target_path:
            cmd.append(target_path)
        
        # Execute submodule add
        process = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Submodule add failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        # Determine the target path if not provided
        if not target_path:
            target_path = os.path.basename(repo_url)
            if target_path.endswith(".git"):
                target_path = target_path[:-4]
        
        return {
            "success": True,
            "message": f"Successfully added submodule {repo_url} at {target_path}",
            "submodule_path": target_path
        }
    except Exception as e:
        log_error(f"Error adding submodule: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_submodule_update(path: str = None, submodule_path: Optional[str] = None, 
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
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Build submodule update command
        cmd = ["git", "submodule", "update"]
        
        if init:
            cmd.append("--init")
        
        if recursive:
            cmd.append("--recursive")
        
        if submodule_path:
            cmd.append("--")
            cmd.append(submodule_path)
        
        # Execute submodule update
        process = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Submodule update failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        return {
            "success": True,
            "message": f"Successfully updated {'submodule ' + submodule_path if submodule_path else 'all submodules'}",
            "output": process.stdout.strip()
        }
    except Exception as e:
        log_error(f"Error updating submodules: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_submodule_list(path: str = None) -> Dict[str, Any]:
    """
    List submodules.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with submodule list results
    """
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Read .gitmodules file
        submodules = []
        
        try:
            # Try to get the .gitmodules file from the repository
            gitmodules_blob = repo.revparse_single("HEAD:.gitmodules")
            gitmodules_content = gitmodules_blob.data.decode('utf-8')
            
            # Parse .gitmodules content
            current_submodule = {}
            for line in gitmodules_content.split('\n'):
                line = line.strip()
                
                if line.startswith('[submodule "'):
                    if current_submodule:
                        submodules.append(current_submodule)
                        current_submodule = {}
                    
                    # Extract submodule name
                    name = line[12:-2]  # Remove [submodule " and "]
                    current_submodule["name"] = name
                
                elif line.startswith('path = '):
                    current_submodule["path"] = line[7:]
                
                elif line.startswith('url = '):
                    current_submodule["url"] = line[6:]
                
                elif line.startswith('branch = '):
                    current_submodule["branch"] = line[9:]
            
            # Add the last submodule
            if current_submodule:
                submodules.append(current_submodule)
            
            # Get submodule status
            for submodule in submodules:
                path = submodule["path"]
                
                try:
                    # Check if submodule is initialized
                    submodule_path = os.path.join(os.path.dirname(repo.path), path)
                    submodule["initialized"] = os.path.exists(os.path.join(submodule_path, ".git"))
                    
                    # Get submodule HEAD if initialized
                    if submodule["initialized"]:
                        try:
                            submodule_repo = pygit2.Repository(submodule_path)
                            if not submodule_repo.head_is_detached:
                                submodule["head"] = {
                                    "branch": submodule_repo.head.shorthand,
                                    "commit": str(submodule_repo.head.target)
                                }
                            else:
                                submodule["head"] = {
                                    "detached": True,
                                    "commit": str(submodule_repo.head.target)
                                }
                        except:
                            submodule["head"] = None
                except:
                    submodule["initialized"] = False
            
            return {
                "success": True,
                "submodules": submodules,
                "count": len(submodules)
            }
        except KeyError:
            # No .gitmodules file found
            return {
                "success": True,
                "message": "No submodules found",
                "submodules": [],
                "count": 0
            }
    except Exception as e:
        log_error(f"Error listing submodules: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_bisect_start(path: str = None, bad: str = "HEAD", good: str = None) -> Dict[str, Any]:
    """
    Start a bisect session.
    
    Args:
        path: Path to the repository (default: current directory)
        bad: Bad commit
        good: Good commit
    
    Returns:
        Dictionary with bisect start operation results
    """
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Check if good commit is provided
        if not good:
            return {
                "success": False,
                "message": "Good commit is required for bisect start"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Execute bisect start
        process = subprocess.run(
            ["git", "bisect", "start", bad, good],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Bisect start failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        # Get current HEAD
        head_commit = repo.head.peel(pygit2.Commit)
        
        return {
            "success": True,
            "message": f"Successfully started bisect session with bad={bad} and good={good}",
            "current_commit": format_commit(head_commit),
            "output": process.stdout.strip()
        }
    except Exception as e:
        log_error(f"Error starting bisect: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_bisect_good(path: str = None) -> Dict[str, Any]:
    """
    Mark the current commit as good in a bisect session.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with bisect good operation results
    """
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Check if in bisect session
        git_dir = repo.path
        if not os.path.exists(os.path.join(git_dir, "BISECT_START")):
            return {
                "success": False,
                "message": "No bisect session in progress"
            }
        
        # Execute bisect good
        process = subprocess.run(
            ["git", "bisect", "good"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Bisect good failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        # Check if bisect is complete
        output = process.stdout.strip()
        bisect_complete = "first bad commit" in output
        
        # Get current HEAD if bisect is not complete
        head_commit = None
        if not bisect_complete:
            head_commit = repo.head.peel(pygit2.Commit)
        
        result = {
            "success": True,
            "message": "Successfully marked current commit as good",
            "output": output,
            "complete": bisect_complete
        }
        
        if head_commit:
            result["current_commit"] = format_commit(head_commit)
        
        # Parse first bad commit if bisect is complete
        if bisect_complete:
            # Extract commit hash from output
            match = re.search(r'([0-9a-f]{7,40}) is the first bad commit', output)
            if match:
                bad_commit_hash = match.group(1)
                try:
                    bad_commit = repo.revparse_single(bad_commit_hash)
                    result["bad_commit"] = format_commit(bad_commit)
                except:
                    result["bad_commit_hash"] = bad_commit_hash
        
        return result
    except Exception as e:
        log_error(f"Error marking commit as good: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_bisect_bad(path: str = None) -> Dict[str, Any]:
    """
    Mark the current commit as bad in a bisect session.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with bisect bad operation results
    """
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Check if in bisect session
        git_dir = repo.path
        if not os.path.exists(os.path.join(git_dir, "BISECT_START")):
            return {
                "success": False,
                "message": "No bisect session in progress"
            }
        
        # Execute bisect bad
        process = subprocess.run(
            ["git", "bisect", "bad"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Bisect bad failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        # Check if bisect is complete
        output = process.stdout.strip()
        bisect_complete = "first bad commit" in output
        
        # Get current HEAD if bisect is not complete
        head_commit = None
        if not bisect_complete:
            head_commit = repo.head.peel(pygit2.Commit)
        
        result = {
            "success": True,
            "message": "Successfully marked current commit as bad",
            "output": output,
            "complete": bisect_complete
        }
        
        if head_commit:
            result["current_commit"] = format_commit(head_commit)
        
        # Parse first bad commit if bisect is complete
        if bisect_complete:
            # Extract commit hash from output
            match = re.search(r'([0-9a-f]{7,40}) is the first bad commit', output)
            if match:
                bad_commit_hash = match.group(1)
                try:
                    bad_commit = repo.revparse_single(bad_commit_hash)
                    result["bad_commit"] = format_commit(bad_commit)
                except:
                    result["bad_commit_hash"] = bad_commit_hash
        
        return result
    except Exception as e:
        log_error(f"Error marking commit as bad: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_bisect_reset(path: str = None) -> Dict[str, Any]:
    """
    End a bisect session.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with bisect reset operation results
    """
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Check if in bisect session
        git_dir = repo.path
        if not os.path.exists(os.path.join(git_dir, "BISECT_START")):
            return {
                "success": False,
                "message": "No bisect session in progress"
            }
        
        # Execute bisect reset
        process = subprocess.run(
            ["git", "bisect", "reset"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Bisect reset failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        # Get current HEAD
        head_commit = repo.head.peel(pygit2.Commit)
        
        return {
            "success": True,
            "message": "Successfully ended bisect session",
            "head_commit": format_commit(head_commit)
        }
    except Exception as e:
        log_error(f"Error resetting bisect: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_reflog(path: str = None, max_count: int = 10) -> Dict[str, Any]:
    """
    Show reflog entries.
    
    Args:
        path: Path to the repository (default: current directory)
        max_count: Maximum number of entries to show
    
    Returns:
        Dictionary with reflog results
    """
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Execute reflog
        process = subprocess.run(
            ["git", "reflog", f"-n{max_count}", "--pretty=format:%H %gd %gs"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Reflog failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        # Parse output
        entries = []
        for line in process.stdout.strip().split('\n'):
            if not line:
                continue
            
            parts = line.split(' ', 2)
            if len(parts) >= 3:
                commit_id, ref_name, message = parts
                
                # Get commit details
                commit = None
                try:
                    commit = repo.get(pygit2.Oid(hex=commit_id))
                    commit_info = format_commit(commit)
                except:
                    commit_info = {"id": commit_id}
                
                entries.append({
                    "commit": commit_info,
                    "ref_name": ref_name,
                    "message": message
                })
        
        return {
            "success": True,
            "entries": entries,
            "count": len(entries)
        }
    except Exception as e:
        log_error(f"Error getting reflog: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_clean(path: str = None, directories: bool = False, force: bool = False,
             dry_run: bool = True, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Remove untracked files from the working tree.
    
    Args:
        path: Path to the repository (default: current directory)
        directories: Whether to remove untracked directories as well
        force: Whether to force removal
        dry_run: Whether to perform a dry run
        exclude: Patterns to exclude
    
    Returns:
        Dictionary with clean operation results
    """
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Build clean command
        cmd = ["git", "clean"]
        
        if dry_run:
            cmd.append("-n")
        
        if force:
            cmd.append("-f")
        
        if directories:
            cmd.append("-d")
        
        if exclude:
            for pattern in exclude:
                cmd.extend(["--exclude", pattern])
        
        # Execute clean
        process = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Clean failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        # Parse output
        output = process.stdout.strip()
        files = []
        
        for line in output.split('\n'):
            if line.startswith("Would remove "):
                files.append(line[13:])
            elif line.startswith("Removing "):
                files.append(line[9:])
        
        return {
            "success": True,
            "message": f"Successfully {'listed' if dry_run else 'removed'} {len(files)} untracked {'files and directories' if directories else 'files'}",
            "files": files,
            "count": len(files),
            "dry_run": dry_run
        }
    except Exception as e:
        log_error(f"Error cleaning repository: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_archive(path: str = None, output_file: str = None, format: str = "tar",
               prefix: Optional[str] = None, ref: str = "HEAD") -> Dict[str, Any]:
    """
    Create an archive of files from a named tree.
    
    Args:
        path: Path to the repository (default: current directory)
        output_file: Output file
        format: Archive format (tar, zip)
        prefix: Prefix to prepend to each filename in the archive
        ref: Tree to archive
    
    Returns:
        Dictionary with archive operation results
    """
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Check if output file is provided
        if not output_file:
            return {
                "success": False,
                "message": "Output file is required for archive"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Build archive command
        cmd = ["git", "archive"]
        
        if format:
            cmd.extend(["--format", format])
        
        if prefix:
            cmd.extend(["--prefix", prefix])
        
        cmd.extend(["-o", output_file, ref])
        
        # Execute archive
        process = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Archive failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        return {
            "success": True,
            "message": f"Successfully created archive {output_file}",
            "output_file": output_file,
            "format": format
        }
    except Exception as e:
        log_error(f"Error creating archive: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_gc(path: str = None, aggressive: bool = False, 
          prune: Optional[str] = None) -> Dict[str, Any]:
    """
    Cleanup unnecessary files and optimize the local repository.
    
    Args:
        path: Path to the repository (default: current directory)
        aggressive: Whether to perform an aggressive garbage collection
        prune: Prune objects older than the specified date
    
    Returns:
        Dictionary with gc operation results
    """
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Determine repository path
        repo_path = os.path.dirname(repo.path)
        
        # Build gc command
        cmd = ["git", "gc"]
        
        if aggressive:
            cmd.append("--aggressive")
        
        if prune:
            cmd.extend(["--prune", prune])
        
        # Execute gc
        process = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            return {
                "success": False,
                "message": f"Garbage collection failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
        
        return {
            "success": True,
            "message": "Successfully performed garbage collection",
            "output": process.stdout.strip()
        }
    except Exception as e:
        log_error(f"Error performing garbage collection: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }
