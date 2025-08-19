import os
import shutil
import git
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..tools.base import BaseTool

class BackupFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "backup_file"
    
    @property
    def description(self) -> str:
        return "Create a backup of a file before making changes"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "required": ["file_path"],
            "optional": {
                "backup_dir": {
                    "type": "string",
                    "default": "",
                    "description": "Directory to store backups (default: .agent_backups)"
                }
            }
        }
    
    def execute(self, file_path: str, backup_dir: str = '') -> Dict[str, Any]:
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File {file_path} does not exist",
                    "message": f"Cannot backup non-existent file: {file_path}"
                }
            
            # Use same drive as source file to avoid cross-drive issues
            if not backup_dir:
                # Create backup directory on the same drive as the source file
                drive_letter = os.path.splitdrive(file_path)[0]  # Get 'C:' from 'C:\path\file'
                if drive_letter:
                    backup_dir = os.path.join(drive_letter, "\\.agent_backups")
                else:
                    backup_dir = os.path.join(os.getcwd(), '.agent_backups')
            
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            relative_path = os.path.relpath(file_path, os.getcwd())
            safe_filename = relative_path.replace(os.sep, '_').replace('.', '_')
            backup_filename = f'{safe_filename}_{timestamp}'
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Use shutil.copy2 which preserves metadata and handles cross-drive copies
            shutil.copy2(file_path, backup_path)
            
            metadata = {
                "original_path": file_path,
                "backup_path": backup_path,
                "timestamp": timestamp,
                "size": os.path.getsize(file_path)
            }
            
            metadata_path = f'{backup_path}.meta'
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            return {
                "success": True,
                "backup_path": backup_path,
                "metadata": metadata,
                "message": f"Successfully created backup of {file_path} at {backup_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to backup file {file_path}: {str(e)}"
            }

class RestoreFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "restore_file"
    
    @property
    def description(self) -> str:
        return "Restore a file from a backup"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "required": ["backup_path"],
            "optional": {
                "target_path": {
                    "type": "string",
                    "default": "",
                    "description": "Path where the file should be restored (default: original location)"
                },
                "create_backup": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to create a backup of the current file before restoring"
                }
            }
        }
    
    def execute(self, backup_path: str, target_path: str = '', create_backup: bool = True) -> Dict[str, Any]:
        try:
            if not os.path.exists(backup_path):
                return {
                    "success": False,
                    "error": f"Backup file {backup_path} does not exist",
                    "message": f"Cannot restore from non-existent backup: {backup_path}"
                }
            
            metadata_path = f'{backup_path}.meta'
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            if not target_path:
                target_path = metadata.get("original_path", backup_path)
            
            if os.path.exists(target_path) and create_backup and target_path != backup_path:
                backup_tool = BackupFileTool()
                backup_result = backup_tool.execute(
                    file_path=target_path,
                    backup_dir=os.path.dirname(backup_path)
                )
                if not backup_result["success"]:
                    return {
                        "success": False,
                        "error": "Failed to create backup before restore",
                        "message": f"Could not backup current file: {backup_result['error']}"
                    }
            
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            shutil.copy2(backup_path, target_path)
            
            return {
                "success": True,
                "target_path": target_path,
                "backup_path": backup_path,
                "metadata": metadata,
                "message": f"Successfully restored file from {backup_path} to {target_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to restore file: {str(e)}"
            }

class ListBackupsTool(BaseTool):
    @property
    def name(self) -> str:
        return "list_backups"
    
    @property
    def description(self) -> str:
        return "List available backups"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "optional": {
                "backup_dir": {
                    "type": "string",
                    "default": "",
                    "description": "Directory to search for backups (default: .agent_backups)"
                },
                "file_pattern": {
                    "type": "string",
                    "default": "",
                    "description": "Pattern to filter backups (default: all)"
                }
            }
        }
    
    def execute(self, backup_dir: str = '', file_pattern: str = '') -> Dict[str, Any]:
        try:
            if not backup_dir:
                backup_dir = os.path.join(os.getcwd(), '.agent_backups')
            
            if not os.path.exists(backup_dir):
                return {
                    "success": True,
                    "backups": [],
                    "message": f"No backups found in {backup_dir}"
                }
            
            backups = []
            
            for filename in os.listdir(backup_dir):
                if filename.endswith('.meta'):
                    continue
                
                if file_pattern and file_pattern not in filename:
                    continue
                
                backup_path = os.path.join(backup_dir, filename)
                metadata_path = f'{backup_path}.meta'
                
                metadata = {}
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                    except:
                        pass
                
                stat = os.stat(backup_path)
                
                backups.append({
                    "filename": filename,
                    "backup_path": backup_path,
                    "original_path": metadata.get("original_path", ""),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "metadata": metadata
                })
            
            backups.sort(key=lambda x: x["created"], reverse=True)
            
            return {
                "success": True,
                "backups": backups,
                "count": len(backups),
                "message": f"Found {len(backups)} backups in {backup_dir}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to list backups: {str(e)}"
            }