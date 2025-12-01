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
@mcp.tool(
    description="""List files and directories at a given path.

Use when: You need to see what files exist in a directory, explore project structure, or verify file presence before operations.
Prefer over: Using 'find' for simple directory listing, or 'tree' when you only need immediate children.

Returns: List of filenames (not full paths). Use with pwd() to get absolute context.
Example: ls(".") or ls("src/components")""",
    annotations={"readOnlyHint": True, "openWorldHint": False}
)
def fastfs_ls(path: str = ".") -> List[str]:
    """List files and directories at a given path."""
    try:
        print(f"[DEBUG] ls called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return [f"Error: Path '{path}' does not exist. Try pwd() to check current directory, or tree() to visualize structure. Paths are relative to /mnt/workspace."]
        return os.listdir(path)
    except Exception as e:
        print(f"[ERROR] ls failed: {str(e)}", file=sys.stderr, flush=True)
        return [f"Error: {str(e)}"]

@mcp.tool(
    description="""Print the current working directory.

Use when: You need to know your current location in the filesystem, verify context before operations, or construct absolute paths.
Prefer over: Guessing paths or assuming location.

Returns: Absolute path string. Default is /mnt/workspace.
Example: pwd()""",
    annotations={"readOnlyHint": True, "openWorldHint": False}
)
def fastfs_pwd() -> str:
    """Print the current working directory."""
    try:
        print(f"[DEBUG] pwd called", file=sys.stderr, flush=True)
        return os.getcwd()
    except Exception as e:
        print(f"[ERROR] pwd failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="""Change the current working directory.

Use when: You need to switch context to work within a specific project or subdirectory for multiple operations.
Prefer over: Using absolute paths repeatedly. Note: Changes persist across tool calls in this session.

Returns: Confirmation with new absolute path.
Example: cd("my-project") or cd("/mnt/workspace/src")""")
def fastfs_cd(path: str) -> str:
    """Change the current working directory."""
    try:
        print(f"[DEBUG] cd called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist. Try ls() to see available directories, or find(pattern='*', file_type='d') to search for directories."
        if not os.path.isdir(path):
            return f"Error: '{path}' is not a directory. It appears to be a file. Use read() to view its contents instead."

        os.chdir(path)
        return f"Changed directory to {os.getcwd()}"
    except Exception as e:
        print(f"[ERROR] cd failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(
    description="""Read the contents of a file.

Use when: You need to examine file contents, review code, check configuration, or extract data from text files.
Prefer over: head() or tail() when you need the full file. For large files (>1MB), consider head() or tail() first.

Returns: Full file contents as UTF-8 string. Binary files may produce errors.
Example: read("src/main.py") or read("config.json")""",
    annotations={"readOnlyHint": True, "openWorldHint": False}
)
def fastfs_read(path: str) -> str:
    """Read the contents of a file."""
    try:
        print(f"[DEBUG] read called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist. Try find(pattern='*{os.path.basename(path)}*') to locate it, or ls() to see files in current directory."
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file, it's a directory. Use ls('{path}') to list its contents, or tree('{path}') to see its structure."
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        return f"Error: '{path}' appears to be a binary file and cannot be read as text. Use stat('{path}') to check file info."
    except Exception as e:
        print(f"[ERROR] read failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(
    description="""Write contents to a file. WARNING: Overwrites existing files without confirmation.

Use when: You need to create a new file or completely replace existing file contents.
Prefer over: Manual echo/cat commands. For appending, read the file first and include existing content.

DESTRUCTIVE: Will overwrite existing files. Creates parent directories automatically.
Returns: Success confirmation with path.
Example: write("output.txt", "Hello World") or write("src/new_module.py", "# New module")""",
    annotations={"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}
)
def fastfs_write(path: str, content: str = "") -> str:
    """Write contents to a file."""
    try:
        print(f"[DEBUG] write called with path: {path}", file=sys.stderr, flush=True)
        existed = os.path.exists(path)
        # Create directory if it doesn't exist
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        if existed:
            return f"Successfully overwrote {path} ({len(content)} bytes)"
        return f"Successfully created {path} ({len(content)} bytes)"
    except PermissionError:
        return f"Error: Permission denied writing to '{path}'. Check file permissions with stat('{path}') or verify mount permissions."
    except Exception as e:
        print(f"[ERROR] write failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(
    description="""Search for a pattern in a file using grep with line numbers.

Use when: You need to find specific text, code patterns, or occurrences within a single file.
Prefer over: read() when you only need matching lines. For searching across multiple files, use find() with grep or git_grep() for tracked files.

Returns: Matching lines with line numbers (format: "linenum:content"). Empty if no matches.
Example: grep("TODO", "src/main.py") or grep("function.*export", "index.js")""",
    annotations={"readOnlyHint": True, "openWorldHint": False}
)
def fastfs_grep(pattern: str, path: str) -> str:
    """Search for a pattern in a file."""
    if not os.path.exists(path):
        return f"Error: File '{path}' does not exist. Try find(pattern='*{os.path.basename(path)}*') to locate it."
    if not os.path.isfile(path):
        return f"Error: '{path}' is not a file. For directory-wide search, use: find(path='{path}', pattern='*') then grep each result, or git_grep() for git repos."

    # Escape the pattern to avoid shell injection
    escaped_pattern = pattern.replace("'", "'\\''")
    cmd = f"grep -n '{escaped_pattern}' {path}"
    result = run_command(cmd)

    if not result:
        return f"No matches found for pattern '{pattern}' in '{path}'. Try a broader pattern or check spelling. For regex, escape special chars."
    return result

@mcp.tool(description="Locate a command in the system path.")
def fastfs_which(command: str) -> str:
    """Locate a command in the system path."""
    # Escape the command to avoid shell injection
    escaped_command = command.replace("'", "'\\''")
    result = run_command(f"which '{escaped_command}'")
    
    if not result or "not found" in result.lower():
        return f"Command '{command}' not found in PATH"
    return result

@mcp.tool(description="Use sed to transform file content using stream editing.")
def fastfs_sed(script: str, path: str) -> str:
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
def fastfs_gawk(script: str, path: str) -> str:
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
def fastfs_stat(path: str) -> Dict[str, Any]:
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

@mcp.tool(description="""Display directory tree structure with visual hierarchy.

Use when: You need to understand project layout, visualize folder structure, or get an overview before diving into specific files.
Prefer over: Multiple ls() calls for hierarchy overview. Use ls() for single directory contents only.

Returns: ASCII tree visualization showing directories and files.
Example: tree(".") or tree("src", depth=2) for shallow view""")
def fastfs_tree(path: str = ".", depth: int = 3) -> str:
    """Display directory tree structure."""
    try:
        print(f"[DEBUG] tree called with path: {path}, depth: {depth}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist. Try pwd() to check current location, or ls() to see available directories."

        # Escape path for shell command
        escaped_path = path.replace("'", "'\\''")
        cmd = f"tree -L {depth} '{escaped_path}'"
        result = run_command(cmd)

        if not result:
            return f"Directory '{path}' appears to be empty. Use ls('{path}') to confirm."
        return result
    except Exception as e:
        print(f"[ERROR] tree failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="""Find files by name pattern recursively.

Use when: You need to locate files by name pattern, search for specific file types, or find files across subdirectories.
Prefer over: Manual directory traversal. For content search, use grep() on results or git_grep() for tracked files.

Parameters:
- pattern: Glob pattern like "*.py", "test_*", "*.{js,ts}"
- file_type: 'f' (files), 'd' (directories), 'l' (symlinks)
- max_depth: Limit search depth (None = unlimited)

Returns: List of matching file paths relative to search path.
Example: find(pattern="*.py") or find(path="src", pattern="*.test.js", file_type="f")""")
def fastfs_find(path: str = ".", pattern: str = "*", file_type: str = None, max_depth: int = None) -> List[str]:
    """Find files by pattern and other criteria."""
    try:
        print(f"[DEBUG] find called with path: {path}, pattern: {pattern}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return [f"Error: Path '{path}' does not exist. Try pwd() to check current directory."]

        # Build find command
        cmd_parts = ["find", path]
        if max_depth is not None:
            cmd_parts.extend(["-maxdepth", str(max_depth)])
        if file_type:
            if file_type in ['f', 'd', 'l', 'b', 'c', 'p', 's']:
                cmd_parts.extend(["-type", file_type])
            else:
                return [f"Error: Invalid file_type '{file_type}'. Valid options: 'f' (file), 'd' (directory), 'l' (symlink)"]
        cmd_parts.extend(["-name", pattern])

        # Join and escape the command
        cmd = " ".join(f"'{p}'" if ' ' in p else p for p in cmd_parts)
        result = run_command(cmd)

        if not result:
            return [f"No files found matching pattern '{pattern}' in '{path}'. Try a broader pattern like '*{pattern.strip('*')}*' or check the path."]
        return result.split('\n')
    except Exception as e:
        print(f"[ERROR] find failed: {str(e)}", file=sys.stderr, flush=True)
        return [f"Error: {str(e)}"]

@mcp.tool(description="""Copy files or directories.

Use when: You need to duplicate files, create backups, or copy project templates.
Prefer over: read() + write() for binary files or when preserving metadata matters.

Parameters:
- recursive: Required for directories, copies entire tree
WARNING: Will overwrite destination if it exists.

Returns: Success confirmation with paths.
Example: cp("config.json", "config.backup.json") or cp("template/", "new-project/", recursive=True)""")
def fastfs_cp(source: str, destination: str, recursive: bool = False) -> str:
    """Copy files or directories."""
    try:
        print(f"[DEBUG] cp called with source: {source}, destination: {destination}", file=sys.stderr, flush=True)
        if not os.path.exists(source):
            return f"Error: Source '{source}' does not exist. Try find(pattern='*{os.path.basename(source)}*') to locate it."

        if os.path.isdir(source) and not recursive:
            return f"Error: '{source}' is a directory. Set recursive=True to copy directories, or specify a file within it."

        if os.path.exists(destination):
            dest_info = "directory" if os.path.isdir(destination) else "file"
            print(f"[WARNING] Destination '{destination}' exists ({dest_info}), will overwrite", file=sys.stderr, flush=True)

        if recursive:
            shutil.copytree(source, destination, dirs_exist_ok=True)
            return f"Successfully copied directory '{source}' to '{destination}'"
        else:
            shutil.copy2(source, destination)
            return f"Successfully copied file '{source}' to '{destination}'"
    except Exception as e:
        print(f"[ERROR] cp failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="""Move or rename files or directories.

Use when: You need to relocate files, rename them, or reorganize directory structure.
Prefer over: cp() + rm() when you don't need the original.

DESTRUCTIVE: Original file/directory will no longer exist at source path.
Returns: Success confirmation with old and new paths.
Example: mv("old_name.py", "new_name.py") or mv("src/utils", "lib/utils")""")
def fastfs_mv(source: str, destination: str) -> str:
    """Move or rename files or directories."""
    try:
        print(f"[DEBUG] mv called with source: {source}, destination: {destination}", file=sys.stderr, flush=True)
        if not os.path.exists(source):
            return f"Error: Source '{source}' does not exist. Try find(pattern='*{os.path.basename(source)}*') to locate it."

        if os.path.exists(destination):
            return f"Error: Destination '{destination}' already exists. Remove it first with rm() or choose a different name."

        shutil.move(source, destination)
        return f"Successfully moved '{source}' to '{destination}'"
    except Exception as e:
        print(f"[ERROR] mv failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(
    description="""Remove files or directories. DANGEROUS: Deletion is permanent.

Use when: You need to delete files or clean up directories.
CAUTION: This operation cannot be undone. There is no trash/recycle bin.

Parameters:
- recursive: Required for directories, removes entire tree
- force: Suppress errors if path doesn't exist

DESTRUCTIVE: Permanently deletes data. Consider cp() for backup first.
Returns: Success confirmation.
Example: rm("temp.txt") or rm("node_modules", recursive=True)""",
    annotations={"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}
)
def fastfs_rm(path: str, recursive: bool = False, force: bool = False) -> str:
    """Remove files or directories."""
    try:
        print(f"[DEBUG] rm called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            if force:
                return f"Warning: Path '{path}' does not exist, nothing removed"
            else:
                return f"Error: Path '{path}' does not exist. Try find(pattern='*{os.path.basename(path)}*') to locate it."

        if os.path.isdir(path):
            if not recursive:
                item_count = len(os.listdir(path))
                return f"Error: '{path}' is a directory with {item_count} items. Set recursive=True to remove directories. Use tree('{path}', depth=1) to preview contents."
            item_count = sum(1 for _ in os.walk(path))
            shutil.rmtree(path)
            return f"Successfully removed directory '{path}' ({item_count} items deleted)"
        else:
            size = os.path.getsize(path)
            os.remove(path)
            return f"Successfully removed file '{path}' ({size} bytes)"
    except PermissionError:
        return f"Error: Permission denied removing '{path}'. Check permissions with stat('{path}')."
    except Exception as e:
        print(f"[ERROR] rm failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Create a new empty file or update its timestamp.")
def fastfs_touch(path: str) -> str:
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
def fastfs_mkdir(path: str, parents: bool = False) -> str:
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
def fastfs_du(path: str = ".", human_readable: bool = True, max_depth: int = 1) -> str:
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
def fastfs_df(human_readable: bool = True) -> str:
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
def fastfs_chmod(path: str, mode: str) -> str:
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
def fastfs_chown(path: str, owner: str, group: Optional[str] = None) -> str:
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
def fastfs_cat(paths: List[str]) -> str:
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
def fastfs_head(path: str, lines: int = 10) -> str:
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
def fastfs_tail(path: str, lines: int = 10) -> str:
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
def fastfs_readlink(path: str) -> str:
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
def fastfs_realpath(path: str) -> str:
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
def fastfs_cut(path: str, delimiter: str = '\t', fields: str = '1') -> str:
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
def fastfs_sort(path: str, reverse: bool = False, numeric: bool = False, field: Optional[int] = None) -> str:
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
def fastfs_uniq(path: str, count: bool = False, repeated: bool = False, ignore_case: bool = False) -> str:
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
def fastfs_wc(path: str, lines: bool = True, words: bool = True, bytes: bool = True) -> Dict[str, int]:
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
def fastfs_nl(path: str, number_empty: bool = True, number_format: str = '%6d  ') -> str:
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
def fastfs_split(path: str, prefix: str = 'x', lines: Optional[int] = 1000, bytes_size: Optional[str] = None) -> str:
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
def fastfs_tar(operation: str, archive_file: str, files: Optional[List[str]] = None, options: str = "") -> str:
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
def fastfs_gzip(path: str, decompress: bool = False, keep: bool = False) -> str:
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
def fastfs_zip(operation: str, archive_file: str, files: Optional[List[str]] = None, options: str = "") -> str:
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
@mcp.tool(description="""Clone a Git repository to local filesystem.

Use when: You need to download a repository to work on it locally. Supports GitHub authentication via PAT or GitHub App.
Prefer over: Manual git commands when working with private repos (authentication is handled automatically).

Returns: Success message with clone location.
Example: clone("https://github.com/user/repo.git") or clone("https://github.com/user/repo.git", "my-local-dir")""")
def fastfs_clone(repo_url: str, target_dir: Optional[str] = None, options: str = "") -> str:
    """Clone a Git repository."""
    return git_clone(repo_url, target_dir, options)

@mcp.tool(description="""Initialize a new Git repository.

Use when: Starting a new project that should be version controlled, or initializing git in an existing directory.
Prefer over: clone() when starting fresh rather than downloading existing code.

Returns: Success message with repository path.
Example: init(".") or init("new-project")""")
def fastfs_init(directory: str = ".") -> str:
    """Initialize a new Git repository."""
    return git_init(directory)

@mcp.tool(description="""Add file(s) to the Git staging area for next commit.

Use when: You've made changes and want to prepare them for committing. Run status() first to see what's changed.
Prefer over: Committing without staging when you want selective commits.

Returns: Confirmation of staged files.
Example: add(".") for all, add("src/main.py") for specific, add(["file1.py", "file2.py"]) for multiple""")
def fastfs_add(paths: Union[str, List[str]], options: str = "") -> str:
    """Add file(s) to the Git staging area."""
    return git_add(paths, options)

@mcp.tool(description="""Commit staged changes to the Git repository.

Use when: You have staged changes (via add()) ready to save as a commit. Use status() to verify what will be committed.
Prefer over: Making changes without committing (preserves history and enables collaboration).

IMPORTANT: Creates a permanent record in git history.
Returns: Commit hash and summary.
Example: commit("feat: add user authentication") or commit("fix: resolve null pointer issue")""")
def fastfs_commit(message: str, options: str = "") -> str:
    """Commit changes to the Git repository."""
    return git_commit(message, options)

@mcp.tool(
    description="""Show the working tree status - staged, unstaged, and untracked files.

Use when: You need to understand the current state before committing, or verify what files have changed.
Prefer over: Manual file inspection. This is your primary tool for understanding repository state.

IMPORTANT: Always run this BEFORE add() and commit() to verify what you're committing.
Returns: Status summary showing modified, staged, and untracked files.
Example: status() or status("--short") for compact view""",
    annotations={"readOnlyHint": True, "openWorldHint": False}
)
def fastfs_status(options: str = "") -> str:
    """Show the working tree status."""
    return git_status(options)

@mcp.tool(
    description="""Push commits to a remote repository.

Use when: You have local commits ready to share with the remote (GitHub, etc.). Requires commits first.
Prefer over: Manual sharing of code changes.

DESTRUCTIVE: Publishes commits to remote. Cannot easily undo pushed commits. Requires authentication for private repos.
Returns: Push result summary.
Example: push() for default, push("origin", "main") for specific branch""",
    annotations={"readOnlyHint": False, "destructiveHint": True, "openWorldHint": True}
)
def fastfs_push(remote: str = "origin", branch: str = "", options: str = "") -> str:
    """Push changes to a remote repository."""
    return git_push(remote, branch, options)

@mcp.tool(description="""Pull changes from a remote repository and merge into current branch.

Use when: You need to get the latest changes from the remote before making edits or pushing.
Prefer over: Manually fetching and merging.

CAUTION: May cause merge conflicts if local and remote have diverged.
Returns: Pull result with changes summary.
Example: pull() for default, pull("origin", "main") for specific branch""")
def fastfs_pull(remote: str = "origin", branch: str = "", options: str = "") -> str:
    """Pull changes from a remote repository."""
    return git_pull(remote, branch, options)

@mcp.tool(description="""Show commit history log.

Use when: You need to see previous commits, find specific changes, or understand project history.
Prefer over: Reading individual files to understand what changed.

Returns: Commit list with hashes, authors, dates, and messages.
Example: log() for recent 10, log("--oneline -n 20") for more, log("--author=name") to filter""")
def fastfs_log(options: str = "--oneline -n 10") -> str:
    """Show commit logs."""
    return git_log(options)

@mcp.tool(description="""Switch branches or restore working tree files.

Use when: You need to switch to a different branch, or restore a file to its committed state.
Prefer over: Manually editing files to undo changes. Use branch() to see available branches first.

CAUTION: May lose uncommitted changes. Run status() first to check for unsaved work.
Returns: Confirmation of checkout.
Example: checkout("main"), checkout("feature-branch"), checkout("-b new-branch") to create and switch""")
def fastfs_checkout(revision: str, options: str = "") -> str:
    """Switch branches or restore working tree files."""
    return git_checkout(revision, options)

@mcp.tool(description="""List, create, or delete branches.

Use when: You need to see available branches, create a new feature branch, or clean up old branches.
Prefer over: Guessing branch names. Use with checkout() to switch branches.

Returns: Branch list (current marked with *) or operation result.
Example: branch() to list, branch(branch_name="feature-x") to create, branch(options="-d", branch_name="old-branch") to delete""")
def fastfs_branch(options: str = "", branch_name: Optional[str] = None) -> str:
    """List, create, or delete branches."""
    return git_branch(options, branch_name)

@mcp.tool(description="""Merge another branch into the current branch.

Use when: You want to combine changes from another branch (e.g., merging feature into main).
Prefer over: Manual copying of changes between branches.

CAUTION: May cause merge conflicts. Run status() to ensure clean working tree first.
Returns: Merge result or conflict information.
Example: merge("feature-branch") or merge("main")""")
def fastfs_merge(branch: str, options: str = "") -> str:
    """Join two or more development histories together."""
    return git_merge(branch, options)

@mcp.tool(description="""Show detailed information about a Git object (commit, tag, etc.).

Use when: You need to see full details of a specific commit including diff, or examine a tag.
Prefer over: log() when you need full commit details rather than just the list.

Returns: Full commit information including message and changes.
Example: show("HEAD") for latest, show("abc123") for specific commit, show("v1.0.0") for tag""")
def fastfs_show(object: str = "HEAD", options: str = "") -> str:
    """Show various types of Git objects."""
    return git_show(object, options)

@mcp.tool(description="""Show changes between commits, staging area, and working tree.

Use when: You need to see exactly what changed in files before committing, or compare versions.
Prefer over: Manually comparing file versions. Essential for code review before commit.

Returns: Unified diff showing additions (+) and deletions (-).
Example: diff() for unstaged, diff("--staged") for staged, diff("HEAD~1") for last commit""")
def fastfs_diff(options: str = "", path: Optional[str] = None) -> str:
    """Show changes between commits, commit and working tree, etc."""
    return git_diff(options, path)

@mcp.tool(description="Manage remote repositories.")
def fastfs_remote(command: str = "show", name: Optional[str] = None, options: str = "") -> str:
    """Manage remote repositories."""
    return git_remote(command, name, options)

@mcp.tool(description="Pick out and massage parameters for low-level Git commands.")
def fastfs_rev_parse(rev: str, options: str = "") -> str:
    """Pick out and massage parameters for low-level Git commands."""
    return git_rev_parse(rev, options)

@mcp.tool(description="Show information about files in the index and the working tree.")
def fastfs_ls_files(options: str = "") -> List[str]:
    """Show information about files in the index and the working tree."""
    return git_ls_files(options)

@mcp.tool(description="Give an object a human-readable name based on available ref.")
def fastfs_describe(options: str = "--tags") -> str:
    """Give an object a human-readable name based on available ref."""
    return git_describe(options)

@mcp.tool(description="Reapply commits on top of another base tip.")
def fastfs_rebase(branch: str, options: str = "") -> str:
    """Reapply commits on top of another base tip."""
    return git_rebase(branch, options)

@mcp.tool(description="""Stash changes in a dirty working directory temporarily.

Use when: You need to switch branches but have uncommitted work, or want to save work-in-progress without committing.
Prefer over: Committing unfinished work. Stash is temporary storage.

Commands: 'push' (save), 'pop' (restore and remove), 'apply' (restore and keep), 'list' (show stashes)
Returns: Stash operation result.
Example: stash() to save, stash("pop") to restore, stash("list") to see stashes""")
def fastfs_stash(command: str = "push", options: str = "") -> str:
    """Stash the changes in a dirty working directory away."""
    return git_stash(command, options)

@mcp.tool(
    description="""Reset current HEAD to a specified state. DANGEROUS: Can lose uncommitted work.

Use when: You need to unstage files, or undo commits (use with extreme caution).
Prefer over: Manual file restoration for undoing staged changes.

DESTRUCTIVE with --hard: Permanently loses uncommitted changes!
- No options: Unstage files but keep changes in working directory
- --soft: Undo commits but keep changes staged
- --hard: Undo everything (DANGEROUS - loses all uncommitted work)

Example: reset() to unstage all, reset("HEAD~1") to undo last commit, reset("--hard HEAD") to discard all changes""",
    annotations={"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}
)
def fastfs_reset(options: str = "", paths: Optional[Union[str, List[str]]] = None) -> str:
    """Reset current HEAD to the specified state."""
    return git_reset(options, paths)

@mcp.tool(
    description="""Remove untracked files from the working tree. DANGEROUS: Permanent deletion.

Use when: You need to clean up build artifacts, temporary files, or reset to a clean state.
CAUTION: Deleted files cannot be recovered (they're not in git history).

Options:
- -n (default): Dry run - show what would be deleted without deleting
- -f: Actually delete files (required for real deletion)
- -d: Also remove untracked directories

ALWAYS run with -n first to preview, then -f to execute.
Example: clean() to preview, clean("-f") to delete, clean("-fd") to delete files and directories""",
    annotations={"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}
)
def fastfs_clean(options: str = "-n") -> str:
    """Remove untracked files from the working tree."""
    return git_clean(options)

@mcp.tool(description="Create, list, delete or verify a tag object.")
def fastfs_tag(tag_name: Optional[str] = None, options: str = "") -> Union[str, List[str]]:
    """Create, list, delete or verify a tag object."""
    return git_tag(tag_name, options)

@mcp.tool(description="Get or set repository or global options.")
def fastfs_config(name: Optional[str] = None, value: Optional[str] = None, options: str = "") -> str:
    """Get or set repository or global options."""
    return git_config(name, value, options)

@mcp.tool(description="Download objects and refs from another repository.")
def fastfs_fetch(remote: str = "origin", options: str = "") -> str:
    """Download objects and refs from another repository."""
    return git_fetch(remote, options)

@mcp.tool(description="Show what revision and author last modified each line of a file.")
def fastfs_blame(file_path: str, options: str = "") -> str:
    """Show what revision and author last modified each line of a file."""
    return git_blame(file_path, options)

@mcp.tool(description="Print lines matching a pattern in tracked files.")
def fastfs_git_grep(pattern: str, options: str = "") -> str:
    """Print lines matching a pattern in tracked files."""
    return git_grep(pattern, options)

# Advanced Git Tools
@mcp.tool(
    description="""Get comprehensive context about the current Git repository in a single call.

Use when: Starting work on a repo, need full situational awareness, or preparing to make changes. This is your GO-TO tool for understanding repository state.
Prefer over: Multiple calls to status(), log(), branch(), diff(). Gets everything at once.

Returns structured data including:
- current_branch: Active branch name
- repository_root: Absolute path to repo root
- is_clean: Whether working tree has uncommitted changes
- head_commit: Current commit hash
- remotes: Dict of remote names to URLs
- recent_commits: Last 5 commits (oneline format)
- branches: List of local branches
- tags: List of tags

Example: context() to get full picture before starting work""",
    annotations={"readOnlyHint": True, "openWorldHint": False}
)
def fastfs_context(options: str = "--all") -> Dict[str, Any]:
    """Get comprehensive context about the current Git repository."""
    return git_context(options)

@mcp.tool(description="""Show the current HEAD commit information in detail.

Use when: You need to see the full details of the most recent commit.
Prefer over: log() when you need complete commit info rather than a list.

Returns: Full commit details including message, author, date, and diff.
Example: git_show_head()""")
def fastfs_git_show_head(options: str = "") -> str:
    """Show the current HEAD commit information."""
    return git_head(options)

@mcp.tool(description="""Get the Git version installed in the container.

Use when: Debugging git issues or checking compatibility.
Returns: Git version string.
Example: version()""")
def fastfs_version() -> str:
    """Get the Git version."""
    return git_version()

@mcp.tool(description="""Validate the Git repository for common issues and potential problems.

Use when: Troubleshooting repository issues, before important operations, or auditing repo health.
Prefer over: Manual inspection for common problems.

Returns structured validation results:
- valid: Boolean overall status
- issues: Critical problems found
- warnings: Non-critical concerns
- info: Informational notes

Example: validate() to check repo health""")
def fastfs_validate() -> Dict[str, Any]:
    """Validate the Git repository for common issues."""
    return git_validate()

@mcp.tool(description="""Get comprehensive statistics and information about the Git repository.

Use when: You need detailed repository metrics like commit count, contributors, file count, size.
Prefer over: Running multiple commands to gather statistics.

Returns detailed info including:
- repository_path, current_branch, remote_url
- commit_count, contributor_count, file_count
- contributors (with commit counts per author)
- size_kb, tag_count, branch_count

Example: repo_info() for full repository statistics""")
def fastfs_repo_info() -> Dict[str, Any]:
    """Get comprehensive information about the Git repository."""
    return git_repo_info()

@mcp.tool(description="""Summarize the git log with statistics per author, date distribution, and change metrics.

Use when: You need to analyze recent activity, understand contribution patterns, or generate reports.
Prefer over: Parsing log() output manually.

Returns:
- commits: List of commit details with changes
- stats: Aggregated metrics (total_commits, authors with counts, date_distribution)

Example: summarize_log(count=20) for last 20 commits with stats""")
def fastfs_summarize_log(count: int = 10, options: str = "") -> Dict[str, Any]:
    """Summarize the git log with useful statistics."""
    return git_summarize_log(count, options)

@mcp.tool(description="""Analyze staged changes and suggest a conventional commit message.

Use when: You've staged changes and want help writing a good commit message following conventions.
Prefer over: Guessing commit message format. Analyzes actual changes to suggest type (feat, fix, docs, etc.).

Returns:
- changes: File change summary (files_changed, insertions, deletions, file_details)
- suggested_message: Auto-generated commit message
- suggested_type: Commit type (feat, fix, docs, test, chore)
- suggested_scope: Inferred scope from directory structure

Example: suggest_commit() after staging changes with add()""")
def fastfs_suggest_commit(options: str = "") -> Dict[str, Any]:
    """Analyze changes and suggest a commit message."""
    return git_suggest_commit(options)

@mcp.tool(description="""Audit repository history for security issues and problematic patterns.

Use when: Checking for accidentally committed secrets, large files, or other issues in git history.
Prefer over: Manual git log inspection for security auditing.

Checks for:
- Large files in history
- Merge conflict markers accidentally committed
- Binary files
- Potential secrets (passwords, tokens, keys)
- Very short commit messages
- Orphaned commits

Returns: {issues: [], warnings: [], info: [], stats: {}}
Example: audit_history() for full security audit""")
def fastfs_audit_history(options: str = "") -> Dict[str, Any]:
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
