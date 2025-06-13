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

# Additional Git functions can be implemented as needed
