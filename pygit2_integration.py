#!/usr/bin/env python3
"""
PyGit2 Integration for FastFS-MCP.

This module integrates all PyGit2 features into a single interface for use
with FastFS-MCP, including basic and advanced Git operations, SSH support,
and error handling.
"""

import os
import sys
import json
import time
from typing import Dict, Any, List, Optional, Union, Callable

try:
    import pygit2
except ImportError:
    print("Error: PyGit2 is not installed. Please install it with 'pip install pygit2'", file=sys.stderr)
    sys.exit(1)

# Import all modules
try:
    # Import basic PyGit2 tools
    from pygit2_tools import (
        # Helper functions
        find_repository, log_debug, log_error, format_commit,
        format_diff, _is_binary_blob,
        
        # Basic Git operations
        git_init, git_clone, git_status, git_add, git_commit,
        git_log, git_branch, git_checkout, git_merge, git_show,
        git_diff, git_remote, git_push, git_pull, git_fetch,
        git_reset, git_stash, git_tag, git_blame, git_grep,
        git_context, git_validate, git_suggest_commit
    )
    
    # Import advanced PyGit2 tools
    from advanced_pygit2 import (
        git_rebase, git_rebase_continue, git_rebase_abort,
        git_cherry_pick, git_worktree_add, git_worktree_list,
        git_worktree_remove, git_submodule_add, git_submodule_update,
        git_submodule_list, git_bisect_start, git_bisect_good,
        git_bisect_bad, git_bisect_reset, git_reflog, git_clean,
        git_archive, git_gc
    )
    
    # Import enhanced PyGit2 tools
    from enhanced_pygit2 import (
        AuthenticationManager, ConflictResolver,
        DocumentationGenerator, RepositoryHealth,
        timing_decorator
    )
    
    # Import SSH support
    from ssh_support import (
        SSHCredential, SSHConfig, SSHKeyManager
    )
    
    # Import error handling
    from git_error_handler import (
        GitErrorHandler, GitRetry, GitRepair
    )
    
    # Set flag to indicate all modules are imported
    all_modules_imported = True
except ImportError as e:
    print(f"Warning: Some modules could not be imported: {str(e)}", file=sys.stderr)
    all_modules_imported = False

