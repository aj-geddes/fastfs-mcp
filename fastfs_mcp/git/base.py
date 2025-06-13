                    "type": obj.type_str,
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

def _get_tree_entry_type(type_id: int) -> str:
    """Convert a tree entry type code to a string."""
    if type_id == pygit2.GIT_OBJ_BLOB:
        return "blob"
    elif type_id == pygit2.GIT_OBJ_TREE:
        return "tree"
    elif type_id == pygit2.GIT_OBJ_COMMIT:
        return "commit"
    elif type_id == pygit2.GIT_OBJ_TAG:
        return "tag"
    else:
        return "unknown"

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

# Additional functions and remaining implementations...
