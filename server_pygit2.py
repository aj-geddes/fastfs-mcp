 mode: {mode}", file=sys.stderr, flush=True)
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

# ===== REGISTER PYGIT2 TOOLS =====

# Git Repository Operations
@mcp.tool(description="Clone a Git repository using PyGit2.")
def clone(repo_url: str, target_dir: Optional[str] = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Clone a Git repository."""
    return git_clone(repo_url, target_dir, options)

@mcp.tool(description="Initialize a new Git repository using PyGit2.")
def init(directory: str = ".", bare: bool = False, initial_commit: bool = False) -> Dict[str, Any]:
    """Initialize a new Git repository."""
    return git_init(directory, bare, initial_commit)

@mcp.tool(description="Add file(s) to the Git staging area using PyGit2.")
def add(paths: Union[str, List[str]], path: str = None) -> Dict[str, Any]:
    """Add file(s) to the Git staging area."""
    return git_add(paths, path)

@mcp.tool(description="Commit changes to the Git repository using PyGit2.")
def commit(message: str, author_name: Optional[str] = None, author_email: Optional[str] = None, 
           path: str = None, amend: bool = False) -> Dict[str, Any]:
    """Commit changes to the Git repository."""
    return git_commit(message, author_name, author_email, path, amend)

@mcp.tool(description="Show the working tree status using PyGit2.")
def status(path: str = None) -> Dict[str, Any]:
    """Show the working tree status."""
    return git_status(path)

@mcp.tool(description="Push changes to a remote repository using PyGit2.")
def push(path: str = None, remote: str = "origin", refspecs: Optional[List[str]] = None,
         force: bool = False, token: Optional[str] = None) -> Dict[str, Any]:
    """Push changes to a remote repository."""
    return git_push(path, remote, refspecs, force, token)

@mcp.tool(description="Pull changes from a remote repository using PyGit2.")
def pull(path: str = None, remote: str = "origin", branch: Optional[str] = None,
         fast_forward_only: bool = False, token: Optional[str] = None) -> Dict[str, Any]:
    """Pull changes from a remote repository."""
    return git_pull(path, remote, branch, fast_forward_only, token)

@mcp.tool(description="Show commit logs using PyGit2.")
def log(path: str = None, max_count: int = 10, skip: int = 0, 
       ref: Optional[str] = None, path_filter: Optional[str] = None) -> Dict[str, Any]:
    """Show commit logs."""
    return git_log(path, max_count, skip, ref, path_filter)

@mcp.tool(description="Switch branches or restore working tree files using PyGit2.")
def checkout(revision: str, path: str = None, create_branch: bool = False, 
             force: bool = False) -> Dict[str, Any]:
    """Switch branches or restore working tree files."""
    return git_checkout(revision, path, create_branch, force)

@mcp.tool(description="List, create, or delete branches using PyGit2.")
def branch(name: Optional[str] = None, path: str = None, start_point: Optional[str] = None,
           delete: bool = False, force: bool = False) -> Dict[str, Any]:
    """List, create, or delete branches."""
    return git_branch(name, path, start_point, delete, force)

@mcp.tool(description="Join two or more development histories together using PyGit2.")
def merge(path: str = None, branch: str = None, commit_message: Optional[str] = None,
         no_commit: bool = False, no_ff: bool = False) -> Dict[str, Any]:
    """Join two or more development histories together."""
    return git_merge(path, branch, commit_message, no_commit, no_ff)

@mcp.tool(description="Show various types of Git objects using PyGit2.")
def show(path: str = None, object_name: str = "HEAD") -> Dict[str, Any]:
    """Show various types of Git objects."""
    return git_show(path, object_name)

@mcp.tool(description="Show changes between commits, commit and working tree, etc. using PyGit2.")
def diff(path: str = None, from_ref: Optional[str] = None, to_ref: Optional[str] = None,
        staged: bool = False, path_filter: Optional[str] = None, 
        context_lines: int = 3) -> Dict[str, Any]:
    """Show changes between commits, commit and working tree, etc."""
    return git_diff(path, from_ref, to_ref, staged, path_filter, context_lines)

@mcp.tool(description="Manage remote repositories using PyGit2.")
def remote(path: str = None, command: str = "list", name: Optional[str] = None,
         url: Optional[str] = None) -> Dict[str, Any]:
    """Manage remote repositories."""
    return git_remote(path, command, name, url)

@mcp.tool(description="Reset current HEAD to the specified state using PyGit2.")
def reset(path: str = None, mode: str = "mixed", target: str = "HEAD", 
         paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """Reset current HEAD to the specified state."""
    return git_reset(path, mode, target, paths)

@mcp.tool(description="Stash the changes in a dirty working directory away using PyGit2.")
def stash(path: str = None, command: str = "push", message: Optional[str] = None,
         include_untracked: bool = False, stash_index: Optional[int] = None) -> Dict[str, Any]:
    """Stash the changes in a dirty working directory away."""
    return git_stash(path, command, message, include_untracked, stash_index)

@mcp.tool(description="Create, list, delete or verify a tag object using PyGit2.")
def tag(path: str = None, name: Optional[str] = None, target: str = "HEAD",
      message: Optional[str] = None, delete: bool = False, 
      force: bool = False) -> Dict[str, Any]:
    """Create, list, delete or verify a tag object."""
    return git_tag(path, name, target, message, delete, force)

@mcp.tool(description="Download objects and refs from another repository using PyGit2.")
def fetch(path: str = None, remote: str = "origin", refspec: Optional[str] = None,
        token: Optional[str] = None) -> Dict[str, Any]:
    """Download objects and refs from another repository."""
    return git_fetch(path, remote, refspec, token)

@mcp.tool(description="Show what revision and author last modified each line of a file using PyGit2.")
def blame(path: str = None, file_path: str = None, rev: str = "HEAD") -> Dict[str, Any]:
    """Show what revision and author last modified each line of a file."""
    return git_blame(path, file_path, rev)

@mcp.tool(description="Search for a pattern in tracked files using PyGit2.")
def git_grep(path: str = None, pattern: str = None, revision: str = "HEAD",
           ignore_case: bool = False, word_regexp: bool = False,
           paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """Search for a pattern in tracked files."""
    return git_grep(path, pattern, revision, ignore_case, word_regexp, paths)

# Advanced Git Tools
@mcp.tool(description="Get comprehensive context about the current Git repository using PyGit2.")
def context(path: str = None, details: str = "all") -> Dict[str, Any]:
    """Get comprehensive context about the current Git repository."""
    return git_context(path, details)

@mcp.tool(description="Validate the Git repository for common issues using PyGit2.")
def validate(path: str = None) -> Dict[str, Any]:
    """Validate the Git repository for common issues."""
    return git_validate(path)

@mcp.tool(description="Analyze changes and suggest a commit message using PyGit2.")
def suggest_commit(path: str = None) -> Dict[str, Any]:
    """Analyze changes and suggest a commit message."""
    return git_suggest_commit(path)

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
