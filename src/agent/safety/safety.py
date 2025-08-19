import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import sys
import os
import json
import hashlib
from pathlib import Path
import difflib
from typing import Dict, Any, List, Callable, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

class SafetyFramework:
    """Enhanced safety framework with learning capabilities"""
    
    def __init__(self):
        self.destructive_operations = [
            "write_file",
            "delete_file",
            "git_commit",
            "git_merge",
            "run_command",
            "build_project"
        ]
        
        self.high_risk_operations = [
            "delete_file",
            "git_merge",
            "run_command"
        ]
        
        self.approval_callbacks = {}
        self.approval_history = []
        self.console = Console()
        
        # Safety preferences
        self.auto_approve_safe = False
        self.remember_decisions = True
        self.confidence_threshold = 0.8
    
    def register_approval_callback(self, operation: str, callback: Callable):
        """Register a callback for operation approval"""
        self.approval_callbacks[operation] = callback
    
    def is_destructive(self, operation: str) -> bool:
        """Check if an operation is potentially destructive"""
        return operation in self.destructive_operations
    
    def is_high_risk(self, operation: str) -> bool:
        """Check if an operation is high risk"""
        return operation in self.high_risk_operations
    
    def get_risk_level(self, operation: str) -> str:
        """Get the risk level of an operation"""
        if operation in self.high_risk_operations:
            return "high"
        elif operation in self.destructive_operations:
            return "medium"
        else:
            return "low"
    
    def request_approval(self, operation: str, parameters: Dict[str, Any], 
                       context: Dict[str, Any] = None) -> bool:
        """Request user approval for an operation"""
        # Check if we have a remembered decision
        if self.remember_decisions:
            remembered_decision = self._get_remembered_decision(operation, parameters)
            if remembered_decision is not None:
                confidence = remembered_decision.get("confidence", 0.0)
                if confidence >= self.confidence_threshold:
                    return remembered_decision["approved"]
        
        # Generate preview
        preview = self.preview_changes(operation, parameters, context)
        
        # Display preview
        self._display_enhanced_preview(operation, preview, context)
        
        # Get approval
        if operation in self.approval_callbacks:
            approved = self.approval_callbacks[operation](operation, parameters, preview)
        else:
            approved = self._get_manual_approval(operation, preview)
        
        # Remember decision
        if self.remember_decisions:
            self._remember_decision(operation, parameters, approved)
        
        # Record in history
        self.approval_history.append({
            "operation": operation,
            "parameters": parameters,
            "approved": approved,
            "timestamp": time.time(),
            "preview": preview
        })
        
        return approved
    
    def preview_changes(self, operation: str, parameters: Dict[str, Any], 
                  context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a comprehensive preview of changes"""
        preview = {
            "operation": operation,
            "risk_level": self.get_risk_level(operation),
            "timestamp": time.time(),
            "changes": [],
            "impact": "unknown",
            "reversibility": "unknown",
            "recommendations": [],
            "preview": ""  # Add this line
        }
        
        # Operation-specific previews
        if operation == "write_file":
            preview = self._preview_write_file(parameters, preview)
        elif operation == "delete_file":
            preview = self._preview_delete_file(parameters, preview)
        elif operation == "git_commit":
            preview = self._preview_git_commit(parameters, preview, context)
        elif operation == "git_merge":
            preview = self._preview_git_merge(parameters, preview, context)
        elif operation == "run_command":
            preview = self._preview_run_command(parameters, preview)
        elif operation == "build_project":
            preview = self._preview_build_project(parameters, preview)
        
        return preview
    def _preview_write_file(self, parameters: Dict[str, Any], preview: Dict[str, Any]) -> Dict[str, Any]:
        """Preview write file operation"""
        file_path = parameters.get("file_path", "")
        content = parameters.get("content", "")
        
        preview["changes"] = [f"Write to file: {file_path}"]
        preview["impact"] = "moderate" if Path(file_path).exists() else "low"
        preview["reversibility"] = "high"  # Can be restored from backup
        
        # Add content preview
        if len(content) > 200:
            preview["content_preview"] = content[:200] + "..."
            preview["preview"] = f"Will write {len(content)} characters to {file_path}"
        else:
            preview["content_preview"] = content
            preview["preview"] = f"Will write to file: {file_path}"
        
        # Check if file exists
        if Path(file_path).exists():
            try:
                with open(file_path, 'r') as f:
                    old_content = f.read()
                
                # Generate diff
                diff = list(difflib.unified_diff(
                    old_content.splitlines(keepends=True),
                    content.splitlines(keepends=True),
                    fromfile="Current",
                    tofile="New"
                ))
                preview["diff"] = "".join(diff)
                
                preview["recommendations"].append("Consider creating a backup before overwriting")
            except Exception:
                preview["recommendations"].append("Unable to read existing file - backup recommended")
        else:
            preview["recommendations"].append("New file will be created")
        
        return preview
    
    def _preview_delete_file(self, parameters: Dict[str, Any], preview: Dict[str, Any]) -> Dict[str, Any]:
        """Preview delete file operation"""
        file_path = parameters.get("file_path", "")
        
        preview["changes"] = [f"Delete file: {file_path}"]
        preview["impact"] = "high"
        preview["reversibility"] = "low"  # Difficult to recover once deleted
        
        # Check file info
        if Path(file_path).exists():
            file_stat = Path(file_path).stat()
            preview["file_size"] = file_stat.st_size
            preview["file_modified"] = file_stat.st_mtime
            preview["recommendations"].append("This operation cannot be undone easily")
            preview["recommendations"].append("Consider moving to backup instead of deleting")
        else:
            preview["impact"] = "none"  # File doesn't exist
            preview["recommendations"].append("File does not exist")
        
        return preview
    
    def _preview_git_commit(self, parameters: Dict[str, Any], preview: Dict[str, Any], 
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Preview git commit operation"""
        message = parameters.get("message", "")
        files = parameters.get("files", [])
        
        preview["changes"] = [f"Commit with message: '{message}'"]
        preview["impact"] = "medium"
        preview["reversibility"] = "medium"  # Can be undone with git reset
        
        # Get git status if available
        if context and "git_status" in context:
            git_status = context["git_status"]
            if git_status.get("is_dirty", False):
                preview["staged_files"] = git_status.get("staged_files", [])
                preview["modified_files"] = git_status.get("modified_files", [])
                preview["recommendations"].append("Review staged changes before committing")
            else:
                preview["impact"] = "low"
                preview["recommendations"].append("No changes to commit")
        
        return preview
    
    def _preview_git_merge(self, parameters: Dict[str, Any], preview: Dict[str, Any], 
                         context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Preview git merge operation"""
        branch_name = parameters.get("branch_name", "")
        strategy = parameters.get("strategy", "merge")
        
        preview["changes"] = [f"Merge branch '{branch_name}' using {strategy} strategy"]
        preview["impact"] = "high"
        preview["reversibility"] = "low"  # Can be difficult to undo
        
        preview["recommendations"].append("Ensure you have committed all changes before merging")
        preview["recommendations"].append("Consider creating a backup branch first")
        
        if strategy == "merge":
            preview["recommendations"].append("This will create a merge commit")
        elif strategy == "rebase":
            preview["recommendations"].append("This will rebase your current branch on top of the target")
        elif strategy == "squash":
            preview["recommendations"].append("This will squash all commits into one")
        
        return preview
    
    def _preview_run_command(self, parameters: Dict[str, Any], preview: Dict[str, Any]) -> Dict[str, Any]:
        """Preview run command operation"""
        command = parameters.get("command", "")
        working_dir = parameters.get("working_directory", "")
        
        preview["changes"] = [f"Execute command: '{command}'"]
        preview["impact"] = "high"  # Commands can do anything
        preview["reversibility"] = "low"
        
        # Analyze command risk
        command_lower = command.lower()
        
        if any(cmd in command_lower for cmd in ["rm ", "del ", "format", "shutdown"]):
            preview["risk_level"] = "critical"
            preview["recommendations"].append("  WARNING: This command may cause data loss!")
        elif any(cmd in command_lower for cmd in ["git ", "mv ", "cp "]):
            preview["risk_level"] = "high"
            preview["recommendations"].append("This command modifies files or version control")
        elif any(cmd in command_lower for cmd in ["echo", "ls", "dir", "cat"]):
            preview["risk_level"] = "low"
            preview["impact"] = "low"
        
        preview["recommendations"].append("Review the command carefully before execution")
        
        if working_dir:
            preview["changes"].append(f"Working directory: {working_dir}")
        
        return preview
    
    def _preview_build_project(self, parameters: Dict[str, Any], preview: Dict[str, Any]) -> Dict[str, Any]:
        """Preview build project operation"""
        target = parameters.get("target", "")
        configuration = parameters.get("configuration", "release")
        
        preview["changes"] = [f"Build project with target: {target}, configuration: {configuration}"]
        preview["impact"] = "medium"
        preview["reversibility"] = "high"  # Build artifacts can be deleted
        
        preview["recommendations"].append("Ensure all dependencies are installed")
        preview["recommendations"].append("Build may take some time")
        
        return preview
    
    def _display_enhanced_preview(self, operation: str, preview: Dict[str, Any], 
                                context: Dict[str, Any] = None):
        """Display an enhanced preview with rich formatting"""
        # Create main preview panel
        risk_color = {
            "low": "green",
            "medium": "yellow",
            "high": "red",
            "critical": "bold red"
        }.get(preview["risk_level"], "white")
        
        preview_content = f"[bold]{operation}[/bold]\n"
        preview_content += f"Risk Level: [{risk_color}]{preview['risk_level'].upper()}[/{risk_color}]\n"
        preview_content += f"Impact: {preview['impact']}\n"
        preview_content += f"Reversibility: {preview['reversibility']}\n\n"
        
        preview_content += "[bold]Changes:[/bold]\n"
        for change in preview["changes"]:
            preview_content += f" {change}\n"
        
        if "content_preview" in preview:
            preview_content += f"\n[bold]Content Preview:[/bold]\n"
            preview_content += f"[dim]{preview['content_preview']}[/dim]\n"
        
        if "diff" in preview:
            preview_content += f"\n[bold]Diff:[/bold]\n"
            preview_content += f"[dim]{preview['diff'][:500]}[/dim]...\n"
        
        if preview["recommendations"]:
            preview_content += f"\n[bold]Recommendations:[/bold]\n"
            for rec in preview["recommendations"]:
                preview_content += f" {rec}\n"
        
        panel = Panel(
            preview_content,
            title=f"Operation Preview - {operation}",
            border_style=risk_color,
            expand=False
        )
        
        self.console.print(panel)
        
        # Display additional info if available
        if "file_size" in preview:
            size_mb = preview["file_size"] / (1024 * 1024)
            self.console.print(f"File size: {size_mb:.2f} MB")
    
    def _get_manual_approval(self, operation: str, preview: Dict[str, Any]) -> bool:
        """Get manual approval from user"""
        risk_level = preview["risk_level"]
        
        # For low risk operations with auto-approve enabled
        if self.auto_approve_safe and risk_level == "low":
            return True
        
        # Get user input based on risk level
        if risk_level == "critical":
            prompt = "\n[bold red]  CRITICAL RISK OPERATION [/bold red]\n"
            prompt += "Type 'CONFIRM' to proceed, or anything else to cancel: "
            response = input(prompt)
            return response.strip().upper() == "CONFIRM"
        
        elif risk_level == "high":
            prompt = "\n[bold red]High risk operation![/bold red]\n"
            prompt += "Are you sure you want to proceed? (yes/no): "
            response = input(prompt)
            return response.lower() in ["yes", "y"]
        
        else:
            prompt = "\nProceed with this operation? (yes/no): "
            response = input(prompt)
            return response.lower() in ["yes", "y"]
    
    def _get_remembered_decision(self, operation: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get a remembered decision for this operation"""
        # Create a hash of the operation and parameters
        decision_key = self._create_decision_key(operation, parameters)
        
        # Look for recent decisions (last 7 days)
        cutoff_time = time.time() - (7 * 24 * 60 * 60)
        
        for decision in reversed(self.approval_history):
            if decision["timestamp"] < cutoff_time:
                break
            
            if "decision_key" in decision and decision["decision_key"] == decision_key:
                return {
                    "approved": decision["approved"],
                    "confidence": min(1.0, decision.get("confidence", 0.5) + 0.1)
                }
        
        return None
    
    def _remember_decision(self, operation: str, parameters: Dict[str, Any], approved: bool):
        """Remember a decision for future reference"""
        # Add decision key to the last approval history entry
        if self.approval_history:
            last_decision = self.approval_history[-1]
            last_decision["decision_key"] = self._create_decision_key(operation, parameters)
            last_decision["confidence"] = 0.5  # Initial confidence
    
    def _create_decision_key(self, operation: str, parameters: Dict[str, Any]) -> str:
        """Create a unique key for a decision"""
        # Create a simplified version of parameters for hashing
        simplified_params = {}
        
        if operation == "write_file":
            simplified_params["file_path"] = parameters.get("file_path", "")
        elif operation == "run_command":
            simplified_params["command"] = parameters.get("command", "")
        elif operation == "git_commit":
            simplified_params["message"] = parameters.get("message", "")
        
        # Create hash
        param_str = json.dumps(simplified_params, sort_keys=True)
        return hashlib.md5(f"{operation}:{param_str}".encode()).hexdigest()
    
    def get_approval_statistics(self) -> Dict[str, Any]:
        """Get statistics about approval decisions"""
        total_approvals = len(self.approval_history)
        if total_approvals == 0:
            return {"total": 0}
        
        approved = sum(1 for decision in self.approval_history if decision["approved"])
        
        # Count by operation type
        by_operation = {}
        for decision in self.approval_history:
            op = decision["operation"]
            if op not in by_operation:
                by_operation[op] = {"total": 0, "approved": 0}
            by_operation[op]["total"] += 1
            if decision["approved"]:
                by_operation[op]["approved"] += 1
        
        # Count by risk level
        by_risk = {}
        for decision in self.approval_history:
            risk = decision.get("preview", {}).get("risk_level", "unknown")
            if risk not in by_risk:
                by_risk[risk] = {"total": 0, "approved": 0}
            by_risk[risk]["total"] += 1
            if decision["approved"]:
                by_risk[risk]["approved"] += 1
        
        return {
            "total": total_approvals,
            "approved": approved,
            "approval_rate": approved / total_approvals,
            "by_operation": by_operation,
            "by_risk_level": by_risk
        }
    
    def set_auto_approve_safe(self, enabled: bool):
        """Enable or disable auto-approval for safe operations"""
        self.auto_approve_safe = enabled
        print(f"Auto-approve for safe operations: {'enabled' if enabled else 'disabled'}")
    
    def set_remember_decisions(self, enabled: bool):
        """Enable or disable decision remembering"""
        self.remember_decisions = enabled
        print(f"Decision remembering: {'enabled' if enabled else 'disabled'}")
    
    def set_confidence_threshold(self, threshold: float):
        """Set the confidence threshold for remembered decisions"""
        self.confidence_threshold = max(0.0, min(1.0, threshold))
        print(f"Confidence threshold set to: {self.confidence_threshold}")