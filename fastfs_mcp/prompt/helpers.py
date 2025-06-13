"""
Prompt helpers for the fastfs-mcp server.

This module provides prompt templates and utilities to help Claude interact with users
through the MCP server in more structured ways.
"""

# Common prompt templates that Claude can use
PROMPT_TEMPLATES = {
    # File operations prompts
    "confirm_file_overwrite": """
⚠️ WARNING: The file '{path}' already exists.
Do you want to overwrite it? (yes/no)
""",
    
    "confirm_directory_delete": """
⚠️ WARNING: You're about to delete the directory '{path}' and all its contents.
Are you sure you want to continue? (yes/no)
""",
    
    "file_not_found_options": """
❌ The file '{path}' was not found. Would you like to:
1. Create a new file at this location
2. Specify a different path
3. Cancel the operation

Enter your choice (1-3):
""",
    
    # Content input prompts
    "enter_file_content": """
Please enter the content for the file '{path}':
(Type 'END_OF_CONTENT' on a new line when finished)
""",

    "enter_search_pattern": """
Enter the pattern you want to search for:
""",
    
    # Project/task prompts
    "project_initialization": """
📋 Project Initialization

I'll help you set up a new project. Please provide the following information:

1. Project name: 
2. Project type (web, api, cli, library, other): 
3. Programming language: 
4. Would you like to create a git repository? (yes/no): 
""",
    
    "coding_task": """
🧩 Coding Task Definition

Let's define the coding task you'd like help with:

1. What are you trying to accomplish?
2. Any specific requirements or constraints?
3. Preferred language or framework?
4. Would you like me to explain the code as I write it? (yes/no)
""",
    
    # File selection prompt
    "select_file_from_list": """
Please select a file from the list:
{file_list}

Enter the number of your choice:
""",
    
    # Custom user prompt
    "custom": "{message}"
}

# Helper functions
def format_prompt(prompt_type, **kwargs):
    """Format a prompt template with the provided parameters."""
    if prompt_type not in PROMPT_TEMPLATES:
        return f"Error: Unknown prompt type '{prompt_type}'"
    
    template = PROMPT_TEMPLATES[prompt_type]
    try:
        return template.format(**kwargs)
    except KeyError as e:
        return f"Error: Missing required parameter {e} for prompt type '{prompt_type}'"

def format_file_list(files):
    """Format a list of files for display in a prompt."""
    result = ""
    for i, file in enumerate(files, 1):
        result += f"{i}. {file}\n"
    return result
