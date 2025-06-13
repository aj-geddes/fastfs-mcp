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
    GITHUB_APP_PRIVATE_KEY - The GitHub App private key (PEM format)
    GITHUB_APP_INSTALLATION_ID - (Optional) The installation ID
"""

import os
import sys
import json
from git_tools import generate_jwt, get_installation_token

def test_github_app_auth():
    """Test GitHub App authentication."""
    # Check if required environment variables are set
    github_app_id = os.environ.get('GITHUB_APP_ID')
    github_app_private_key = os.environ.get('GITHUB_APP_PRIVATE_KEY')
    
    if not github_app_id or not github_app_private_key:
        print("Error: GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY environment variables must be set.")
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
