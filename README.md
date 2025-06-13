# FastFS-MCP with PyGit2

<img src="https://img.shields.io/badge/Version-2.8.0-blue" alt="Version" /> <img src="https://img.shields.io/badge/License-MIT-green" alt="License" /> <img src="https://img.shields.io/badge/Docker-Ready-informational" alt="Docker Ready" />

A high-speed MCP (Model Context Protocol) server for filesystem operations, Git integration, and interactive prompting capabilities, designed to work seamlessly with Claude and AI-native tooling.

## 🚀 Overview

FastFS-MCP enables AI assistants like Claude to interact with your local filesystem, manage Git repositories, and provide interactive experiences through a standardized JSON-based protocol. This repository implements a version with PyGit2 for improved Git operations, providing better performance, more structured responses, and enhanced error handling.

## ✨ Key Features

- **Ultra-fast filesystem operations**: Access, modify, and manage files with minimal latency
- **Complete Git integration with PyGit2**: Perform all standard Git operations and advanced repository analysis with native Git support
- **Interactive prompting**: Enable Claude to engage users through structured prompts and forms
- **GitHub authentication**: Securely authenticate with GitHub using personal access tokens or GitHub Apps
- **JSON protocol**: Communicate with Claude Desktop, VSCode, and other AI-native tools using a standard interface
- **SSH support**: Enhanced SSH credential management for Git operations
- **Error handling and recovery**: Robust error handling and repository repair tools

## 🗂️ Project Structure

```
fastfs-mcp/
├── Dockerfile           # Unified Docker build file for the project
├── build_fastfs_mcp.sh  # Script to build and run the Docker image
├── docs/                # Documentation files
├── fastfs_mcp/          # Main package
│   ├── __init__.py      # Package initialization
│   ├── git/             # Git operations module
│   │   ├── __init__.py  # Git module initialization
│   │   ├── advanced.py  # Advanced Git operations
│   │   ├── base.py      # Basic Git operations
│   │   ├── enhanced.py  # Enhanced Git features
│   │   ├── error_handler.py  # Error handling for Git operations
│   │   ├── integration.py    # PyGit2 integration for FastFS-MCP
│   │   └── ssh.py       # SSH support for Git operations
│   └── server.py        # FastFS-MCP server implementation
├── requirements.txt     # Python package dependencies
└── tests/               # Test suite
```

## 💻 Installation & Quick Start

### Docker Quick Start

```bash
# Build the Docker image
./build_fastfs_mcp.sh

# Run with your local filesystem mounted
docker run -i --rm \
  -v C:\\Users\\username:/mnt/workspace:rw \
  fastfs-mcp
```

> On Unix/macOS: replace with `-v $HOME:/mnt/workspace`

### With GitHub Authentication

#### Using Personal Access Token

```bash
docker run -i --rm \
  -v C:\\Users\\username:/mnt/workspace:rw \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here \
  fastfs-mcp
```

#### Using GitHub App (Option 1: Private Key as Environment Variable)

```bash
docker run -i --rm \
  -v C:\\Users\\username:/mnt/workspace:rw \
  -e GITHUB_APP_ID=your_app_id \
  -e GITHUB_APP_PRIVATE_KEY="$(cat path/to/private-key.pem)" \
  -e GITHUB_APP_INSTALLATION_ID=your_installation_id \
  fastfs-mcp
```

#### Using GitHub App (Option 2: Private Key from File in Workspace)

```bash
# First, copy your private key to the workspace
cp path/to/private-key.pem C:\\Users\\username\\github-app-key.pem

# Then run with the path to the private key
docker run -i --rm \
  -v C:\\Users\\username:/mnt/workspace:rw \
  -e GITHUB_APP_ID=your_app_id \
  -e GITHUB_APP_PRIVATE_KEY_PATH=/mnt/workspace/github-app-key.pem \
  -e GITHUB_APP_INSTALLATION_ID=your_installation_id \
  fastfs-mcp
```

