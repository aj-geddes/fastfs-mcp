#!/usr/bin/env python3
"""
Enhanced authentication and performance metrics for PyGit2 implementation.

This module extends the PyGit2 implementation with better authentication handling
and performance tracking capabilities.
"""

import os
import time
import stat
import json
import tempfile
from typing import Dict, Any, Optional, Callable

# Performance tracking
def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure execution time of Git operations."""
    def wrapper(*args, **kwargs):
        # Check if timing is enabled
        if os.environ.get("PYGIT2_TIMING", "").lower() in ("true", "1", "yes"):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            # Add timing information to result
            if isinstance(result, dict):
                result["timing"] = {
                    "execution_time_ms": round((end_time - start_time) * 1000, 2)
                }
            
            return result
        else:
            return func(*args, **kwargs)
    
    return wrapper

# Authentication helpers
class AuthenticationManager:
    """Manage Git authentication methods."""
    
    @staticmethod
    def get_credentials_callback(auth_method: str, **kwargs) -> Callable:
        """
        Get credentials callback based on authentication method.
        
        Args:
            auth_method: Authentication method (token, ssh, username_password)
            **kwargs: Authentication parameters
        
        Returns:
            Credentials callback function
        """
        import pygit2
        
        if auth_method == "token":
            token = kwargs.get("token")
            if not token:
                raise ValueError("Token is required for token authentication")
            
            def credentials_cb(url, username_from_url, allowed_types):
                if allowed_types & pygit2.CredentialType.USERPASS_PLAINTEXT:
                    return pygit2.UserPass("x-access-token", token)
                else:
                    raise ValueError(f"Token authentication not supported for {url}")
            
            return credentials_cb
        
        elif auth_method == "ssh":
            ssh_public_key = kwargs.get("ssh_public_key")
            ssh_private_key = kwargs.get("ssh_private_key")
            ssh_passphrase = kwargs.get("ssh_passphrase", "")
            
            if not ssh_private_key:
                raise ValueError("SSH private key is required for SSH authentication")
            
            # Create temporary files for SSH keys if they are provided as content
            if ssh_private_key and not os.path.exists(ssh_private_key):
                temp_private_key = tempfile.NamedTemporaryFile(delete=False)
                temp_private_key.write(ssh_private_key.encode())
                temp_private_key.close()
                os.chmod(temp_private_key.name, stat.S_IRUSR | stat.S_IWUSR)
                ssh_private_key = temp_private_key.name
            
            if ssh_public_key and not os.path.exists(ssh_public_key):
                temp_public_key = tempfile.NamedTemporaryFile(delete=False)
                temp_public_key.write(ssh_public_key.encode())
                temp_public_key.close()
                ssh_public_key = temp_public_key.name
            
            def credentials_cb(url, username_from_url, allowed_types):
                if allowed_types & pygit2.CredentialType.SSH_KEY:
                    return pygit2.Keypair(
                        username_from_url or "git",
                        ssh_public_key,
                        ssh_private_key,
                        ssh_passphrase
                    )
                else:
                    raise ValueError(f"SSH authentication not supported for {url}")
            
            return credentials_cb
        
        elif auth_method == "username_password":
            username = kwargs.get("username")
            password = kwargs.get("password")
            
            if not username or not password:
                raise ValueError("Username and password are required for username/password authentication")
            
            def credentials_cb(url, username_from_url, allowed_types):
                if allowed_types & pygit2.CredentialType.USERPASS_PLAINTEXT:
                    return pygit2.UserPass(username, password)
                else:
                    raise ValueError(f"Username/password authentication not supported for {url}")
            
            return credentials_cb
        
        else:
            raise ValueError(f"Unknown authentication method: {auth_method}")
    
    @staticmethod
    def create_remote_callbacks(auth_method: str, **kwargs) -> Dict[str, Any]:
        """
        Create remote callbacks for authentication.
        
        Args:
            auth_method: Authentication method
            **kwargs: Authentication parameters
        
        Returns:
            Dictionary with remote callbacks
        """
        import pygit2
        
        credentials_cb = AuthenticationManager.get_credentials_callback(auth_method, **kwargs)
        
        # Create callbacks
        callbacks = pygit2.RemoteCallbacks(credentials=credentials_cb)
        
        return callbacks

# Repository health checks
class RepositoryHealth:
    """Repository health checks and diagnostics."""
    
    @staticmethod
    def check_repository(repo_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive health check on repository.
        
        Args:
            repo_path: Path to the repository
        
        Returns:
            Dictionary with health check results
        """
        import pygit2
        
        try:
            # Find repository
            repo = pygit2.Repository(repo_path)
            
            # Initialize result
            result = {
                "success": True,
                "repository": {
                    "path": repo_path,
                    "is_bare": repo.is_bare,
                    "is_empty": repo.is_empty,
                    "is_shallow": repo.is_shallow
                },
                "issues": [],
                "warnings": [],
                "recommendations": []
            }
            
            # Check if repository is empty
            if repo.is_empty:
                result["warnings"].append("Repository is empty")
                return result
            
            # Check if HEAD is detached
            if repo.head_is_detached:
                result["warnings"].append("HEAD is detached")
            
            # Check for uncommitted changes
            status = repo.status()
            if status:
                unstaged_count = 0
                staged_count = 0
                untracked_count = 0
                
                for file_path, status_flags in status.items():
                    if status_flags & pygit2.GIT_STATUS_WT_NEW:
                        untracked_count += 1
                    elif (status_flags & pygit2.GIT_STATUS_INDEX_NEW or
                          status_flags & pygit2.GIT_STATUS_INDEX_MODIFIED or
                          status_flags & pygit2.GIT_STATUS_INDEX_DELETED):
                        staged_count += 1
                    elif (status_flags & pygit2.GIT_STATUS_WT_MODIFIED or
                          status_flags & pygit2.GIT_STATUS_WT_DELETED):
                        unstaged_count += 1
                
                total_changes = unstaged_count + staged_count + untracked_count
                
                if total_changes > 0:
                    result["warnings"].append(
                        f"Repository has uncommitted changes ({total_changes} files)"
                    )
                    result["uncommitted_changes"] = {
                        "unstaged": unstaged_count,
                        "staged": staged_count,
                        "untracked": untracked_count,
                        "total": total_changes
                    }
            
            # Check for .gitignore
            try:
                repo.revparse_single("HEAD:.gitignore")
            except KeyError:
                result["warnings"].append("No .gitignore file found")
                result["recommendations"].append("Create a .gitignore file to exclude unnecessary files")
            
            # Check for unpushed commits
            if not repo.head_is_detached:
                branch_name = repo.head.shorthand
                
                # Check if branch has upstream
                try:
                    remote_name = repo.config[f"branch.{branch_name}.remote"]
                    remote_branch = repo.config[f"branch.{branch_name}.merge"].replace("refs/heads/", "")
                    
                    # Check if remote exists
                    if remote_name in repo.remotes:
                        remote_ref = f"refs/remotes/{remote_name}/{remote_branch}"
                        try:
                            remote_commit = repo.revparse_single(remote_ref)
                            head_commit = repo.revparse_single("HEAD")
                            
                            # Count unpushed commits
                            walker = repo.walk(head_commit.id, pygit2.GIT_SORT_TOPOLOGICAL)
                            walker.hide(remote_commit.id)
                            
                            unpushed_count = sum(1 for _ in walker)
                            
                            if unpushed_count > 0:
                                result["warnings"].append(f"{unpushed_count} unpushed commits")
                                result["unpushed_commits"] = unpushed_count
                        except KeyError:
                            result["warnings"].append(f"Remote branch '{remote_branch}' not found")
                except KeyError:
                    result["warnings"].append(f"Branch '{branch_name}' has no tracking branch")
            
            # Check if repository is shallow
            if repo.is_shallow:
                result["warnings"].append("Repository is shallow")
                result["recommendations"].append("Consider converting to a full clone for better history")
            
            # Check for large files
            try:
                walker = repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL)
                large_files = []
                
                for commit in walker:
                    # Only check the most recent 10 commits
                    if len(large_files) >= 10:
                        break
                    
                    tree = commit.tree
                    for entry in tree:
                        if entry.type == pygit2.GIT_OBJ_BLOB:
                            blob = repo.get(entry.id)
                            # Check if file is larger than 1MB
                            if blob.size > 1024 * 1024:
                                large_files.append({
                                    "path": entry.name,
                                    "size_mb": round(blob.size / (1024 * 1024), 2),
                                    "commit": str(commit.id)[:7]
                                })
                
                if large_files:
                    result["warnings"].append(f"Found {len(large_files)} large files (>1MB)")
                    result["large_files"] = large_files
                    result["recommendations"].append("Consider using Git LFS for large files")
            except:
                # Ignore errors when checking for large files
                pass
            
            # Check for stale branches
            branches = []
            for ref in repo.references:
                if ref.startswith('refs/heads/'):
                    branch_name = ref[11:]  # Strip 'refs/heads/'
                    branch_ref = repo.references[ref]
                    commit = branch_ref.peel(pygit2.Commit)
                    
                    branches.append({
                        "name": branch_name,
                        "commit_time": commit.commit_time,
                        "days_old": (time.time() - commit.commit_time) / (60 * 60 * 24)
                    })
            
            stale_branches = [b for b in branches if b["days_old"] > 90]
            if stale_branches:
                result["warnings"].append(f"Found {len(stale_branches)} stale branches (>90 days old)")
                result["stale_branches"] = stale_branches
                result["recommendations"].append("Consider cleaning up stale branches")
            
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"Error checking repository health: {str(e)}",
                "error": str(e)
            }
    
    @staticmethod
    def suggest_optimization(repo_path: str) -> Dict[str, Any]:
        """
        Suggest repository optimizations.
        
        Args:
            repo_path: Path to the repository
        
        Returns:
            Dictionary with optimization suggestions
        """
        import pygit2
        import subprocess
        
        try:
            # Find repository
            repo = pygit2.Repository(repo_path)
            
            # Initialize result
            result = {
                "success": True,
                "repository": {
                    "path": repo_path,
                    "is_bare": repo.is_bare,
                    "is_empty": repo.is_empty
                },
                "suggestions": []
            }
            
            # Check repository size
            repo_size = 0
            git_dir = repo.path
            
            # Use du command to get repository size
            process = subprocess.run(
                ["du", "-sk", git_dir],
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                try:
                    repo_size = int(process.stdout.split()[0])
                except:
                    pass
            
            if repo_size > 100 * 1024:  # Larger than 100MB
                result["suggestions"].append({
                    "type": "gc",
                    "message": "Repository is large, consider running git gc",
                    "command": "git gc",
                    "priority": "high"
                })
            
            # Check if repository has too many branches
            branch_count = 0
            for ref in repo.references:
                if ref.startswith('refs/heads/'):
                    branch_count += 1
            
            if branch_count > 50:
                result["suggestions"].append({
                    "type": "prune_branches",
                    "message": f"Repository has {branch_count} branches, consider cleaning up stale branches",
                    "command": "git branch -r | grep -v '\\->' | while read remote; do git branch --track \"${remote#origin/}\" \"$remote\"; done",
                    "priority": "medium"
                })
            
            # Check if repository could benefit from Git LFS
            large_file_count = 0
            large_file_extensions = set()
            
            try:
                if not repo.is_empty:
                    for commit in repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL | pygit2.GIT_SORT_TIME):
                        # Only check the most recent commit
                        tree = commit.tree
                        for entry in tree:
                            if entry.type == pygit2.GIT_OBJ_BLOB:
                                blob = repo.get(entry.id)
                                # Check if file is larger than 1MB
                                if blob.size > 1024 * 1024:
                                    large_file_count += 1
                                    if "." in entry.name:
                                        ext = entry.name.split(".")[-1].lower()
                                        large_file_extensions.add(ext)
                        break
            except:
                pass
            
            if large_file_count > 10 or len(large_file_extensions) > 3:
                lfs_command = "git lfs install"
                if large_file_extensions:
                    for ext in large_file_extensions:
                        lfs_command += f" && git lfs track \"*.{ext}\""
                
                result["suggestions"].append({
                    "type": "git_lfs",
                    "message": f"Repository has {large_file_count} large files with extensions: {', '.join(large_file_extensions)}",
                    "command": lfs_command,
                    "priority": "high"
                })
            
            # Check for potential submodule candidates
            vendor_dirs = ["vendor", "third_party", "external", "deps", "lib"]
            submodule_candidates = []
            
            try:
                if not repo.is_empty:
                    head_tree = repo.revparse_single("HEAD").tree
                    
                    for dir_name in vendor_dirs:
                        try:
                            entry = head_tree[dir_name]
                            if entry.type == pygit2.GIT_OBJ_TREE:
                                submodule_candidates.append(dir_name)
                        except KeyError:
                            pass
            except:
                pass
            
            if submodule_candidates:
                result["suggestions"].append({
                    "type": "submodules",
                    "message": f"Consider using Git submodules for: {', '.join(submodule_candidates)}",
                    "command": "git submodule add <repository-url> <directory>",
                    "priority": "low"
                })
            
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"Error suggesting optimizations: {str(e)}",
                "error": str(e)
            }

