# src/agent/tools/file_tools.py
import os
import json
from .base import BaseTool
from typing import Dict, Any

# src/agent/tools/file_tools.py - Update the ReadFileTool
class ReadFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "read_file"
    
    @property
    def description(self) -> str:
        return "Read the contents of a file"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "required": ["file_path"],
            "optional": {}
        }
    
    def execute(self, file_path: str) -> Dict[str, Any]:
        try:
            # Debug: Log the file path
            print(f"DEBUG: ReadFileTool attempting to read file: '{file_path}'")
            print(f"DEBUG: Current working directory: '{os.getcwd()}'")
            
            # Check if file exists
            if not os.path.exists(file_path):
                print(f"DEBUG: File does not exist: '{file_path}'")
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "message": f"The file {file_path} does not exist"
                }
            
            # Check if it's a file (not a directory)
            if not os.path.isfile(file_path):
                print(f"DEBUG: Path is not a file: '{file_path}'")
                return {
                    "success": False,
                    "error": f"Not a file: {file_path}",
                    "message": f"The path {file_path} is not a file"
                }
            
            # Try reading the file with different encodings
            encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'utf-16', 'ascii']
            content = None
            used_encoding = None
            last_error = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                    used_encoding = encoding
                    break
                except UnicodeDecodeError as e:
                    last_error = e
                    continue
            
            if content is None:
                print(f"DEBUG: Could not decode file with any of the tried encodings")
                return {
                    "success": False,
                    "error": f"Encoding error: {str(last_error)}",
                    "message": f"Failed to read file {file_path} due to encoding issues"
                }
            
            # Clean up BOM if present
            if content.startswith('\ufeff'):
                content = content[1:]
                print(f"DEBUG: Removed UTF-8 BOM from content")
            
            print(f"DEBUG: Successfully read file with encoding {used_encoding}, content length: {len(content)}")
            print(f"DEBUG: Content preview: '{content[:100]}...'")
            
            return {
                "success": True,
                "content": content,
                "message": f"Successfully read file: {file_path} (encoding: {used_encoding})"
            }
        except Exception as e:
            print(f"DEBUG: Error reading file: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to read file: {file_path}"
            }

class WriteFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "write_file"
    
    @property
    def description(self) -> str:
        return "Write content to a file"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "required": ["file_path", "content"],
            "optional": {}
        }
    
    def execute(self, file_path: str, content: str) -> Dict[str, Any]:
        try:
            print(f"DEBUG: WriteFileTool attempting to write to file: '{file_path}'")
            
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                print(f"DEBUG: Created directory: '{directory}'")
            
            # Write the file
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            print(f"DEBUG: Successfully wrote {len(content)} characters to file")
            
            return {
                "success": True,
                "message": f"Successfully wrote to file: {file_path}"
            }
        except Exception as e:
            print(f"DEBUG: Error writing file: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to write to file: {file_path}"
            }

class ListDirectoryTool(BaseTool):
    @property
    def name(self) -> str:
        return "list_directory"
    
    @property
    def description(self) -> str:
        return "List the contents of a directory"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "required": [],
            "optional": {
                "path": {"type": "string", "default": "."}
            }
        }
    
    def execute(self, path: str = ".") -> Dict[str, Any]:
        try:
            print(f"DEBUG: ListDirectoryTool attempting to list directory: '{path}'")
            
            if not os.path.exists(path):
                print(f"DEBUG: Directory does not exist: '{path}'")
                return {
                    "success": False,
                    "error": f"Directory not found: {path}",
                    "message": f"The directory {path} does not exist"
                }
            
            if not os.path.isdir(path):
                print(f"DEBUG: Path is not a directory: '{path}'")
                return {
                    "success": False,
                    "error": f"Not a directory: {path}",
                    "message": f"The path {path} is not a directory"
                }
            
            items = os.listdir(path)
            print(f"DEBUG: Found {len(items)} items in directory")
            
            return {
                "success": True,
                "items": items,
                "message": f"Successfully listed directory: {path}"
            }
        except Exception as e:
            print(f"DEBUG: Error listing directory: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to list directory: {path}"
            }