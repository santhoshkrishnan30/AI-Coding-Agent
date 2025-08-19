import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import os
import json
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import re
import threading

class LearningSystem:
    def __init__(self, persistent_memory):
        self.persistent_memory = persistent_memory
        self.learning_cache = {}
        self.cache_lock = threading.Lock()
        self.insight_generators = {
            "tool_effectiveness": self._generate_tool_effectiveness_insights,
            "user_patterns": self._generate_user_pattern_insights,
            "project_structure": self._generate_project_structure_insights,
            "error_patterns": self._generate_error_pattern_insights
        }
    
    def record_interaction(self, user_input: str, action: Dict[str, Any], 
                         result: Dict[str, Any], context: Dict[str, Any]):
        """Record an interaction and trigger learning processes"""
        # Record in persistent memory
        context_hash = self.persistent_memory.generate_context_hash(context)
        session_id = context.get("session_id", "unknown")
        
        self.persistent_memory.record_interaction(
            session_id, user_input, action, result, context.get("project_path")
        )
        
        # Record tool usage
        tool_name = action.get("tool_name", "")
        if tool_name:
            execution_time = result.get("execution_time", 0.0)
            self.persistent_memory.record_tool_usage(
                tool_name, context_hash, result.get("success", False), execution_time
            )
        
        # Update file knowledge
        if "file_path" in action.get("parameters", {}):
            file_path = action["parameters"]["file_path"]
            self.persistent_memory.update_file_knowledge(file_path)
        
        # Generate insights asynchronously
        self._trigger_async_learning(user_input, action, result, context)
    
    def _trigger_async_learning(self, user_input: str, action: Dict[str, Any], 
                              result: Dict[str, Any], context: Dict[str, Any]):
        """Trigger learning processes in background"""
        def learn():
            try:
                # Generate various types of insights
                for insight_type, generator in self.insight_generators.items():
                    insights = generator(user_input, action, result, context)
                    for insight in insights:
                        self.persistent_memory.store_learning_insight(
                            insight_type, insight["data"], insight["confidence"]
                        )
            except Exception as e:
                # Don't let learning errors affect main functionality
                pass
        
        # Run in separate thread to avoid blocking
        thread = threading.Thread(target=learn, daemon=True)
        thread.start()
    
    def _generate_tool_effectiveness_insights(self, user_input: str, action: Dict[str, Any], 
                                            result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict]:
        """Generate insights about tool effectiveness"""
        insights = []
        tool_name = action.get("tool_name", "")
        
        if tool_name and result.get("success"):
            # Analyze tool effectiveness in similar contexts
            context_hash = self.persistent_memory.generate_context_hash(context)
            effectiveness = self.persistent_memory.get_tool_effectiveness(tool_name, context_hash)
            
            if effectiveness["usage_count"] > 3 and effectiveness["success_rate"] > 0.8:
                insights.append({
                    "data": {
                        "type": "high_effectiveness_tool",
                        "tool_name": tool_name,
                        "context_pattern": self._extract_context_pattern(context),
                        "success_rate": effectiveness["success_rate"]
                    },
                    "confidence": min(1.0, effectiveness["usage_count"] / 10)
                })
        
        return insights
    
    def _generate_user_pattern_insights(self, user_input: str, action: Dict[str, Any], 
                                      result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict]:
        """Generate insights about user behavior patterns"""
        insights = []
        
        if result.get("success"):
            # Extract successful interaction patterns
            pattern = self._extract_user_pattern(user_input, action)
            
            if pattern:
                insights.append({
                    "data": {
                        "type": "successful_pattern",
                        "pattern": pattern,
                        "action_type": action.get("tool_name", ""),
                        "context_features": self._extract_context_features(context)
                    },
                    "confidence": 0.7
                })
        
        return insights
    
    def _generate_project_structure_insights(self, user_input: str, action: Dict[str, Any], 
                                           result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict]:
        """Generate insights about project structure"""
        insights = []
        project_path = context.get("project_path", "")
        
        if project_path and "file_path" in action.get("parameters", {}):
            file_path = action["parameters"]["file_path"]
            
            # Learn about file importance
            if result.get("success"):
                insights.append({
                    "data": {
                        "type": "important_file",
                        "file_path": file_path,
                        "action_type": action.get("tool_name", ""),
                        "project_path": project_path
                    },
                    "confidence": 0.6
                })
        
        return insights
    
    def _generate_error_pattern_insights(self, user_input: str, action: Dict[str, Any], 
                                        result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict]:
        """Generate insights about error patterns"""
        insights = []
        
        if not result.get("success"):
            error = result.get("error", "")
            tool_name = action.get("tool_name", "")
            
            # Analyze error patterns
            error_pattern = self._extract_error_pattern(error)
            
            if error_pattern:
                insights.append({
                    "data": {
                        "type": "error_pattern",
                        "error_pattern": error_pattern,
                        "tool_name": tool_name,
                        "context": self._extract_context_features(context)
                    },
                    "confidence": 0.8
                })
        
        return insights
    
    def _extract_context_pattern(self, context: Dict[str, Any]) -> str:
        """Extract a simple pattern from context"""
        features = []
        
        # Add project type
        if "project_path" in context:
            project_path = context["project_path"]
            if project_path:
                if "node_modules" in project_path or "package.json" in project_path:
                    features.append("nodejs")
                elif "requirements.txt" in project_path or "setup.py" in project_path:
                    features.append("python")
                elif "pom.xml" in project_path:
                    features.append("java")
        
        # Add git status
        git_status = context.get("git_status", {})
        if git_status and git_status.get("is_dirty"):
            features.append("dirty_repo")
        
        return "_".join(features) if features else "general"
    
    def _extract_user_pattern(self, user_input: str, action: Dict[str, Any]) -> Optional[str]:
        """Extract pattern from user input and action"""
        # Simple pattern extraction
        words = re.findall(r'\b\w+\b', user_input.lower())
        important_words = [w for w in words if len(w) > 3 and w not in 
                          ["what", "that", "this", "with", "from", "have", "were", "will"]]
        
        if important_words:
            return f"{'_'.join(important_words[:3])}_{action.get('tool_name', '')}"
        return None
    
    def _extract_context_features(self, context: Dict[str, Any]) -> List[str]:
        """Extract features from context"""
        features = []
        
        # Time-based features
        hour = datetime.now().hour
        if 9 <= hour <= 17:
            features.append("work_hours")
        else:
            features.append("off_hours")
        
        # Project features
        if "project_path" in context and context["project_path"]:
            project_path = context["project_path"]
            if "test" in project_path.lower():
                features.append("testing_context")
            if "src" in project_path.lower():
                features.append("development_context")
        
        return features
    
    def _extract_error_pattern(self, error: str) -> Optional[str]:
        """Extract pattern from error message"""
        if not error:
            return None
            
        error_lower = error.lower()
        
        if "file not found" in error_lower:
            return "file_not_found"
        elif "permission" in error_lower:
            return "permission_error"
        elif "timeout" in error_lower:
            return "timeout_error"
        elif "syntax" in error_lower:
            return "syntax_error"
        elif "module" in error_lower and "not found" in error_lower:
            return "module_not_found"
        
        return None
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get all learned user preferences"""
        preferences = {}
        
        # Get preference patterns from persistent memory directly
        try:
            # Get user preferences stored directly
            verbosity, _ = self.persistent_memory.get_preference("verbosity", "normal")
            if verbosity != "normal":
                preferences["verbosity"] = verbosity
            
            auto_approve, _ = self.persistent_memory.get_preference("auto_approve", False)
            if auto_approve:
                preferences["auto_approve"] = True
            
            show_diffs, _ = self.persistent_memory.get_preference("show_diffs", True)
            if not show_diffs:
                preferences["show_diffs"] = False
            
            # Get communication style
            comm_style, _ = self.persistent_memory.get_preference("communication_style", "balanced")
            if comm_style != "balanced":
                preferences["communication_style"] = comm_style
                
        except Exception as e:
            # If there's an error, return empty preferences
            pass
        
        return preferences
    
    def get_tool_recommendations(self, context: Dict[str, Any], task_description: str) -> List[Dict[str, Any]]:
        """Get tool recommendations based on learning"""
        recommendations = []
        context_hash = self.persistent_memory.generate_context_hash(context)
        
        # Get high-effectiveness tools for similar contexts
        try:
            insights = self.persistent_memory.get_learning_insights("tool_effectiveness")
            
            for insight in insights:
                if insight.get("confidence", 0) > 0.7:
                    data = insight.get("data", {})
                    if isinstance(data, dict) and data.get("type") == "high_effectiveness_tool":
                        # Check if context is similar
                        if self._is_context_similar(context, data.get("context_pattern", "")):
                            recommendations.append({
                                "tool_name": data.get("tool_name", ""),
                                "confidence": insight.get("confidence", 0.5),
                                "reason": f"High effectiveness ({data.get('success_rate', 0.5):.1%}) in similar contexts"
                            })
        except Exception as e:
            pass
        
        return recommendations[:3]  # Top 3 recommendations
    
    def _is_context_similar(self, context: Dict[str, Any], pattern: str) -> bool:
        """Check if context matches a pattern"""
        if not pattern:
            return False
        context_pattern = self._extract_context_pattern(context)
        return context_pattern == pattern or pattern in context_pattern
    
    def learn_from_feedback(self, user_input: str, action: Dict[str, Any], 
                           result: Dict[str, Any], feedback: str):
        """Learn from explicit user feedback"""
        if not feedback:
            return
            
        feedback_lower = feedback.lower()
        
        # Update user preferences based on feedback
        if "good" in feedback_lower or "yes" in feedback_lower or "correct" in feedback_lower:
            # Positive feedback - reinforce the pattern
            self.persistent_memory.store_preference(
                f"positive_feedback_{action.get('tool_name', '')}", 
                {"pattern": self._extract_user_pattern(user_input, action)},
                0.8
            )
            
        elif "bad" in feedback_lower or "no" in feedback_lower or "wrong" in feedback_lower:
            # Negative feedback - avoid the pattern
            self.persistent_memory.store_preference(
                f"negative_feedback_{action.get('tool_name', '')}", 
                {"pattern": self._extract_user_pattern(user_input, action)},
                0.8
            )
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get a summary of what the system has learned"""
        try:
            stats = self.persistent_memory.get_memory_stats()
            
            # Get top insights
            top_insights = {}
            for insight_type in ["tool_effectiveness", "user_patterns", "error_patterns"]:
                try:
                    insights = self.persistent_memory.get_learning_insights(insight_type)
                    top_insights[insight_type] = insights[:3]  # Top 3 per type
                except:
                    top_insights[insight_type] = []
            
            # Get user preferences
            preferences = self.get_user_preferences()
            
            return {
                "memory_stats": stats,
                "top_insights": top_insights,
                "user_preferences": preferences,
                "learning_coverage": {
                    "interactions_analyzed": stats.get("interaction_history_count", 0),
                    "tools_learned": len([i for i in top_insights.get("tool_effectiveness", []) 
                                        if i.get("confidence", 0) > 0.5]),
                    "patterns_discovered": len(top_insights.get("user_patterns", [])),
                    "error_patterns": len(top_insights.get("error_patterns", []))
                }
            }
        except Exception as e:
            # Return a minimal summary if there's an error
            return {
                "memory_stats": {},
                "top_insights": {},
                "user_preferences": {},
                "learning_coverage": {
                    "interactions_analyzed": 0,
                    "tools_learned": 0,
                    "patterns_discovered": 0,
                    "error_patterns": 0
                }
            }
    
    def adapt_communication_style(self, user_feedback: List[str]):
        """Adapt communication style based on user feedback"""
        if not user_feedback:
            return
            
        feedback_text = " ".join(user_feedback).lower()
        
        # Analyze feedback for communication preferences
        if "verbose" in feedback_text or "detailed" in feedback_text:
            self.persistent_memory.store_preference("communication_style", "verbose", 0.7)
        elif "concise" in feedback_text or "brief" in feedback_text:
            self.persistent_memory.store_preference("communication_style", "concise", 0.7)
        
        if "technical" in feedback_text:
            self.persistent_memory.store_preference("technical_level", "high", 0.7)
        elif "simple" in feedback_text or "basic" in feedback_text:
            self.persistent_memory.store_preference("technical_level", "low", 0.7)
    
    def predict_user_needs(self, context: Dict[str, Any]) -> List[str]:
        """Predict what the user might need next"""
        predictions = []
        
        try:
            # Get recent successful patterns
            insights = self.persistent_memory.get_learning_insights("user_patterns")
            
            # Find patterns that match current context
            context_features = self._extract_context_features(context)
            
            for insight in insights:
                if insight.get("confidence", 0) > 0.6:
                    data = insight.get("data", {})
                    if isinstance(data, dict) and data.get("type") == "successful_pattern":
                        # Check if context features match
                        pattern_features = data.get("context_features", [])
                        if any(feature in pattern_features for feature in context_features):
                            predictions.append(f"Likely to use {data.get('action_type', '')} tool")
        except Exception as e:
            pass
        
        return predictions[:3]  # Top 3 predictions