class PyGit2Integration:
    """
    PyGit2 Integration for FastFS-MCP.
    
    This class provides a unified interface to all PyGit2 features for use
    with FastFS-MCP, including basic and advanced Git operations, SSH support,
    and error handling.
    """
    
    def __init__(self, enable_timing: bool = False, 
                debug: bool = False, 
                default_repository: Optional[str] = None):
        """
        Initialize PyGit2 Integration.
        
        Args:
            enable_timing: Whether to enable timing information
            debug: Whether to enable debug logging
            default_repository: Default repository path
        """
        self.enable_timing = enable_timing
        self.debug = debug
        self.default_repository = default_repository
        
        # Set environment variables
        if enable_timing:
            os.environ["PYGIT2_TIMING"] = "true"
        
        if debug:
            os.environ["FASTFS_DEBUG"] = "true"
        
        # Initialize authentication
        self.auth_manager = None
        self.ssh_credential = None
        
        # Check if all modules are imported
        if not all_modules_imported:
            print("Warning: Some modules could not be imported. Some features may not be available.", file=sys.stderr)
    
    def execute(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Git operation.
        
        Args:
            method: Git operation method name
            params: Git operation parameters
            
        Returns:
            Operation result
        """
        # Check if method exists
        if not hasattr(self, method) or not callable(getattr(self, method)):
            return {
                "success": False,
                "message": f"Unknown method: {method}"
            }
        
        # Get method
        method_func = getattr(self, method)
        
        try:
            # Add default repository if not provided
            if self.default_repository and "path" not in params:
                params["path"] = self.default_repository
            
            # Execute method
            if self.enable_timing:
                start_time = time.time()
                result = method_func(**params)
                end_time = time.time()
                
                # Add timing information
                if isinstance(result, dict):
                    result["timing"] = {
                        "execution_time_ms": round((end_time - start_time) * 1000, 2)
                    }
                
                return result
            else:
                return method_func(**params)
        except Exception as e:
            # Handle error
            return GitErrorHandler.handle_error(
                error=e,
                operation=method,
                repository_path=params.get("path", self.default_repository)
            )
    
    def configure_auth(self, auth_type: str, **kwargs) -> Dict[str, Any]:
        """
        Configure authentication.
        
        Args:
            auth_type: Authentication type (token, ssh, username_password)
            **kwargs: Authentication parameters
            
        Returns:
            Configuration result
        """
        try:
            # Configure authentication
            if auth_type == "token":
                # Token authentication
                token = kwargs.get("token")
                if not token:
                    return {
                        "success": False,
                        "message": "Token is required for token authentication"
                    }
                
                self.auth_manager = AuthenticationManager.create_remote_callbacks(
                    "token", token=token
                )
                
                return {
                    "success": True,
                    "message": "Token authentication configured",
                    "auth_type": "token"
                }
            
            elif auth_type == "ssh":
                # SSH authentication
                private_key = kwargs.get("private_key")
                public_key = kwargs.get("public_key")
                passphrase = kwargs.get("passphrase", "")
                username = kwargs.get("username", "git")
                
                if private_key:
                    # Create SSH credential from key content or file
                    if os.path.exists(private_key):
                        # From key file
                        self.ssh_credential = SSHCredential(
                            username=username,
                            private_key_path=private_key,
                            public_key_path=public_key,
                            passphrase=passphrase
                        )
                    else:
                        # From key content
                        self.ssh_credential = SSHCredential.from_key_content(
                            private_key_content=private_key,
                            public_key_content=public_key,
                            username=username,
                            passphrase=passphrase
                        )
                elif kwargs.get("use_agent", False):
                    # Use SSH agent
                    self.ssh_credential = SSHCredential.from_agent(username=username)
                elif kwargs.get("use_default_key", False):
                    # Use default SSH key
                    self.ssh_credential = SSHCredential.from_default_key(username=username)
                else:
                    return {
                        "success": False,
                        "message": "SSH authentication requires private_key, use_agent, or use_default_key"
                    }
                
                # Create callbacks
                self.auth_manager = self.ssh_credential.create_remote_callbacks()
                
                return {
                    "success": True,
                    "message": "SSH authentication configured",
                    "auth_type": "ssh"
                }
            
            elif auth_type == "username_password":
                # Username/password authentication
                username = kwargs.get("username")
                password = kwargs.get("password")
                
                if not username or not password:
                    return {
                        "success": False,
                        "message": "Username and password are required for username/password authentication"
                    }
                
                self.auth_manager = AuthenticationManager.create_remote_callbacks(
                    "username_password", username=username, password=password
                )
                
                return {
                    "success": True,
                    "message": "Username/password authentication configured",
                    "auth_type": "username_password"
                }
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown authentication type: {auth_type}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error configuring authentication: {str(e)}",
                "error": str(e)
            }
    
    def get_api_documentation(self) -> Dict[str, Any]:
        """
        Get API documentation for all Git operations.
        
        Returns:
            API documentation
        """
        # Generate documentation for all modules
        modules = [
            {"path": "pygit2_tools.py", "name": "Basic Git Operations"},
            {"path": "advanced_pygit2.py", "name": "Advanced Git Operations"},
            {"path": "enhanced_pygit2.py", "name": "Enhanced Features"},
            {"path": "ssh_support.py", "name": "SSH Support"},
            {"path": "git_error_handler.py", "name": "Error Handling"}
        ]
        
        docs = {}
        
        for module in modules:
            try:
                module_docs = DocumentationGenerator.generate_function_docs(module["path"])
                if module_docs["success"]:
                    docs[module["name"]] = module_docs
            except:
                pass
        
        return {
            "success": True,
            "modules": list(docs.keys()),
            "documentation": docs
        }
    
    # Forward all methods to the appropriate functions
    
    # Basic Git operations
    def init(self, **kwargs) -> Dict[str, Any]:
        """Initialize a new Git repository."""
        return git_init(**kwargs)
    
    def clone(self, **kwargs) -> Dict[str, Any]:
        """Clone a Git repository."""
        # Add authentication if configured
        if self.auth_manager and "options" not in kwargs:
            kwargs["options"] = {"callbacks": self.auth_manager}
        elif self.auth_manager and "options" in kwargs:
            kwargs["options"]["callbacks"] = self.auth_manager
        
        # Use retry for clone operations
        return GitRetry.retry(git_clone, **kwargs)
    
    def status(self, **kwargs) -> Dict[str, Any]:
        """Show the working tree status."""
        return git_status(**kwargs)
    
    def add(self, **kwargs) -> Dict[str, Any]:
        """Add file(s) to the Git staging area."""
        return git_add(**kwargs)
    
    def commit(self, **kwargs) -> Dict[str, Any]:
        """Commit changes to the Git repository."""
        return git_commit(**kwargs)
    
    def log(self, **kwargs) -> Dict[str, Any]:
        """Show commit logs."""
        return git_log(**kwargs)
    
    def branch(self, **kwargs) -> Dict[str, Any]:
        """List, create, or delete branches."""
        return git_branch(**kwargs)
    
    def checkout(self, **kwargs) -> Dict[str, Any]:
        """Switch branches or restore working tree files."""
        return git_checkout(**kwargs)
    
    def merge(self, **kwargs) -> Dict[str, Any]:
        """Join two or more development histories together."""
        return git_merge(**kwargs)
    
    def show(self, **kwargs) -> Dict[str, Any]:
        """Show various types of Git objects."""
        return git_show(**kwargs)
    
    def diff(self, **kwargs) -> Dict[str, Any]:
        """Show changes between commits, commit and working tree, etc."""
        return git_diff(**kwargs)
    
    def remote(self, **kwargs) -> Dict[str, Any]:
        """Manage remote repositories."""
        return git_remote(**kwargs)
    
    def push(self, **kwargs) -> Dict[str, Any]:
        """Push changes to a remote repository."""
        # Add authentication if configured
        if self.auth_manager and "token" not in kwargs:
            kwargs["token"] = "dummy_token"  # Will be replaced by callback
        
        # Use retry for push operations
        return GitRetry.retry(git_push, **kwargs)
    
    def pull(self, **kwargs) -> Dict[str, Any]:
        """Pull changes from a remote repository."""
        # Add authentication if configured
        if self.auth_manager and "token" not in kwargs:
            kwargs["token"] = "dummy_token"  # Will be replaced by callback
        
        # Use retry for pull operations
        return GitRetry.retry(git_pull, **kwargs)
    
    def fetch(self, **kwargs) -> Dict[str, Any]:
        """Download objects and refs from another repository."""
        # Add authentication if configured
        if self.auth_manager and "token" not in kwargs:
            kwargs["token"] = "dummy_token"  # Will be replaced by callback
        
        # Use retry for fetch operations
        return GitRetry.retry(git_fetch, **kwargs)
    
    def reset(self, **kwargs) -> Dict[str, Any]:
        """Reset current HEAD to the specified state."""
        return git_reset(**kwargs)
    
    def stash(self, **kwargs) -> Dict[str, Any]:
        """Stash the changes in a dirty working tree away."""
        return git_stash(**kwargs)
    
    def tag(self, **kwargs) -> Dict[str, Any]:
        """Create, list, delete or verify a tag object."""
        return git_tag(**kwargs)
    
    def blame(self, **kwargs) -> Dict[str, Any]:
        """Show what revision and author last modified each line of a file."""
        return git_blame(**kwargs)
    
    def grep(self, **kwargs) -> Dict[str, Any]:
        """Search for a pattern in tracked files."""
        return git_grep(**kwargs)
    
    def context(self, **kwargs) -> Dict[str, Any]:
        """Get comprehensive context about the current Git repository."""
        return git_context(**kwargs)
    
    def validate(self, **kwargs) -> Dict[str, Any]:
        """Validate the Git repository for common issues."""
        return git_validate(**kwargs)
    
    def suggest_commit(self, **kwargs) -> Dict[str, Any]:
        """Analyze changes and suggest a commit message."""
        return git_suggest_commit(**kwargs)
    
    # Advanced Git operations
    def rebase(self, **kwargs) -> Dict[str, Any]:
        """Reapply commits on top of another base tip."""
        return git_rebase(**kwargs)
    
    def rebase_continue(self, **kwargs) -> Dict[str, Any]:
        """Continue a rebase operation after resolving conflicts."""
        return git_rebase_continue(**kwargs)
    
    def rebase_abort(self, **kwargs) -> Dict[str, Any]:
        """Abort a rebase operation and return to the original state."""
        return git_rebase_abort(**kwargs)
    
    def cherry_pick(self, **kwargs) -> Dict[str, Any]:
        """Apply the changes introduced by existing commits."""
        return git_cherry_pick(**kwargs)
    
    def worktree_add(self, **kwargs) -> Dict[str, Any]:
        """Add a new working tree."""
        return git_worktree_add(**kwargs)
    
    def worktree_list(self, **kwargs) -> Dict[str, Any]:
        """List working trees."""
        return git_worktree_list(**kwargs)
    
    def worktree_remove(self, **kwargs) -> Dict[str, Any]:
        """Remove a working tree."""
        return git_worktree_remove(**kwargs)
    
    def submodule_add(self, **kwargs) -> Dict[str, Any]:
        """Add a submodule."""
        return git_submodule_add(**kwargs)
    
    def submodule_update(self, **kwargs) -> Dict[str, Any]:
        """Update submodules."""
        return git_submodule_update(**kwargs)
    
    def submodule_list(self, **kwargs) -> Dict[str, Any]:
        """List submodules."""
        return git_submodule_list(**kwargs)
    
    def bisect_start(self, **kwargs) -> Dict[str, Any]:
        """Start a bisect session."""
        return git_bisect_start(**kwargs)
    
    def bisect_good(self, **kwargs) -> Dict[str, Any]:
        """Mark the current commit as good in a bisect session."""
        return git_bisect_good(**kwargs)
    
    def bisect_bad(self, **kwargs) -> Dict[str, Any]:
        """Mark the current commit as bad in a bisect session."""
        return git_bisect_bad(**kwargs)
    
    def bisect_reset(self, **kwargs) -> Dict[str, Any]:
        """End a bisect session."""
        return git_bisect_reset(**kwargs)
    
    def reflog(self, **kwargs) -> Dict[str, Any]:
        """Show reflog entries."""
        return git_reflog(**kwargs)
    
    def clean(self, **kwargs) -> Dict[str, Any]:
        """Remove untracked files from the working tree."""
        return git_clean(**kwargs)
    
    def archive(self, **kwargs) -> Dict[str, Any]:
        """Create an archive of files from a named tree."""
        return git_archive(**kwargs)
    
    def gc(self, **kwargs) -> Dict[str, Any]:
        """Cleanup unnecessary files and optimize the local repository."""
        return git_gc(**kwargs)
    
    # Enhanced features
    def check_repository(self, **kwargs) -> Dict[str, Any]:
        """Perform comprehensive health check on repository."""
        return RepositoryHealth.check_repository(**kwargs)
    
    def suggest_optimization(self, **kwargs) -> Dict[str, Any]:
        """Suggest repository optimizations."""
        return RepositoryHealth.suggest_optimization(**kwargs)
    
    def list_conflicts(self, **kwargs) -> Dict[str, Any]:
        """List all conflicts in the repository."""
        return ConflictResolver.list_conflicts(**kwargs)
    
    def resolve_conflict(self, **kwargs) -> Dict[str, Any]:
        """Resolve a conflict for a specific file."""
        return ConflictResolver.resolve_conflict(**kwargs)
    
    # Error handling and recovery
    def repair_repository(self, **kwargs) -> Dict[str, Any]:
        """Attempt to repair a Git repository."""
        return GitRepair.repair_repository(**kwargs)
    
    def restore_backup(self, **kwargs) -> Dict[str, Any]:
        """Restore a backup of a Git repository."""
        return GitRepair.restore_backup(**kwargs)
    
    def fix_corrupted_index(self, **kwargs) -> Dict[str, Any]:
        """Fix a corrupted Git index."""
        return GitRepair.fix_corrupted_index(**kwargs)
    
    def fix_detached_head(self, **kwargs) -> Dict[str, Any]:
        """Fix a detached HEAD state by pointing it to a branch."""
        return GitRepair.fix_detached_head(**kwargs)
    
    def fix_missing_refs(self, **kwargs) -> Dict[str, Any]:
        """Fix missing references in a Git repository."""
        return GitRepair.fix_missing_refs(**kwargs)
    
    def recover_lost_commits(self, **kwargs) -> Dict[str, Any]:
        """Recover lost commits in a Git repository using reflog."""
        return GitRepair.recover_lost_commits(**kwargs)
    
    # SSH support
    def generate_ssh_key(self, **kwargs) -> Dict[str, Any]:
        """Generate a new SSH key pair."""
        return SSHKeyManager.generate_key(**kwargs)
    
    def import_ssh_key(self, **kwargs) -> Dict[str, Any]:
        """Import SSH key pair."""
        return SSHKeyManager.import_key(**kwargs)
    
    def verify_ssh_key(self, **kwargs) -> Dict[str, Any]:
        """Verify SSH key pair."""
        return SSHKeyManager.verify_key(**kwargs)
    
    def test_ssh_connection(self, **kwargs) -> Dict[str, Any]:
        """Test SSH connection."""
        return SSHKeyManager.test_connection(**kwargs)


# FastFS-MCP integration
class PyGit2MCP:
    """
    PyGit2 integration for FastFS-MCP.
    
    This class provides the FastFS-MCP integration for PyGit2.
    """
    
    def __init__(self):
        """Initialize PyGit2 MCP."""
        # Create PyGit2 integration
        self.pygit2 = PyGit2Integration(
            enable_timing="PYGIT2_TIMING" in os.environ and os.environ["PYGIT2_TIMING"].lower() in ("true", "1", "yes"),
            debug="FASTFS_DEBUG" in os.environ and os.environ["FASTFS_DEBUG"].lower() in ("true", "1", "yes")
        )
        
        # Configure authentication
        self.configure_authentication()
    
    def configure_authentication(self):
        """Configure authentication from environment variables."""
        # Check for token
        if "GITHUB_PERSONAL_ACCESS_TOKEN" in os.environ:
            self.pygit2.configure_auth(
                "token",
                token=os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]
            )
        # Check for GitHub App
        elif all(key in os.environ for key in ["GITHUB_APP_ID", "GITHUB_APP_PRIVATE_KEY", "GITHUB_APP_INSTALLATION_ID"]):
            # Create JWT token
            import jwt
            import time
            
            now = int(time.time())
            payload = {
                "iat": now,
                "exp": now + 600,
                "iss": os.environ["GITHUB_APP_ID"]
            }
            
            private_key = os.environ["GITHUB_APP_PRIVATE_KEY"]
            token = jwt.encode(payload, private_key, algorithm="RS256")
            
            # Configure token authentication
            self.pygit2.configure_auth(
                "token",
                token=token
            )
        # Check for SSH key
        elif os.path.exists(os.path.expanduser("~/.ssh/id_rsa")):
            self.pygit2.configure_auth(
                "ssh",
                use_default_key=True
            )
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle FastFS-MCP request.
        
        Args:
            request: FastFS-MCP request
            
        Returns:
            FastFS-MCP response
        """
        # Extract method and parameters
        method = request.get("method")
        params = request.get("params", {})
        
        if not method:
            return {
                "error": {
                    "code": -32600,
                    "message": "Invalid request: method is required"
                }
            }
        
        # Execute method
        try:
            result = self.pygit2.execute(method, params)
            return {"result": result}
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }


# Main function
def main():
    """Main function."""
    # Create PyGit2 MCP
    mcp = PyGit2MCP()
    
    # Read requests from stdin
    for line in sys.stdin:
        try:
            # Parse request
            request = json.loads(line)
            
            # Handle request
            response = mcp.handle_request(request)
            
            # Send response
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            # Invalid JSON
            print(json.dumps({
                "error": {
                    "code": -32700,
                    "message": "Parse error: invalid JSON"
                }
            }))
            sys.stdout.flush()
        except Exception as e:
            # Other error
            print(json.dumps({
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
