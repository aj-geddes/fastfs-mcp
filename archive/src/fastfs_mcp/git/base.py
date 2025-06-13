                    "object": {
                        "id": str(obj.id),
                        "type": obj.type_str
                    }
                }
            
        except KeyError:
            return {
                "success": False,
                "message": f"Object '{object_name}' not found"
            }
    except Exception as e:
        log_error(f"Error showing object {object_name}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def _is_binary_blob(blob: pygit2.Blob) -> bool:
    """Check if a blob is binary by looking for null bytes and text encoding."""
    # Check for null bytes in the first chunk of data
    chunk_size = min(8000, blob.size)
    data = blob.data[:chunk_size]
    
    # If there are null bytes, it's likely binary
    if b'\x00' in data:
        return True
    
    # Try to decode as UTF-8
    try:
        data.decode('utf-8')
        return False
    except UnicodeDecodeError:
        return True

def git_reset(path: str = None, mode: str = "mixed", target: str = "HEAD", 
             paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Reset current HEAD to the specified state.
    
    Args:
        path: Path to the repository (default: current directory)
        mode: Reset mode (soft, mixed, hard)
        target: Target commit to reset to
        paths: Optional list of paths to reset (for mixed and soft modes)
    
    Returns:
        Dictionary with reset operation results
    """
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Resolve the target
        try:
            target_obj = repo.revparse_single(target)
            if not isinstance(target_obj, pygit2.Commit):
                target_obj = target_obj.peel(pygit2.Commit)
        except KeyError:
            return {
                "success": False,
                "message": f"Target '{target}' not found"
            }
        
        # Path-specific reset (index only)
        if paths:
            # Only reset specific paths
            index = repo.index
            tree = target_obj.tree
            
            for path_pattern in paths:
                # Handle wildcards with glob
                if '*' in path_pattern or '?' in path_pattern:
                    import glob
                    repo_dir = os.path.dirname(repo.path)
                    glob_paths = glob.glob(os.path.join(repo_dir, path_pattern))
                    for gp in glob_paths:
                        rel_path = os.path.relpath(gp, repo_dir)
                        try:
                            # Find the tree entry for this path
                            entry = tree[rel_path]
                            index.add(entry.id, rel_path)
                        except KeyError:
                            # If path doesn't exist in the target, remove it from index
                            try:
                                index.remove(rel_path)
                            except KeyError:
                                pass
                else:
                    try:
                        # Find the tree entry for this path
                        entry = tree[path_pattern]
                        index.add(entry.id, path_pattern)
                    except KeyError:
                        # If path doesn't exist in the target, remove it from index
                        try:
                            index.remove(path_pattern)
                        except KeyError:
                            pass
            
            index.write()
            
            return {
                "success": True,
                "message": f"Reset paths to {target}",
                "paths": paths
            }
        
        # Full reset
        if mode == "soft":
            # Just move HEAD to the target commit
            reference = repo.head
            reference.set_target(target_obj.id)
            
            return {
                "success": True,
                "message": f"Soft reset to {target}",
                "target": str(target_obj.id)
            }
            
        elif mode == "mixed":
            # Move HEAD and reset index
            reference = repo.head
            reference.set_target(target_obj.id)
            repo.reset(target_obj.id, pygit2.GIT_RESET_MIXED)
            
            return {
                "success": True,
                "message": f"Mixed reset to {target}",
                "target": str(target_obj.id)
            }
            
        elif mode == "hard":
            # Move HEAD, reset index, and checkout working directory
            repo.reset(target_obj.id, pygit2.GIT_RESET_HARD)
            
            return {
                "success": True,
                "message": f"Hard reset to {target}",
                "target": str(target_obj.id)
            }
            
        else:
            return {
                "success": False,
                "message": f"Unknown reset mode: {mode}"
            }
    except Exception as e:
        log_error(f"Error resetting to {target}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_merge(path: str = None, branch: str = None, commit_message: Optional[str] = None,
             no_commit: bool = False, no_ff: bool = False) -> Dict[str, Any]:
    """
    Merge a branch into the current branch.
    
    Args:
        path: Path to the repository (default: current directory)
        branch: Branch to merge
        commit_message: Custom commit message for the merge
        no_commit: Don't automatically commit the merge
        no_ff: Don't fast-forward merge
    
    Returns:
        Dictionary with merge operation results
    """
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        if not branch:
            return {
                "success": False,
                "message": "Branch to merge is required"
            }
        
        # Check if the branch exists
        if f"refs/heads/{branch}" not in repo.references:
            return {
                "success": False,
                "message": f"Branch '{branch}' not found"
            }
        
        # Get the branch reference
        branch_ref = repo.references[f"refs/heads/{branch}"]
        branch_commit = branch_ref.peel(pygit2.Commit)
        
        # Get current HEAD
        if repo.head_is_detached:
            return {
                "success": False,
                "message": "Cannot merge when HEAD is detached"
            }
        
        head_ref = repo.head
        head_commit = head_ref.peel(pygit2.Commit)
        
        # Check if this is a fast-forward merge
        is_ff = repo.merge_base(head_commit.id, branch_commit.id) == head_commit.id
        
        if is_ff and not no_ff:
            # Fast-forward merge
            repo.checkout_tree(branch_commit)
            head_ref.set_target(branch_commit.id)
            
            return {
                "success": True,
                "message": f"Fast-forward merge of '{branch}' into '{head_ref.shorthand}'",
                "merge_type": "fast-forward",
                "result_commit": str(branch_commit.id)
            }
        else:
            # Non-fast-forward merge
            repo.merge(branch_commit.id)
            
            # Check for conflicts
            index = repo.index
            if index.conflicts:
                conflicts = []
                for conflict in index.conflicts:
                    conflict_info = {
                        "ancestor": conflict[0].path if conflict[0] else None,
                        "ours": conflict[1].path if conflict[1] else None,
                        "theirs": conflict[2].path if conflict[2] else None
                    }
                    conflicts.append(conflict_info)
                
                # Abort the merge
                repo.state_cleanup()
                
                return {
                    "success": False,
                    "message": "Merge conflicts detected",
                    "conflicts": conflicts
                }
            
            # No conflicts, create the merge commit if requested
            if not no_commit:
                author = None
                try:
                    author = pygit2.Signature(
                        repo.config['user.name'],
                        repo.config['user.email']
                    )
                except KeyError:
                    author = pygit2.Signature('FastFS-MCP', 'mcp@fastfs.com')
                
                # Determine commit message
                if not commit_message:
                    commit_message = f"Merge branch '{branch}' into {head_ref.shorthand}"
                
                # Write the index as a tree
                tree_id = index.write_tree()
                
                # Create the merge commit
                commit_id = repo.create_commit(
                    'HEAD',
                    author,
                    author,
                    commit_message,
                    tree_id,
                    [head_commit.id, branch_commit.id]
                )
                
                # Clean up the merge state
                repo.state_cleanup()
                
                commit = repo.get(commit_id)
                
                return {
                    "success": True,
                    "message": f"Merged '{branch}' into '{head_ref.shorthand}'",
                    "merge_type": "merge",
                    "result_commit": str(commit_id),
                    "commit": format_commit(commit)
                }
            else:
                # No commit requested, just leave the index with the merged state
                return {
                    "success": True,
                    "message": f"Merged '{branch}' into index (no commit)",
                    "merge_type": "merge-no-commit"
                }
    except Exception as e:
        log_error(f"Error merging branch {branch}: {str(e)}")
        # Clean up any merge state
        try:
            if repo and repo.state == pygit2.GIT_REPOSITORY_STATE_MERGE:
                repo.state_cleanup()
        except:
            pass
        
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_stash(path: str = None, command: str = "push", message: Optional[str] = None,
             include_untracked: bool = False, stash_index: Optional[int] = None) -> Dict[str, Any]:
    """
    Stash changes in the working directory.
    
    Args:
        path: Path to the repository (default: current directory)
        command: Stash command (push, pop, apply, list, drop, clear)
        message: Optional message for stash push
        include_untracked: Include untracked files in stash
        stash_index: Index of stash for pop, apply, drop commands
    
    Returns:
        Dictionary with stash operation results
    """
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        repo_path = repo.path
        
        # Fallback to git command for stashing (pygit2 stash support is limited)
        if command == "push":
            cmd = ["git", "stash", "push"]
            
            if message:
                cmd.extend(["-m", message])
            
            if include_untracked:
                cmd.append("--include-untracked")
            
            # Execute stash push
            process = subprocess.run(
                cmd,
                cwd=os.path.dirname(repo_path),
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                output = process.stdout.strip()
                if "No local changes to save" in output:
                    return {
                        "success": True,
                        "message": "No changes to stash"
                    }
                else:
                    return {
                        "success": True,
                        "message": "Changes stashed successfully",
                        "stash_id": "stash@{0}",
                        "output": output
                    }
            else:
                return {
                    "success": False,
                    "message": f"Stash push failed: {process.stderr.strip()}",
                    "error": process.stderr.strip()
                }
        
        elif command == "pop":
            cmd = ["git", "stash", "pop"]
            
            if stash_index is not None:
                cmd.append(f"stash@{{{stash_index}}}")
            
            # Execute stash pop
            process = subprocess.run(
                cmd,
                cwd=os.path.dirname(repo_path),
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": "Stash popped successfully",
                    "output": process.stdout.strip()
                }
            else:
                # Check for conflicts
                if "Merge conflict" in process.stderr:
                    return {
                        "success": False,
                        "message": "Stash pop resulted in conflicts",
                        "error": process.stderr.strip()
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Stash pop failed: {process.stderr.strip()}",
                        "error": process.stderr.strip()
                    }
        
        elif command == "apply":
            cmd = ["git", "stash", "apply"]
            
            if stash_index is not None:
                cmd.append(f"stash@{{{stash_index}}}")
            
            # Execute stash apply
            process = subprocess.run(
                cmd,
                cwd=os.path.dirname(repo_path),
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": "Stash applied successfully",
                    "output": process.stdout.strip()
                }
            else:
                # Check for conflicts
                if "Merge conflict" in process.stderr:
                    return {
                        "success": False,
                        "message": "Stash apply resulted in conflicts",
                        "error": process.stderr.strip()
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Stash apply failed: {process.stderr.strip()}",
                        "error": process.stderr.strip()
                    }
        
        elif command == "list":
            cmd = ["git", "stash", "list"]
            
            # Execute stash list
            process = subprocess.run(
                cmd,
                cwd=os.path.dirname(repo_path),
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                output = process.stdout.strip()
                stashes = []
                
                # Parse stash list output
                for line in output.split('\n'):
                    if line.strip():
                        match = re.match(r'stash@\{(\d+)\}: (.*)', line)
                        if match:
                            index = int(match.group(1))
                            message = match.group(2)
                            stashes.append({
                                "index": index,
                                "stash_id": f"stash@{{{index}}}",
                                "message": message
                            })
                
                return {
                    "success": True,
                    "stashes": stashes,
                    "count": len(stashes)
                }
            else:
                return {
                    "success": False,
                    "message": f"Stash list failed: {process.stderr.strip()}",
                    "error": process.stderr.strip()
                }
        
        elif command == "drop":
            cmd = ["git", "stash", "drop"]
            
            if stash_index is not None:
                cmd.append(f"stash@{{{stash_index}}}")
            
            # Execute stash drop
            process = subprocess.run(
                cmd,
                cwd=os.path.dirname(repo_path),
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Dropped stash@{{{stash_index if stash_index is not None else 0}}}",
                    "output": process.stdout.strip()
                }
            else:
                return {
                    "success": False,
                    "message": f"Stash drop failed: {process.stderr.strip()}",
                    "error": process.stderr.strip()
                }
        
        elif command == "clear":
            cmd = ["git", "stash", "clear"]
            
            # Execute stash clear
            process = subprocess.run(
                cmd,
                cwd=os.path.dirname(repo_path),
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": "Cleared all stashes"
                }
            else:
                return {
                    "success": False,
                    "message": f"Stash clear failed: {process.stderr.strip()}",
                    "error": process.stderr.strip()
                }
        
        else:
            return {
                "success": False,
                "message": f"Unknown stash command: {command}"
            }
    except Exception as e:
        log_error(f"Error in stash operation: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_tag(path: str = None, name: Optional[str] = None, target: str = "HEAD",
          message: Optional[str] = None, delete: bool = False, 
          force: bool = False) -> Dict[str, Any]:
    """
    Create, list, delete or verify a tag object.
    
    Args:
        path: Path to the repository (default: current directory)
        name: Name of the tag
        target: Target to tag (default: HEAD)
        message: Optional message for annotated tag
        delete: Whether to delete the tag
        force: Whether to force tag creation or deletion
    
    Returns:
        Dictionary with tag operation results
    """
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # List tags if no name provided
        if not name:
            tags = []
            for tag_name in repo.listall_references():
                if tag_name.startswith('refs/tags/'):
                    tag_shortname = tag_name[10:]  # Strip 'refs/tags/'
                    reference = repo.references[tag_name]
                    target_obj = reference.peel()
                    
                    # Check if this is an annotated tag
                    is_annotated = isinstance(target_obj, pygit2.Tag)
                    
                    tag_info = {
                        "name": tag_shortname,
                        "is_annotated": is_annotated,
                        "target": str(reference.target)
                    }
                    
                    if is_annotated:
                        tag_obj = target_obj
                        tag_info["message"] = tag_obj.message
                        tag_info["tagger"] = {
                            "name": tag_obj.tagger.name,
                            "email": tag_obj.tagger.email,
                            "time": datetime.fromtimestamp(tag_obj.tagger.time).isoformat()
                        }
                        tag_info["target_commit"] = str(tag_obj.get_object().id)
                    else:
                        # Lightweight tag
                        tag_info["target_commit"] = str(reference.target)
                    
                    tags.append(tag_info)
            
            return {
                "success": True,
                "tags": tags,
                "count": len(tags)
            }
        
        # Delete tag
        if delete:
            tag_ref = f"refs/tags/{name}"
            if tag_ref not in repo.references:
                return {
                    "success": False,
                    "message": f"Tag '{name}' not found"
                }
            
            repo.references.delete(tag_ref)
            
            return {
                "success": True,
                "message": f"Deleted tag '{name}'"
            }
        
        # Create tag
        tag_ref = f"refs/tags/{name}"
        if tag_ref in repo.references and not force:
            return {
                "success": False,
                "message": f"Tag '{name}' already exists. Use force=True to overwrite."
            }
        elif tag_ref in repo.references:
            # Delete existing tag if force is True
            repo.references.delete(tag_ref)
        
        # Resolve the target
        try:
            target_obj = repo.revparse_single(target)
            if not isinstance(target_obj, pygit2.Commit):
                target_obj = target_obj.peel(pygit2.Commit)
        except KeyError:
            return {
                "success": False,
                "message": f"Target '{target}' not found"
            }
        
        # Create the tag
        if message:
            # Annotated tag
            author = None
            try:
                author = pygit2.Signature(
                    repo.config['user.name'],
                    repo.config['user.email']
                )
            except KeyError:
                author = pygit2.Signature('FastFS-MCP', 'mcp@fastfs.com')
            
            tag_id = repo.create_tag(name, target_obj.id, pygit2.GIT_OBJ_COMMIT, author, message)
            tag_obj = repo.get(tag_id)
            
            return {
                "success": True,
                "message": f"Created annotated tag '{name}' at {target}",
                "tag": {
                    "name": name,
                    "is_annotated": True,
                    "target": str(tag_id),
                    "target_commit": str(target_obj.id),
                    "message": message,
                    "tagger": {
                        "name": author.name,
                        "email": author.email,
                        "time": datetime.fromtimestamp(author.time).isoformat()
                    }
                }
            }
        else:
            # Lightweight tag
            reference = repo.references.create(tag_ref, target_obj.id, force=force)
            
            return {
                "success": True,
                "message": f"Created lightweight tag '{name}' at {target}",
                "tag": {
                    "name": name,
                    "is_annotated": False,
                    "target": str(reference.target),
                    "target_commit": str(target_obj.id)
                }
            }
    except Exception as e:
        log_error(f"Error in tag operation: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_blame(path: str = None, file_path: str = None, rev: str = "HEAD") -> Dict[str, Any]:
    """
    Show what revision and author last modified each line of a file.
    
    Args:
        path: Path to the repository (default: current directory)
        file_path: Path to the file to blame
        rev: Revision to blame (default: HEAD)
    
    Returns:
        Dictionary with blame information
    """
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        if not file_path:
            return {
                "success": False,
                "message": "File path is required"
            }
        
        # Resolve the revision
        try:
            rev_obj = repo.revparse_single(rev)
            if not isinstance(rev_obj, pygit2.Commit):
                rev_obj = rev_obj.peel(pygit2.Commit)
        except KeyError:
            return {
                "success": False,
                "message": f"Revision '{rev}' not found"
            }
        
        # Get the tree from the revision
        tree = rev_obj.tree
        
        # Check if file exists in the tree
        try:
            tree[file_path]
        except KeyError:
            return {
                "success": False,
                "message": f"File '{file_path}' not found in revision {rev}"
            }
        
        # Perform blame
        blame = repo.blame(file_path, newest_commit=rev_obj.id)
        
        # Format blame results
        lines = []
        for i, hunk in enumerate(blame):
            commit = repo.get(hunk.final_commit_id)
            
            for j in range(hunk.lines_in_hunk):
                line_num = hunk.final_start_line_number + j
                
                line_info = {
                    "line_number": line_num,
                    "commit": {
                        "id": str(hunk.final_commit_id),
                        "short_id": str(hunk.final_commit_id)[:7],
                        "author": commit.author.name,
                        "author_email": commit.author.email,
                        "time": datetime.fromtimestamp(commit.author.time).isoformat(),
                        "summary": commit.message.split('\n', 1)[0] if commit.message else ""
                    }
                }
                
                lines.append(line_info)
        
        # Get the file content
        blob = repo.get(tree[file_path].id)
        content = blob.data.decode('utf-8', errors='replace').split('\n')
        
        # Add content to the lines
        for i, line_info in enumerate(lines):
            line_num = line_info["line_number"] - 1  # 0-based index
            if line_num < len(content):
                line_info["content"] = content[line_num]
        
        return {
            "success": True,
            "file_path": file_path,
            "revision": str(rev_obj.id),
            "lines": lines
        }
    except Exception as e:
        log_error(f"Error blaming file {file_path}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_grep(path: str = None, pattern: str = None, revision: str = "HEAD",
           ignore_case: bool = False, word_regexp: bool = False,
           paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Search for a pattern in tracked files.
    
    Note: pygit2 doesn't provide direct grep functionality, so we fall back to
    git command for this operation.
    
    Args:
        path: Path to the repository (default: current directory)
        pattern: Pattern to search for
        revision: Revision to search in (default: HEAD)
        ignore_case: Whether to ignore case
        word_regexp: Whether to match whole words
        paths: Optional list of paths to search
    
    Returns:
        Dictionary with grep results
    """
    import subprocess
    
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        if not pattern:
            return {
                "success": False,
                "message": "Search pattern is required"
            }
        
        # Build git grep command
        cmd = ["git", "grep", "-n"]  # -n to show line numbers
        
        if ignore_case:
            cmd.append("-i")
        
        if word_regexp:
            cmd.append("-w")
        
        cmd.append(pattern)
        cmd.append(revision)
        
        if paths:
            cmd.append("--")
            cmd.extend(paths)
        
        # Execute git grep
        process = subprocess.run(
            cmd,
            cwd=os.path.dirname(repo.path),
            capture_output=True,
            text=True
        )
        
        # Parse results
        matches = []
        if process.returncode == 0:
            for line in process.stdout.strip().split('\n'):
                if line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        file_path, line_num, content = parts
                        matches.append({
                            "file": file_path,
                            "line_number": int(line_num),
                            "content": content
                        })
            
            return {
                "success": True,
                "matches": matches,
                "count": len(matches),
                "pattern": pattern
            }
        elif process.returncode == 1:
            # No matches
            return {
                "success": True,
                "matches": [],
                "count": 0,
                "pattern": pattern,
                "message": "No matches found"
            }
        else:
            # Error
            return {
                "success": False,
                "message": f"Grep failed: {process.stderr.strip()}",
                "error": process.stderr.strip()
            }
    except Exception as e:
        log_error(f"Error grepping for pattern {pattern}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_context(path: str = None, details: str = "all") -> Dict[str, Any]:
    """
    Get comprehensive context about the current Git repository.
    
    Args:
        path: Path to the repository (default: current directory)
        details: Level of detail to include ("basic", "standard", "all")
    
    Returns:
        Dictionary with repository context information
    """
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Basic repository information
        result = {
            "success": True,
            "repository": {
                "path": os.path.dirname(repo.path),
                "is_bare": repo.is_bare,
                "is_empty": repo.is_empty,
                "is_shallow": repo.is_shallow
            }
        }
        
        # Current branch and HEAD information
        if not repo.is_empty:
            if not repo.head_is_detached:
                result["head"] = {
                    "type": "branch",
                    "name": repo.head.shorthand,
                    "commit": str(repo.head.target)
                }
            else:
                result["head"] = {
                    "type": "detached",
                    "commit": str(repo.head.target)
                }
            
            # Current HEAD commit
            head_commit = repo.head.peel(pygit2.Commit)
            result["head_commit"] = format_commit(head_commit)
        
        # Status information (staged, unstaged, untracked)
        status = git_status(path)
        if status["success"]:
            result["status"] = {
                "is_clean": status["is_clean"],
                "counts": status["counts"]
            }
            
            if details in ["standard", "all"]:
                result["status"]["files"] = status["files"]
        
        # Branches
        branches = git_branch(path=path)
        if branches["success"]:
            result["branches"] = branches["branches"]
        
        # Remotes
        remotes = git_remote(path=path)
        if remotes["success"]:
            result["remotes"] = remotes["remotes"]
        
        # Additional details for standard and all levels
        if details in ["standard", "all"]:
            # Recent commits
            log_result = git_log(path=path, max_count=5)
            if log_result["success"]:
                result["recent_commits"] = log_result["commits"]
            
            # Tags
            tags_result = git_tag(path=path)
            if tags_result["success"]:
                result["tags"] = tags_result["tags"]
        
        # Additional details for all level
        if details == "all":
            # Stashes
            stash_result = git_stash(path=path, command="list")
            if stash_result["success"]:
                result["stashes"] = stash_result["stashes"]
            
            # Repository info
            repo_info = {
                "is_worktree": repo.is_worktree,
                "path": repo.path,
                "workdir": repo.workdir
            }
            
            if not repo.is_empty:
                # Count commits
                walker = repo.walk(repo.head.target, pygit2.GIT_SORT_TIME)
                commit_count = sum(1 for _ in walker)
                repo_info["commit_count"] = commit_count
            
            result["repo_info"] = repo_info
        
        return result
    except Exception as e:
        log_error(f"Error getting repository context: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_validate(path: str = None) -> Dict[str, Any]:
    """
    Validate the Git repository for common issues.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with validation results
    """
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        result = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "info": []
        }
        
        # Check if repository is empty
        if repo.is_empty:
            result["info"].append("Repository is empty")
        
        # Check for uncommitted changes
        status = git_status(path)
        if status["success"] and not status["is_clean"]:
            result["warnings"].append(f"Repository has uncommitted changes ({status['counts']['total']} files)")
            result["status"] = status
        
        # Check for unpushed commits
        if not repo.is_empty and not repo.head_is_detached:
            branch_name = repo.head.shorthand
            remote_name = None
            remote_branch = None
            
            # Find the tracking branch
            try:
                config_key = f"branch.{branch_name}.remote"
                remote_name = repo.config[config_key]
                
                config_key = f"branch.{branch_name}.merge"
                remote_ref = repo.config[config_key]
                remote_branch = remote_ref.replace("refs/heads/", "")
                
                # Check if remote exists
                if remote_name in repo.remotes:
                    remote = repo.remotes[remote_name]
                    
                    # Check for unpushed commits
                    import subprocess
                    cmd = ["git", "rev-list", "--count", f"{remote_name}/{remote_branch}..{branch_name}"]
                    process = subprocess.run(
                        cmd,
                        cwd=os.path.dirname(repo.path),
                        capture_output=True,
                        text=True
                    )
                    
                    if process.returncode == 0:
                        unpushed_count = int(process.stdout.strip())
                        if unpushed_count > 0:
                            result["warnings"].append(f"{unpushed_count} unpushed commits")
                            result["unpushed_commits"] = unpushed_count
            except KeyError:
                # No tracking branch
                result["info"].append(f"Branch '{branch_name}' has no tracking branch")
        
        # Check for stashed changes
        stash_result = git_stash(path=path, command="list")
        if stash_result["success"] and stash_result.get("stashes"):
            stash_count = len(stash_result["stashes"])
            result["info"].append(f"{stash_count} stashed changes")
            result["stashes"] = stash_result["stashes"]
        
        # Check for .gitignore
        try:
            repo.revparse_single("HEAD:.gitignore")
        except KeyError:
            result["warnings"].append("No .gitignore file found")
        
        # Check if HEAD is detached
        if not repo.is_empty and repo.head_is_detached:
            result["warnings"].append("HEAD is detached")
        
        # Check if this is a shallow repository
        if repo.is_shallow:
            result["info"].append("Repository is shallow")
        
        return result
    except Exception as e:
        log_error(f"Error validating repository: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }

def git_suggest_commit(path: str = None) -> Dict[str, Any]:
    """
    Analyze changes and suggest a commit message.
    
    Args:
        path: Path to the repository (default: current directory)
    
    Returns:
        Dictionary with suggestion information
    """
    try:
        repo = find_repository(path)
        if not repo:
            return {
                "success": False,
                "message": f"No git repository found at {path or os.getcwd()}"
            }
        
        # Check if there are staged changes
        status = git_status(path)
        if not status["success"] or status["is_clean"] or status["counts"]["staged"] == 0:
            return {
                "success": False,
                "message": "No staged changes to analyze"
            }
        
        # Get diff of staged changes
        diff_result = git_diff(path=path, staged=True)
        if not diff_result["success"]:
            return {
                "success": False,
                "message": "Failed to get diff of staged changes"
            }
        
        diff = diff_result["diff"]
        
        result = {
            "success": True,
            "changes": {
                "files_changed": diff["stats"]["files_changed"],
                "insertions": diff["stats"]["insertions"],
                "deletions": diff["stats"]["deletions"],
                "file_details": []
            },
            "suggested_message": "",
            "suggested_type": "",
            "suggested_scope": ""
        }
        
        # Add file details
        for change in diff["changes"]:
            result["changes"]["file_details"].append({
                "path": change["new_file_path"],
                "status": change["status"],
                "additions": change["additions"],
                "deletions": change["deletions"],
                "is_binary": change["is_binary"]
            })
        
        # Determine file types changed
        file_types = set()
        has_tests = False
        has_docs = False
        has_config = False
        has_feature = False
        has_fix = False
        has_refactor = False
        
        for file in result["changes"]["file_details"]:
            path = file["path"]
            
            if path.endswith((".md", ".txt", ".rst", ".html", ".adoc")):
                has_docs = True
            elif path.endswith((".test.js", ".spec.js", ".test.py", ".spec.py", "_test.py", "_spec.py")) or "test" in path.lower() or "spec" in path.lower():
                has_tests = True
            elif path.endswith((".json", ".yml", ".yaml", ".toml", ".ini", ".conf", ".config", ".env", ".properties")):
                has_config = True
            
            # Extract file extension
            if "." in path:
                ext = path.split(".")[-1].lower()
                file_types.add(ext)
        
        # Analyze changes to determine the type of commit
        for change in diff["changes"]:
            if not change["is_binary"]:
                for hunk in change.get("hunks", []):
                    for line in hunk.get("lines", []):
                        if line["origin"] == '+':  # Addition
                            content = line["content"].lower()
                            if "fix" in content or "bug" in content or "issue" in content or "error" in content or "crash" in content:
                                has_fix = True
                            if "feature" in content or "feat" in content or "new" in content or "add" in content:
                                has_feature = True
                            if "refactor" in content or "clean" in content or "improve" in content or "simplify" in content:
                                has_refactor = True
        
        # Determine commit type based on changes
        if has_docs and all(file["path"].endswith((".md", ".txt", ".rst", ".html", ".adoc")) for file in result["changes"]["file_details"]):
            result["suggested_type"] = "docs"
        elif has_tests and all("test" in file["path"].lower() or "spec" in file["path"].lower() for file in result["changes"]["file_details"]):
            result["suggested_type"] = "test"
        elif has_config and all(file["path"].endswith((".json", ".yml", ".yaml", ".toml", ".ini", ".conf", ".config", ".env", ".properties")) for file in result["changes"]["file_details"]):
            result["suggested_type"] = "chore"
        elif has_fix:
            result["suggested_type"] = "fix"
        elif has_feature:
            result["suggested_type"] = "feat"
        elif has_refactor:
            result["suggested_type"] = "refactor"
        else:
            result["suggested_type"] = "chore"
        
        # Determine scope based on directories changed
        directories = set()
        for file in result["changes"]["file_details"]:
            path = file["path"]
            if "/" in path:
                directories.add(path.split("/")[0])
        
        if len(directories) == 1:
            result["suggested_scope"] = next(iter(directories))
        
        # Generate suggested commit message
        if result["suggested_type"] == "docs":
            if result["suggested_scope"]:
                result["suggested_message"] = f"docs({result['suggested_scope']}): update documentation"
            else:
                result["suggested_message"] = "docs: update documentation"
        elif result["suggested_type"] == "test":
            if result["suggested_scope"]:
                result["suggested_message"] = f"test({result['suggested_scope']}): add/update tests"
            else:
                result["suggested_message"] = "test: add/update tests"
        elif result["suggested_type"] == "fix":
            if result["suggested_scope"]:
                result["suggested_message"] = f"fix({result['suggested_scope']}): fix issue"
            else:
                result["suggested_message"] = "fix: fix issue"
        elif result["suggested_type"] == "feat":
            if result["suggested_scope"]:
                result["suggested_message"] = f"feat({result['suggested_scope']}): add new feature"
            else:
                result["suggested_message"] = "feat: add new feature"
        elif result["suggested_type"] == "refactor":
            if result["suggested_scope"]:
                result["suggested_message"] = f"refactor({result['suggested_scope']}): improve code structure"
            else:
                result["suggested_message"] = "refactor: improve code structure"
        else:
            if result["suggested_scope"]:
                result["suggested_message"] = f"chore({result['suggested_scope']}): update code"
            else:
                result["suggested_message"] = "chore: update code"
        
        return result
    except Exception as e:
        log_error(f"Error suggesting commit message: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "error": str(e)
        }