## 🤖 Claude Desktop Configuration

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "C:\\Users\\username:/mnt/workspace:rw",
        "fastfs-mcp"
      ]
    }
  }
}
```

### With GitHub Authentication

#### Using Personal Access Token

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", 
        "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
        "-v", "C:\\Users\\username:/mnt/workspace:rw",
        "fastfs-mcp"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

## 🌿 Git Operations with PyGit2

The PyGit2 implementation provides enhanced Git operations with better performance, more structured responses, and improved error handling. It includes:

### Basic Git Operations

| Method | Description |
|--------|-------------|
| `clone` | Clone a Git repository |
| `init` | Initialize a new Git repository |
| `add` | Add file(s) to staging area |
| `commit` | Commit changes to repository |
| `status` | Show working tree status |
| `push` | Push changes to remote repository |
| `pull` | Pull changes from remote repository |
| `log` | Show commit logs |
| `checkout` | Switch branches or restore files |
| `branch` | List, create, or delete branches |
| `merge` | Join development histories together |
| `show` | Show Git objects |
| `diff` | Show changes between commits/working tree |
| `remote` | Manage remote repositories |
| `stash` | Stash changes in working directory |
| `tag` | Manage Git tags |
| `blame` | Show what revision and author last modified each line of a file |
| `git_grep` | Print lines matching a pattern in tracked files |

### Advanced Git Operations

| Method | Description |
|--------|-------------|
| `rebase` | Reapply commits on top of another base tip |
| `rebase_continue` | Continue a rebase operation after resolving conflicts |
| `rebase_abort` | Abort a rebase operation |
| `cherry_pick` | Apply changes from existing commits |
| `worktree_add` | Add a new working tree |
| `worktree_list` | List working trees |
| `worktree_remove` | Remove a working tree |
| `submodule_add` | Add a submodule |
| `submodule_update` | Update submodules |
| `submodule_list` | List submodules |

### Repository Analysis and Health

| Method | Description |
|--------|-------------|
| `context` | Get comprehensive repository context |
| `validate` | Validate the repository for common issues |
| `suggest_commit` | Analyze changes and suggest a commit message |
| `check_repository` | Perform comprehensive health check on repository |
| `suggest_optimization` | Suggest repository optimizations |
| `list_conflicts` | List all conflicts in the repository |

### Error Handling and Recovery

| Method | Description |
|--------|-------------|
| `repair_repository` | Attempt to repair a Git repository |
| `restore_backup` | Restore a backup of a Git repository |
| `fix_corrupted_index` | Fix a corrupted Git index |
| `fix_detached_head` | Fix a detached HEAD state by pointing it to a branch |
| `fix_missing_refs` | Fix missing references in a Git repository |
| `recover_lost_commits` | Recover lost commits using reflog |

### SSH Support

| Method | Description |
|--------|-------------|
| `generate_ssh_key` | Generate a new SSH key pair |
| `import_ssh_key` | Import SSH key pair |
| `verify_ssh_key` | Verify SSH key pair |
| `test_ssh_connection` | Test SSH connection |
| `configure_auth` | Configure authentication |

## 📝 Protocol Usage

FastFS-MCP uses a simple JSON-based protocol to communicate with Claude and other AI tools.

### Request Format

```json
{
  "method": "METHOD_NAME",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

### Response Format

```json
{
  "result": RESPONSE_DATA
}
```

### Examples

#### Basic Git Operation

```json
// Request
{
  "method": "status",
  "params": { "path": "/mnt/workspace/my-project" }
}

// Response
{
  "result": {
    "success": true,
    "branch": "main",
    "index": {
      "new": ["new_file.txt"],
      "modified": ["README.md"],
      "deleted": []
    },
    "working_tree": {
      "untracked": ["temp.log"],
      "modified": ["src/main.py"],
      "deleted": []
    },
    "is_clean": false
  }
}
```

#### Git Repository Context

```json
// Request
{
  "method": "context",
  "params": { "path": "/mnt/workspace/my-project" }
}

// Response
{
  "result": {
    "success": true,
    "repository": {
      "path": "/mnt/workspace/my-project",
      "is_bare": false,
      "is_empty": false,
      "is_shallow": false
    },
    "head": {
      "branch": "main",
      "is_detached": false,
      "commit": {
        "id": "a1b2c3d4e5f6...",
        "message": "Update README.md",
        "author": "John Doe <john@example.com>",
        "time": "2023-10-10T15:30:45Z"
      }
    },
    "branches": [
      {
        "name": "main",
        "is_head": true
      },
      {
        "name": "feature/new-api",
        "is_head": false
      }
    ],
    "remotes": [
      {
        "name": "origin",
        "url": "https://github.com/user/repo.git"
      }
    ],
    "status": {
      "is_clean": false,
      "has_conflicts": false
    },
    "recent_commits": [
      {
        "id": "a1b2c3d4e5f6...",
        "message": "Update README.md",
        "author": "John Doe",
        "time": "2023-10-10T15:30:45Z"
      },
      {
        "id": "b2c3d4e5f6a1...",
        "message": "Fix bug in main function",
        "author": "Jane Smith",
        "time": "2023-10-09T14:25:30Z"
      }
    ]
  }
}
```

## 🔧 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

FastFS-MCP is released under the MIT License. See the LICENSE file for details.

---

Built for AI-enhanced CLI and developer workflows with speed, structure, and simplicity.
