# FastFS-MCP: Interactive Prompts Guide

This guide describes how to use the interactive prompt capabilities of FastFS-MCP when working with Claude.

## Overview

FastFS-MCP now includes interactive prompting capabilities that allow Claude to:

1. Send structured prompts to users
2. Collect user input
3. Use that input to perform filesystem operations
4. Guide users through complex workflows

## Available Prompt Types

The MCP server includes several pre-defined prompt templates:

| Prompt Type | Description |
|-------------|-------------|
| `confirm_file_overwrite` | Ask user to confirm before overwriting an existing file |
| `confirm_directory_delete` | Warn user before deleting a directory |
| `file_not_found_options` | Provide options when a file is not found |
| `enter_file_content` | Get content for a file from the user |
| `enter_search_pattern` | Ask user for a search pattern |
| `project_initialization` | Collect information to initialize a new project |
| `coding_task` | Define parameters of a coding task |
| `select_file_from_list` | Let user select a file from a list |
| `custom` | Create a completely custom prompt message |

## Interactive File Operations

The MCP server provides enhanced interactive versions of standard file operations:

| Function | Description |
|----------|-------------|
| `interactive_write(path)` | Write file content with user input |
| `confirm_overwrite(path)` | Ask user before overwriting a file |
| `select_file(path, pattern)` | Let user choose a file from a directory |
| `get_file_content(path)` | Get content for a file from the user |
| `init_project()` | Initialize a project with user input |

## Examples for Claude

Here are examples of how Claude can use these interactive capabilities:

### Interactive File Write

```
I can help you create a new file. Let me ask for the content:

[Call interactive_write("example.txt")]

Great! I've created the file with the content you provided.
```

### File Selection

```
Let me help you find the file you're looking for:

[Call select_file(".", "*.txt")]

I found the file you selected. Here's its content:

[Call read(selected_file)]
```

### Project Initialization

```
I'll help you set up a new project:

[Call init_project()]

Great! I've created a new project directory with the basic structure.
```

### Custom Prompts

```
Let me get some additional information:

[Call prompt("custom", message="What would you like to name your application?")]

Thanks! I'll use that name in the configuration file.
```

## Protocol Details

When Claude calls the `prompt` function, the MCP server:

1. Formats the prompt using the specified template
2. Sends a special JSON message to the stdout stream
3. Waits for a response on stdin
4. Returns the response to Claude

This allows for seamless interactive workflows between Claude and the user through the MCP server.

## Best Practices

- Use appropriate prompt types for different scenarios
- Provide clear instructions in prompts
- Handle user cancellations gracefully
- Confirm before potentially destructive operations
- Use interactive prompts sparingly and purposefully

## Getting Started

To use these capabilities, Claude simply needs to call the appropriate functions when interacting with users through the FastFS-MCP server.
