#!/usr/bin/env python3
"""
Test script for fastfs-mcp prompt functionality.
This script simulates how Claude would interact with the prompt capabilities.
"""

import json
import sys
import time
import threading

# Simulated MCP client (similar to what Claude would do)
def send_mcp_request(method, params=None):
    """Send a request to the MCP server."""
    if params is None:
        params = {}
    
    request = {
        "method": method,
        "params": params
    }
    
    print(json.dumps(request), flush=True)
    
    # Wait for and parse the response
    for line in sys.stdin:
        try:
            response = json.loads(line)
            
            # If this is a prompt to the user, handle it
            if isinstance(response, dict) and response.get("type") == "user_prompt":
                # Print the prompt for demonstration purposes
                print(f"\n>>> USER PROMPT: {response.get('prompt')}\n")
                
                # Simulate user response after a brief delay
                user_input = input("Enter your response: ")
                
                # Send the user's response back to the MCP server
                user_response = {
                    "type": "user_response",
                    "response": user_input
                }
                print(json.dumps(user_response), flush=True)
                continue
                
            # Regular response, return it
            return response
        except json.JSONDecodeError:
            continue

def test_get_prompt_types():
    """Test getting available prompt types."""
    print("\n=== Testing get_prompt_types ===")
    response = send_mcp_request("get_prompt_types")
    print("Available prompt types:", response.get("result", []))

def test_custom_prompt():
    """Test sending a custom prompt."""
    print("\n=== Testing custom prompt ===")
    response = send_mcp_request("prompt", {
        "prompt_type": "custom",
        "message": "What is your favorite programming language?"
    })
    print("User response:", response.get("result", {}).get("response", ""))

def test_file_content_prompt():
    """Test getting file content from user."""
    print("\n=== Testing get_file_content ===")
    response = send_mcp_request("get_file_content", {
        "path": "test_file.txt"
    })
    print("Result:", response.get("result", {}))

def test_file_overwrite_confirm():
    """Test confirming file overwrite."""
    print("\n=== Testing confirm_overwrite ===")
    
    # First create a test file
    send_mcp_request("write", {
        "path": "test_overwrite.txt",
        "content": "This is a test file that might be overwritten."
    })
    
    # Now test overwrite confirmation
    response = send_mcp_request("confirm_overwrite", {
        "path": "test_overwrite.txt"
    })
    print("Overwrite confirmed:", response.get("result", {}).get("confirmed", False))

def test_select_file():
    """Test file selection."""
    print("\n=== Testing select_file ===")
    response = send_mcp_request("select_file", {
        "path": ".",
        "pattern": "*.md"
    })
    print("Selected file:", response.get("result", {}).get("file", ""))

def test_project_init():
    """Test project initialization."""
    print("\n=== Testing init_project ===")
    response = send_mcp_request("init_project")
    print("Project initialization result:", response.get("result", {}))

def test_interactive_write():
    """Test interactive file writing."""
    print("\n=== Testing interactive_write ===")
    response = send_mcp_request("interactive_write", {
        "path": "interactive_test.txt"
    })
    print("Write result:", response.get("result", ""))

def main():
    """Run all tests."""
    try:
        # Test all prompt functionality
        test_get_prompt_types()
        test_custom_prompt()
        test_file_content_prompt()
        test_file_overwrite_confirm()
        test_select_file()
        test_interactive_write()
        test_project_init()
        
        print("\n=== All tests completed ===")
    except Exception as e:
        print(f"Error during tests: {str(e)}")

if __name__ == "__main__":
    main()
