#!/usr/bin/env python3
"""
Enhanced SSH authentication for PyGit2 implementation.

This module provides improved SSH authentication handling for Git operations,
including support for multiple SSH keys, agent-based authentication, and
more robust error handling.
"""

import os
import sys
import tempfile
import subprocess
import shutil
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    import pygit2
except ImportError:
    print("Error: PyGit2 is not installed. Please install it with 'pip install pygit2'", file=sys.stderr)
    sys.exit(1)

# Import logging helpers
from pygit2_tools import log_debug, log_error

class SSHCredential:
    """
    Manages SSH credentials for Git operations.
    
    This class provides utilities for creating and managing SSH credentials
    for Git operations, including support for different authentication methods.
    """
    
    def __init__(self, username: str = "git",
                public_key_path: Optional[str] = None,
                private_key_path: Optional[str] = None,
                passphrase: str = "",
                agent_socket_path: Optional[str] = None):
        """
        Initialize SSH credential.
        
        Args:
            username: SSH username (default: git)
            public_key_path: Path to SSH public key file
            private_key_path: Path to SSH private key file
            passphrase: Passphrase for SSH private key
            agent_socket_path: Path to SSH agent socket
        """
        self.username = username
        self.public_key_path = public_key_path
        self.private_key_path = private_key_path
        self.passphrase = passphrase
        self.agent_socket_path = agent_socket_path
        
        # Temporary files for SSH keys provided as content
        self.temp_files = []
    
    @classmethod
    def from_key_content(cls, private_key_content: str, 
                        public_key_content: Optional[str] = None,
                        username: str = "git",
                        passphrase: str = "") -> 'SSHCredential':
        """
        Create SSH credential from key content.
        
        Args:
            private_key_content: SSH private key content
            public_key_content: SSH public key content
            username: SSH username (default: git)
            passphrase: Passphrase for SSH private key
            
        Returns:
            SSH credential
        """
        # Create temporary file for private key
        private_key_file = tempfile.NamedTemporaryFile(delete=False)
        private_key_file.write(private_key_content.encode())
        private_key_file.close()
        
        # Set appropriate permissions
        os.chmod(private_key_file.name, 0o600)
        
        # Create temporary file for public key if provided
        public_key_file = None
        if public_key_content:
            public_key_file = tempfile.NamedTemporaryFile(delete=False)
            public_key_file.write(public_key_content.encode())
            public_key_file.close()
        
        # Create credential
        credential = cls(
            username=username,
            public_key_path=public_key_file.name if public_key_file else None,
            private_key_path=private_key_file.name,
            passphrase=passphrase
        )
        
        # Keep track of temporary files
        credential.temp_files.append(private_key_file.name)
        if public_key_file:
            credential.temp_files.append(public_key_file.name)
        
        return credential
    
    @classmethod
    def from_agent(cls, username: str = "git") -> 'SSHCredential':
        """
        Create SSH credential using SSH agent.
        
        Args:
            username: SSH username (default: git)
            
        Returns:
            SSH credential
        """
        # Get SSH agent socket
        agent_socket_path = os.environ.get("SSH_AUTH_SOCK")
        if not agent_socket_path:
            raise ValueError("SSH agent socket not found in environment")
        
        # Create credential
        return cls(
            username=username,
            agent_socket_path=agent_socket_path
        )
    
    @classmethod
    def from_default_key(cls, username: str = "git") -> 'SSHCredential':
        """
        Create SSH credential using default SSH key.
        
        Args:
            username: SSH username (default: git)
            
        Returns:
            SSH credential
        """
        # Check for default SSH key
        home_dir = os.path.expanduser("~")
        private_key_path = os.path.join(home_dir, ".ssh", "id_rsa")
        public_key_path = os.path.join(home_dir, ".ssh", "id_rsa.pub")
        
        if not os.path.exists(private_key_path):
            # Try id_ed25519
            private_key_path = os.path.join(home_dir, ".ssh", "id_ed25519")
            public_key_path = os.path.join(home_dir, ".ssh", "id_ed25519.pub")
            
            if not os.path.exists(private_key_path):
                raise ValueError("Default SSH key not found")
        
        # Create credential
        return cls(
            username=username,
            public_key_path=public_key_path if os.path.exists(public_key_path) else None,
            private_key_path=private_key_path
        )
    
    def get_credential_callback(self) -> callable:
        """
        Get pygit2 credential callback.
        
        Returns:
            Credential callback function
        """
        def credentials_cb(url, username_from_url, allowed_types):
            # Check for SSH key authentication
            if self.private_key_path:
                if allowed_types & pygit2.CredentialType.SSH_KEY:
                    return pygit2.Keypair(
                        self.username if not username_from_url else username_from_url,
                        self.public_key_path,
                        self.private_key_path,
                        self.passphrase
                    )
            # Check for SSH agent authentication
            elif self.agent_socket_path:
                if allowed_types & pygit2.CredentialType.SSH_KEY:
                    return pygit2.KeypairFromAgent(
                        self.username if not username_from_url else username_from_url
                    )
            
            # Fallback to default username
            if allowed_types & pygit2.CredentialType.USERNAME:
                return pygit2.Username(self.username)
            
            raise ValueError(f"No suitable authentication method found for {url}")
        
        return credentials_cb
    
    def create_remote_callbacks(self) -> pygit2.RemoteCallbacks:
        """
        Create remote callbacks for Git operations.
        
        Returns:
            RemoteCallbacks object
        """
        return pygit2.RemoteCallbacks(credentials=self.get_credential_callback())
    
    def cleanup(self) -> None:
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file)
            except:
                pass
        
        self.temp_files = []
    
    def __del__(self) -> None:
        """Destructor to clean up temporary files."""
        self.cleanup()