# Conflict resolution helpers
class ConflictResolver:
    """Helper methods for conflict resolution."""
    
    @staticmethod
    def list_conflicts(repo_path: str) -> Dict[str, Any]:
        """
        List all conflicts in the repository.
        
        Args:
            repo_path: Path to the repository
        
        Returns:
            Dictionary with conflict information
        """
        import pygit2
        
        try:
            # Find repository
            repo = pygit2.Repository(repo_path)
            
            # Check if repository is in merge state
            if repo.state != pygit2.GIT_REPOSITORY_STATE_MERGE:
                return {
                    "success": True,
                    "message": "Repository is not in merge state",
                    "conflicts": [],
                    "count": 0
                }
            
            # Get index
            index = repo.index
            
            # Get conflicts
            conflicts = []
            for conflict in index.conflicts:
                conflict_info = {
                    "ancestor": conflict[0].path if conflict[0] else None,
                    "ours": conflict[1].path if conflict[1] else None,
                    "theirs": conflict[2].path if conflict[2] else None
                }
                
                # Read file contents if available
                if conflict[1]:  # Ours
                    try:
                        blob = repo.get(conflict[1].id)
                        if not ConflictResolver._is_binary_blob(blob):
                            conflict_info["ours_content"] = blob.data.decode('utf-8', errors='replace')
                    except:
                        pass
                
                if conflict[2]:  # Theirs
                    try:
                        blob = repo.get(conflict[2].id)
                        if not ConflictResolver._is_binary_blob(blob):
                            conflict_info["theirs_content"] = blob.data.decode('utf-8', errors='replace')
                    except:
                        pass
                
                if conflict[0]:  # Ancestor
                    try:
                        blob = repo.get(conflict[0].id)
                        if not ConflictResolver._is_binary_blob(blob):
                            conflict_info["ancestor_content"] = blob.data.decode('utf-8', errors='replace')
                    except:
                        pass
                
                conflicts.append(conflict_info)
            
            return {
                "success": True,
                "message": f"Found {len(conflicts)} conflicts",
                "conflicts": conflicts,
                "count": len(conflicts)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error listing conflicts: {str(e)}",
                "error": str(e)
            }
    
    @staticmethod
    def _is_binary_blob(blob) -> bool:
        """
        Check if a blob is binary.
        
        Args:
            blob: Git blob object
        
        Returns:
            True if blob is binary, False otherwise
        """
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
    
    @staticmethod
    def resolve_conflict(repo_path: str, file_path: str, resolution: str, 
                         content: Optional[str] = None) -> Dict[str, Any]:
        """
        Resolve a conflict for a specific file.
        
        Args:
            repo_path: Path to the repository
            file_path: Path to the conflicted file
            resolution: Resolution type (ours, theirs, custom)
            content: Custom content if resolution is 'custom'
        
        Returns:
            Dictionary with resolution result
        """
        import pygit2
        import os
        
        try:
            # Find repository
            repo = pygit2.Repository(repo_path)
            
            # Check if repository is in merge state
            if repo.state != pygit2.GIT_REPOSITORY_STATE_MERGE:
                return {
                    "success": False,
                    "message": "Repository is not in merge state"
                }
            
            # Get index
            index = repo.index
            
            # Check if file is in conflict
            in_conflict = False
            for conflict in index.conflicts:
                if ((conflict[1] and conflict[1].path == file_path) or 
                    (conflict[2] and conflict[2].path == file_path)):
                    in_conflict = True
                    break
            
            if not in_conflict:
                return {
                    "success": False,
                    "message": f"File '{file_path}' is not in conflict"
                }
            
            # Resolve conflict
            if resolution == "ours":
                # Use our version
                for conflict in index.conflicts:
                    if ((conflict[1] and conflict[1].path == file_path) or 
                        (conflict[2] and conflict[2].path == file_path)):
                        if conflict[1]:
                            # Add our version to index
                            index.add_by_id(file_path, conflict[1].id, conflict[1].mode)
                            index.add(file_path)
                            break
                        else:
                            # Remove file from index (deleted in ours)
                            index.remove(file_path)
                            break
                
                # Mark as resolved
                ConflictResolver._mark_resolved(index, file_path)
                index.write()
                
                return {
                    "success": True,
                    "message": f"Resolved conflict for '{file_path}' using 'ours' strategy",
                    "file": file_path,
                    "resolution": "ours"
                }
            
            elif resolution == "theirs":
                # Use their version
                for conflict in index.conflicts:
                    if ((conflict[1] and conflict[1].path == file_path) or 
                        (conflict[2] and conflict[2].path == file_path)):
                        if conflict[2]:
                            # Add their version to index
                            index.add_by_id(file_path, conflict[2].id, conflict[2].mode)
                            index.add(file_path)
                            break
                        else:
                            # Remove file from index (deleted in theirs)
                            index.remove(file_path)
                            break
                
                # Mark as resolved
                ConflictResolver._mark_resolved(index, file_path)
                index.write()
                
                return {
                    "success": True,
                    "message": f"Resolved conflict for '{file_path}' using 'theirs' strategy",
                    "file": file_path,
                    "resolution": "theirs"
                }
            
            elif resolution == "custom":
                if content is None:
                    return {
                        "success": False,
                        "message": "Custom content is required for 'custom' resolution"
                    }
                
                # Create file with custom content
                file_path_abs = os.path.join(os.path.dirname(repo.path), file_path)
                os.makedirs(os.path.dirname(file_path_abs), exist_ok=True)
                
                with open(file_path_abs, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Add to index
                index.add(file_path)
                
                # Mark as resolved
                ConflictResolver._mark_resolved(index, file_path)
                index.write()
                
                return {
                    "success": True,
                    "message": f"Resolved conflict for '{file_path}' using custom content",
                    "file": file_path,
                    "resolution": "custom"
                }
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown resolution type: {resolution}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error resolving conflict: {str(e)}",
                "error": str(e)
            }
    
    @staticmethod
    def _mark_resolved(index, file_path: str) -> None:
        """
        Mark a file as resolved in the index.
        
        Args:
            index: Repository index
            file_path: Path to the file
        """
        # This is a bit of a hack, but pygit2 doesn't provide a direct way to remove conflicts
        # Adding the file to the index should mark it as resolved
        try:
            if hasattr(index, "remove_conflict"):
                index.remove_conflict(file_path)
            if hasattr(index, "conflicts"):
                index.conflicts.remove(file_path)
        except:
            pass

