#!/usr/bin/env python3
"""
Error handling and recovery utilities for PyGit2 implementation.

This module provides robust error handling, retry mechanisms, and
recovery utilities for Git operations using PyGit2.
"""

import os
import sys
import time
import json
import shutil
import tempfile
import traceback
from typing import Dict, Any, List, Tuple, Optional, Union, Callable

try:
    import pygit2
except ImportError:
    print("Error: PyGit2 is not installed. Please install it with 'pip install pygit2'", file=sys.stderr)
    sys.exit(1)

# Import logging helpers
from pygit2_tools import log_debug, log_error

class GitErrorHandler:
    """Handle Git operation errors and provide recovery options."""
    
    @staticmethod
    def handle_error(error: Exception, operation: str, 
                    repository_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle Git operation errors.
        
        Args:
            error: The exception that occurred
            operation: The Git operation that failed
            repository_path: Path to the repository
        
        Returns:
            Dictionary with error information and recovery options
        """
        error_type = type(error).__name__
        error_message = str(error)
        traceback_str = traceback.format_exc()
        
        log_error(f"Error in {operation}: {error_type}: {error_message}")
        
        # Prepare error result
        result = {
            "success": False,
            "message": f"Error in {operation}: {error_message}",
            "error": {
                "type": error_type,
                "message": error_message,
                "traceback": traceback_str
            }
        }
        
        # Add recovery options based on error type and operation
        recovery_options = GitErrorHandler.get_recovery_options(error, operation, repository_path)
        if recovery_options:
            result["recovery_options"] = recovery_options
        
        return result
    
    @staticmethod
    def get_recovery_options(error: Exception, operation: str,
                           repository_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recovery options for a Git operation error.
        
        Args:
            error: The exception that occurred
            operation: The Git operation that failed
            repository_path: Path to the repository
        
        Returns:
            List of recovery options
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Initialize recovery options
        recovery_options = []
        
        # Handle specific error types
        if isinstance(error, pygit2.GitError):
            # Repository errors
            if "repository not found" in error_message.lower():
                recovery_options.append({
                    "action": "initialize",
                    "description": "Initialize a new Git repository",
                    "operation": "git_init",
                    "params": {"directory": repository_path}
                })
            
            # Reference errors
            elif "reference not found" in error_message.lower() or "reference 'refs/" in error_message.lower():
                if operation == "git_checkout":
                    recovery_options.append({
                        "action": "create_branch",
                        "description": "Create the missing branch",
                        "operation": "git_branch",
                        "params": {"name": error_message.split("'")[1].replace("refs/heads/", "")}
                    })
            
            # Remote errors
            elif "remote not found" in error_message.lower():
                recovery_options.append({
                    "action": "add_remote",
                    "description": "Add the missing remote",
                    "operation": "git_remote",
                    "params": {"command": "add", "name": "<remote_name>", "url": "<remote_url>"}
                })
            
            # Merge conflicts
            elif "conflicts" in error_message.lower():
                recovery_options.append({
                    "action": "resolve_conflicts",
                    "description": "Resolve conflicts manually",
                    "operation": "ConflictResolver.list_conflicts",
                    "params": {"path": repository_path}
                })
                
                recovery_options.append({
                    "action": "abort_merge",
                    "description": "Abort the merge operation",
                    "operation": "git_merge_abort",
                    "params": {"path": repository_path}
                })
            
            # Uncommitted changes
            elif "uncommitted changes" in error_message.lower():
                recovery_options.append({
                    "action": "commit_changes",
                    "description": "Commit the changes",
                    "operation": "git_commit",
                    "params": {"message": "Commit before operation", "path": repository_path}
                })
                
                recovery_options.append({
                    "action": "stash_changes",
                    "description": "Stash the changes",
                    "operation": "git_stash",
                    "params": {"path": repository_path}
                })
        
        # Handle Python exceptions
        elif isinstance(error, FileNotFoundError):
            recovery_options.append({
                "action": "create_directory",
                "description": "Create the missing directory",
                "operation": "os.makedirs",
                "params": {"path": os.path.dirname(error.filename)}
            })
        
        elif isinstance(error, PermissionError):
            recovery_options.append({
                "action": "fix_permissions",
                "description": "Fix file permissions",
                "operation": "os.chmod",
                "params": {"path": repository_path, "mode": "0755"}
            })
        
        # Operation-specific recovery options
        if operation == "git_clone":
            recovery_options.append({
                "action": "retry_with_depth",
                "description": "Retry with a shallow clone",
                "operation": "git_clone",
                "params": {"depth": 1}
            })
        
        elif operation == "git_pull":
            recovery_options.append({
                "action": "retry_with_fetch",
                "description": "Fetch changes instead of pulling",
                "operation": "git_fetch",
                "params": {"path": repository_path}
            })
        
        elif operation == "git_push":
            recovery_options.append({
                "action": "retry_with_force",
                "description": "Retry with force push",
                "operation": "git_push",
                "params": {"force": True, "path": repository_path}
            })
        
        return recovery_options

class GitRetry:
    """Retry mechanism for Git operations."""
    
    @staticmethod
    def retry(func: Callable, max_retries: int = 3, delay: float = 1.0,
             backoff_factor: float = 2.0, **kwargs) -> Dict[str, Any]:
        """
        Retry a Git operation with exponential backoff.
        
        Args:
            func: The function to retry
            max_retries: Maximum number of retries
            delay: Initial delay between retries in seconds
            backoff_factor: Backoff factor for exponential delay
            **kwargs: Arguments to pass to the function
        
        Returns:
            Result of the function or error information
        """
        retries = 0
        current_delay = delay
        last_error = None
        
        while retries < max_retries:
            try:
                # Attempt the operation
                result = func(**kwargs)
                
                # Check if operation was successful
                if result.get("success", False):
                    return result
                
                # Operation failed but returned a result
                last_error = result.get("error")
                
                # Increment retry counter
                retries += 1
                
                # Break if we've reached max retries
                if retries >= max_retries:
                    break
                
                # Log retry attempt
                log_debug(f"Retrying operation (attempt {retries}/{max_retries}) after {current_delay}s delay...")
                
                # Delay before next attempt
                time.sleep(current_delay)
                
                # Increase delay for next attempt
                current_delay *= backoff_factor
            
            except Exception as e:
                # Store error
                last_error = e
                
                # Increment retry counter
                retries += 1
                
                # Break if we've reached max retries
                if retries >= max_retries:
                    break
                
                # Log retry attempt
                log_debug(f"Retrying operation (attempt {retries}/{max_retries}) after {current_delay}s delay...")
                
                # Delay before next attempt
                time.sleep(current_delay)
                
                # Increase delay for next attempt
                current_delay *= backoff_factor
        
        # All retries failed
        operation_name = func.__name__ if hasattr(func, "__name__") else "operation"
        
        if isinstance(last_error, Exception):
            return GitErrorHandler.handle_error(last_error, operation_name, kwargs.get("path"))
        else:
            return {
                "success": False,
                "message": f"Operation {operation_name} failed after {max_retries} retries",
                "error": last_error
            }

class GitRepair:
    """Repair utilities for Git repositories."""
    
    @staticmethod
    def repair_repository(path: str) -> Dict[str, Any]:
        """
        Attempt to repair a Git repository.
        
        Args:
            path: Path to the repository
        
        Returns:
            Dictionary with repair results
        """
        import subprocess
        
        try:
            # Verify the repository path
            if not os.path.exists(path):
                return {
                    "success": False,
                    "message": f"Repository path '{path}' does not exist"
                }
            
            # Check if the path is a Git repository
            git_dir = os.path.join(path, ".git")
            if not os.path.exists(git_dir):
                return {
                    "success": False,
                    "message": f"Path '{path}' is not a Git repository"
                }
            
            # Create a backup of the repository
            backup_dir = tempfile.mkdtemp(prefix="git_repair_backup_")
            log_debug(f"Creating backup of repository at {backup_dir}")
            
            try:
                shutil.copytree(git_dir, os.path.join(backup_dir, ".git"))
            except Exception as e:
                log_error(f"Failed to create backup: {str(e)}")
                return {
                    "success": False,
                    "message": f"Failed to create backup: {str(e)}",
                    "error": str(e)
                }
            
            # Attempt repair steps
            repair_steps = [
                {"name": "fsck", "command": ["git", "fsck", "--full"]},
                {"name": "prune", "command": ["git", "prune"]},
                {"name": "reflog_expire", "command": ["git", "reflog", "expire", "--expire=now", "--all"]},
                {"name": "repack", "command": ["git", "repack", "-a", "-d", "-f"]},
                {"name": "gc", "command": ["git", "gc", "--aggressive"]}
            ]
            
            repair_results = []
            
            for step in repair_steps:
                log_debug(f"Executing repair step: {step['name']}")
                
                try:
                    process = subprocess.run(
                        step["command"],
                        cwd=path,
                        capture_output=True,
                        text=True
                    )
                    
                    if process.returncode == 0:
                        repair_results.append({
                            "step": step["name"],
                            "success": True,
                            "output": process.stdout.strip()
                        })
                    else:
                        repair_results.append({
                            "step": step["name"],
                            "success": False,
                            "error": process.stderr.strip()
                        })
                except Exception as e:
                    repair_results.append({
                        "step": step["name"],
                        "success": False,
                        "error": str(e)
                    })
            
            # Check if repository can be opened
            try:
                repo = pygit2.Repository(path)
                
                # Verify HEAD
                head_valid = True
                try:
                    head = repo.head
                except:
                    head_valid = False
                
                # Return success result
                return {
                    "success": True,
                    "message": "Repository repair completed",
                    "backup_path": backup_dir,
                    "repair_results": repair_results,
                    "repository_valid": True,
                    "head_valid": head_valid
                }
            except Exception as e:
                # Repository still cannot be opened
                return {
                    "success": False,
                    "message": f"Repository repair failed: {str(e)}",
                    "backup_path": backup_dir,
                    "repair_results": repair_results,
                    "error": str(e)
                }
        except Exception as e:
            log_error(f"Error repairing repository: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }
    
    @staticmethod
    def restore_backup(path: str, backup_path: str) -> Dict[str, Any]:
        """
        Restore a backup of a Git repository.
        
        Args:
            path: Path to the repository
            backup_path: Path to the backup
        
        Returns:
            Dictionary with restore results
        """
        try:
            # Verify the repository path
            if not os.path.exists(path):
                return {
                    "success": False,
                    "message": f"Repository path '{path}' does not exist"
                }
            
            # Verify the backup path
            if not os.path.exists(backup_path):
                return {
                    "success": False,
                    "message": f"Backup path '{backup_path}' does not exist"
                }
            
            # Check if the backup is a Git repository
            backup_git_dir = os.path.join(backup_path, ".git")
            if not os.path.exists(backup_git_dir):
                return {
                    "success": False,
                    "message": f"Backup path '{backup_path}' is not a Git repository"
                }
            
            # Remove the current .git directory
            git_dir = os.path.join(path, ".git")
            if os.path.exists(git_dir):
                shutil.rmtree(git_dir)
            
            # Copy the backup .git directory
            shutil.copytree(backup_git_dir, git_dir)
            
            # Check if repository can be opened
            try:
                repo = pygit2.Repository(path)
                
                # Verify HEAD
                head_valid = True
                try:
                    head = repo.head
                except:
                    head_valid = False
                
                # Return success result
                return {
                    "success": True,
                    "message": "Repository backup restored",
                    "repository_valid": True,
                    "head_valid": head_valid
                }
            except Exception as e:
                # Repository still cannot be opened
                return {
                    "success": False,
                    "message": f"Repository restore failed: {str(e)}",
                    "error": str(e)
                }
        except Exception as e:
            log_error(f"Error restoring repository backup: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }
    
    @staticmethod
    def fix_corrupted_index(path: str) -> Dict[str, Any]:
        """
        Fix a corrupted Git index.
        
        Args:
            path: Path to the repository
        
        Returns:
            Dictionary with fix results
        """
        try:
            # Verify the repository path
            if not os.path.exists(path):
                return {
                    "success": False,
                    "message": f"Repository path '{path}' does not exist"
                }
            
            # Check if the path is a Git repository
            git_dir = os.path.join(path, ".git")
            if not os.path.exists(git_dir):
                return {
                    "success": False,
                    "message": f"Path '{path}' is not a Git repository"
                }
            
            # Backup the index
            index_path = os.path.join(git_dir, "index")
            if os.path.exists(index_path):
                backup_index_path = index_path + ".backup"
                shutil.copy2(index_path, backup_index_path)
                
                # Remove the corrupted index
                os.remove(index_path)
            
            # Recreate the index
            try:
                repo = pygit2.Repository(path)
                
                # Checkout the current HEAD to recreate the index
                if not repo.is_empty:
                    head_commit = repo.head.peel(pygit2.Commit)
                    repo.reset(head_commit.id, pygit2.GIT_RESET_MIXED)
                
                return {
                    "success": True,
                    "message": "Successfully fixed corrupted index",
                    "backup_path": backup_index_path if os.path.exists(index_path) else None
                }
            except Exception as e:
                # Repository still cannot be opened
                return {
                    "success": False,
                    "message": f"Index repair failed: {str(e)}",
                    "error": str(e)
                }
        except Exception as e:
            log_error(f"Error fixing corrupted index: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }
    
    @staticmethod
    def fix_detached_head(path: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Fix a detached HEAD state by pointing it to a branch.
        
        Args:
            path: Path to the repository
            branch: Branch to point HEAD to (default: create a new branch)
        
        Returns:
            Dictionary with fix results
        """
        try:
            # Verify the repository path
            if not os.path.exists(path):
                return {
                    "success": False,
                    "message": f"Repository path '{path}' does not exist"
                }
            
            # Check if the path is a Git repository
            git_dir = os.path.join(path, ".git")
            if not os.path.exists(git_dir):
                return {
                    "success": False,
                    "message": f"Path '{path}' is not a Git repository"
                }
            
            # Open the repository
            repo = pygit2.Repository(path)
            
            # Check if HEAD is detached
            if not repo.head_is_detached:
                return {
                    "success": False,
                    "message": "HEAD is not detached"
                }
            
            # Get the current HEAD commit
            head_commit = repo.head.peel(pygit2.Commit)
            
            if branch:
                # Check if branch exists
                branch_ref = f"refs/heads/{branch}"
                if branch_ref in repo.references:
                    # Point the branch to the current HEAD
                    ref = repo.references[branch_ref]
                    ref.set_target(head_commit.id)
                else:
                    # Create a new branch
                    repo.create_reference(branch_ref, head_commit.id)
                
                # Point HEAD to the branch
                repo.set_head(branch_ref)
            else:
                # Create a new branch
                timestamp = int(time.time())
                new_branch = f"detached-head-{timestamp}"
                branch_ref = f"refs/heads/{new_branch}"
                
                # Create the branch
                repo.create_reference(branch_ref, head_commit.id)
                
                # Point HEAD to the branch
                repo.set_head(branch_ref)
                
                branch = new_branch
            
            return {
                "success": True,
                "message": f"Successfully fixed detached HEAD by creating branch '{branch}'",
                "branch": branch,
                "commit": str(head_commit.id)
            }
        except Exception as e:
            log_error(f"Error fixing detached HEAD: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }
    
    @staticmethod
    def fix_missing_refs(path: str) -> Dict[str, Any]:
        """
        Fix missing references in a Git repository.
        
        Args:
            path: Path to the repository
        
        Returns:
            Dictionary with fix results
        """
        import subprocess
        
        try:
            # Verify the repository path
            if not os.path.exists(path):
                return {
                    "success": False,
                    "message": f"Repository path '{path}' does not exist"
                }
            
            # Check if the path is a Git repository
            git_dir = os.path.join(path, ".git")
            if not os.path.exists(git_dir):
                return {
                    "success": False,
                    "message": f"Path '{path}' is not a Git repository"
                }
            
            # Execute git fsck to find missing references
            process = subprocess.run(
                ["git", "fsck", "--full"],
                cwd=path,
                capture_output=True,
                text=True
            )
            
            # Parse output to find dangling commits
            dangling_commits = []
            for line in process.stdout.split('\n'):
                if "dangling commit" in line:
                    commit_hash = line.split()[-1]
                    dangling_commits.append(commit_hash)
            
            if not dangling_commits:
                return {
                    "success": True,
                    "message": "No dangling commits found"
                }
            
            # Create a refs/recovered directory if it doesn't exist
            recovered_dir = os.path.join(git_dir, "refs", "recovered")
            os.makedirs(recovered_dir, exist_ok=True)
            
            # Create references for dangling commits
            repo = pygit2.Repository(path)
            
            recovered_refs = []
            for i, commit_hash in enumerate(dangling_commits):
                try:
                    # Validate the commit hash
                    commit = repo.get(pygit2.Oid(hex=commit_hash))
                    
                    # Create a reference
                    ref_name = f"refs/recovered/commit-{i}"
                    repo.create_reference(ref_name, commit.id)
                    
                    recovered_refs.append({
                        "ref": ref_name,
                        "commit": str(commit.id),
                        "message": commit.message.split('\n', 1)[0] if commit.message else ""
                    })
                except Exception as e:
                    log_error(f"Error recovering commit {commit_hash}: {str(e)}")
            
            return {
                "success": True,
                "message": f"Successfully recovered {len(recovered_refs)} dangling commits",
                "recovered_refs": recovered_refs,
                "dangling_commits": dangling_commits
            }
        except Exception as e:
            log_error(f"Error fixing missing refs: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }
    
    @staticmethod
    def recover_lost_commits(path: str) -> Dict[str, Any]:
        """
        Recover lost commits in a Git repository using reflog.
        
        Args:
            path: Path to the repository
        
        Returns:
            Dictionary with recovery results
        """
        import subprocess
        
        try:
            # Verify the repository path
            if not os.path.exists(path):
                return {
                    "success": False,
                    "message": f"Repository path '{path}' does not exist"
                }
            
            # Check if the path is a Git repository
            git_dir = os.path.join(path, ".git")
            if not os.path.exists(git_dir):
                return {
                    "success": False,
                    "message": f"Path '{path}' is not a Git repository"
                }
            
            # Execute git reflog to find lost commits
            process = subprocess.run(
                ["git", "reflog", "--all", "--pretty=format:%H %gd %gs"],
                cwd=path,
                capture_output=True,
                text=True
            )
            
            # Parse output to find lost commits
            reflog_entries = []
            for line in process.stdout.split('\n'):
                if not line.strip():
                    continue
                
                parts = line.split(' ', 2)
                if len(parts) >= 3:
                    commit_hash, ref_name, message = parts
                    
                    # Check if the commit exists in any branch
                    is_lost = True
                    
                    try:
                        process_branch = subprocess.run(
                            ["git", "branch", "--contains", commit_hash],
                            cwd=path,
                            capture_output=True,
                            text=True
                        )
                        
                        if process_branch.stdout.strip():
                            is_lost = False
                    except:
                        pass
                    
                    if is_lost:
                        reflog_entries.append({
                            "commit": commit_hash,
                            "ref_name": ref_name,
                            "message": message
                        })
            
            if not reflog_entries:
                return {
                    "success": True,
                    "message": "No lost commits found in reflog"
                }
            
            # Create a refs/recovered directory if it doesn't exist
            recovered_dir = os.path.join(git_dir, "refs", "recovered")
            os.makedirs(recovered_dir, exist_ok=True)
            
            # Create references for lost commits
            repo = pygit2.Repository(path)
            
            recovered_refs = []
            for i, entry in enumerate(reflog_entries):
                try:
                    # Validate the commit hash
                    commit = repo.get(pygit2.Oid(hex=entry["commit"]))
                    
                    # Create a reference
                    ref_name = f"refs/recovered/reflog-{i}"
                    repo.create_reference(ref_name, commit.id)
                    
                    recovered_refs.append({
                        "ref": ref_name,
                        "commit": str(commit.id),
                        "message": commit.message.split('\n', 1)[0] if commit.message else ""
                    })
                except Exception as e:
                    log_error(f"Error recovering commit {entry['commit']}: {str(e)}")
            
            return {
                "success": True,
                "message": f"Successfully recovered {len(recovered_refs)} lost commits",
                "recovered_refs": recovered_refs,
                "reflog_entries": reflog_entries
            }
        except Exception as e:
            log_error(f"Error recovering lost commits: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }
