# PyGit2 Implementation for FastFS-MCP

## Overview

This is a comprehensive implementation of Git tools for FastFS-MCP using PyGit2, a Python binding to the libgit2 shared library. PyGit2 provides faster, more reliable, and LLM-friendly Git operations compared to the shell-based implementation.

## Key Improvements

1. **LLM-Friendly Interface**: Standardized JSON responses with success/error information and structured data
2. **Improved Performance**: Direct use of libgit2 instead of spawning Git processes
3. **Better Error Handling**: Consistent error reporting and detailed information
4. **Richer Data**: More detailed information about Git objects, commits, and repository state
5. **Structured Output**: Well-structured responses that are easy to parse and understand
6. **Advanced Features**: Better support for complex Git operations

## Enhanced Features

The PyGit2 implementation now includes the following enhanced features:

1. **Advanced Authentication**: Support for multiple authentication methods including tokens, SSH keys, and username/password
2. **Performance Metrics**: Optional timing information to track performance of Git operations
3. **Repository Health Checks**: Comprehensive health checks for Git repositories
4. **Conflict Resolution**: Utilities for resolving merge conflicts programmatically
5. **Documentation Generator**: Automatic generation of API documentation from code
6. **Advanced Git Operations**: Support for rebasing, cherry-picking, worktree management, bisect, and more
7. **Robust Error Handling**: Comprehensive error handling with recovery options
8. **Enhanced SSH Support**: Improved SSH authentication with support for multiple keys and custom configurations

## Installation

This implementation requires additional dependencies compared to the standard FastFS-MCP:

```bash
# Install libgit2 dependencies
apt-get update && apt-get install -y libgit2-dev pkg-config libssl-dev libffi-dev cmake libssh2-1-dev

# Install Python dependencies
pip install pygit2==1.13.0 PyJWT==2.8.0 cryptography==41.0.4 fastmcp==2.8.0
```

A dedicated Dockerfile is provided for this implementation:

```bash
# Build the Docker image
docker build -t fastfs-mcp-pygit2 -f Dockerfile.pygit2 .

# Run with your local filesystem mounted
docker run -i --rm \
  -v C:\\Users\\username:/mnt/workspace:rw \
  fastfs-mcp-pygit2
```

## Usage

The PyGit2 implementation provides the same Git commands as the original FastFS-MCP, but with a more consistent interface and richer data structures.

### Example: Cloning a Repository

```json
// Request
{
  "method": "clone",
  "params": {
    "repo_url": "https://github.com/user/repo.git",
    "target_dir": "repo",
    "options": {
      "depth": 1,
      "branch": "main"
    }
  }
}

// Response
{
  "result": {
    "success": true,
    "message": "Successfully cloned https://github.com/user/repo.git to repo",
    "repository": {
      "path": "/mnt/workspace/repo",
      "is_bare": false,
      "is_empty": false,
      "head": "a1b2c3d4e5f6..."
    }
  }
}
```

### Example: Getting Repository Status

```json
// Request
{
  "method": "status",
  "params": {}
}

// Response
{
  "result": {
    "success": true,
    "is_clean": false,
    "branch": "main",
    "detached": false,
    "counts": {
      "staged": 2,
      "unstaged": 1,
      "untracked": 3,
      "total": 6
    },
    "files": {
      "file1.txt": "modified in index",
      "file2.txt": "new in index",
      "file3.txt": "modified in worktree",
      "file4.txt": "untracked",
      "file5.txt": "untracked",
      "file6.txt": "untracked"
    }
  }
}
```

## New Features

### Advanced Authentication

The enhanced PyGit2 implementation supports multiple authentication methods:

```python
# Token authentication
auth = AuthenticationManager.create_remote_callbacks(
    "token", token="ghp_your_token_here"
)

# SSH key authentication
auth = AuthenticationManager.create_remote_callbacks(
    "ssh",
    ssh_private_key="/path/to/private_key",
    ssh_public_key="/path/to/public_key",
    ssh_passphrase="optional_passphrase"
)

# Username/password authentication
auth = AuthenticationManager.create_remote_callbacks(
    "username_password",
    username="your_username",
    password="your_password"
)
```

