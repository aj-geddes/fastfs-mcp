# FastFS-MCP

<img src="https://img.shields.io/badge/Version-2.8.0-blue" alt="Version" /> <img src="https://img.shields.io/badge/License-MIT-green" alt="License" /> <img src="https://img.shields.io/badge/Docker-Ready-informational" alt="Docker Ready" />

A high-speed MCP (Model Context Protocol) server for filesystem operations, Git integration, and interactive prompting capabilities, designed to work seamlessly with Claude and AI-native tooling.

## 🚀 Overview

FastFS-MCP enables AI assistants like Claude to interact with your local filesystem, manage Git repositories, and provide interactive experiences through a standardized JSON-based protocol. Whether you're building AI-assisted development workflows, creating content with Claude, or automating file management tasks, FastFS-MCP provides the bridge between your AI assistant and your local environment.

```mermaid
%%{ init: { "theme": "dark", "look": "handDrawn", "themeVariables": { "handDrawn": true } } }%%
graph TD
    Claude[Claude AI Assistant] <-->|JSON Protocol| MCP[FastFS-MCP Server]
    MCP <-->|File Operations| FS[Local Filesystem]
    MCP <-->|Git Operations| Git[Git Repositories]
    MCP <-->|Interactive Prompts| User[Human User]
    
    subgraph "FastFS-MCP Capabilities"
        FS
        Git
        User
    end
```

## ✨ Key Features

- **Ultra-fast filesystem operations**: Access, modify, and manage files with minimal latency
- **Complete Git integration**: Perform all standard Git operations and advanced repository analysis
- **Interactive prompting**: Enable Claude to engage users through structured prompts and forms
- **GitHub authentication**: Securely authenticate with GitHub using personal access tokens or GitHub Apps
- **JSON protocol**: Communicate with Claude Desktop, VSCode, and other AI-native tools using a standard interface

## 🛠️ Core Components Architecture

```mermaid
%%{ init: { "theme": "dark", "look": "handDrawn", "themeVariables": { "handDrawn": true } } }%%
graph TD
    Server[server.py] --> FastMCP[FastMCP Class]
    Server --> FileOps[Filesystem Operations]
    Server --> GitTools[git_tools.py]
    Server --> PromptHelpers[prompt_helpers.py]
    
    FileOps --> Basic[Basic Commands]
    FileOps --> Advanced[Advanced Operations]
    FileOps --> Text[Text Processing]
    FileOps --> Archive[Archive & Compression]
    
    GitTools --> BasicGit[Basic Git]
    GitTools --> AdvancedGit[Advanced Git]
    GitTools --> GitAnalysis[Repository Analysis]
    GitTools --> GitAuth[GitHub Authentication]
    
    PromptHelpers --> Templates[Prompt Templates]
    PromptHelpers --> Interactive[Interactive Tools]
    
    GitAuth --> PAT[Personal Access Token]
    GitAuth --> GitHubApp[GitHub App]
    GitHubApp --> DirectKey[Direct Key]
    GitHubApp --> KeyFromFile[Key from File]
```

## 💻 Installation & Quick Start

### Docker Quick Start

```bash
# Build the Docker image
docker build -t fastfs-mcp .

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

#### Using GitHub App with Private Key as Environment Variable

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", 
        "-e", "GITHUB_APP_ID",
        "-e", "GITHUB_APP_PRIVATE_KEY",
        "-e", "GITHUB_APP_INSTALLATION_ID",
        "-v", "C:\\Users\\username:/mnt/workspace:rw",
        "fastfs-mcp"
      ],
      "env": {
        "GITHUB_APP_ID": "your_app_id",
        "GITHUB_APP_PRIVATE_KEY": "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----",
        "GITHUB_APP_INSTALLATION_ID": "your_installation_id"
      }
    }
  }
}
```