class SSHConfig:
    """
    Manages SSH configuration for Git operations.
    
    This class provides utilities for creating and managing SSH configurations
    for Git operations, including support for custom SSH options.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize SSH configuration.
        
        Args:
            config_path: Path to SSH config file
        """
        self.config_path = config_path or os.path.expanduser("~/.ssh/config")
        self.temp_config = None
    
    def create_temp_config(self, host: str, options: Dict[str, str]) -> str:
        """
        Create temporary SSH config file.
        
        Args:
            host: Host pattern
            options: SSH options
            
        Returns:
            Path to temporary config file
        """
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        
        # Write base config if exists
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                temp_file.write(f.read().encode())
        
        # Write custom host config
        temp_file.write(f"\nHost {host}\n".encode())
        for key, value in options.items():
            temp_file.write(f"    {key} {value}\n".encode())
        
        temp_file.close()
        
        # Store temp config path
        self.temp_config = temp_file.name
        
        return temp_file.name
    
    def get_ssh_command(self, config_file: Optional[str] = None) -> str:
        """
        Get SSH command with config file.
        
        Args:
            config_file: Path to SSH config file
            
        Returns:
            SSH command
        """
        config_path = config_file or self.temp_config or self.config_path
        
        if config_path and os.path.exists(config_path):
            return f"ssh -F {config_path}"
        
        return "ssh"
    
    def cleanup(self) -> None:
        """Clean up temporary config file."""
        if self.temp_config and os.path.exists(self.temp_config):
            try:
                os.remove(self.temp_config)
            except:
                pass
            
            self.temp_config = None
    
    def __del__(self) -> None:
        """Destructor to clean up temporary config file."""
        self.cleanup()