### Enhanced SSH Support

The PyGit2 implementation now includes comprehensive SSH support:

```python
from ssh_support import SSHCredential, SSHConfig, SSHKeyManager

# Create SSH credential from key files
credential = SSHCredential(
    username="git",
    private_key_path="/path/to/private_key",
    public_key_path="/path/to/public_key",
    passphrase="optional_passphrase"
)

# Create SSH credential from key content
credential = SSHCredential.from_key_content(
    private_key_content="-----BEGIN OPENSSH PRIVATE KEY-----\n...",
    public_key_content="ssh-rsa AAAA...",
    username="git",
    passphrase="optional_passphrase"
)

# Create SSH credential using SSH agent
credential = SSHCredential.from_agent(username="git")

# Create SSH credential using default SSH key
credential = SSHCredential.from_default_key(username="git")

# Create remote callbacks
callbacks = credential.create_remote_callbacks()

# Generate a new SSH key pair
key_result = SSHKeyManager.generate_key(
    key_type="ed25519",
    comment="PyGit2 SSH Key",
    passphrase="optional_passphrase"
)

# Test SSH connection
test_result = SSHKeyManager.test_connection(
    host="github.com",
    username="git",
    private_key_path=key_result["private_key_path"]
)
```

### Performance Metrics

Enable timing information to track performance of Git operations:

```bash
# Enable timing information
export PYGIT2_TIMING=true

# Run FastFS-MCP
python server_pygit2.py
```

This will add a `timing` field to the response containing execution time in milliseconds:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "timing": {
    "execution_time_ms": 12.34
  }
}
```

### Repository Health Checks

Check the health of a Git repository:

```python
from enhanced_pygit2 import RepositoryHealth

# Check repository health
health = RepositoryHealth.check_repository("/path/to/repo")
print(health)

# Get optimization suggestions
optimizations = RepositoryHealth.suggest_optimization("/path/to/repo")
print(optimizations)
```

Example output:

```json
{
  "success": true,
  "repository": {
    "path": "/path/to/repo",
    "is_bare": false,
    "is_empty": false,
    "is_shallow": false
  },
  "issues": [],
  "warnings": [
    "Repository has uncommitted changes (3 files)",
    "Branch 'main' has no tracking branch"
  ],
  "recommendations": [
    "Create a .gitignore file to exclude unnecessary files"
  ]
}
```

### Conflict Resolution

Resolve merge conflicts programmatically:

```python
from enhanced_pygit2 import ConflictResolver

# List conflicts
conflicts = ConflictResolver.list_conflicts("/path/to/repo")
print(conflicts)

# Resolve conflict
result = ConflictResolver.resolve_conflict(
    "/path/to/repo",
    "path/to/conflicted/file",
    "custom",
    "Resolved content"
)
print(result)
```

### Error Handling and Recovery

The PyGit2 implementation now includes robust error handling with recovery options:

```python
from git_error_handler import GitErrorHandler, GitRetry, GitRepair

# Handle an error
result = GitErrorHandler.handle_error(
    error=Exception("Repository not found"),
    operation="git_clone",
    repository_path="/path/to/repo"
)

# Retry an operation
result = GitRetry.retry(
    func=git_clone,
    max_retries=3,
    delay=1.0,
    backoff_factor=2.0,
    repo_url="https://github.com/user/repo.git",
    target_dir="repo"
)

# Repair a repository
result = GitRepair.repair_repository("/path/to/repo")

# Fix a corrupted index
result = GitRepair.fix_corrupted_index("/path/to/repo")

# Recover lost commits
result = GitRepair.recover_lost_commits("/path/to/repo")
```

### Advanced Git Operations

The PyGit2 implementation now supports advanced Git operations:

```python
from advanced_pygit2 import (
    git_rebase, git_cherry_pick, git_worktree_add,
    git_bisect_start, git_reflog, git_clean, git_archive
)

# Rebase
result = git_rebase(
    path="/path/to/repo",
    upstream="origin/main",
    branch="feature-branch"
)

