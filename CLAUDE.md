# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastFS-MCP is a high-speed MCP (Model Context Protocol) server that enables AI assistants to interact with local filesystems and Git repositories. It runs in Docker and communicates via JSON protocol over stdio.

## Build and Run Commands

```bash
# Build Docker image
docker build -t fastfs-mcp .

# Run with local filesystem mounted
docker run -i --rm -v /path/to/workspace:/mnt/workspace:rw fastfs-mcp

# Run with GitHub PAT authentication
docker run -i --rm -v /path/to/workspace:/mnt/workspace:rw \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx fastfs-mcp

# Run with GitHub App authentication
docker run -i --rm -v /path/to/workspace:/mnt/workspace:rw \
  -e GITHUB_APP_ID=xxx \
  -e GITHUB_APP_PRIVATE_KEY_PATH=/mnt/workspace/key.pem \
  -e GITHUB_APP_INSTALLATION_ID=xxx fastfs-mcp
```

## Testing

```bash
# Run prompt tests (requires MCP server running)
python test_prompts.py

# Run GitHub App tests
python test_github_app.py
```

## Architecture

### Core Components

- **server.py** - Main MCP server using FastMCP. Registers all filesystem and Git tools with `fastfs_` prefix (e.g., `fastfs_ls`, `fastfs_read`, `fastfs_commit`). Runs on `/mnt/workspace` by default.

- **git_tools.py** - Complete Git operations module. Handles GitHub authentication (PAT and GitHub App via JWT). All git functions return `Tuple[bool, str]` from `run_git_command()` and are wrapped as MCP tools in `server.py`.

- **prompt_helpers.py** - Prompt templates (`PROMPT_TEMPLATES` dict) for interactive user communication.

### Key Patterns

1. **Tool Naming**: All tools use `fastfs_` prefix for disambiguation (e.g., `fastfs_read`, `fastfs_commit`)
2. **Tool Registration**: Functions decorated with `@mcp.tool(description="...", annotations={...})` in `server.py`
3. **Tool Annotations**: Critical tools include FastMCP annotations:
   - `readOnlyHint: True` for read operations (`fastfs_ls`, `fastfs_read`, `fastfs_status`, `fastfs_context`)
   - `destructiveHint: True` for dangerous operations (`fastfs_rm`, `fastfs_write`, `fastfs_push`, `fastfs_reset`, `fastfs_clean`)
4. **Command Execution**: `run_command()` for shell commands, `run_git_command()` for git operations
5. **GitHub Auth Priority**: PAT checked first via `GITHUB_PAT` env var, then GitHub App via `GITHUB_APP_ID` + private key
6. **URL Transformation**: `transform_github_url()` injects auth tokens into GitHub HTTPS URLs

### Tool Description Pattern

Tool descriptions follow a consistent format for AI assistants:
```
Use when: [scenario where this tool is preferred]
Prefer over: [alternative tools and when to use them instead]
Returns: [output format]
Example: [usage example]
```

### Dependencies

- `fastmcp==2.8.0` - MCP server framework
- `PyJWT==2.8.0` - JWT generation for GitHub App auth
- `cryptography==41.0.4` - RSA key handling

### Docker Environment

The container includes: ripgrep, jq, sed, gawk, fd-find, tree, coreutils, zip/unzip, gzip, xz-utils, git. Workspace mounts to `/mnt/workspace`.