#### Using GitHub App with Private Key from File

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", 
        "-e", "GITHUB_APP_ID",
        "-e", "GITHUB_APP_PRIVATE_KEY_PATH",
        "-e", "GITHUB_APP_INSTALLATION_ID",
        "-v", "C:\\Users\\username:/mnt/workspace:rw",
        "fastfs-mcp"
      ],
      "env": {
        "GITHUB_APP_ID": "your_app_id",
        "GITHUB_APP_PRIVATE_KEY_PATH": "/mnt/workspace/github-app-key.pem",
        "GITHUB_APP_INSTALLATION_ID": "your_installation_id"
      }
    }
  }
}
```

## 📋 Tool Categories

FastFS-MCP provides a comprehensive set of tools organized into logical categories:

```mermaid
%%{ init: { "theme": "dark", "look": "handDrawn", "themeVariables": { "handDrawn": true } } }%%
graph TD
    MCP[FastFS-MCP] --> FS[Filesystem Operations]
    MCP --> Git[Git Operations]
    MCP --> Prompts[Interactive Prompts]
    MCP --> Processing[Text & File Processing]
    MCP --> Archive[Archive & Compression]
    
    FS --> Basic[Basic Operations]
    FS --> Advanced[Advanced Operations]
    
    Git --> BasicGit[Basic Commands]
    Git --> AdvancedGit[Advanced Analysis]
    Git --> GitHubAuth[GitHub Authentication]
    
    GitHubAuth --> PAT[Personal Access Token]
    GitHubAuth --> GitHubApp[GitHub App]
    
    Prompts --> Templates[Prompt Templates]
    Prompts --> Interactive[Interactive Tools]
    
    Processing --> Text[Text Manipulation]
    Processing --> Filters[Filters & Transformations]
    
    Archive --> Tar[Tar Operations]
    Archive --> Zip[Zip Operations]
    Archive --> Compress[Compression Tools]
```

## 🗂️ Filesystem Operations

### Basic Operations

```mermaid
%%{ init: { "theme": "dark", "look": "handDrawn", "themeVariables": { "handDrawn": true } } }%%
graph LR
    ls[ls] --> list[List files and directories]
    cd[cd] --> change[Change current directory]
    pwd[pwd] --> print[Print working directory]
    read[read] --> display[Display file contents]
    write[write] --> create[Create or modify files]
    grep[grep] --> search[Search file content]
    which[which] --> locate[Locate executables]
```

| Method | Description |
|--------|-------------|
| `ls` | List files in a directory |
| `cd` | Change the current working directory |
| `pwd` | Print the current working directory |
| `read` | Read file contents |
| `write` | Create or overwrite file content |
| `grep` | Fast file searching via ripgrep |
| `which` | Locate executables in PATH |

### Advanced Operations

| Method | Description |
|--------|-------------|
| `tree` | Display directory structure |
| `find` | Find files by pattern |
| `cp` | Copy files or directories |
| `mv` | Move or rename files |
| `rm` | Remove files or directories |
| `mkdir` | Create directories |
| `stat` | Display file metadata |
| `chmod` | Change file permissions |
| `du` | Show disk usage |
| `df` | Show disk space |
| `touch` | Create a new empty file or update timestamp |

### Text & File Processing

| Method | Description |
|--------|-------------|
| `sed` | Stream editor for text transformation |
| `gawk` | Text processing with AWK |
| `head` | Show first lines of a file |
| `tail` | Show last lines of a file |
| `wc` | Count lines, words, and bytes |
| `cut` | Select columns from file |
| `sort` | Sort lines of text files |
| `uniq` | Report or filter repeated lines |
| `nl` | Number lines in a file |
| `split` | Split a file into smaller parts |
| `readlink` | Print the resolved path of a symbolic link |
| `realpath` | Print the resolved absolute path |

### Archive & Compression

| Method | Description |
|--------|-------------|
| `tar` | Create/extract tar archives |
| `gzip` | Compress/decompress files |
| `zip` | Create/extract zip archives |

## 🌿 Git Operations

```mermaid
%%{ init: { "theme": "dark", "look": "handDrawn", "themeVariables": { "handDrawn": true } } }%%
graph TD
    Git[Git Operations] --> Repo[Repository Management]
    Git --> Changes[Change Management]
    Git --> Branch[Branch Operations]
    Git --> Remote[Remote Operations]
    Git --> Analysis[Repository Analysis]
    Git --> Auth[GitHub Authentication]
    
    Repo --> init[Initialize Repository]
    Repo --> clone[Clone Repository]
    Repo --> status[Check Status]
    
    Changes --> add[Stage Changes]
    Changes --> commit[Commit Changes]
    Changes --> diff[View Differences]
    
    Branch --> checkout[Switch Branches]
    Branch --> branch[Manage Branches]
    Branch --> merge[Merge Branches]
    
    Remote --> push[Push Changes]
    Remote --> pull[Pull Changes]
    Remote --> fetch[Fetch Updates]
    
    Analysis --> context[Get Repository Context]
    Analysis --> validate[Validate Repository]
    Analysis --> suggest[Suggest Commit Messages]
    Analysis --> audit[Audit Repository History]
    
    Auth --> PAT[Personal Access Token]
    Auth --> GitHubApp[GitHub App]
