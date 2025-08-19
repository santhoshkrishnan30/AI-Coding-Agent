from ..tools.base import BaseTool
from typing import Dict, Any, Optional

class SetPreferenceTool(BaseTool):
    @property
    def name(self) -> str:
        return "set_preference"
    
    @property
    def description(self) -> str:
        return "Set a user preference value"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "required": ["key", "value"],
            "optional": {}
        }
    
     
    def execute(self, key: str, value: Any) -> Dict[str, Any]:
        try:
            # Use the agent reference passed during registration
            if hasattr(self, 'agent') and self.agent:
                self.agent.working_memory.set_user_preference(key, value)
                self.agent.persistent_memory.store_preference(key, value, 0.8)
            
            return {
                "success": True,
                "message": f"Preference '{key}' set to '{value}'"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to set preference: {str(e)}"
            }

class ShowPreferencesTool(BaseTool):
    @property
    def name(self) -> str:
        return "show_preferences"
    
    @property
    def description(self) -> str:
        return "Display current user preferences"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "optional": {}
        }
    
    def execute(self) -> Dict[str, Any]:
        try:
            # Use the agent reference passed during registration
            if hasattr(self, 'agent') and self.agent:
                preferences = {
                    "verbosity": self.agent.working_memory.get_user_preference("verbosity", "normal"),
                    "auto_approve": self.agent.working_memory.get_user_preference("auto_approve", False),
                    "show_diffs": self.agent.working_memory.get_user_preference("show_diffs", True),
                    "communication_style": self.agent.working_memory.get_user_preference("communication_style", "balanced")
                }
            else:
                # Fallback preferences if agent not available
                preferences = {
                    "verbosity": "normal",
                    "auto_approve": False,
                    "show_diffs": True,
                    "communication_style": "balanced"
                }
            
            return {
                "success": True,
                "preferences": preferences,
                "message": "Current user preferences"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to show preferences: {str(e)}"
            }

class ShowLearningTool(BaseTool):
    @property
    def name(self) -> str:
        return "show_learning"
    
    @property
    def description(self) -> str:
        return "Display learning summary and insights"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "optional": {}
        }
    
    def execute(self) -> Dict[str, Any]:
        try:
            # Use the agent reference passed during registration
            if hasattr(self, 'agent') and self.agent:
                summary = self.agent.learning_system.get_learning_summary()
            else:
                # Fallback summary if agent not available
                summary = {
                    "memory_stats": {},
                    "learning_coverage": {
                        "interactions_analyzed": 0,
                        "tools_learned": 0,
                        "patterns_discovered": 0,
                        "error_patterns": 0
                    },
                    "user_preferences": {},
                    "top_insights": {}
                }
            return {
                "success": True,
                "summary": summary,
                "message": "Learning summary"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to show learning summary: {str(e)}"
            }