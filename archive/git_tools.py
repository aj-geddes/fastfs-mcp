#!/usr/bin/env python3
"""
Git tools module for fastfs-mcp.

This module provides Git operations as MCP tools, allowing Claude to
interact with Git repositories through the MCP server.
"""

import os
import sys
import json
import time
import subprocess
from typing import Dict, List, Optional, Any, Union, Tuple
import jwt  # For GitHub App authentication
from datetime import datetime, timedelta

# Check for GitHub auth credentials in environment variables
GITHUB_PAT = os.environ.get('GITHUB_PERSONAL_ACCESS_TOKEN')
GITHUB_APP_ID = os.environ.get('GITHUB_APP_ID')
GITHUB_APP_PRIVATE_KEY = os.environ.get('GITHUB_APP_PRIVATE_KEY')
GITHUB_APP_PRIVATE_KEY_PATH = os.environ.get('GITHUB_APP_PRIVATE_KEY_PATH')
GITHUB_APP_INSTALLATION_ID = os.environ.get('GITHUB_APP_INSTALLATION_ID')

# Configure Git to use GitHub authentication if available
if GITHUB_PAT:
    # Configure Git to use HTTPS with credentials in URL
    try:
        subprocess.run(
            "git config --global credential.helper store",
            shell=True,
            capture_output=True,
            text=True
        )
        
        print("[INFO] GitHub Personal Access Token detected. Git configured for authentication.", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[WARNING] Failed to configure Git credential helper: {str(e)}", file=sys.stderr, flush=True)
elif GITHUB_APP_ID and (GITHUB_APP_PRIVATE_KEY or GITHUB_APP_PRIVATE_KEY_PATH):
    print("[INFO] GitHub App credentials detected. GitHub App authentication will be used.", file=sys.stderr, flush=True)
    if GITHUB_APP_PRIVATE_KEY_PATH:
        print(f"[INFO] Using GitHub App private key from path: {GITHUB_APP_PRIVATE_KEY_PATH}", file=sys.stderr, flush=True)

def get_private_key() -> str:
    """
    Get the GitHub App private key from either the environment variable or the specified file path.
    
    Returns:
        The private key as a string
    """
    if GITHUB_APP_PRIVATE_KEY:
        # Use the key directly from the environment variable
        private_key = GITHUB_APP_PRIVATE_KEY
    elif GITHUB_APP_PRIVATE_KEY_PATH:
        # Read the key from the specified file
        try:
            with open(GITHUB_APP_PRIVATE_KEY_PATH, 'r') as key_file:
                private_key = key_file.read()
            print(f"[INFO] Successfully read private key from {GITHUB_APP_PRIVATE_KEY_PATH}", file=sys.stderr, flush=True)
        except Exception as e:
            raise ValueError(f"Failed to read private key from {GITHUB_APP_PRIVATE_KEY_PATH}: {str(e)}")
    else:
        raise ValueError("No GitHub App private key available. Set either GITHUB_APP_PRIVATE_KEY or GITHUB_APP_PRIVATE_KEY_PATH")
    
    # Fix newlines if needed
    return private_key.replace('\\n', '\n')

# GitHub App authentication functions
def generate_jwt() -> str:
    """
    Generate a JWT for GitHub App authentication.
    
    Returns:
        A JWT token string for GitHub App authentication
    """
    if not GITHUB_APP_ID:
        raise ValueError("GitHub App ID must be set in environment variables")
    
    # Create JWT payload with expiration time (10 minutes maximum)
    now = int(time.time())
    payload = {
        "iat": now - 60,  # issued at time, 60 seconds in the past to allow for clock drift
        "exp": now + (10 * 60),  # JWT expiration time (10 minute maximum)
        "iss": GITHUB_APP_ID  # GitHub App's identifier
    }
    
    # Get the private key and sign the JWT
    private_key = get_private_key()
    token = jwt.encode(payload, private_key, algorithm="RS256")
    
    # If token is bytes, decode to string (depends on jwt library version)
    if isinstance(token, bytes):
        return token.decode('utf-8')
    return token

def get_installation_token() -> Tuple[bool, str]:
    """
    Get an installation access token for GitHub App.
    
    Returns:
        Tuple of (success, token or error message)
    """
    try:
        # First generate a JWT
        jwt_token = generate_jwt()
        
        # Determine installation ID
        installation_id = GITHUB_APP_INSTALLATION_ID
        if not installation_id:
            # If no specific installation ID provided, get the first installation
            cmd = [
                "curl", "-s",
                "-H", f"Authorization: Bearer {jwt_token}",
                "-H", "Accept: application/vnd.github+json",
                "-H", "X-GitHub-Api-Version: 2022-11-28",
                "https://api.github.com/app/installations"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Failed to get installations: {result.stderr}"
            
            installations = json.loads(result.stdout)
            if not installations:
                return False, "No installations found for this GitHub App"
            
            installation_id = installations[0]["id"]
        
        # Exchange JWT for an installation token
        cmd = [
            "curl", "-s",
            "-X", "POST",
            "-H", f"Authorization: Bearer {jwt_token}",
            "-H", "Accept: application/vnd.github+json",
            "-H", "X-GitHub-Api-Version: 2022-11-28",
            f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"Failed to get installation token: {result.stderr}"
        
        response = json.loads(result.stdout)
        if "token" not in response:
            return False, f"No token in response: {result.stdout}"
        
        return True, response["token"]
        
    except Exception as e:
        print(f"[ERROR] Failed to get installation token: {str(e)}", file=sys.stderr, flush=True)
        return False, f"Exception: {str(e)}"

# Utility function to run Git commands
def run_git_command(command: str, cwd: Optional[str] = None) -> Tuple[bool, str]:
    """
    Execute a git command and return its success status and output.
    
    Args:
        command: The git command to run (without the 'git ' prefix)
        cwd: Optional working directory to run the command in
    
    Returns:
        Tuple of (success, output) where success is a boolean and output is the command output
    """
    try:
        # Redact any potential credentials in the command for logging
        log_command = command
        if GITHUB_PAT and GITHUB_PAT in command:
            log_command = command.replace(GITHUB_PAT, "***PAT***")
        
        print(f"[DEBUG] Running git command: git {log_command}", file=sys.stderr, flush=True)
        
        # Set environment with GitHub PAT if available
        env = os.environ.copy()
        
        # If it's a GitHub operation that might need authentication
        if any(x in command.lower() for x in ['clone', 'push', 'pull', 'fetch']):
            if GITHUB_PAT:
                # Use Personal Access Token
                env['GIT_ASKPASS'] = 'echo'
                env['GIT_TERMINAL_PROMPT'] = '0'
            elif GITHUB_APP_ID and (GITHUB_APP_PRIVATE_KEY or GITHUB_APP_PRIVATE_KEY_PATH):
                # Use GitHub App authentication
                success, token = get_installation_token()
                if success:
                    # Extract the Git URL from the command if it's a clone operation
                    if 'clone' in command.lower():
                        # Add the token to the URL
                        parts = command.split()
                        for i, part in enumerate(parts):
                            if part.startswith('https://github.com'):
                                # Replace https://github.com with https://x-access-token:TOKEN@github.com
                                parts[i] = part.replace('https://github.com', f'https://x-access-token:{token}@github.com')
                                command = ' '.join(parts)
                                break
                    else:
                        # For other operations, set the credential helper
                        subprocess.run(
                            f'git config credential.helper "!f() {{ echo username=x-access-token; echo password={token}; }}; f"',
                            shell=True,
                            capture_output=True,
                            text=True,
                            cwd=cwd
                        )
        
        result = subprocess.run(
            f"git {command}",
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env
        )
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            error_message = result.stderr.strip()
            # Redact any potential credentials in error messages
            if GITHUB_PAT and GITHUB_PAT in error_message:
                error_message = error_message.replace(GITHUB_PAT, "***PAT***")
            print(f"[ERROR] Git command failed: {error_message}", file=sys.stderr, flush=True)
            return False, f"Error: {error_message}"
    except Exception as e:
        print(f"[ERROR] Exception running git command: {str(e)}", file=sys.stderr, flush=True)
        return False, f"Exception: {str(e)}"

# GitHub-specific utility function to transform URLs to include auth
def transform_github_url(url: str) -> str:
    """
    Transform a GitHub URL to include the authentication if available.
    
    Args:
        url: The GitHub URL to transform
    
    Returns:
        The transformed URL with authentication if applicable
    """
    if "github.com" not in url:
        return url
    
    # For HTTPS URLs, insert the authentication
    if url.startswith("https://github.com"):
        if GITHUB_PAT:
            # Use Personal Access Token
            return url.replace("https://", f"https://{GITHUB_PAT}:x-oauth-basic@")
        elif GITHUB_APP_ID and (GITHUB_APP_PRIVATE_KEY or GITHUB_APP_PRIVATE_KEY_PATH):
            # Use GitHub App authentication
            success, token = get_installation_token()
            if success:
                return url.replace("https://", f"https://x-access-token:{token}@")
    
    return url

# Helper function to clone with authentication
def clone_with_auth(repo_url: str, target_dir: Optional[str] = None, options: str = "") -> Tuple[bool, str]:
    """
    Clone a repository with GitHub authentication if applicable.
    
    Args:
        repo_url: URL of the repository to clone
        target_dir: Optional directory to clone into
        options: Additional options for git clone
    
    Returns:
        Tuple of (success, output)
    """
    # Transform URL for GitHub repositories if authentication is available
    auth_url = transform_github_url(repo_url)
    
    cmd = f"clone {options} {auth_url}"
    if target_dir:
        cmd += f" {target_dir}"
    
    return run_git_command(cmd)

# Git tool functions
# These will be imported and registered as tools in server.py

def git_clone(repo_url: str, target_dir: Optional[str] = None, options: str = "") -> str:
    """
    Clone a Git repository.
    
    Args:
        repo_url: URL of the repository to clone
        target_dir: Optional directory to clone into
        options: Additional options for git clone
    
    Returns:
        Result of the clone operation
    """
    success, output = clone_with_auth(repo_url, target_dir, options)
    if success:
        return f"Successfully cloned {repo_url}" + (f" to {target_dir}" if target_dir else "")
    return output

def git_init(directory: str = ".") -> str:
    """
    Initialize a new Git repository.
    
    Args:
        directory: Directory to initialize
    
    Returns:
        Result of the init operation
    """
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception as e:
            return f"Error creating directory: {str(e)}"
            
    success, output = run_git_command(f"init", cwd=directory)
    if success:
        return f"Initialized empty Git repository in {os.path.abspath(directory)}"
    return output

def git_add(paths: Union[str, List[str]], options: str = "") -> str:
    """
    Add file(s) to the Git staging area.
    
    Args:
        paths: Path or list of paths to add
        options: Additional options for git add
    
    Returns:
        Result of the add operation
    """
    if isinstance(paths, list):
        # Escape spaces in filenames
        path_list = [f'"{p}"' if " " in p else p for p in paths]
        path_str = " ".join(path_list)
    else:
        path_str = f'"{paths}"' if " " in paths else paths
        
    success, output = run_git_command(f"add {options} {path_str}")
    if success:
        return f"Added {path_str} to staging area" if output == "" else output
    return output

def git_commit(message: str, options: str = "") -> str:
    """
    Commit changes to the Git repository.
    
    Args:
        message: Commit message
        options: Additional options for git commit
    
    Returns:
        Result of the commit operation
    """
    # Escape quotes in the message
    escaped_message = message.replace('"', '\\"')
    success, output = run_git_command(f'commit {options} -m "{escaped_message}"')
    if success:
        return output
    return output

def git_status(options: str = "") -> str:
    """
    Show the working tree status.
    
    Args:
        options: Additional options for git status
    
    Returns:
        Repository status information
    """
    success, output = run_git_command(f"status {options}")
    if success:
        return output
    return output

def git_push(remote: str = "origin", branch: str = "", options: str = "") -> str:
    """
    Push changes to a remote repository.
    
    Args:
        remote: Remote repository name
        branch: Branch to push
        options: Additional options for git push
    
    Returns:
        Result of the push operation
    """
    branch_str = f" {branch}" if branch else ""
    success, output = run_git_command(f"push {options} {remote}{branch_str}")
    if success:
        return output
    return output

def git_pull(remote: str = "origin", branch: str = "", options: str = "") -> str:
    """
    Pull changes from a remote repository.
    
    Args:
        remote: Remote repository name
        branch: Branch to pull
        options: Additional options for git pull
    
    Returns:
        Result of the pull operation
    """
    branch_str = f" {branch}" if branch else ""
    success, output = run_git_command(f"pull {options} {remote}{branch_str}")
    if success:
        return output
    return output

def git_log(options: str = "--oneline -n 10") -> str:
    """
    Show commit logs.
    
    Args:
        options: Options for git log
    
    Returns:
        Commit history information
    """
    success, output = run_git_command(f"log {options}")
    if success:
        return output
    return output

def git_checkout(revision: str, options: str = "") -> str:
    """
    Switch branches or restore working tree files.
    
    Args:
        revision: Branch, tag, or commit to checkout
        options: Additional options for git checkout
    
    Returns:
        Result of the checkout operation
    """
    success, output = run_git_command(f"checkout {options} {revision}")
    if success:
        return output or f"Switched to {revision}"
    return output

def git_branch(options: str = "", branch_name: Optional[str] = None) -> str:
    """
    List, create, or delete branches.
    
    Args:
        options: Options for git branch
        branch_name: Optional name of the branch to create
    
    Returns:
        Branch information or result of the branch operation
    """
    cmd = f"branch {options}"
    if branch_name:
        cmd += f" {branch_name}"
        
    success, output = run_git_command(cmd)
    if success:
        return output or f"Branch operation completed successfully"
    return output

def git_merge(branch: str, options: str = "") -> str:
    """
    Join two or more development histories together.
    
    Args:
        branch: Branch to merge
        options: Additional options for git merge
    
    Returns:
        Result of the merge operation
    """
    success, output = run_git_command(f"merge {options} {branch}")
    if success:
        return output
    return output

def git_show(object: str = "HEAD", options: str = "") -> str:
    """
    Show various types of Git objects.
    
    Args:
        object: Object to show (commit, tag, etc.)
        options: Additional options for git show
    
    Returns:
        Information about the specified object
    """
    success, output = run_git_command(f"show {options} {object}")
    if success:
        return output
    return output

def git_diff(options: str = "", path: Optional[str] = None) -> str:
    """
    Show changes between commits, commit and working tree, etc.
    
    Args:
        options: Options for git diff
        path: Optional path to restrict the diff to
    
    Returns:
        Diff information
    """
    cmd = f"diff {options}"
    if path:
        cmd += f" -- {path}"
        
    success, output = run_git_command(cmd)
    if success:
        return output
    return output

def git_remote(command: str = "show", name: Optional[str] = None, options: str = "") -> str:
    """
    Manage remote repositories.
    
    Args:
        command: Remote command (show, add, remove, etc.)
        name: Optional remote name
        options: Additional options for git remote
    
    Returns:
        Remote information or result of the remote operation
    """
    cmd = f"remote {command} {options}"
    if name:
        cmd += f" {name}"
        
    success, output = run_git_command(cmd)
    if success:
        return output
    return output

def git_rev_parse(rev: str, options: str = "") -> str:
    """
    Pick out and massage parameters for low-level Git commands.
    
    Args:
        rev: Revision to parse
        options: Additional options for git rev-parse
    
    Returns:
        Parsed revision information
    """
    success, output = run_git_command(f"rev-parse {options} {rev}")
    if success:
        return output
    return output

def git_ls_files(options: str = "") -> List[str]:
    """
    Show information about files in the index and the working tree.
    
    Args:
        options: Options for git ls-files
    
    Returns:
        List of files in the repository
    """
    success, output = run_git_command(f"ls-files {options}")
    if success:
        if not output:
            return []
        return output.split("\n")
    return [output]

def git_describe(options: str = "--tags") -> str:
    """
    Give an object a human-readable name based on available ref.
    
    Args:
        options: Options for git describe
    
    Returns:
        Description of the current commit
    """
    success, output = run_git_command(f"describe {options}")
    if success:
        return output
    return output

def git_rebase(branch: str, options: str = "") -> str:
    """
    Reapply commits on top of another base tip.
    
    Args:
        branch: Branch to rebase onto
        options: Additional options for git rebase
    
    Returns:
        Result of the rebase operation
    """
    success, output = run_git_command(f"rebase {options} {branch}")
    if success:
        return output
    return output

def git_stash(command: str = "push", options: str = "") -> str:
    """
    Stash the changes in a dirty working directory away.
    
    Args:
        command: Stash command (push, pop, apply, list, etc.)
        options: Additional options for git stash
    
    Returns:
        Result of the stash operation
    """
    success, output = run_git_command(f"stash {command} {options}")
    if success:
        return output
    return output

def git_reset(options: str = "", paths: Optional[Union[str, List[str]]] = None) -> str:
    """
    Reset current HEAD to the specified state.
    
    Args:
        options: Options for git reset
        paths: Optional path(s) to reset
    
    Returns:
        Result of the reset operation
    """
    cmd = f"reset {options}"
    
    if paths:
        if isinstance(paths, list):
            path_list = [f'"{p}"' if " " in p else p for p in paths]
            path_str = " ".join(path_list)
        else:
            path_str = f'"{paths}"' if " " in paths else paths
        cmd += f" -- {path_str}"
        
    success, output = run_git_command(cmd)
    if success:
        return output or "Reset completed successfully"
    return output

def git_clean(options: str = "-n") -> str:
    """
    Remove untracked files from the working tree.
    
    Args:
        options: Options for git clean (default is dry run)
    
    Returns:
        Result of the clean operation
    """
    success, output = run_git_command(f"clean {options}")
    if success:
        return output
    return output

def git_tag(tag_name: Optional[str] = None, options: str = "") -> Union[str, List[str]]:
    """
    Create, list, delete or verify a tag object.
    
    Args:
        tag_name: Optional name of the tag to create or delete
        options: Options for git tag
    
    Returns:
        Tag information or result of the tag operation
    """
    cmd = f"tag {options}"
    if tag_name:
        cmd += f" {tag_name}"
        
    success, output = run_git_command(cmd)
    if success:
        if not tag_name and output:  # List of tags
            return output.split("\n")
        return output or f"Tag operation completed successfully"
    return output

def git_config(name: Optional[str] = None, value: Optional[str] = None, options: str = "") -> str:
    """
    Get or set repository or global options.
    
    Args:
        name: Config variable name
        value: Optional value to set
        options: Additional options for git config
    
    Returns:
        Config information or result of the config operation
    """
    cmd = f"config {options}"
    
    if name:
        cmd += f" {name}"
        if value is not None:
            escaped_value = value.replace('"', '\\"')
            cmd += f' "{escaped_value}"'
            
    success, output = run_git_command(cmd)
    if success:
        return output or f"Config operation completed successfully"
    return output

def git_fetch(remote: str = "origin", options: str = "") -> str:
    """
    Download objects and refs from another repository.
    
    Args:
        remote: Remote repository name
        options: Additional options for git fetch
    
    Returns:
        Result of the fetch operation
    """
    success, output = run_git_command(f"fetch {options} {remote}")
    if success:
        return output or f"Fetched from {remote}"
    return output

def git_blame(file_path: str, options: str = "") -> str:
    """
    Show what revision and author last modified each line of a file.
    
    Args:
        file_path: Path to the file to blame
        options: Additional options for git blame
    
    Returns:
        Blame information
    """
    escaped_path = f'"{file_path}"' if " " in file_path else file_path
    success, output = run_git_command(f"blame {options} {escaped_path}")
    if success:
        return output
    return output

def git_grep(pattern: str, options: str = "") -> str:
    """
    Print lines matching a pattern in tracked files.
    
    Args:
        pattern: Pattern to search for
        options: Additional options for git grep
    
    Returns:
        Grep results
    """
    escaped_pattern = pattern.replace('"', '\\"')
    success, output = run_git_command(f'grep {options} "{escaped_pattern}"')
    if success:
        return output
    return output

def git_context(options: str = "--all") -> Dict[str, Any]:
    """
    Get comprehensive context about the current Git repository.
    
    Args:
        options: Additional options
    
    Returns:
        Dictionary with repository context information
    """
    result = {}
    
    # Check if we're in a git repository
    success, is_git_repo = run_git_command("rev-parse --is-inside-work-tree")
    if not success or is_git_repo != "true":
        return {"error": "Not a git repository"}
    
    # Get current branch
    success, branch = run_git_command("rev-parse --abbrev-ref HEAD")
    if success:
        result["current_branch"] = branch
    
    # Get repository root
    success, root = run_git_command("rev-parse --show-toplevel")
    if success:
        result["repository_root"] = root
    
    # Get status information
    success, status = run_git_command("status --porcelain")
    if success:
        result["is_clean"] = status == ""
        if status:
            result["status_summary"] = status
    
    # Get HEAD commit
    success, head_commit = run_git_command("rev-parse HEAD")
    if success:
        result["head_commit"] = head_commit
    
    # Get remote information
    success, remotes = run_git_command("remote -v")
    if success and remotes:
        remote_info = {}
        for line in remotes.split("\n"):
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                name, url = parts[0], parts[1]
                remote_info[name] = url
        result["remotes"] = remote_info
    
    # Get recent commits
    success, commits = run_git_command("log -n 5 --oneline")
    if success and commits:
        result["recent_commits"] = commits.split("\n")
    
    # Get branch list
    success, branches = run_git_command("branch")
    if success and branches:
        branch_list = [b.strip() for b in branches.split("\n") if b.strip()]
        result["branches"] = branch_list
    
    # Get tags
    success, tags = run_git_command("tag")
    if success and tags:
        result["tags"] = tags.split("\n")
    
    return result

def git_head(options: str = "") -> str:
    """
    Show the current HEAD commit information.
    
    Args:
        options: Additional options for git show HEAD
    
    Returns:
        HEAD commit information
    """
    success, output = run_git_command(f"show HEAD {options}")
    if success:
        return output
    return output

def git_version() -> str:
    """
    Get the Git version.
    
    Returns:
        Git version information
    """
    success, output = run_git_command("--version")
    if success:
        return output
    return output

def git_validate() -> Dict[str, Any]:
    """
    Validate the Git repository for common issues.
    
    Returns:
        Dictionary with validation results
    """
    result = {
        "valid": True,
        "issues": [],
        "warnings": [],
        "info": []
    }
    
    # Check if we're in a git repository
    success, is_git_repo = run_git_command("rev-parse --is-inside-work-tree")
    if not success or is_git_repo != "true":
        result["valid"] = False
        result["issues"].append("Not a git repository")
        return result
    
    # Check for uncommitted changes
    success, status = run_git_command("status --porcelain")
    if success and status:
        result["warnings"].append("Uncommitted changes present")
    
    # Check for untracked files
    success, untracked = run_git_command("ls-files --others --exclude-standard")
    if success and untracked:
        untracked_count = len(untracked.split("\n"))
        result["warnings"].append(f"{untracked_count} untracked files present")
    
    # Check for unpushed commits
    success, unpushed = run_git_command("log @{u}.. --oneline 2>/dev/null || echo ''")
    if success and unpushed:
        unpushed_count = len(unpushed.split("\n"))
        if unpushed_count > 0:
            result["warnings"].append(f"{unpushed_count} unpushed commits")
    
    # Check for stashed changes
    success, stashed = run_git_command("stash list")
    if success and stashed:
        stash_count = len(stashed.split("\n"))
        result["info"].append(f"{stash_count} stashed changes")
    
    # Check for .gitignore
    success, gitignore = run_git_command("ls-files .gitignore")
    if success and not gitignore:
        result["warnings"].append("No .gitignore file found")
    
    # Check for large files
    success, large_files = run_git_command("ls-files | xargs -I{} du -h {} | sort -hr | head -n 5")
    if success and large_files:
        result["info"].append("Largest files in repository:")
        result["large_files"] = large_files.split("\n")
    
    return result

def git_repo_info() -> Dict[str, Any]:
    """
    Get comprehensive information about the Git repository.
    
    Returns:
        Dictionary with repository information
    """
    result = {}
    
    # Check if we're in a git repository
    success, is_git_repo = run_git_command("rev-parse --is-inside-work-tree")
    if not success or is_git_repo != "true":
        return {"error": "Not a git repository"}
    
    # Get repository path
    success, repo_path = run_git_command("rev-parse --show-toplevel")
    if success:
        result["repository_path"] = repo_path
    
    # Get current branch
    success, branch = run_git_command("rev-parse --abbrev-ref HEAD")
    if success:
        result["current_branch"] = branch
    
    # Get remote URL
    success, remote_url = run_git_command("config --get remote.origin.url")
    if success:
        result["remote_url"] = remote_url
    
    # Get commit count
    success, commit_count = run_git_command("rev-list --count HEAD")
    if success:
        result["commit_count"] = int(commit_count)
    
    # Get first commit
    success, first_commit = run_git_command("rev-list --max-parents=0 HEAD")
    if success:
        result["first_commit"] = first_commit
    
    # Get contributor count and list
    success, contributors = run_git_command("shortlog -sne HEAD")
    if success:
        contributor_list = []
        total_contributors = 0
        for line in contributors.split("\n"):
            if line.strip():
                total_contributors += 1
                parts = line.strip().split("\t", 1)
                if len(parts) > 1:
                    count, author = parts
                    contributor_list.append({"name": author, "commits": int(count)})
        
        result["contributor_count"] = total_contributors
        result["contributors"] = contributor_list
    
    # Get file count
    success, files = run_git_command("ls-files")
    if success:
        file_list = files.split("\n") if files else []
        result["file_count"] = len(file_list)
    
    # Get repository size (approximate)
    success, repo_size = run_git_command("count-objects -v")
    if success:
        size_info = {}
        for line in repo_size.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                size_info[key.strip()] = value.strip()
        
        if "size" in size_info:
            result["size_kb"] = int(size_info["size"])
    
    # Get tags
    success, tags = run_git_command("tag")
    if success:
        tag_list = tags.split("\n") if tags else []
        result["tag_count"] = len(tag_list)
        result["tags"] = tag_list
    
    # Get branches
    success, branches = run_git_command("branch")
    if success:
        branch_list = [b.strip("* ") for b in branches.split("\n") if b.strip()]
        result["branch_count"] = len(branch_list)
        result["branches"] = branch_list
    
    return result

def git_summarize_log(count: int = 10, options: str = "") -> Dict[str, Any]:
    """
    Summarize the git log with useful statistics.
    
    Args:
        count: Number of commits to analyze
        options: Additional options for git log
    
    Returns:
        Dictionary with log summary information
    """
    result = {
        "commits": [],
        "stats": {
            "total_commits": 0,
            "authors": {},
            "date_distribution": {},
            "file_changes": {}
        }
    }
    
    # Get commits with stats
    success, log_output = run_git_command(f"log -n {count} --stat --date=short {options}")
    if not success:
        return {"error": log_output}
    
    commits = []
    current_commit = None
    
    for line in log_output.split("\n"):
        if line.startswith("commit "):
            if current_commit:
                commits.append(current_commit)
            
            commit_hash = line.split(" ")[1]
            current_commit = {
                "hash": commit_hash,
                "author": "",
                "date": "",
                "message": "",
                "changes": {
                    "files_changed": 0,
                    "insertions": 0,
                    "deletions": 0
                }
            }
        elif line.startswith("Author: "):
            if current_commit:
                current_commit["author"] = line[8:].strip()
        elif line.startswith("Date: "):
            if current_commit:
                current_commit["date"] = line[6:].strip()
        elif line.strip() and current_commit and not current_commit["message"] and not line.startswith(" "):
            current_commit["message"] = line.strip()
        elif " | " in line and "+" in line and "-" in line:
            if current_commit:
                current_commit["changes"]["files_changed"] += 1
                
                # Try to parse insertions and deletions
                parts = line.split("|")[1].strip()
                plus_idx = parts.find("+")
                minus_idx = parts.find("-")
                
                if plus_idx != -1:
                    ins_str = parts[plus_idx+1:].split()[0]
                    try:
                        current_commit["changes"]["insertions"] += int(ins_str)
                    except ValueError:
                        pass
                
                if minus_idx != -1:
                    del_str = parts[minus_idx+1:].split()[0]
                    try:
                        current_commit["changes"]["deletions"] += int(del_str)
                    except ValueError:
                        pass
    
    # Add the last commit
    if current_commit:
        commits.append(current_commit)
    
    # Add commits to result
    result["commits"] = commits
    result["stats"]["total_commits"] = len(commits)
    
    # Calculate statistics
    for commit in commits:
        # Author stats
        author = commit["author"]
        if author not in result["stats"]["authors"]:
            result["stats"]["authors"][author] = {
                "commit_count": 0,
                "insertions": 0,
                "deletions": 0
            }
        result["stats"]["authors"][author]["commit_count"] += 1
        result["stats"]["authors"][author]["insertions"] += commit["changes"]["insertions"]
        result["stats"]["authors"][author]["deletions"] += commit["changes"]["deletions"]
        
        # Date stats
        date = commit["date"]
        if date:
            if date not in result["stats"]["date_distribution"]:
                result["stats"]["date_distribution"][date] = 0
            result["stats"]["date_distribution"][date] += 1
    
    return result

def git_suggest_commit(options: str = "") -> Dict[str, Any]:
    """
    Analyze changes and suggest a commit message.
    
    Args:
        options: Additional options for git diff
    
    Returns:
        Dictionary with suggestion information
    """
    result = {
        "changes": {
            "files_changed": 0,
            "insertions": 0,
            "deletions": 0,
            "file_details": []
        },
        "suggested_message": "",
        "suggested_type": "",
        "suggested_scope": ""
    }
    
    # Get diff stats
    success, diff_stat = run_git_command(f"diff --staged --stat {options}")
    if not success:
        return {"error": diff_stat}
    
    # Parse diff stats
    lines = diff_stat.split("\n")
    for line in lines:
        if " | " in line:
            result["changes"]["files_changed"] += 1
            file_path = line.split(" | ")[0].strip()
            result["changes"]["file_details"].append(file_path)
        elif " insertions" in line or " deletions" in line:
            if "changed" in line:
                try:
                    result["changes"]["files_changed"] = int(line.split(" ")[0])
                except ValueError:
                    pass
            
            if "insertion" in line:
                try:
                    result["changes"]["insertions"] = int(line.split(" ")[3])
                except (ValueError, IndexError):
                    pass
            
            if "deletion" in line:
                try:
                    index = 5 if "insertions" in line else 3
                    result["changes"]["deletions"] = int(line.split(" ")[index])
                except (ValueError, IndexError):
                    pass
    
    # Analyze changes to suggest commit type and message
    if result["changes"]["files_changed"] == 0:
        result["suggested_message"] = "No changes to commit"
        return result
    
    # Determine file types changed
    file_types = set()
    has_tests = False
    has_docs = False
    has_config = False
    has_feature = False
    has_fix = False
    
    for file_path in result["changes"]["file_details"]:
        if file_path.endswith((".md", ".txt", ".rst")):
            has_docs = True
        elif file_path.endswith((".test.js", ".spec.js", "test_", "_test", "spec_", "_spec")):
            has_tests = True
        elif file_path.endswith((".json", ".yml", ".yaml", ".toml", ".ini", ".config")):
            has_config = True
        
        ext = file_path.split(".")[-1] if "." in file_path else ""
        if ext:
            file_types.add(ext)
    
    # Get diff to analyze content changes
    success, diff_content = run_git_command(f"diff --staged {options}")
    if success:
        lower_diff = diff_content.lower()
        if "fix" in lower_diff or "bug" in lower_diff or "issue" in lower_diff:
            has_fix = True
        if "feature" in lower_diff or "add" in lower_diff or "new" in lower_diff:
            has_feature = True
    
    # Determine commit type
    if has_docs and result["changes"]["files_changed"] == len([f for f in result["changes"]["file_details"] if f.endswith((".md", ".txt", ".rst"))]):
        result["suggested_type"] = "docs"
    elif has_tests and result["changes"]["files_changed"] == len([f for f in result["changes"]["file_details"] if any(test_pattern in f for test_pattern in (".test.", ".spec.", "test_", "_test", "spec_", "_spec"))]):
        result["suggested_type"] = "test"
    elif has_config and result["changes"]["files_changed"] == len([f for f in result["changes"]["file_details"] if f.endswith((".json", ".yml", ".yaml", ".toml", ".ini", ".config"))]):
        result["suggested_type"] = "chore"
    elif has_fix:
        result["suggested_type"] = "fix"
    elif has_feature:
        result["suggested_type"] = "feat"
    else:
        result["suggested_type"] = "chore"
    
    # Determine scope based on directories changed
    directories = set()
    for file_path in result["changes"]["file_details"]:
        if "/" in file_path:
            directories.add(file_path.split("/")[0])
    
    if len(directories) == 1:
        result["suggested_scope"] = next(iter(directories))
    
    # Suggest commit message
    if result["suggested_type"] == "docs":
        result["suggested_message"] = f"docs{': ' + result['suggested_scope'] if result['suggested_scope'] else ''}: update documentation"
    elif result["suggested_type"] == "test":
        result["suggested_message"] = f"test{': ' + result['suggested_scope'] if result['suggested_scope'] else ''}: add/update tests"
    elif result["suggested_type"] == "fix":
        result["suggested_message"] = f"fix{': ' + result['suggested_scope'] if result['suggested_scope'] else ''}: fix issue"
    elif result["suggested_type"] == "feat":
        result["suggested_message"] = f"feat{': ' + result['suggested_scope'] if result['suggested_scope'] else ''}: add new feature"
    else:
        result["suggested_message"] = f"chore{': ' + result['suggested_scope'] if result['suggested_scope'] else ''}: update code"
    
    return result

def git_audit_history(options: str = "") -> Dict[str, Any]:
    """
    Audit repository history for potential issues.
    
    Args:
        options: Additional options
    
    Returns:
        Dictionary with audit results
    """
    result = {
        "issues": [],
        "warnings": [],
        "info": [],
        "stats": {}
    }
    
    # Check for large files in history
    success, large_files = run_git_command("rev-list --objects --all | grep -f <(git verify-pack -v .git/objects/pack/*.idx | sort -k 3 -n | tail -10 | awk '{print $1}') | sort -k2")
    if success and large_files:
        result["warnings"].append("Large files found in repository history")
        result["stats"]["large_files"] = large_files.split("\n")
    
    # Check for merge conflicts markers accidentally committed
    success, conflict_markers = run_git_command("log -p --all -G'^[<=>]{7}' --pretty=format:'%h: %s'")
    if success and conflict_markers:
        result["issues"].append("Merge conflict markers found in repository history")
        result["stats"]["conflict_markers"] = conflict_markers.split("\n")
    
    # Check for binary files
    success, binary_files = run_git_command("git ls-files | grep -v -E '\\.(md|txt|json|yml|yaml|js|ts|css|html|svg|py|rb|sh|java|c|cpp|h|go|rs|php)$'")
    if success and binary_files:
        binary_list = binary_files.split("\n")
        if binary_list:
            result["info"].append(f"Found {len(binary_list)} potential binary files in repository")
            result["stats"]["binary_files"] = binary_list
    
    # Check for potentially sensitive data
    sensitive_patterns = [
        "password", "secret", "token", "key", "credential", "auth", 
        "api_key", "apikey", "api key", "private_key", "privatekey", "private key"
    ]
    
    for pattern in sensitive_patterns:
        success, sensitive_matches = run_git_command(f"log -p --all -i -G'{pattern}' --pretty=format:'%h: %s'")
        if success and sensitive_matches:
            result["warnings"].append(f"Potential sensitive data ({pattern}) found in repository history")
    
    # Check commit messages quality
    success, short_messages = run_git_command("log --pretty=format:'%h: %s' | awk 'length($0) < 20 {print}'")
    if success and short_messages:
        short_list = short_messages.split("\n")
        if short_list:
            result["warnings"].append(f"Found {len(short_list)} commits with very short messages")
    
    # Check for orphaned commits
    success, orphaned = run_git_command("log --all --oneline --graph --decorate | grep -A1 '\\*.*' | grep -B1 '^\\* ' | grep -v '^\\* '")
    if success and orphaned:
        result["warnings"].append("Potential orphaned commits found")
    
    # Check for empty commits
    success, empty_commits = run_git_command("git log --pretty=format:'%h: %s' --all --diff-filter=A")
    if success and empty_commits:
        result["info"].append("Found empty commits (with no file changes)")
    
    return result