```

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
| `config` | Get or set repository or global options |
| `fetch` | Download objects and refs from another repository |
| `blame` | Show what revision and author last modified each line of a file |
| `git_grep` | Print lines matching a pattern in tracked files |
| `head` | Show the current HEAD commit information |

### Advanced Git Analysis

| Method | Description |
|--------|-------------|
| `context` | Get comprehensive repo context |
| `repo_info` | Get detailed repository information |
| `validate` | Check repository for common issues |
| `summarize_log` | Generate commit log statistics |
| `suggest_commit` | Auto-suggest commit messages |
| `audit_history` | Audit repository for security issues |

## 🤝 Interactive Prompts

```mermaid
%%{ init: { "theme": "dark", "look": "handDrawn", "themeVariables": { "handDrawn": true } } }%%
graph TD
    Prompts[Interactive Prompts] --> Templates[Prompt Templates]
    Prompts --> Operations[Prompt Operations]
    
    Templates --> FilePrompts[File Prompts]
    Templates --> ContentPrompts[Content Prompts]
    Templates --> ProjectPrompts[Project Prompts]
    Templates --> CustomPrompts[Custom Prompts]
    
    Operations --> prompt[Send Prompt]
    Operations --> interactive_write[Interactive Write]
    Operations --> confirm_overwrite[Confirm Overwrite]
    Operations --> select_file[Select File]
    Operations --> get_file_content[Get File Content]
    Operations --> init_project[Initialize Project]
    
    FilePrompts --> confirm_file_overwrite[Confirm File Overwrite]
    FilePrompts --> confirm_directory_delete[Confirm Directory Delete]
    FilePrompts --> file_not_found_options[File Not Found Options]
    
    ContentPrompts --> enter_file_content[Enter File Content]
    ContentPrompts --> enter_search_pattern[Enter Search Pattern]
    
    ProjectPrompts --> project_initialization[Project Initialization]
    ProjectPrompts --> coding_task[Coding Task]
    
    CustomPrompts --> custom[Custom Message]
```

### Prompt Templates

| Template | Description |
|----------|-------------|
| `confirm_file_overwrite` | Ask user to confirm before overwriting an existing file |
| `confirm_directory_delete` | Warn user before deleting a directory |
| `file_not_found_options` | Provide options when a file is not found |
| `enter_file_content` | Get content for a file from the user |
| `enter_search_pattern` | Ask user for a search pattern |
| `project_initialization` | Collect information to initialize a new project |
| `coding_task` | Define parameters of a coding task |
| `select_file_from_list` | Let user select a file from a list |
| `custom` | Create a completely custom prompt message |

### Interactive Functions

| Function | Description |
|----------|-------------|
| `prompt` | Send an interactive prompt to the user |
| `get_prompt_types` | List available prompt templates |
| `interactive_write` | Write file with user-provided content |
| `confirm_overwrite` | Ask before overwriting files |
| `select_file` | Let user choose from file list |
| `get_file_content` | Get content for file from user |
| `init_project` | Initialize project with guided setup |

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

#### Basic File Operation

```json
// Request
{
  "method": "ls",
  "params": { "path": "." }
}

// Response
{
  "result": ["main.tf", "README.md"]
}
```

#### Git Repository Context

```json
// Request
{
  "method": "context",
  "params": {}
}

// Response
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

#### Interactive Prompt Flow

```
// Request
{
  "method": "prompt",
  "params": { 
    "prompt_type": "custom", 
    "message": "What would you like to name your file?" 
  }
}

// Response to stdout (visible to user)
{
  "type": "user_prompt",
  "prompt": "What would you like to name your file?"
}

// User response (from stdin)
{
  "type": "user_response",
  "response": "myfile.txt"
}

// Final result to Claude
{
  "result": {
    "response": "myfile.txt",
    "timestamp": 1622548123.45
  }
}
```

## 🔧 GitHub Authentication

FastFS-MCP supports two methods of GitHub authentication to enable secure Git operations with GitHub repositories:

### Personal Access Token (PAT) Authentication

```mermaid
%%{ init: { "theme": "dark", "look": "handDrawn", "themeVariables": { "handDrawn": true } } }%%
sequenceDiagram
    participant Claude
    participant FastFS
    participant GitHub
    
    Claude->>FastFS: git_clone(private_repo_url)
    FastFS->>GitHub: Authentication with PAT
    GitHub-->>FastFS: Authentication successful
    FastFS->>GitHub: Clone repository
    GitHub-->>FastFS: Repository content
    FastFS-->>Claude: Clone successful
```

