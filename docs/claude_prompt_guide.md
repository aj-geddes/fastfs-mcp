# Claude's Guide to Interactive Prompts with FastFS-MCP

This guide will help Claude effectively use the interactive prompt capabilities of FastFS-MCP when helping users with filesystem operations and tasks.

## Core Prompt Functions

### Basic Prompting

The most fundamental function is the general `prompt` function:

```python
prompt(prompt_type: str = "custom", message: str = "", **kwargs) -> Dict[str, Any]
```

This allows Claude to send a prompt to the user and get their response. The response is returned as a dictionary with:
- `response`: The user's text response
- `timestamp`: When the response was received

### Available Prompt Types

Use `get_prompt_types()` to get a list of all available prompt templates. The most commonly used are:

- `custom`: A completely custom message
- `confirm_file_overwrite`: Asks the user to confirm before overwriting an existing file
- `confirm_directory_delete`: Warns the user before deleting a directory
- `enter_file_content`: Gets content for a file from the user
- `select_file_from_list`: Lets the user select a file from a list
- `project_initialization`: Collects information to initialize a new project

## Best Practices for Claude

### When to Use Interactive Prompts

Use interactive prompts when:

1. User input is required for a decision (e.g., confirm an operation)
2. Collecting content from the user (e.g., file content)
3. Guiding the user through a multi-step process
4. Clarifying ambiguous requests

### Clear Communication Patterns

When using interactive prompts:

1. **Introduce the interaction**: "I'll help you create a new file. First, let me ask you some questions."
2. **Explain what you're doing**: "I'm going to prompt you for the file content now."
3. **Acknowledge responses**: "Thanks for providing that information."
4. **Summarize actions taken**: "I've created the file with your content."

### Handling User Responses

When working with user responses:

1. Check if the user cancelled the operation
2. Validate input when necessary
3. Provide feedback about what you understood
4. Handle errors gracefully

### Example Dialogues

#### Creating a File

```
User: Can you help me create a configuration file?

Claude: I'd be happy to help you create a configuration file. Let me ask you a few questions first.

[Call prompt("custom", message="What would you like to name the configuration file?")]

I'll create a file named "[user's response]". Now I need the content for this file.

[Call get_file_content("[user's response]")]

Thank you! I've created the configuration file with the content you provided.
```

#### Project Initialization

```
User: Help me start a new React project

Claude: I'll help you set up a new React project. Let's start by gathering some basic information.

[Call init_project()]

Great! I've created a new project directory named "[project name]" with the basic structure for a React project. I've set up the following files:
- README.md with project information
- Basic directory structure for a React application
[List other created files]

Would you like me to help you with anything specific in your new React project?
```

#### File Selection

```
User: Show me the content of one of my JavaScript files

Claude: I'll help you view one of your JavaScript files. Let me list the available JavaScript files so you can choose which one to view.

[Call select_file(".", "*.js")]

Here's the content of the file you selected:

[Call read(selected_file)]

Would you like me to explain any part of this code?
```

## Advanced Usage Patterns

### Chaining Prompts

For complex workflows, chain multiple prompts together:

```
[Call prompt("custom", message="What type of project would you like to create?")]
[Based on response, call a more specific prompt template]
[Use responses to initialize appropriate project structure]
```

### Confirming Destructive Operations

Always confirm before performing potentially destructive operations:

```
[Call confirm_overwrite(file_path)]
[Only proceed if confirmed]
```

### Progressive Disclosure

For complex tasks, use a series of prompts that progressively guide the user:

1. Start with high-level options
2. Based on selection, ask more specific questions
3. Confirm before finalizing

## Debugging and Troubleshooting

If you encounter issues with the prompt functionality:

1. Check if the prompt_helpers.py file is loaded correctly
2. Verify that the correct prompt_type is being used
3. Make sure all required parameters for the prompt template are provided
4. Handle potential errors in the prompt response

Remember that the primary goal is to provide a smooth, intuitive experience for the user while helping them accomplish their tasks effectively.
