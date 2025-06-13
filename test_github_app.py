#!/usr/bin/env python3
"""
Test script for GitHub App authentication in fastfs-mcp.

This script tests the GitHub App authentication functionality
by generating a JWT token and exchanging it for an installation
access token.

Usage:
    python test_github_app.py

Environment variables required:
    GITHUB_APP_ID - The GitHub App ID
    
And either:
    GITHUB_APP_PRIVATE_KEY - The GitHub App private key (PEM format)
    
Or:
    GITHUB_APP_PRIVATE_KEY_PATH - Path to the private key file (PEM format)
    
Optional:
    GITHUB_APP_INSTALLATION_ID - The installation ID
"""

import os
import sys
import json
from git_tools import generate_jwt, get_installation_token, get_private_key

def test_github_app_auth():
    """Test GitHub App authentication."""
    # Check if required environment variables are set
    github_app_id = os.environ.get('GITHUB_APP_ID')
    github_app_private_key = os.environ.get('GITHUB_APP_PRIVATE_KEY')
    github_app_private_key_path = os.environ.get('GITHUB_APP_PRIVATE_KEY_PATH')
    
    if not github_app_id:
        print("Error: GITHUB_APP_ID environment variable must be set.")
        sys.exit(1)
    
    if not github_app_private_key and not github_app_private_key_path:
        print("Error: Either GITHUB_APP_PRIVATE_KEY or GITHUB_APP_PRIVATE_KEY_PATH environment variable must be set.")
        sys.exit(1)
    
    # Test private key retrieval
    try:
        private_key = get_private_key()
        print("✅ Private key retrieved successfully.")
        print(f"Private key length: {len(private_key)} characters")
    except Exception as e:
        print(f"❌ Failed to retrieve private key: {str(e)}")
        sys.exit(1)
    
    # Test JWT generation
    try:
        jwt_token = generate_jwt()
        print("✅ JWT token generated successfully.")
        print(f"JWT token: {jwt_token[:10]}...{jwt_token[-10:]}")
    except Exception as e:
        print(f"❌ Failed to generate JWT token: {str(e)}")
        sys.exit(1)
    
    # Test installation token generation
    try:
        success, result = get_installation_token()
        if success:
            print("✅ Installation token obtained successfully.")
            print(f"Token: {result[:10]}...{result[-10:]}")
        else:
            print(f"❌ Failed to get installation token: {result}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Exception during installation token retrieval: {str(e)}")
        sys.exit(1)
    
    print("\n✅ All GitHub App authentication tests passed!")

if __name__ == "__main__":
    test_github_app_auth()