When a GitHub PAT is provided via the `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable, Git operations that interact with GitHub (clone, push, pull, fetch) will automatically use the token for authentication, enabling:

- Access to private repositories
- Operations that require authentication (push, create repo, etc.)
- Avoiding rate limits on API calls

### GitHub App Authentication

```mermaid
%%{ init: { "theme": "dark", "look": "handDrawn", "themeVariables": { "handDrawn": true } } }%%
sequenceDiagram
    participant Claude
    participant FastFS
    participant GitHub
    
    Claude->>FastFS: git_clone(private_repo_url)
    FastFS->>FastFS: Generate JWT using private key
    FastFS->>GitHub: Request installation token with JWT
    GitHub-->>FastFS: Installation token
    FastFS->>GitHub: Clone repository with installation token
    GitHub-->>FastFS: Repository content
    FastFS-->>Claude: Clone successful
```

GitHub App authentication provides more granular permissions and better security compared to Personal Access Tokens:

- **Fine-grained permissions**: GitHub Apps can be configured with specific permissions
- **Repository-specific access**: GitHub Apps can be installed on specific repositories
- **Organization-level control**: Organization admins can control which apps are installed
- **Automatic token refresh**: Installation tokens expire after 1 hour and are automatically refreshed

To use GitHub App authentication, provide the following environment variables:

- `GITHUB_APP_ID`: Your GitHub App's ID

And one of these options for the private key:

- `GITHUB_APP_PRIVATE_KEY`: The private key content for your GitHub App (PEM format) as an environment variable
- `GITHUB_APP_PRIVATE_KEY_PATH`: Path to a file containing the private key (PEM format)

Optionally:
- `GITHUB_APP_INSTALLATION_ID`: The specific installation ID to use (if not provided, FastFS-MCP will attempt to use the first installation)

#### Security Considerations for Private Keys

When using GitHub App authentication, consider these security practices for managing private keys:

1. **File-based private key** (recommended): 
   - Store your private key in your workspace and use `GITHUB_APP_PRIVATE_KEY_PATH`
   - Ensure proper file permissions (chmod 600) on the private key file
   - This approach avoids having the key in process environment variables or shell history

2. **Environment variable private key**:
   - Use this for development or when you can't mount a file
   - Be aware that environment variables can be visible in process lists on some systems

## 🐳 Docker Environment

FastFS-MCP runs in a Docker container for portability and isolation, with the following tools installed:

- `ripgrep` for high-performance file searching
- `jq` for JSON parsing and manipulation
- `sed` and `gawk` for text processing
- `tree` for directory visualization
- `fd-find` for alternative file finding
- `coreutils` for standard Unix tools
- `zip/unzip`, `gzip`, and `xz-utils` for compression
- `git` for repository operations

## 🚀 Use Cases

- **AI-assisted development**: Let Claude help you code, manage files, and use Git all within the same conversation
- **Content creation workflows**: Enable Claude to read, write, and organize files for writing projects
- **Repository management**: Get insights into Git repositories and automate common Git operations
- **Interactive project setup**: Guide users through structured project initialization with interactive prompts
- **System administration**: Perform file system operations and maintenance tasks with AI assistance

## 🔒 Security Considerations

FastFS-MCP provides direct access to your filesystem and Git repositories. Consider the following security practices:

1. Only run FastFS-MCP with appropriate file system permissions
2. Mount only the directories you need to expose to Claude
3. Use separate GitHub PATs with limited scope for authentication, or prefer GitHub Apps for better security
4. Regularly review the logs and commands executed by the server
5. For GitHub Apps, store the private key securely and use installation-specific tokens
6. When using GitHub App authentication, prefer file-based private keys over environment variables when possible

## 📄 License

FastFS-MCP is released under the MIT License. See the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📚 Further Documentation

- [Prompt Guide](prompt_guide.md) - Detailed documentation on interactive prompts
- [Claude Prompt Examples](claude_prompt_examples.md) - Examples of how Claude can use FastFS-MCP
- [Claude Prompt Guide](claude_prompt_guide.md) - Guide for Claude on working with FastFS-MCP

<!-- These stylish mermaid diagrams use a hand-drawn theme to enhance visual appeal. The dark theme with hand-drawn styling makes them more readable and engaging for users. -->

---

Built for AI-enhanced CLI and developer workflows with speed, structure, and simplicity.