class SSHKeyManager:
    """
    Manages SSH keys for Git operations.
    
    This class provides utilities for generating, importing, and managing
    SSH keys for Git operations.
    """
    
    @staticmethod
    def generate_key(key_type: str = "rsa", bits: int = 4096, 
                    comment: str = "PyGit2 SSH Key", passphrase: str = "",
                    output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a new SSH key pair.
        
        Args:
            key_type: SSH key type (rsa, ed25519, ecdsa)
            bits: Key size in bits (for RSA and ECDSA)
            comment: Key comment
            passphrase: Key passphrase
            output_dir: Output directory
            
        Returns:
            Dictionary with key information
        """
        try:
            # Determine output directory
            if not output_dir:
                output_dir = tempfile.mkdtemp(prefix="ssh_key_")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Determine key parameters
            key_params = []
            if key_type == "rsa":
                key_params = ["-t", "rsa", "-b", str(bits)]
            elif key_type == "ed25519":
                key_params = ["-t", "ed25519"]
            elif key_type == "ecdsa":
                key_params = ["-t", "ecdsa", "-b", str(bits)]
            else:
                return {
                    "success": False,
                    "message": f"Invalid key type: {key_type}"
                }
            
            # Determine key file paths
            key_file = os.path.join(output_dir, "id_" + key_type)
            
            # Generate key
            cmd = ["ssh-keygen", "-f", key_file, "-C", comment, "-N", passphrase]
            cmd.extend(key_params)
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "message": f"Key generation failed: {process.stderr.strip()}",
                    "error": process.stderr.strip()
                }
            
            # Read generated keys
            private_key = None
            public_key = None
            
            with open(key_file, 'r') as f:
                private_key = f.read()
            
            with open(key_file + ".pub", 'r') as f:
                public_key = f.read()
            
            return {
                "success": True,
                "message": "Successfully generated SSH key pair",
                "key_type": key_type,
                "bits": bits,
                "comment": comment,
                "private_key_path": key_file,
                "public_key_path": key_file + ".pub",
                "private_key": private_key,
                "public_key": public_key
            }
        except Exception as e:
            log_error(f"Error generating SSH key: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }
    
    @staticmethod
    def import_key(private_key: str, public_key: Optional[str] = None,
                  output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Import SSH key pair.
        
        Args:
            private_key: Private key content or file path
            public_key: Public key content or file path
            output_dir: Output directory
            
        Returns:
            Dictionary with key information
        """
        try:
            # Determine output directory
            if not output_dir:
                output_dir = tempfile.mkdtemp(prefix="ssh_key_")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Determine key type
            if os.path.exists(private_key):
                # Read private key from file
                with open(private_key, 'r') as f:
                    private_key_content = f.read()
            else:
                # Use provided content
                private_key_content = private_key
            
            # Determine key type
            key_type = "rsa"
            if "BEGIN OPENSSH PRIVATE KEY" in private_key_content:
                if "ssh-ed25519" in private_key_content:
                    key_type = "ed25519"
                elif "ecdsa-sha2" in private_key_content:
                    key_type = "ecdsa"
            
            # Determine key file paths
            key_file = os.path.join(output_dir, "id_" + key_type)
            
            # Write private key
            with open(key_file, 'w') as f:
                f.write(private_key_content)
            
            # Set appropriate permissions
            os.chmod(key_file, 0o600)
            
            # Write public key if provided
            if public_key:
                if os.path.exists(public_key):
                    # Copy public key file
                    shutil.copy2(public_key, key_file + ".pub")
                else:
                    # Write public key content
                    with open(key_file + ".pub", 'w') as f:
                        f.write(public_key)
            else:
                # Generate public key from private key
                process = subprocess.run(
                    ["ssh-keygen", "-y", "-f", key_file],
                    capture_output=True,
                    text=True
                )
                
                if process.returncode == 0:
                    with open(key_file + ".pub", 'w') as f:
                        f.write(process.stdout.strip())
                        f.write("\n")
                else:
                    log_error(f"Failed to generate public key: {process.stderr.strip()}")
            
            # Get public key content
            public_key_content = None
            if os.path.exists(key_file + ".pub"):
                with open(key_file + ".pub", 'r') as f:
                    public_key_content = f.read()
            
            return {
                "success": True,
                "message": "Successfully imported SSH key pair",
                "key_type": key_type,
                "private_key_path": key_file,
                "public_key_path": key_file + ".pub" if public_key_content else None,
                "private_key": private_key_content,
                "public_key": public_key_content
            }
        except Exception as e:
            log_error(f"Error importing SSH key: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }
    
    @staticmethod
    def verify_key(private_key_path: str, public_key_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify SSH key pair.
        
        Args:
            private_key_path: Path to private key file
            public_key_path: Path to public key file
            
        Returns:
            Dictionary with verification results
        """
        try:
            # Check if private key exists
            if not os.path.exists(private_key_path):
                return {
                    "success": False,
                    "message": f"Private key file '{private_key_path}' does not exist"
                }
            
            # Verify private key
            process = subprocess.run(
                ["ssh-keygen", "-l", "-f", private_key_path],
                capture_output=True,
                text=True
            )
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "message": f"Invalid private key: {process.stderr.strip()}",
                    "error": process.stderr.strip()
                }
            
            private_key_fingerprint = process.stdout.strip()
            
            # Verify public key if provided
            if public_key_path and os.path.exists(public_key_path):
                process = subprocess.run(
                    ["ssh-keygen", "-l", "-f", public_key_path],
                    capture_output=True,
                    text=True
                )
                
                if process.returncode != 0:
                    return {
                        "success": False,
                        "message": f"Invalid public key: {process.stderr.strip()}",
                        "error": process.stderr.strip()
                    }
                
                public_key_fingerprint = process.stdout.strip()
                
                # Compare fingerprints
                if private_key_fingerprint != public_key_fingerprint:
                    return {
                        "success": False,
                        "message": "Private and public key fingerprints do not match",
                        "private_key_fingerprint": private_key_fingerprint,
                        "public_key_fingerprint": public_key_fingerprint
                    }
            
            # Extract key information
            key_info = private_key_fingerprint.split()
            bits = key_info[0] if len(key_info) > 0 else None
            fingerprint = key_info[1] if len(key_info) > 1 else None
            
            return {
                "success": True,
                "message": "SSH key pair is valid",
                "fingerprint": fingerprint,
                "bits": bits,
                "private_key_path": private_key_path,
                "public_key_path": public_key_path
            }
        except Exception as e:
            log_error(f"Error verifying SSH key: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }
    
    @staticmethod
    def test_connection(host: str, port: int = 22, username: str = "git",
                      private_key_path: Optional[str] = None,
                      timeout: int = 10) -> Dict[str, Any]:
        """
        Test SSH connection.
        
        Args:
            host: Host to connect to
            port: Port to connect to
            username: Username to use
            private_key_path: Path to private key file
            timeout: Connection timeout in seconds
            
        Returns:
            Dictionary with test results
        """
        try:
            # Build SSH command
            cmd = ["ssh", "-T", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={timeout}"]
            
            if private_key_path:
                cmd.extend(["-i", private_key_path])
            
            cmd.extend(["-p", str(port), f"{username}@{host}"])
            
            # Execute SSH command
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # Check exit code
            success = process.returncode == 0 or process.returncode == 1
            
            return {
                "success": success,
                "message": "SSH connection test " + ("successful" if success else "failed"),
                "exit_code": process.returncode,
                "stdout": process.stdout.strip(),
                "stderr": process.stderr.strip()
            }
        except Exception as e:
            log_error(f"Error testing SSH connection: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }
