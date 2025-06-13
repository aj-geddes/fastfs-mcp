# Testing the Prompt Functionality

This document explains how to test the interactive prompt functionality in the FastFS-MCP server.

## Test Script

We've included a test script `test_prompts.py` that simulates how Claude would interact with the interactive prompt capabilities. This script:

1. Sends requests to the MCP server
2. Handles prompt responses
3. Collects user input
4. Sends user responses back to the server

## Running the Tests

To test the prompt functionality:

1. Build the Docker image:
   ```bash
   docker build -t fastfs-mcp .
   ```

2. Run the server with the test script:
   ```bash
   # On Windows
   cat test_prompts.py | docker run -i --rm -v C:\\Users\\username:/mnt/workspace:rw fastfs-mcp
   
   # On Unix/macOS
   cat test_prompts.py | docker run -i --rm -v $HOME:/mnt/workspace:rw fastfs-mcp
   ```

The test script will execute a series of tests for different prompt types, allowing you to interact with each one.

## What to Expect

When running the tests, you'll see:

1. Information about which test is being run
2. Prompts that would normally be shown to the user
3. Request for your input (simulating user responses)
4. Results of each operation

## Manual Testing with Claude

To test this with Claude:

1. Configure Claude Desktop with the FastFS-MCP server as shown in the README
2. Ask Claude to perform tasks that require interactive input
3. Observe how Claude uses the prompt functionality to collect information

Example prompts for Claude:

- "Help me create a new file with some content"
- "Initialize a new project for me"
- "Show me one of the Markdown files in this directory"

## Expected Protocol Flow

The protocol flow for interactive prompts is:

1. Claude calls a function that uses prompts (e.g., `interactive_write`)
2. The MCP server sends a prompt message to stdout
3. Claude displays this prompt to the user
4. The user responds to Claude
5. Claude sends the user's response to the MCP server
6. The MCP server processes the response and continues execution

## Troubleshooting

If you encounter issues:

- Ensure the `prompt_helpers.py` file is in the same directory as `server.py`
- Check that the Docker container has proper permissions for the mounted volume
- Verify that the JSON messages are correctly formatted
- Check the server logs for any error messages

## Extending the Tests

You can extend the test script to test additional prompt types or workflows by:

1. Adding new test functions for specific scenarios
2. Calling those functions from the `main()` function
3. Running the updated test script

## Security Considerations

Remember that the prompt functionality gives Claude the ability to ask for and collect user input. This should be used responsibly and with clear communication about what is being requested and why.
