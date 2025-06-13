#!/usr/bin/env python3
import os
import sys
import subprocess
import signal
import json
import shutil
import stat
import glob
from typing import Dict, List, Optional, Any, Union
from fastmcp import FastMCP

# Import git tools
from git_tools import (
    git_clone, git_init, git_add, git_commit, git_status, git_push, git_pull,
    git_log, git_checkout, git_branch, git_merge, git_show, git_diff, git_remote,
    git_rev_parse, git_ls_files, git_describe, git_rebase, git_stash, git_reset,
    git_clean, git_tag, git_config, git_fetch, git_blame, git_grep, git_context,
    git_head, git_version, git_validate, git_repo_info, git_summarize_log,
    git_suggest_commit, git_audit_history
)

# Print startup message
print("[fastfs-mcp] Server starting...", file=sys.stderr, flush=True)

# Set the default workspace directory to the parent directory
WORKSPACE_DIR = "/mnt/workspace"
if os.path.exists(WORKSPACE_DIR):
    os.chdir(WORKSPACE_DIR)
    print(f"[fastfs-mcp] Working directory set to {WORKSPACE_DIR}", file=sys.stderr, flush=True)
else:
    current_dir = os.getcwd()
    print(f"[fastfs-mcp] Warning: {WORKSPACE_DIR} not found, using current directory: {current_dir}", file=sys.stderr, flush=True)

# Initialize the MCP server
mcp = FastMCP(name="fastfs-mcp")

def run_command(cmd: str, input_text: Optional[str] = None) -> str:
    """Execute a shell command and return its output."""
    try:
        print(f"[DEBUG] Running command: {cmd}", file=sys.stderr, flush=True)
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            input=input_text
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"[ERROR] Command failed: {result.stderr}", file=sys.stderr, flush=True)
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        print(f"[ERROR] Exception running command: {str(e)}", file=sys.stderr, flush=True)
        return f"Exception: {str(e)}"

