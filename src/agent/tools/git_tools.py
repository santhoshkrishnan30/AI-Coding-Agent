import os
import git
from .base import BaseTool
from typing import Dict, Any, List

class GitStatusTool(BaseTool):
    @property
    def name(self) -> str:
        return "git_status"

    @property
    def description(self) -> str:
        return "Get the current git repository status"

    def execute(self) -> Dict[str, Any]:
        try:
            repo = git.Repo(os.getcwd())
            return {
                "success": True,
                "is_dirty": repo.is_dirty(),
                "untracked_files": repo.untracked_files,
                "modified_files": [item.a_path for item in repo.index.diff(None)],
                "staged_files": [item.a_path for item in repo.index.diff("HEAD")],
                "active_branch": repo.active_branch.name,
                "message": "Successfully retrieved git status"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get git status"
            }

class GitDiffTool(BaseTool):
    @property
    def name(self) -> str:
        return "git_diff"

    @property
    def description(self) -> str:
        return "Show git diff for a file or all changes"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "required": [],
            "optional": {
                "file_path": ""
            }
        }

    def execute(self, file_path: str = "") -> Dict[str, Any]:
        try:
            repo = git.Repo(os.getcwd())
            
            if file_path:
                # Diff for a specific file
                diff_text = repo.git.diff([file_path]) if os.path.exists(file_path) else ""
            else:
                # Diff for all changes
                diff_text = repo.git.diff()
            
            return {
                "success": True,
                "diff": diff_text,
                "message": f"Successfully retrieved git diff for {file_path if file_path else 'all files'}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get git diff for {file_path if file_path else 'all files'}"
            }

class GitCommitTool(BaseTool):
    @property
    def name(self) -> str:
        return "git_commit"

    @property
    def description(self) -> str:
        return "Commit changes to the git repository"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "required": ["message"],
            "optional": {
                "files": []
            }
        }

    def execute(self, message: str, files: list = None) -> Dict[str, Any]:
        try:
            repo = git.Repo(os.getcwd())
            
            if files:
                # Add specific files
                for file_path in files:
                    repo.index.add([file_path])
            else:
                # Add all changes
                repo.git.add("-A")
            
            # Create commit
            commit = repo.index.commit(message)
            
            return {
                "success": True,
                "commit_hash": commit.hexsha,
                "message": f"Successfully committed changes with message: '{message}'"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to commit changes: {str(e)}"
            }

class GitBranchTool(BaseTool):
    @property
    def name(self) -> str:
        return "git_branch"
    
    @property
    def description(self) -> str:
        return "Manage git branches (list, create, delete, switch)"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "required": [],
            "optional": {
                "action": {
                    "type": "string",
                    "default": "list",
                    "description": "Action to perform (list, create, delete, switch)"
                },
                "branch_name": {
                    "type": "string",
                    "default": "",
                    "description": "Name of the branch"
                },
                "force": {
                    "type": "boolean",
                    "default": False,
                    "description": "Force operation"
                }
            }
        }
    
    def execute(self, action: str = "list", branch_name: str = "", force: bool = False) -> Dict[str, Any]:
        try:
            repo = git.Repo(os.getcwd())
            
            if action == "list":
                branches = []
                for branch in repo.branches:
                    branches.append({
                        "name": branch.name,
                        "is_current": branch.name == repo.active_branch.name,
                        "commit": branch.commit.hexsha[:7]
                    })
                
                return {
                    "success": True,
                    "branches": branches,
                    "current_branch": repo.active_branch.name,
                    "message": f"Found {len(branches)} branches"
                }
            
            elif action == "create":
                if not branch_name:
                    return {
                        "success": False,
                        "error": "Branch name is required for create action",
                        "message": "Please provide a branch name to create"
                    }
                
                new_branch = repo.create_head(branch_name)
                return {
                    "success": True,
                    "branch_name": branch_name,
                    "message": f"Created new branch '{branch_name}'"
                }
            
            elif action == "delete":
                if not branch_name:
                    return {
                        "success": False,
                        "error": "Branch name is required for delete action",
                        "message": "Please provide a branch name to delete"
                    }
                
                if branch_name == repo.active_branch.name:
                    return {
                        "success": False,
                        "error": "Cannot delete current branch",
                        "message": "Switch to another branch before deleting this one"
                    }
                
                repo.delete_head(branch_name, force=force)
                return {
                    "success": True,
                    "branch_name": branch_name,
                    "message": f"Deleted branch '{branch_name}'"
                }
            
            elif action == "switch":
                if not branch_name:
                    return {
                        "success": False,
                        "error": "Branch name is required for switch action",
                        "message": "Please provide a branch name to switch to"
                    }
                
                repo.git.checkout(branch_name)
                return {
                    "success": True,
                    "branch_name": branch_name,
                    "message": f"Switched to branch '{branch_name}'"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "message": f"Action '{action}' is not supported. Use list, create, delete, or switch."
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to manage git branches: {str(e)}"
            }

class GitMergeTool(BaseTool):
    @property
    def name(self) -> str:
        return "git_merge"
    
    @property
    def description(self) -> str:
        return "Merge a branch into the current branch"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "required": ["branch_name"],
            "optional": {
                "message": {
                    "type": "string",
                    "default": "",
                    "description": "Merge commit message"
                },
                "strategy": {
                    "type": "string",
                    "default": "merge",
                    "description": "Merge strategy (merge, rebase, squash)"
                }
            }
        }
    
    def execute(self, branch_name: str, message: str = "", strategy: str = "merge") -> Dict[str, Any]:
        try:
            repo = git.Repo(os.getcwd())
            
            if strategy == "merge":
                repo.git.merge(branch_name, m=message if message else f"Merge branch '{branch_name}'")
            elif strategy == "rebase":
                repo.git.rebase(branch_name)
            elif strategy == "squash":
                repo.git.merge("--squash", branch_name)
                if message:
                    repo.git.commit("-m", message)
                else:
                    repo.git.commit("-m", f"Squashed merge of branch '{branch_name}'")
            else:
                return {
                    "success": False,
                    "error": f"Unknown merge strategy: {strategy}",
                    "message": f"Strategy '{strategy}' is not supported. Use merge, rebase, or squash."
                }
            
            return {
                "success": True,
                "branch_name": branch_name,
                "strategy": strategy,
                "message": f"Merged branch '{branch_name}' using {strategy} strategy"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to merge branch '{branch_name}': {str(e)}"
            }