# Documentation generator
class DocumentationGenerator:
    """Generate documentation for PyGit2 implementation."""
    
    @staticmethod
    def generate_function_docs(module_path: str) -> Dict[str, Any]:
        """
        Generate documentation for functions in a module.
        
        Args:
            module_path: Path to the module
        
        Returns:
            Dictionary with function documentation
        """
        import inspect
        import importlib.util
        import sys
        
        try:
            # Load module
            module_name = os.path.basename(module_path).replace('.py', '')
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Get all functions
            functions = []
            
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and name.startswith('git_'):
                    # Get function info
                    doc = inspect.getdoc(obj)
                    sig = inspect.signature(obj)
                    
                    # Parse docstring
                    description = ""
                    params = []
                    returns = ""
                    
                    if doc:
                        lines = doc.split('\n')
                        description_lines = []
                        in_params = False
                        in_returns = False
                        
                        for line in lines:
                            line = line.strip()
                            
                            if line.startswith('Args:'):
                                in_params = True
                                in_returns = False
                            elif line.startswith('Returns:'):
                                in_params = False
                                in_returns = True
                            elif in_params:
                                if line:
                                    param_match = line.split(':', 1)
                                    if len(param_match) == 2:
                                        param_name = param_match[0].strip()
                                        param_desc = param_match[1].strip()
                                        params.append({
                                            "name": param_name,
                                            "description": param_desc
                                        })
                            elif in_returns:
                                if line:
                                    returns += line + " "
                            else:
                                description_lines.append(line)
                        
                        description = ' '.join(description_lines).strip()
                    
                    # Get parameter info from signature
                    signature_params = []
                    for param_name, param in sig.parameters.items():
                        if param_name != 'self':
                            param_info = {
                                "name": param_name,
                                "required": param.default == inspect.Parameter.empty,
                                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                                "default": "" if param.default == inspect.Parameter.empty else str(param.default)
                            }
                            
                            # Add description from docstring
                            for p in params:
                                if p["name"] == param_name:
                                    param_info["description"] = p["description"]
                                    break
                            
                            signature_params.append(param_info)
                    
                    # Create function info
                    function_info = {
                        "name": name,
                        "description": description,
                        "parameters": signature_params,
                        "returns": returns
                    }
                    
                    functions.append(function_info)
            
            return {
                "success": True,
                "module": module_name,
                "functions": functions,
                "count": len(functions)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error generating documentation: {str(e)}",
                "error": str(e)
            }
    
    @staticmethod
    def generate_markdown_docs(module_path: str) -> str:
        """
        Generate markdown documentation for functions in a module.
        
        Args:
            module_path: Path to the module
        
        Returns:
            Markdown documentation
        """
        docs = DocumentationGenerator.generate_function_docs(module_path)
        
        if not docs["success"]:
            return f"# Error\n\n{docs['message']}"
        
        markdown = f"# {docs['module']} API Documentation\n\n"
        markdown += "## Table of Contents\n\n"
        
        # Add table of contents
        for function in docs["functions"]:
            markdown += f"- [{function['name']}](#{function['name'].lower()})\n"
        
        markdown += "\n"
        
        # Add function documentation
        for function in docs["functions"]:
            markdown += f"## {function['name']}\n\n"
            markdown += f"{function['description']}\n\n"
            
            markdown += "### Parameters\n\n"
            markdown += "| Name | Type | Required | Default | Description |\n"
            markdown += "|------|------|----------|---------|-------------|\n"
            
            for param in function["parameters"]:
                required = "Yes" if param.get("required", False) else "No"
                default = param.get("default", "")
                description = param.get("description", "")
                param_type = param.get("type", "Any")
                
                markdown += f"| {param['name']} | {param_type} | {required} | {default} | {description} |\n"
            
            markdown += "\n"
            
            markdown += "### Returns\n\n"
            markdown += f"{function['returns']}\n\n"
            
            markdown += "### Example\n\n"
            markdown += "```python\n"
            markdown += f"from {docs['module']} import {function['name']}\n\n"
            
            # Generate example call
            params = []
            for param in function["parameters"]:
                if param.get("required", False):
                    if "path" in param["name"]:
                        params.append(f"{param['name']}='/path/to/repo'")
                    elif "name" in param["name"]:
                        params.append(f"{param['name']}='example'")
                    elif "message" in param["name"]:
                        params.append(f"{param['name']}='Example message'")
                    elif param.get("type", "").lower() == "str":
                        params.append(f"{param['name']}='value'")
                    elif param.get("type", "").lower() == "int":
                        params.append(f"{param['name']}=1")
                    elif param.get("type", "").lower() == "bool":
                        params.append(f"{param['name']}=True")
                    else:
                        params.append(f"{param['name']}=value")
            
            markdown += f"result = {function['name']}({', '.join(params)})\n"
            markdown += "print(result)\n"
            markdown += "```\n\n"
            
            markdown += "### Response\n\n"
            markdown += "```json\n"
            markdown += "{\n"
            markdown += '  "success": true,\n'
            markdown += '  "message": "Operation completed successfully",\n'
            markdown += '  // Additional response fields depending on the operation\n'
            markdown += "}\n"
            markdown += "```\n\n"
            
            markdown += "---\n\n"
        
        return markdown

# Apply timing decorator to all Git operations
def apply_timing_decorator(module):
    """
    Apply timing decorator to all Git operations in a module.
    
    Args:
        module: Module to apply decorator to
    """
    for name in dir(module):
        if name.startswith('git_'):
            func = getattr(module, name)
            if callable(func):
                setattr(module, name, timing_decorator(func))