# Define tool schemas with proper typing and input validation
@mcp.tool(description="List files and directories at a given path.")
def ls(path: str = ".") -> List[str]:
    """List files and directories at a given path."""
    try:
        print(f"[DEBUG] ls called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return [f"Error: Path '{path}' does not exist"]
        return os.listdir(path)
    except Exception as e:
        print(f"[ERROR] ls failed: {str(e)}", file=sys.stderr, flush=True)
        return [f"Error: {str(e)}"]

@mcp.tool(description="Print the current working directory.")
def pwd() -> str:
    """Print the current working directory."""
    try:
        print(f"[DEBUG] pwd called", file=sys.stderr, flush=True)
        return os.getcwd()
    except Exception as e:
        print(f"[ERROR] pwd failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Change the current working directory.")
def cd(path: str) -> str:
    """Change the current working directory."""
    try:
        print(f"[DEBUG] cd called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist"
        if not os.path.isdir(path):
            return f"Error: '{path}' is not a directory"
        
        os.chdir(path)
        return f"Changed directory to {os.getcwd()}"
    except Exception as e:
        print(f"[ERROR] cd failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Read the contents of a file.")
def read(path: str) -> str:
    """Read the contents of a file."""
    try:
        print(f"[DEBUG] read called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist"
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file"
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] read failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Write contents to a file.")
def write(path: str, content: str = "") -> str:
    """Write contents to a file."""
    try:
        print(f"[DEBUG] write called with path: {path}", file=sys.stderr, flush=True)
        # Create directory if it doesn't exist
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully written to {path}"
    except Exception as e:
        print(f"[ERROR] write failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Search for a pattern in a file.")
def grep(pattern: str, path: str) -> str:
    """Search for a pattern in a file."""
    if not os.path.exists(path):
        return f"Error: File '{path}' does not exist"
    if not os.path.isfile(path):
        return f"Error: '{path}' is not a file"
    
    # Escape the pattern to avoid shell injection
    escaped_pattern = pattern.replace("'", "'\\''")
    cmd = f"grep -n '{escaped_pattern}' {path}"
    result = run_command(cmd)
    
    if not result:
        return f"No matches found for pattern '{pattern}' in file '{path}'"
    return result

@mcp.tool(description="Locate a command in the system path.")
def which(command: str) -> str:
    """Locate a command in the system path."""
    # Escape the command to avoid shell injection
    escaped_command = command.replace("'", "'\\''")
    result = run_command(f"which '{escaped_command}'")
    
    if not result or "not found" in result.lower():
        return f"Command '{command}' not found in PATH"
    return result

@mcp.tool(description="Use sed to transform file content using stream editing.")
def sed(script: str, path: str) -> str:
    """Use sed to transform file content using stream editing."""
    if not os.path.exists(path):
        return f"Error: File '{path}' does not exist"
    if not os.path.isfile(path):
        return f"Error: '{path}' is not a file"
    
    # Escape the script to avoid shell injection
    escaped_script = script.replace("'", "'\\''")
    cmd = f"sed '{escaped_script}' {path}"
    result = run_command(cmd)
    
    if not result:
        return f"No output from sed command with script '{script}' on file '{path}'"
    return result

@mcp.tool(description="Use gawk to process file content using AWK scripting.")
def gawk(script: str, path: str) -> str:
    """Use gawk to process file content using AWK scripting."""
    if not os.path.exists(path):
        return f"Error: File '{path}' does not exist"
    if not os.path.isfile(path):
        return f"Error: '{path}' is not a file"
    
    # Escape the script to avoid shell injection
    escaped_script = script.replace("'", "'\\''")
    cmd = f"gawk '{escaped_script}' {path}"
    result = run_command(cmd)
    
    if not result:
        return f"No output from gawk command with script '{script}' on file '{path}'"
    return result

# ===== ADDITIONAL FILESYSTEM TOOLS =====

@mcp.tool(description="Display file status (metadata).")
def stat(path: str) -> Dict[str, Any]:
    """Display file status and metadata."""
    try:
        print(f"[DEBUG] stat called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"Path '{path}' does not exist"}
        
        st = os.stat(path)
        result = {
            "path": path,
            "size": st.st_size,
            "mode": stat.filemode(st.st_mode),
            "mode_octal": oct(st.st_mode)[-3:],
            "inode": st.st_ino,
            "device": st.st_dev,
            "links": st.st_nlink,
            "uid": st.st_uid,
            "gid": st.st_gid,
            "access_time": st.st_atime,
            "modification_time": st.st_mtime,
            "change_time": st.st_ctime,
            "is_file": os.path.isfile(path),
            "is_dir": os.path.isdir(path),
            "is_link": os.path.islink(path)
        }
        return result
    except Exception as e:
        print(f"[ERROR] stat failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Display directory tree structure.")
def tree(path: str = ".", depth: int = 3) -> str:
    """Display directory tree structure."""
    try:
        print(f"[DEBUG] tree called with path: {path}, depth: {depth}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist"
        
        # Escape path for shell command
        escaped_path = path.replace("'", "'\\''")
        cmd = f"tree -L {depth} '{escaped_path}'"
        result = run_command(cmd)
        
        if not result:
            return f"No output from tree command on path '{path}'"
        return result
    except Exception as e:
        print(f"[ERROR] tree failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Find files by pattern.")
def find(path: str = ".", pattern: str = "*", file_type: str = None, max_depth: int = None) -> List[str]:
    """Find files by pattern and other criteria."""
    try:
        print(f"[DEBUG] find called with path: {path}, pattern: {pattern}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return [f"Error: Path '{path}' does not exist"]
        
        # Build find command
        cmd_parts = ["find", path]
        if max_depth is not None:
            cmd_parts.extend(["-maxdepth", str(max_depth)])
        if file_type:
            if file_type in ['f', 'd', 'l', 'b', 'c', 'p', 's']:
                cmd_parts.extend(["-type", file_type])
            else:
                return [f"Error: Invalid file type '{file_type}'"]
        cmd_parts.extend(["-name", pattern])
        
        # Join and escape the command
        cmd = " ".join(f"'{p}'" if ' ' in p else p for p in cmd_parts)
        result = run_command(cmd)
        
        if not result:
            return []
        return result.split('\n')
    except Exception as e:
        print(f"[ERROR] find failed: {str(e)}", file=sys.stderr, flush=True)
        return [f"Error: {str(e)}"]

@mcp.tool(description="Copy files or directories.")
def cp(source: str, destination: str, recursive: bool = False) -> str:
    """Copy files or directories."""
    try:
        print(f"[DEBUG] cp called with source: {source}, destination: {destination}", file=sys.stderr, flush=True)
        if not os.path.exists(source):
            return f"Error: Source '{source}' does not exist"
        
        if os.path.isdir(source) and not recursive:
            return f"Error: Source '{source}' is a directory, use recursive=True to copy directories"
        
        if recursive:
            shutil.copytree(source, destination)
            return f"Successfully copied directory '{source}' to '{destination}'"
        else:
            shutil.copy2(source, destination)
            return f"Successfully copied file '{source}' to '{destination}'"
    except Exception as e:
        print(f"[ERROR] cp failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Move or rename files or directories.")
def mv(source: str, destination: str) -> str:
    """Move or rename files or directories."""
    try:
        print(f"[DEBUG] mv called with source: {source}, destination: {destination}", file=sys.stderr, flush=True)
        if not os.path.exists(source):
            return f"Error: Source '{source}' does not exist"
        
        shutil.move(source, destination)
        return f"Successfully moved '{source}' to '{destination}'"
    except Exception as e:
        print(f"[ERROR] mv failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Remove files or directories.")
def rm(path: str, recursive: bool = False, force: bool = False) -> str:
    """Remove files or directories."""
    try:
        print(f"[DEBUG] rm called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            if force:
                return f"Warning: Path '{path}' does not exist, nothing removed"
            else:
                return f"Error: Path '{path}' does not exist"
        
        if os.path.isdir(path):
            if not recursive:
                return f"Error: '{path}' is a directory, use recursive=True to remove directories"
            shutil.rmtree(path)
            return f"Successfully removed directory '{path}'"
        else:
            os.remove(path)
            return f"Successfully removed file '{path}'"
    except Exception as e:
        print(f"[ERROR] rm failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Create a new empty file or update its timestamp.")
def touch(path: str) -> str:
    """Create a new empty file or update its timestamp."""
    try:
        print(f"[DEBUG] touch called with path: {path}", file=sys.stderr, flush=True)
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(path, 'a'):
            os.utime(path, None)
        return f"Successfully touched '{path}'"
    except Exception as e:
        print(f"[ERROR] touch failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Create a new directory.")
def mkdir(path: str, parents: bool = False) -> str:
    """Create a new directory."""
    try:
        print(f"[DEBUG] mkdir called with path: {path}", file=sys.stderr, flush=True)
        if os.path.exists(path):
            return f"Error: Path '{path}' already exists"
        
        if parents:
            os.makedirs(path)
        else:
            os.mkdir(path)
        return f"Successfully created directory '{path}'"
    except Exception as e:
        print(f"[ERROR] mkdir failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Show disk usage of a directory.")
def du(path: str = ".", human_readable: bool = True, max_depth: int = 1) -> str:
    """Show disk usage of a directory."""
    try:
        print(f"[DEBUG] du called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist"
        
        # Escape path for shell command
        escaped_path = path.replace("'", "'\\''")
        cmd = f"du -{'h' if human_readable else ''}d {max_depth} '{escaped_path}'"
        result = run_command(cmd)
        
        if not result:
            return f"No output from du command on path '{path}'"
        return result
    except Exception as e:
        print(f"[ERROR] du failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Show disk space and usage.")
def df(human_readable: bool = True) -> str:
    """Show disk space and usage."""
    try:
        print(f"[DEBUG] df called", file=sys.stderr, flush=True)
        cmd = f"df {'-h' if human_readable else ''}"
        result = run_command(cmd)
        
        if not result:
            return "No output from df command"
        return result
    except Exception as e:
        print(f"[ERROR] df failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Change file mode (permissions).")
def chmod(path: str, mode: str) -> str:
    """Change file mode (permissions)."""
    try:
        print(f"[DEBUG] chmod called with path: {path}, mode: {mode}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist"
        
        # Parse mode (both octal like "755" and symbolic like "u+x" are supported)
        if mode.isdigit() and len(mode) <= 4:
            mode_int = int(mode, 8)
            os.chmod(path, mode_int)
        else:
            # For symbolic mode, use chmod command
            escaped_path = path.replace("'", "'\\''")
            cmd = f"chmod {mode} '{escaped_path}'"
            run_command(cmd)
            
        return f"Successfully changed mode of '{path}' to {mode}"
    except Exception as e:
        print(f"[ERROR] chmod failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Change file owner and group.")
def chown(path: str, owner: str, group: Optional[str] = None) -> str:
    """Change file owner and group."""
    try:
        print(f"[DEBUG] chown called with path: {path}, owner: {owner}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist"
        
        # Use chown command as Python's os.chown requires numeric IDs
        owner_group = owner if group is None else f"{owner}:{group}"
        escaped_path = path.replace("'", "'\\''")
        cmd = f"chown {owner_group} '{escaped_path}'"
        result = run_command(cmd)
        
        if "error" in result.lower():
            return result
        return f"Successfully changed owner of '{path}' to {owner_group}"
    except Exception as e:
        print(f"[ERROR] chown failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Concatenate and display file contents.")
def cat(paths: List[str]) -> str:
    """Concatenate and display file contents."""
    try:
        print(f"[DEBUG] cat called with paths: {paths}", file=sys.stderr, flush=True)
        result = ""
        
        for path in paths:
            if not os.path.exists(path):
                return f"Error: File '{path}' does not exist"
            if not os.path.isfile(path):
                return f"Error: '{path}' is not a file"
            
            with open(path, 'r', encoding='utf-8') as f:
                result += f.read()
                
        return result
    except Exception as e:
        print(f"[ERROR] cat failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Display the first part of files.")
def head(path: str, lines: int = 10) -> str:
    """Display the first part of files."""
    try:
        print(f"[DEBUG] head called with path: {path}, lines: {lines}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist"
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file"
        
        with open(path, 'r', encoding='utf-8') as f:
            result = ''.join(f.readline() for _ in range(lines))
            
        return result
    except Exception as e:
        print(f"[ERROR] head failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Display the last part of files.")
def tail(path: str, lines: int = 10) -> str:
    """Display the last part of files."""
    try:
        print(f"[DEBUG] tail called with path: {path}, lines: {lines}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist"
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file"
        
        # Using the tail command for efficiency with large files
        escaped_path = path.replace("'", "'\\''")
        cmd = f"tail -n {lines} '{escaped_path}'"
        result = run_command(cmd)
        
        if not result:
            return f"No output from tail command on file '{path}'"
        return result
    except Exception as e:
        print(f"[ERROR] tail failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Print the resolved path of a symbolic link.")
def readlink(path: str) -> str:
    """Print the resolved path of a symbolic link."""
    try:
        print(f"[DEBUG] readlink called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist"
        if not os.path.islink(path):
            return f"Error: '{path}' is not a symbolic link"
        
        return os.readlink(path)
    except Exception as e:
        print(f"[ERROR] readlink failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Print the resolved absolute path.")
def realpath(path: str) -> str:
    """Print the resolved absolute path."""
    try:
        print(f"[DEBUG] realpath called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist"
        
        return os.path.realpath(path)
    except Exception as e:
        print(f"[ERROR] realpath failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

# ===== TEXT MANIPULATION TOOLS =====

@mcp.tool(description="Select specific columns from each line.")
def cut(path: str, delimiter: str = '\t', fields: str = '1') -> str:
    """Select specific columns from each line."""
    try:
        print(f"[DEBUG] cut called with path: {path}, delimiter: {delimiter}, fields: {fields}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist"
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file"
        
        # Escape for shell command
        escaped_path = path.replace("'", "'\\''")
        escaped_delimiter = delimiter.replace("'", "'\\''")
        cmd = f"cut -d'{escaped_delimiter}' -f{fields} '{escaped_path}'"
        result = run_command(cmd)
        
        if not result:
            return f"No output from cut command on file '{path}'"
        return result
    except Exception as e:
        print(f"[ERROR] cut failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Sort lines of text files.")
def sort(path: str, reverse: bool = False, numeric: bool = False, field: Optional[int] = None) -> str:
    """Sort lines of text files."""
    try:
        print(f"[DEBUG] sort called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist"
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file"
        
        # Build sort options
        options = []
        if reverse:
            options.append('-r')
        if numeric:
            options.append('-n')
        if field is not None:
            options.append(f'-k{field}')
        
        # Escape for shell command
        escaped_path = path.replace("'", "'\\''")
        cmd = f"sort {' '.join(options)} '{escaped_path}'"
        result = run_command(cmd)
        
        if not result:
            return f"No output from sort command on file '{path}'"
        return result
    except Exception as e:
        print(f"[ERROR] sort failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Report or filter out repeated lines.")
def uniq(path: str, count: bool = False, repeated: bool = False, ignore_case: bool = False) -> str:
    """Report or filter out repeated lines."""
    try:
        print(f"[DEBUG] uniq called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist"
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file"
        
        # Build uniq options
        options = []
        if count:
            options.append('-c')
        if repeated:
            options.append('-d')
        if ignore_case:
            options.append('-i')
        
        # Escape for shell command
        escaped_path = path.replace("'", "'\\''")
        cmd = f"uniq {' '.join(options)} '{escaped_path}'"
        result = run_command(cmd)
        
        if not result:
            return f"No output from uniq command on file '{path}'"
        return result
    except Exception as e:
        print(f"[ERROR] uniq failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Print line, word, and byte counts.")
def wc(path: str, lines: bool = True, words: bool = True, bytes: bool = True) -> Dict[str, int]:
    """Print line, word, and byte counts."""
    try:
        print(f"[DEBUG] wc called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"File '{path}' does not exist"}
        if not os.path.isfile(path):
            return {"error": f"'{path}' is not a file"}
        
        result = {}
        
        # Count lines if requested
        if lines:
            with open(path, 'r', encoding='utf-8') as f:
                result["lines"] = sum(1 for _ in f)
        
        # Count words if requested
        if words:
            with open(path, 'r', encoding='utf-8') as f:
                result["words"] = sum(len(line.split()) for line in f)
        
        # Count bytes if requested
        if bytes:
            result["bytes"] = os.path.getsize(path)
            
        return result
    except Exception as e:
        print(f"[ERROR] wc failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Number lines in a file.")
def nl(path: str, number_empty: bool = True, number_format: str = '%6d  ') -> str:
    """Number lines in a file."""
    try:
        print(f"[DEBUG] nl called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist"
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file"
        
        # Number lines
        result = []
        with open(path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if number_empty or line.strip():
                    result.append(number_format % i + line)
                else:
                    result.append(line)
        
        return ''.join(result)
    except Exception as e:
        print(f"[ERROR] nl failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Split a file into smaller parts.")
def split(path: str, prefix: str = 'x', lines: Optional[int] = 1000, bytes_size: Optional[str] = None) -> str:
    """Split a file into smaller parts."""
    try:
        print(f"[DEBUG] split called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist"
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file"
        
        # Build split options
        options = []
        if lines is not None:
            options.append(f'-l {lines}')
        if bytes_size is not None:
            options.append(f'-b {bytes_size}')
        
        # Escape for shell command
        escaped_path = path.replace("'", "'\\''")
        escaped_prefix = prefix.replace("'", "'\\''")
        cmd = f"split {' '.join(options)} '{escaped_path}' '{escaped_prefix}'"
        result = run_command(cmd)
        
        # List the created files
        files = glob.glob(f"{prefix}*")
        return f"Successfully split '{path}' into {len(files)} parts with prefix '{prefix}'"
    except Exception as e:
        print(f"[ERROR] split failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

# ===== ARCHIVE & COMPRESSION TOOLS =====

@mcp.tool(description="Create, extract, or list tar archives.")
def tar(operation: str, archive_file: str, files: Optional[List[str]] = None, options: str = "") -> str:
    """Create, extract, or list tar archives.
    Operation: 'create', 'extract', or 'list'
    """
    try:
        print(f"[DEBUG] tar called with operation: {operation}, archive: {archive_file}", file=sys.stderr, flush=True)
        
        # Map operation to tar flag
        op_flags = {
            "create": "c",
            "extract": "x",
            "list": "t"
        }
        
        if operation not in op_flags:
            return f"Error: Invalid operation '{operation}'. Use 'create', 'extract', or 'list'."
        
        flag = op_flags[operation]
        # Always use verbose mode
        cmd = f"tar -{flag}vf"
        
        # Add compression based on file extension
        if archive_file.endswith('.gz') or archive_file.endswith('.tgz'):
            cmd += 'z'
        elif archive_file.endswith('.bz2'):
            cmd += 'j'
        elif archive_file.endswith('.xz'):
            cmd += 'J'
            
        # Add any extra options
        if options:
            cmd += f" {options}"
            
        # Escape archive filename
        escaped_archive = archive_file.replace("'", "'\\''")
        cmd += f" '{escaped_archive}'"
        
        # Add files for create operation
        if operation == "create" and files:
            file_list = []
            for f in files:
                escaped_file = f.replace("'", "'\\''")
                file_list.append(f"'{escaped_file}'")
            file_args = " ".join(file_list)
            cmd += f" {file_args}"
            
        result = run_command(cmd)
        return result or f"Successfully {operation}ed archive '{archive_file}'"
    except Exception as e:
        print(f"[ERROR] tar failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Compress or decompress files.")
def gzip(path: str, decompress: bool = False, keep: bool = False) -> str:
    """Compress or decompress files using gzip."""
    try:
        print(f"[DEBUG] gzip called with path: {path}, decompress: {decompress}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist"
        
        # Build gzip options
        options = []
        if decompress:
            options.append('-d')
        if keep:
            options.append('-k')
        
        # Escape for shell command
        escaped_path = path.replace("'", "'\\''")
        cmd = f"gzip {' '.join(options)} '{escaped_path}'"
        result = run_command(cmd)
        
        action = "Decompressed" if decompress else "Compressed"
        return result or f"Successfully {action} '{path}'"
    except Exception as e:
        print(f"[ERROR] gzip failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Create or extract zip archives.")
def zip(operation: str, archive_file: str, files: Optional[List[str]] = None, options: str = "") -> str:
    """Create or extract zip archives.
    Operation: 'create' or 'extract'
    """
    try:
        print(f"[DEBUG] zip called with operation: {operation}, archive: {archive_file}", file=sys.stderr, flush=True)
        
        if operation not in ["create", "extract"]:
            return f"Error: Invalid operation '{operation}'. Use 'create' or 'extract'."
        
        if operation == "create":
            if not files:
                return "Error: No files specified for zip creation"
            
            # Escape archive filename and files
            escaped_archive = archive_file.replace("'", "'\\''")
            file_list = []
            for f in files:
                escaped_file = f.replace("'", "'\\''")
                file_list.append(f"'{escaped_file}'")
            file_args = " ".join(file_list)
            
            cmd = f"zip {options} '{escaped_archive}' {file_args}"
            result = run_command(cmd)
            return result or f"Successfully created zip archive '{archive_file}'"
            
        else:  # extract
            if not os.path.exists(archive_file):
                return f"Error: Archive '{archive_file}' does not exist"
                
            # Escape archive filename
            escaped_archive = archive_file.replace("'", "'\\''")
            cmd = f"unzip {options} '{escaped_archive}'"
            result = run_command(cmd)
            return result or f"Successfully extracted zip archive '{archive_file}'"
    except Exception as e:
        print(f"[ERROR] zip failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

# ===== REGISTER GIT TOOLS =====

# Git Repository Operations
@mcp.tool(description="Clone a Git repository.")
def clone(repo_url: str, target_dir: Optional[str] = None, options: str = "") -> str:
    """Clone a Git repository."""
    return git_clone(repo_url, target_dir, options)

@mcp.tool(description="Initialize a new Git repository.")
def init(directory: str = ".") -> str:
    """Initialize a new Git repository."""
    return git_init(directory)

@mcp.tool(description="Add file(s) to the Git staging area.")
def add(paths: Union[str, List[str]], options: str = "") -> str:
    """Add file(s) to the Git staging area."""
    return git_add(paths, options)

@mcp.tool(description="Commit changes to the Git repository.")
def commit(message: str, options: str = "") -> str:
    """Commit changes to the Git repository."""
    return git_commit(message, options)

@mcp.tool(description="Show the working tree status.")
def status(options: str = "") -> str:
    """Show the working tree status."""
    return git_status(options)

@mcp.tool(description="Push changes to a remote repository.")
def push(remote: str = "origin", branch: str = "", options: str = "") -> str:
    """Push changes to a remote repository."""
    return git_push(remote, branch, options)

@mcp.tool(description="Pull changes from a remote repository.")
def pull(remote: str = "origin", branch: str = "", options: str = "") -> str:
    """Pull changes from a remote repository."""
    return git_pull(remote, branch, options)

@mcp.tool(description="Show commit logs.")
def log(options: str = "--oneline -n 10") -> str:
    """Show commit logs."""
    return git_log(options)

@mcp.tool(description="Switch branches or restore working tree files.")
def checkout(revision: str, options: str = "") -> str:
    """Switch branches or restore working tree files."""
    return git_checkout(revision, options)

@mcp.tool(description="List, create, or delete branches.")
def branch(options: str = "", branch_name: Optional[str] = None) -> str:
    """List, create, or delete branches."""
    return git_branch(options, branch_name)

@mcp.tool(description="Join two or more development histories together.")
def merge(branch: str, options: str = "") -> str:
    """Join two or more development histories together."""
    return git_merge(branch, options)

@mcp.tool(description="Show various types of Git objects.")
def show(object: str = "HEAD", options: str = "") -> str:
    """Show various types of Git objects."""
    return git_show(object, options)

@mcp.tool(description="Show changes between commits, commit and working tree, etc.")
def diff(options: str = "", path: Optional[str] = None) -> str:
    """Show changes between commits, commit and working tree, etc."""
    return git_diff(options, path)

@mcp.tool(description="Manage remote repositories.")
def remote(command: str = "show", name: Optional[str] = None, options: str = "") -> str:
    """Manage remote repositories."""
    return git_remote(command, name, options)

@mcp.tool(description="Pick out and massage parameters for low-level Git commands.")
def rev_parse(rev: str, options: str = "") -> str:
    """Pick out and massage parameters for low-level Git commands."""
    return git_rev_parse(rev, options)

@mcp.tool(description="Show information about files in the index and the working tree.")
def ls_files(options: str = "") -> List[str]:
    """Show information about files in the index and the working tree."""
    return git_ls_files(options)

@mcp.tool(description="Give an object a human-readable name based on available ref.")
def describe(options: str = "--tags") -> str:
    """Give an object a human-readable name based on available ref."""
    return git_describe(options)

@mcp.tool(description="Reapply commits on top of another base tip.")
def rebase(branch: str, options: str = "") -> str:
    """Reapply commits on top of another base tip."""
    return git_rebase(branch, options)

@mcp.tool(description="Stash the changes in a dirty working directory away.")
def stash(command: str = "push", options: str = "") -> str:
    """Stash the changes in a dirty working directory away."""
    return git_stash(command, options)

@mcp.tool(description="Reset current HEAD to the specified state.")
def reset(options: str = "", paths: Optional[Union[str, List[str]]] = None) -> str:
    """Reset current HEAD to the specified state."""
    return git_reset(options, paths)

@mcp.tool(description="Remove untracked files from the working tree.")
def clean(options: str = "-n") -> str:
    """Remove untracked files from the working tree."""
    return git_clean(options)

@mcp.tool(description="Create, list, delete or verify a tag object.")
def tag(tag_name: Optional[str] = None, options: str = "") -> Union[str, List[str]]:
    """Create, list, delete or verify a tag object."""
    return git_tag(tag_name, options)

@mcp.tool(description="Get or set repository or global options.")
def config(name: Optional[str] = None, value: Optional[str] = None, options: str = "") -> str:
    """Get or set repository or global options."""
    return git_config(name, value, options)

@mcp.tool(description="Download objects and refs from another repository.")
def fetch(remote: str = "origin", options: str = "") -> str:
    """Download objects and refs from another repository."""
    return git_fetch(remote, options)

@mcp.tool(description="Show what revision and author last modified each line of a file.")
def blame(file_path: str, options: str = "") -> str:
    """Show what revision and author last modified each line of a file."""
    return git_blame(file_path, options)

@mcp.tool(description="Print lines matching a pattern in tracked files.")
def git_grep(pattern: str, options: str = "") -> str:
    """Print lines matching a pattern in tracked files."""
    return git_grep(pattern, options)

# Advanced Git Tools
@mcp.tool(description="Get comprehensive context about the current Git repository.")
def context(options: str = "--all") -> Dict[str, Any]:
    """Get comprehensive context about the current Git repository."""
    return git_context(options)

@mcp.tool(description="Show the current HEAD commit information.")
def git_show_head(options: str = "") -> str:
    """Show the current HEAD commit information."""
    return git_head(options)

@mcp.tool(description="Get the Git version.")
def version() -> str:
    """Get the Git version."""
    return git_version()

@mcp.tool(description="Validate the Git repository for common issues.")
def validate() -> Dict[str, Any]:
    """Validate the Git repository for common issues."""
    return git_validate()

@mcp.tool(description="Get comprehensive information about the Git repository.")
def repo_info() -> Dict[str, Any]:
    """Get comprehensive information about the Git repository."""
    return git_repo_info()

@mcp.tool(description="Summarize the git log with useful statistics.")
def summarize_log(count: int = 10, options: str = "") -> Dict[str, Any]:
    """Summarize the git log with useful statistics."""
    return git_summarize_log(count, options)

@mcp.tool(description="Analyze changes and suggest a commit message.")
def suggest_commit(options: str = "") -> Dict[str, Any]:
    """Analyze changes and suggest a commit message."""
    return git_suggest_commit(options)

@mcp.tool(description="Audit repository history for potential issues.")
def audit_history(options: str = "") -> Dict[str, Any]:
    """Audit repository history for potential issues."""
    return git_audit_history(options)

if __name__ == "__main__":
    try:
        # Register signal handlers for graceful shutdown
        def handle_signal(signum, frame):
            print(f"[fastfs-mcp] Received signal {signum}, shutting down...", file=sys.stderr, flush=True)
            sys.exit(0)
            
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        
        # Run MCP server
        print("[fastfs-mcp] Server running, waiting for requests...", file=sys.stderr, flush=True)
        
        # Start the server using the run method (which we now know works)
        mcp.run()
        
    except Exception as e:
        print(f"[fastfs-mcp] Fatal error: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
