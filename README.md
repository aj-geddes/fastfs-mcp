# fastfs-mcp

A high-speed MCP server for filesystem operations using Python with interactive prompting capabilities and Git integration.

---

## 🚀 Features

* Ultra-fast filesystem commands: `ls`, `cat`, `write`, `delete`, `mkdir`
* Blazing-fast `grep` via `ripgrep`
* Executable lookup with `which`
* **Enhanced interactive prompts for user interaction**
* **Project initialization with guided setup**
* **Interactive file editing and selection**
* **Complete Git integration with advanced repository analysis**
* **GitHub authentication with Personal Access Token**
* JSON over stdin/stdout for Claude Desktop, VSCode, and AI-native tooling

---

## 💻 Docker Quick Start

```bash
docker build -t fastfs-mcp .

docker run -i --rm \
  -v C:\\Users\\username:/mnt/workspace:rw \
  fastfs-mcp
```

> On Unix/macOS: replace with `-v $HOME:/mnt/workspace`

### With GitHub Authentication:

```bash
docker run -i --rm \
  -v C:\\Users\\username:/mnt/workspace:rw \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here \
  fastfs-mcp
```

---

## 🛠 Claude Desktop Configuration

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

### With GitHub Authentication:

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

> The server will automatically start in the /mnt/workspace directory

---

## 🤓 VSCode Dev Container

```json
{
  "name": "fastfs-mcp",
  "image": "fastfs-mcp",
  "mounts": [
    "source=C:/Users/username,target=/mnt/workspace,type=bind,consistency=cached"
  ],
  "runArgs": ["--rm"]
}
```

> Mounts local Windows workspace into container for live testing

---

## 🔧 Supported MCP Methods

| Method | Description |
|--------|-------------|
| **Basic Filesystem Operations** | |
| `ls` | List files in a directory |
| `cat` | Read file contents |
| `write` | Create or overwrite file content |
| `delete` | Remove a file or directory |
| `mkdir` | Create directories |
| `which` | Locate executables in PATH |
| `grep` | Fast file searching via ripgrep |
| **Git Operations** | |
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
| **Advanced Git Analysis** | |
| `context` | Get comprehensive repo context |
| `repo_info` | Get detailed repository information |
| `validate` | Check repository for common issues |
| `summarize_log` | Generate commit log statistics |
| `suggest_commit` | Auto-suggest commit messages |
| `audit_history` | Audit repository for security issues |
| **Interactive Features** | |
| `prompt` | Send interactive prompt to user |
| `get_prompt_types` | List available prompt templates |
| `interactive_write` | Write file with user-provided content |
| `confirm_overwrite` | Ask before overwriting files |
| `select_file` | Let user choose from file list |
| `get_file_content` | Get content for file from user |
| `init_project` | Initialize project with guided setup |
| **Text & File Processing** | |
| `sed` | Stream editor for text transformation |
| `gawk` | Text processing with AWK |
| `head` | Show first lines of a file |
| `tail` | Show last lines of a file |
| `wc` | Count lines, words, and bytes |
| `cut` | Select columns from file |
| `sort` | Sort lines of text files |
| `uniq` | Report or filter repeated lines |
| **Advanced Filesystem** | |
| `tree` | Display directory structure |
| `find` | Find files by pattern |
| `cp` | Copy files or directories |
| `mv` | Move or rename files |
| `rm` | Remove files or directories |
| `stat` | Display file metadata |
| `chmod` | Change file permissions |
| `du` | Show disk usage |
| `df` | Show disk space |
| **Archive & Compression** | |
| `tar` | Create/extract tar archives |
| `gzip` | Compress/decompress files |
| `zip` | Create/extract zip archives |

---

## 📦 Tools Included in Image

* `ripgrep`
* `jq`
* `sed`
* `awk`
* `tree`
* `fd-find`
* `coreutils`
* `zip/unzip`
* `gzip`
* `xz-utils`
* `git`

---

## 📧 Protocol Usage

### Example Request

```json
{
  "method": "ls",
  "params": { "path": "." }
}
```

### Example Response

```json
{
  "result": ["main.tf", "README.md"]
}
```

### Git Example

Request:
```json
{
  "method": "context",
  "params": {}
}
```

Response:
```json
{
  "result": {
    "current_branch": "main",
    "repository_root": "/mnt/workspace/my-project",
    "is_clean": false,
    "head_commit": "a1b2c3d4e5f6...",
    "remotes": {
      "origin": "https://github.com/user/repo.git"
    },
    "recent_commits": [
      "a1b2c3d4 Update README.md",
      "b2c3d4e5 Fix bug in main function",
      "c3d4e5f6 Add new feature"
    ]
  }
}
```

### GitHub Authentication

The server supports GitHub authentication using a Personal Access Token (PAT). When a PAT is provided via the `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable, Git operations that interact with GitHub (clone, push, pull, fetch) will automatically use the token for authentication.

This is especially useful for:
- Accessing private repositories
- Performing operations that require authentication (push, create repo, etc.)
- Avoiding rate limits on API calls

Example request with GitHub authentication:
```json
{
  "method": "clone",
  "params": {
    "repo_url": "https://github.com/user/private-repo.git",
    "target_dir": "private-repo"
  }
}
```

### Interactive Prompt Example

Request:
```json
{
  "method": "prompt",
  "params": { 
    "prompt_type": "custom", 
    "message": "What would you like to name your file?" 
  }
}
```

Response (to stdout):
```json
{
  "type": "user_prompt",
  "prompt": "What would you like to name your file?"
}
```

User Response (from stdin):
```json
{
  "type": "user_response",
  "response": "myfile.txt"
}
```

Final Result:
```json
{
  "result": {
    "response": "myfile.txt",
    "timestamp": 1622548123.45
  }
}
```

---

## 🚀 Interactive Prompts

The server includes built-in prompt templates for common scenarios:

* File operation confirmations
* Content input
* Project initialization
* File selection
* Custom prompts

See `prompt_guide.md` for detailed documentation and examples.

---

## Working Directory

The server will automatically start in the `/mnt/workspace` directory, which corresponds to the root of your mounted volume. This makes it easier to navigate your entire filesystem without needing to specify absolute paths or change directories first.

---

Built for AI-enhanced CLI and developer workflows with speed, structure, and simplicity.
