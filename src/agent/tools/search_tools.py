import os
import re
import fnmatch
from typing import Dict, Any, List
from ..tools.base import BaseTool

class SearchCodebaseTool(BaseTool):
    @property
    def name(self) -> str:
        return "search_codebase"
    
    @property
    def description(self) -> str:
        return "Search for text patterns in the codebase"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "required": ["pattern"],
            "optional": {
                "file_pattern": {
                    "type": "string",
                    "default": "*",
                    "description": "Pattern to match file names (e.g., *.py)"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to perform case-sensitive search"
                },
                "include_binary": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to include binary files in search"
                }
            }
        }
    
    def execute(self, pattern: str, file_pattern: str = "*", case_sensitive: bool = False, 
                include_binary: bool = False) -> Dict[str, Any]:
        try:
            matches = []
            total_files = 0
            searched_files = 0
            
            # Compile regex pattern
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return {
                    "success": False,
                    "error": f"Invalid regex pattern: {str(e)}",
                    "message": f"Invalid search pattern: {str(e)}"
                }
            
            # Walk through directory
            for root, dirs, files in os.walk(os.getcwd()):
                for filename in files:
                    total_files += 1
                    
                    # Skip if file doesn't match pattern
                    if not fnmatch.fnmatch(filename, file_pattern):
                        continue
                    
                    filepath = os.path.join(root, filename)
                    
                    # Skip binary files if not included
                    if not include_binary and self._is_binary_file(filepath):
                        continue
                    
                    searched_files += 1
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            # Search for matches
                            line_matches = []
                            lines = content.split('\n')
                            
                            for i, line in enumerate(lines):
                                if regex.search(line):
                                    line_matches.append({
                                        "line_number": i + 1,
                                        "line": line.strip(),
                                        "match": regex.search(line).group()
                                    })
                            
                            if line_matches:
                                matches.append({
                                    "file": filepath,
                                    "matches": line_matches
                                })
                    except Exception as e:
                        # Skip files that can't be read
                        continue
            
            return {
                "success": True,
                "pattern": pattern,
                "file_pattern": file_pattern,
                "matches": matches,
                "match_count": sum(len(m["matches"]) for m in matches),
                "file_count": len(matches),
                "files_searched": searched_files,
                "total_files": total_files,
                "message": f"Found {sum(len(m['matches']) for m in matches)} matches in {len(matches)} files"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to search codebase: {str(e)}"
            }
    
    def _is_binary_file(self, filepath: str) -> bool:
        """Check if a file is binary"""
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except:
            return True

class GetStructureTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_structure"
    
    @property
    def description(self) -> str:
        return "Get the directory structure of the project"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "optional": {
                "path": {
                    "type": "string",
                    "default": ".",
                    "description": "Path to get structure for (default: current directory)"
                },
                "max_depth": {
                    "type": "integer",
                    "default": 5,
                    "description": "Maximum depth to traverse"
                },
                "include_files": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to include files in the structure"
                },
                "exclude_patterns": {
                    "type": "array",
                    "default": ["__pycache__", ".git", "node_modules", ".vscode"],
                    "description": "Patterns to exclude from the structure"
                }
            }
        }
    
    def execute(self, path: str = ".", max_depth: int = 5, include_files: bool = True, 
                exclude_patterns: List[str] = None) -> Dict[str, Any]:
        try:
            if exclude_patterns is None:
                exclude_patterns = ["__pycache__", ".git", "node_modules", ".vscode"]
            
            structure = self._build_structure(path, max_depth, include_files, exclude_patterns)
            
            return {
                "success": True,
                "structure": structure,
                "path": os.path.abspath(path),
                "message": f"Retrieved structure for {os.path.abspath(path)}"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get structure: {str(e)}"
            }
    
    def _build_structure(self, path: str, max_depth: int, include_files: bool, 
                         exclude_patterns: List[str], current_depth: int = 0) -> Dict[str, Any]:
        """Recursively build directory structure"""
        if current_depth >= max_depth:
            return {"type": "directory", "name": os.path.basename(path), "truncated": True}
        
        structure = {
            "type": "directory",
            "name": os.path.basename(path),
            "path": os.path.abspath(path),
            "children": []
        }
        
        try:
            for item in os.listdir(path):
                # Skip excluded patterns
                if any(pattern in item for pattern in exclude_patterns):
                    continue
                
                item_path = os.path.join(path, item)
                
                if os.path.isdir(item_path):
                    # Recursively add directory
                    dir_structure = self._build_structure(
                        item_path, max_depth, include_files, exclude_patterns, current_depth + 1
                    )
                    structure["children"].append(dir_structure)
                elif include_files:
                    # Add file
                    structure["children"].append({
                        "type": "file",
                        "name": item,
                        "path": os.path.abspath(item_path),
                        "size": os.path.getsize(item_path)
                    })
        except PermissionError:
            # Skip directories we can't access
            structure["error"] = "Permission denied"
        
        return structure