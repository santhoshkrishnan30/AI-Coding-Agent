import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import os
import json
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

class WorkingMemory:
    def __init__(self):
        self.sessions = {}
        self.current_session_id = None
        self.max_sessions = 10  # Keep last 10 sessions
        
    def start_session(self) -> str:
        """Start a new working memory session"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "start_time": time.time(),
            "interactions": [],
            "file_contents": {},
            "git_status": None,
            "current_directory": os.getcwd(),
            "context_cache": {},
            "error_history": [],
            "success_patterns": [],
            "user_preferences": {}
        }
        self.current_session_id = session_id
        
        # Clean up old sessions if we have too many
        if len(self.sessions) > self.max_sessions:
            oldest_session = min(self.sessions.keys(), 
                               key=lambda k: self.sessions[k]["start_time"])
            del self.sessions[oldest_session]
            
        return session_id
    
    def end_session(self) -> Optional[Dict[str, Any]]:
        """End current session and return summary"""
        if not self.current_session_id:
            return None
            
        session = self.sessions[self.current_session_id]
        session["end_time"] = time.time()
        session["duration"] = session["end_time"] - session["start_time"]
        
        # Calculate session statistics
        session["stats"] = {
            "total_interactions": len(session["interactions"]),
            "successful_interactions": sum(1 for i in session["interactions"] 
                                         if i.get("result", {}).get("success", False)),
            "files_accessed": len(session["file_contents"]),
            "unique_errors": len(set(e.get("error_type", "") for e in session["error_history"]))
        }
        
        self.current_session_id = None
        return session
    
    def add_interaction(self, user_input: str, action: Dict[str, Any], result: Dict[str, Any]):
        """Add an interaction to the current session"""
        if not self.current_session_id:
            self.start_session()
            
        interaction = {
            "timestamp": time.time(),
            "user_input": user_input,
            "action": action,
            "result": result,
            "context_snapshot": self.get_context_summary()
        }
        
        self.sessions[self.current_session_id]["interactions"].append(interaction)
        
        # Track success patterns
        if result.get("success", False):
            self.sessions[self.current_session_id]["success_patterns"].append({
                "action_type": action.get("tool_name", ""),
                "input_pattern": self._extract_pattern(user_input),
                "timestamp": time.time()
            })
        
        # Track errors
        if not result.get("success", False):
            self.sessions[self.current_session_id]["error_history"].append({
                "error_type": result.get("error", "Unknown error"),
                "action": action,
                "timestamp": time.time()
            })
    
    def store_file_content(self, file_path: str, content: str, metadata: Dict[str, Any] = None):
        """Store file content in working memory with metadata"""
        if not self.current_session_id:
            self.start_session()
            
        self.sessions[self.current_session_id]["file_contents"][file_path] = {
            "content": content,
            "timestamp": time.time(),
            "size": len(content),
            "metadata": metadata or {}
        }
        
        # Update context cache
        self.sessions[self.current_session_id]["context_cache"][file_path] = {
            "last_accessed": time.time(),
            "access_count": self.sessions[self.current_session_id]["context_cache"]
                           .get(file_path, {}).get("access_count", 0) + 1
        }
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get file content from working memory"""
        if not self.current_session_id:
            return None
            
        file_data = self.sessions[self.current_session_id]["file_contents"].get(file_path)
        if file_data:
            # Update access time
            self.sessions[self.current_session_id]["context_cache"][file_path] = {
                "last_accessed": time.time(),
                "access_count": self.sessions[self.current_session_id]["context_cache"]
                               .get(file_path, {}).get("access_count", 0) + 1
            }
            return file_data["content"]
        return None
    
    def update_git_status(self, git_status: Dict[str, Any]):
        """Update git status in working memory"""
        if not self.current_session_id:
            self.start_session()
            
        self.sessions[self.current_session_id]["git_status"] = {
            "status": git_status,
            "timestamp": time.time()
        }
    
    def get_git_status(self) -> Optional[Dict[str, Any]]:
        """Get git status from working memory"""
        if not self.current_session_id:
            return None
        return self.sessions[self.current_session_id].get("git_status", {}).get("status")
    
    def get_recent_interactions(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent interactions from current session"""
        if not self.current_session_id:
            return []
            
        interactions = self.sessions[self.current_session_id]["interactions"]
        return interactions[-count:] if len(interactions) >= count else interactions
    
    def get_success_patterns(self) -> List[Dict[str, Any]]:
        """Get successful interaction patterns"""
        if not self.current_session_id:
            return []
        return self.sessions[self.current_session_id]["success_patterns"]
    
    def get_error_history(self) -> List[Dict[str, Any]]:
        """Get error history from current session"""
        if not self.current_session_id:
            return []
        return self.sessions[self.current_session_id]["error_history"]
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of current context"""
        if not self.current_session_id:
            return {}
            
        session = self.sessions[self.current_session_id]
        git_status_data = session.get("git_status", {})
        
        return {
            "current_directory": session["current_directory"],
            "files_in_memory": list(session["file_contents"].keys()),
            "recent_actions": [i["action"].get("tool_name", "") 
                            for i in session["interactions"][-3:]],
            "git_status": git_status_data.get("status") if git_status_data else None,
            "session_duration": time.time() - session["start_time"]
        }
    
    def get_user_preference(self, key: str, default_value: Any = None) -> Any:
        """Get user preference from working memory"""
        if not self.current_session_id:
            return default_value
        return self.sessions[self.current_session_id]["user_preferences"].get(key, default_value)
    
    def set_user_preference(self, key: str, value: Any):
        """Set user preference in working memory"""
        if not self.current_session_id:
            self.start_session()
        self.sessions[self.current_session_id]["user_preferences"][key] = value
    
    def _extract_pattern(self, text: str) -> str:
        """Extract simple pattern from user input for learning"""
        # Simple pattern extraction - in real implementation, use NLP
        words = text.lower().split()
        important_words = [w for w in words if len(w) > 3 and w not in 
                          ["what", "that", "this", "with", "from", "have", "were"]]
        return " ".join(important_words[:5])  # Top 5 important words
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        if not self.current_session_id:
            return {}
            
        session = self.sessions[self.current_session_id]
        return {
            "session_id": self.current_session_id,
            "duration": time.time() - session["start_time"],
            "interactions": len(session["interactions"]),
            "files_accessed": len(session["file_contents"]),
            "success_rate": (len(session["success_patterns"]) / 
                            max(1, len(session["interactions"]))) * 100,
            "errors": len(session["error_history"]),
            "user_preferences": session["user_preferences"]
        }