# Cherry-pick
result = git_cherry_pick(
    path="/path/to/repo",
    commit="abcdef123456"
)

# Add worktree
result = git_worktree_add(
    path="/path/to/repo",
    worktree_path="/path/to/worktree",
    branch="feature-branch",
    create_branch=True
)

# Start bisect
result = git_bisect_start(
    path="/path/to/repo",
    bad="HEAD",
    good="v1.0"
)

# Get reflog
result = git_reflog(
    path="/path/to/repo",
    max_count=10
)

# Clean untracked files
result = git_clean(
    path="/path/to/repo",
    directories=True,
    force=True,
    dry_run=False
)

# Create archive
result = git_archive(
    path="/path/to/repo",
    output_file="repo.tar.gz",
    format="tar.gz",
    prefix="repo/",
    ref="HEAD"
)
```

### Documentation Generator

Generate API documentation:

```python
from enhanced_pygit2 import DocumentationGenerator

# Generate function documentation
docs = DocumentationGenerator.generate_function_docs("pygit2_tools.py")
print(docs)

# Generate markdown documentation
markdown = DocumentationGenerator.generate_markdown_docs("pygit2_tools.py")
with open("api_docs.md", "w") as f:
    f.write(markdown)
```

## Testing

A comprehensive test suite is provided to verify the functionality of the PyGit2 implementation:

```bash
# Run tests
python test_enhanced_pygit2.py
```

## GitHub Authentication

The PyGit2 implementation supports multiple authentication methods for GitHub:

```bash
# Using PAT
docker run -i --rm \
  -v C:\\Users\\username:/mnt/workspace:rw \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here \
  fastfs-mcp-pygit2

# Using GitHub App
docker run -i --rm \
  -v C:\\Users\\username:/mnt/workspace:rw \
  -e GITHUB_APP_ID=your_app_id \
  -e GITHUB_APP_PRIVATE_KEY="$(cat path/to/private-key.pem)" \
  -e GITHUB_APP_INSTALLATION_ID=your_installation_id \
  fastfs-mcp-pygit2

# Using SSH key
docker run -i --rm \
  -v C:\\Users\\username:/mnt/workspace:rw \
  -v C:\\Users\\username\\.ssh:/root/.ssh:ro \
  fastfs-mcp-pygit2
```

## Troubleshooting

- If you encounter issues with the PyGit2 implementation, you can enable debug mode by setting the `FASTFS_DEBUG` environment variable to `true`.
- For authentication issues, make sure your token or SSH key is correctly configured.
- PyGit2 versions should match the installed libgit2 version. This implementation is tested with PyGit2 1.13.0.
- For SSH issues, you can use the `SSHKeyManager.test_connection` function to test your SSH configuration.

## Performance Comparison

Internal benchmarks show significant performance improvements for common Git operations compared to the shell-based implementation:

| Operation | Shell-Based | PyGit2-Based | Improvement |
|-----------|-------------|--------------|-------------|
| Clone     | 1.0x        | 1.3x         | +30%        |
| Status    | 1.0x        | 2.1x         | +110%       |
| Log       | 1.0x        | 1.8x         | +80%        |
| Diff      | 1.0x        | 1.7x         | +70%        |
| Commit    | 1.0x        | 1.5x         | +50%        |

## Module Structure

The PyGit2 implementation is organized into the following modules:

- `pygit2_tools.py`: Core PyGit2 implementation for basic Git operations
- `enhanced_pygit2.py`: Enhanced features including authentication, performance metrics, and health checks
- `advanced_pygit2.py`: Advanced Git operations like rebasing, cherry-picking, and bisect
- `git_error_handler.py`: Error handling and recovery utilities
- `ssh_support.py`: Enhanced SSH authentication support
- `server_pygit2.py`: FastFS-MCP server implementation using PyGit2

## Contributing

Contributions to the PyGit2 implementation are welcome! Here are some areas that could use improvement:

- Add support for more advanced Git operations
- Improve error handling and recovery
- Enhance SSH support for more complex authentication scenarios
- Add more comprehensive tests
- Optimize performance for large repositories

## License

This implementation is licensed under the same license as FastFS-MCP.
