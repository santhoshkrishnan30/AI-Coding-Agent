import os
import json
import re
import time
from .llm_integration import LLMIntegration
from src.interface.terminal import TerminalInterface
from .tools.base import ToolRegistry
from .memory.working_memory import WorkingMemory
from .memory.persistent_memory import PersistentMemory
from .learning.learning import LearningSystem
from .safety.safety import SafetyFramework
from typing import Dict, Any, List, Optional, Tuple

class Agent:
    def __init__(self):
        self.llm = LLMIntegration()
        self.interface = TerminalInterface()
        self.tool_registry = ToolRegistry()
        self.safety = SafetyFramework()
        
        # Initialize memory systems
        self.working_memory = WorkingMemory()
        self.persistent_memory = PersistentMemory()
        self.learning_system = LearningSystem(self.persistent_memory)
        
        # Start new session
        self.session_id = self.working_memory.start_session()
        
        # Load learned preferences
        self._load_learned_preferences()
        
        # Register tools
        self._register_tools()
        
        # Setup safety callbacks
        self._setup_safety_callbacks()
        
        # Initialize context
        self.current_context = {
            "session_id": self.session_id,
            "project_path": os.getcwd(),
            "start_time": time.time()
        }
    
    def _load_learned_preferences(self):
        """Load preferences learned from previous sessions"""
        # Load user preferences
        verbosity, _ = self.persistent_memory.get_preference("verbosity", "normal")
        self.working_memory.set_user_preference("verbosity", verbosity)
        
        auto_approve, _ = self.persistent_memory.get_preference("auto_approve", False)
        self.working_memory.set_user_preference("auto_approve", auto_approve)
        
        show_diffs, _ = self.persistent_memory.get_preference("show_diffs", True)
        self.working_memory.set_user_preference("show_diffs", show_diffs)
        
        # Load communication style preferences
        comm_style, _ = self.persistent_memory.get_preference("communication_style", "balanced")
        self.working_memory.set_user_preference("communication_style", comm_style)
    
    def _register_tools(self):
        from .tools.file_tools import ReadFileTool, WriteFileTool, ListDirectoryTool
        from .tools.git_tools import GitStatusTool, GitDiffTool, GitCommitTool
        from .tools.execution_tools import RunCommandTool, RunTestsTool
        from .tools.build_tools import BuildProjectTool
        from .tools.code_analysis_tools import RunLinterTool, AnalyzeDependenciesTool, FindReferencesTool
        from .tools.search_tools import SearchCodebaseTool, GetStructureTool
        from .tools.rollback_tools import BackupFileTool, RestoreFileTool, ListBackupsTool
        from .tools.testing_tools import GenerateTestTool
        from .tools.preference_tools import SetPreferenceTool, ShowPreferencesTool, ShowLearningTool
        
        # File tools
        self.tool_registry.register_tool(ReadFileTool())
        self.tool_registry.register_tool(WriteFileTool())
        self.tool_registry.register_tool(ListDirectoryTool())
        
        # Git tools
        self.tool_registry.register_tool(GitStatusTool())
        self.tool_registry.register_tool(GitDiffTool())
        self.tool_registry.register_tool(GitCommitTool())
        
        # Execution tools
        self.tool_registry.register_tool(RunCommandTool())
        self.tool_registry.register_tool(RunTestsTool())
        self.tool_registry.register_tool(BuildProjectTool())
        
        # Code analysis tools
        self.tool_registry.register_tool(RunLinterTool())
        self.tool_registry.register_tool(AnalyzeDependenciesTool())
        self.tool_registry.register_tool(FindReferencesTool())
        
        # Search tools
        self.tool_registry.register_tool(SearchCodebaseTool())
        self.tool_registry.register_tool(GetStructureTool())
        
        # Rollback tools
        self.tool_registry.register_tool(BackupFileTool())
        self.tool_registry.register_tool(RestoreFileTool())
        self.tool_registry.register_tool(ListBackupsTool())
        
        # Testing tools
        self.tool_registry.register_tool(GenerateTestTool())
        
        # Preference tools - pass self to avoid circular imports
        set_pref_tool = SetPreferenceTool()
        set_pref_tool.agent = self
        self.tool_registry.register_tool(set_pref_tool)
        
        show_pref_tool = ShowPreferencesTool()
        show_pref_tool.agent = self
        self.tool_registry.register_tool(show_pref_tool)
        
        show_learning_tool = ShowLearningTool()
        show_learning_tool.agent = self
        self.tool_registry.register_tool(show_learning_tool)

    def _setup_safety_callbacks(self):
        """Setup safety approval callbacks"""
        self.safety.register_approval_callback("write_file", self._approve_file_write)
        self.safety.register_approval_callback("git_commit", self._approve_git_commit)
        self.safety.register_approval_callback("run_command", self._approve_command_execution)
    
    def perceive(self, user_input: str) -> Dict[str, Any]:
        """Perceive the current state and user input"""
        # Get current directory and environment
        current_dir = os.getcwd()
        git_status = self._get_git_status()
        
        # Get context from working memory
        recent_interactions = self.working_memory.get_recent_interactions(3)
        context_summary = self.working_memory.get_context_summary()
        
        # Get learning insights
        tool_recommendations = self.learning_system.get_tool_recommendations(
            self.current_context, user_input
        )
        
        # Update current context
        self.current_context.update({
            "user_input": user_input,
            "current_directory": current_dir,
            "git_status": git_status,
            "recent_interactions": recent_interactions,
            "context_summary": context_summary,
            "tool_recommendations": tool_recommendations,
            "timestamp": time.time()
        })
        
        # Store in working memory
        self.working_memory.update_git_status(git_status)
        
        return self.current_context
    
    def _get_git_status(self) -> Dict[str, Any]:
        """Get current git repository status"""
        try:
            import git
            repo = git.Repo(os.getcwd())
            return {
                "is_git_repo": True,
                "active_branch": repo.active_branch.name,
                "is_dirty": repo.is_dirty(),
                "untracked_files": repo.untracked_files,
                "modified_files": [item.a_path for item in repo.index.diff(None)],
                "staged_files": [item.a_path for item in repo.index.diff("HEAD")]
            }
        except:
            return {"is_git_repo": False}
    
    def reason(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Reason about the current state and plan actions"""
        # Get available tools with effectiveness data
        available_tools = []
        for tool_info in self.tool_registry.list_tools():
            tool_name = tool_info["name"]
            context_hash = self.persistent_memory.generate_context_hash(state)
            effectiveness = self.persistent_memory.get_tool_effectiveness(tool_name, context_hash)
            
            tool_info["effectiveness"] = effectiveness
            available_tools.append(tool_info)
        
        # Get learning insights
        insights = self.learning_system.get_learning_summary()
        
        # Get user preferences
        verbosity = self.working_memory.get_user_preference("verbosity", "normal")
        auto_approve = self.working_memory.get_user_preference("auto_approve", False)
        
        # Build enhanced prompt
        prompt = f"""
        You are an AI coding agent with learning capabilities. Based on the user's input and current context, decide which tool to use and with what parameters.
        
        Current Context:
        - Current Directory: {state['current_directory']}
        - Git Status: {state['git_status']}
        - Session ID: {state.get('session_id', 'unknown')}
        - Recent Interactions: {len(state.get('recent_interactions', []))}
        
        Available Tools with Effectiveness:
        {json.dumps(available_tools, indent=2)}
        
        Learning Insights:
        - Top Tool Recommendations: {[r['tool_name'] for r in state.get('tool_recommendations', [])]}
        - User Preferences: verbosity={verbosity}, auto_approve={auto_approve}
        - Learning Coverage: {insights.get('learning_coverage', {})}
        
        User input: {state['user_input']}
        
        IMPORTANT: If the user asks to read a file (e.g., "read file.txt", "what's in package.json"), ALWAYS use the read_file tool with the exact file path.
        
        Respond in the following JSON format:
        {{
            "tool_name": "[tool_name]",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }},
            "reasoning": "Explain why this tool and parameters were chosen, considering learned patterns and effectiveness"
        }}
        """
        
        messages = [
            {"role": "system", "content": "You are an AI coding agent that learns from interactions and adapts to user preferences. Respond only with valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response_format = {"type": "json_object"}
            response = self.llm.generate_structured_response(messages, response_format)
            
            # Check if response is already a dict (fallback mode)
            if isinstance(response, dict) and "content" in response:
                try:
                    parsed_response = json.loads(response["content"])
                    # Validate that the tool exists
                    tool_name = parsed_response.get("tool_name")
                    if tool_name and tool_name in [tool["name"] for tool in available_tools]:
                        return parsed_response
                    else:
                        print(f"⚠️ Invalid tool requested: {tool_name}, using fallback")
                        return self._fallback_reasoning(state["user_input"])
                except json.JSONDecodeError:
                    print(f"⚠️ Failed to parse JSON: {response['content']}")
                    return self._fallback_reasoning(state["user_input"])
            else:
                return response
                
        except Exception as e:
            print(f"⚠️ LLM reasoning failed: {e}")
            return self._fallback_reasoning(state["user_input"])
    
    def _fix_parameter_structure(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fix parameter structure if LLM returns it incorrectly"""
        fixed_parameters = {}
        
        # Handle the case where LLM returns parameters wrapped in 'optional' or 'required'
        if "optional" in parameters:
            fixed_parameters.update(parameters["optional"])
        elif "required" in parameters:
            fixed_parameters.update(parameters["required"])
        else:
            fixed_parameters = parameters
        
        # Special handling for specific tools
        if tool_name == "analyze_dependencies":
            if "file_path" in fixed_parameters and isinstance(fixed_parameters["file_path"], dict):
                # Extract the actual value from the dict
                if "default" in fixed_parameters["file_path"]:
                    fixed_parameters["file_path"] = fixed_parameters["file_path"]["default"]
                elif "value" in fixed_parameters["file_path"]:
                    fixed_parameters["file_path"] = fixed_parameters["file_path"]["value"]
                else:
                    fixed_parameters["file_path"] = ""
        
        return fixed_parameters
    
    def act(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the planned action"""
        tool_name = action.get("tool_name")
        parameters = action.get("parameters", {})
        
        start_time = time.time()
        
        # Debug: Log the action
        print(f"DEBUG: Agent.act executing tool '{tool_name}' with parameters {parameters}")
        
        # Check if operation requires approval
        if self.safety.is_destructive(tool_name):
            auto_approve = self.working_memory.get_user_preference("auto_approve", False)
            
            if not auto_approve:
                preview = self.safety.preview_changes(tool_name, parameters)
                if not self.safety.request_approval(tool_name, parameters, preview):
                    return {
                        "success": False,
                        "error": "Operation cancelled by user",
                        "message": f"User cancelled the {tool_name} operation",
                        "execution_time": time.time() - start_time
                    }
        
        # Get tool
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            print(f"DEBUG: Tool '{tool_name}' not found in registry")
            return {
                "success": False,
                "error": f"Tool {tool_name} not found",
                "message": "Unknown tool requested",
                "execution_time": time.time() - start_time
            }
        
        # Fix parameter structure if needed
        fixed_parameters = self._fix_parameter_structure(tool_name, parameters)
        
        # Validate parameters
        validation = tool.validate_parameters(fixed_parameters)
        if not validation["valid"]:
            print(f"DEBUG: Parameter validation failed for tool '{tool_name}': {validation['errors']}")
            return {
                "success": False,
                "error": "Invalid parameters",
                "message": f"Parameter validation failed: {', '.join(validation['errors'])}",
                "execution_time": time.time() - start_time
            }
        
        # Execute tool with validated parameters
        print(f"DEBUG: Executing tool '{tool_name}' with validated parameters: {validation['parameters']}")
        result = tool.execute(**validation["parameters"])
        result["execution_time"] = time.time() - start_time
        
        # Store file content in working memory if it's a read operation
        if tool_name == "read_file" and result.get("success"):
            file_path = fixed_parameters.get("file_path", "")
            if file_path:
                self.working_memory.store_file_content(
                    file_path, 
                    result.get("content", ""),
                    {"tool_used": tool_name, "timestamp": time.time()}
                )
        
        # Debug: Log the result
        print(f"DEBUG: Tool execution result: {result}")
        
        return result
    
    def learn(self, state: Dict[str, Any], action: Dict[str, Any], result: Dict[str, Any]):
        """Learn from the interaction"""
        # Record interaction in learning system
        self.learning_system.record_interaction(
            state.get("user_input", ""), 
            action, 
            result, 
            state
        )
        
        # Add interaction to working memory
        self.working_memory.add_interaction(
            state.get("user_input", ""), 
            action, 
            result
        )
        
        # Record in persistent memory
        self.persistent_memory.record_interaction(
            self.session_id,
            state.get("user_input", ""),
            action,
            result,
            state.get("project_path")
        )
        
        # Ask for feedback on significant operations
        if self._is_significant_operation(action):
            self._request_feedback(state, action, result)
    
    def _is_significant_operation(self, action: Dict[str, Any]) -> bool:
        """Determine if an operation is significant enough to request feedback"""
        tool_name = action.get("tool_name", "")
        
        # Destructive operations are significant
        if self.safety.is_destructive(tool_name):
            return True
        
        # Operations that modify files are significant
        if tool_name in ["write_file", "delete_file"]:
            return True
        
        return False
    
    def _request_feedback(self, state: Dict[str, Any], action: Dict[str, Any], result: Dict[str, Any]):
        """Request user feedback for learning"""
        response = self.interface.get_user_input(
            "Was this operation helpful? (good/bad/skip): "
        )
        
        if response.lower() in ["good", "bad"]:
            # Learn from feedback
            self.learning_system.learn_from_feedback(
                state.get("user_input", ""), 
                action, 
                result, 
                response
            )
            
            # Update preferences based on feedback
            if response.lower() == "good":
                # If user approved a destructive operation, they might want to auto-approve
                if self.safety.is_destructive(action.get("tool_name", "")):
                    current_pref, confidence = self.persistent_memory.get_preference("auto_approve", False)
                    new_confidence = min(1.0, confidence + 0.1)
                    self.persistent_memory.store_preference("auto_approve", True, new_confidence)
                    self.working_memory.set_user_preference("auto_approve", True)
            elif response.lower() == "bad":
                # If user didn't like a destructive operation, they might want more warnings
                if self.safety.is_destructive(action.get("tool_name", "")):
                    current_pref, confidence = self.persistent_memory.get_preference("auto_approve", False)
                    new_confidence = min(1.0, confidence + 0.1)
                    self.persistent_memory.store_preference("auto_approve", False, new_confidence)
                    self.working_memory.set_user_preference("auto_approve", False)
    
    def _approve_file_write(self, operation: str, parameters: Dict[str, Any], preview: Dict[str, Any]) -> bool:
        """Approve file write operation"""
        # Show preview
        self.interface.display_response(f"Preview: {preview.get('preview', 'No preview available')}", 
                                     title="File Write Preview")
        
        # Show content preview if available
        if "content_preview" in preview:
            self.interface.display_response(f"Content: {preview['content_preview']}", 
                                         title="Content Preview")
        
        # Check user preference
        auto_approve = self.working_memory.get_user_preference("auto_approve", False)
        if auto_approve:
            return True
        
        response = self.interface.get_user_input("Do you want to proceed with this operation? (y/n): ")
        return response.lower() in ['y', 'yes']
    
    def _approve_git_commit(self, operation: str, parameters: Dict[str, Any], preview: Dict[str, Any]) -> bool:
        """Approve git commit operation"""
        message = parameters.get("message", "")
        self.interface.display_response(f"Will commit changes with message: '{message}'", 
                                     title="Git Commit Preview")
        
        # Check user preference
        auto_approve = self.working_memory.get_user_preference("auto_approve", False)
        if auto_approve:
            return True
        
        response = self.interface.get_user_input("Do you want to proceed with this commit? (y/n): ")
        return response.lower() in ['y', 'yes']
    
    def _approve_command_execution(self, operation: str, parameters: Dict[str, Any], preview: Dict[str, Any]) -> bool:
        """Approve command execution"""
        command = parameters.get("command", "")
        self.interface.display_response(f"Will execute command: '{command}'", 
                                     title="Command Execution Preview")
        
        # Check user preference
        auto_approve = self.working_memory.get_user_preference("auto_approve", False)
        if auto_approve:
            return True
        
        response = self.interface.get_user_input("Do you want to proceed with this command? (y/n): ")
        return response.lower() in ['y', 'yes']
    
    def _is_multi_step_task(self, user_input: str) -> bool:
        """Check if the task is multi-step"""
        multi_step_keywords = ["and then", "after that", "followed by", "then", "next"]
        return any(keyword in user_input.lower() for keyword in multi_step_keywords)
    
    def _split_task_into_steps(self, task: str) -> List[str]:
        """Split a multi-step task into individual steps"""
        steps = []
        current_step = ""
        
        # Split on common delimiters
        delimiters = [" and then ", " after that ", " followed by ", " then ", " next "]
        
        for delimiter in delimiters:
            if delimiter in task.lower():
                parts = task.lower().split(delimiter)
                steps = [part.strip() for part in parts if part.strip()]
                break
        
        if not steps:
            steps = [task]
        
        return steps
    
    
    def _handle_multi_step_task(self, state: Dict[str, Any]):
        """Handle a multi-step task"""
        user_input = state["user_input"]
        steps = self._split_task_into_steps(user_input)
        
        self.interface.display_response(f"I'll break this down into {len(steps)} steps:", 
                                     title="Multi-step Task")
        
        for i, step in enumerate(steps, 1):
            self.interface.display_response(f"Step {i}: {step}", title=f"Step {i}")
            
            # Create state for this step
            step_state = {
                "user_input": step,
                "current_directory": state["current_directory"],
                "git_status": state["git_status"],
                "session_id": state["session_id"],
                "project_path": state["project_path"]
            }
            
            # Execute step
            action = self.reason(step_state)
            result = self.act(action)
            self.learn(step_state, action, result)
            
            if result["success"]:
                self.interface.display_response(result["message"])
                if "content" in result:
                    verbosity = self.working_memory.get_user_preference("verbosity", "normal")
                    if verbosity == "high" or "content" in result.get("message", "").lower():
                        self.interface.display_response(result["content"], title="Result")
                elif "items" in result:
                    self.interface.display_response("\n".join(result["items"]), title="Directory Contents")
                elif "stdout" in result:
                    self.interface.display_response(result["stdout"], title="Command Output")
            else:
                self.interface.display_error(f"Step {i} failed: {result['message']}")
                
                # Ask if user wants to continue
                response = self.interface.get_user_input("Do you want to continue with the next step? (y/n): ")
                if response.lower() not in ['y', 'yes']:
                    break
    
    def _fallback_reasoning(self, user_input: str) -> Dict[str, Any]:
        """Fallback reasoning using pattern matching"""
        user_input = user_input.lower().strip()
        
        # Handle preference commands first (high priority)
        if user_input.startswith("set preference"):
            # Extract preference name and value
            parts = user_input.split("set preference", 1)[1].strip()
            if " " in parts:
                pref_name, pref_value = parts.split(" ", 1)
                pref_name = pref_name.strip()
                pref_value = pref_value.strip()
                
                # Convert boolean values
                if pref_value.lower() in ["true", "yes", "on"]:
                    pref_value = True
                elif pref_value.lower() in ["false", "no", "off"]:
                    pref_value = False
                
                return {
                    "tool_name": "set_preference",  # We'll create this tool
                    "parameters": {
                        "key": pref_name,
                        "value": pref_value
                    },
                    "reasoning": f"User wants to set preference '{pref_name}' to '{pref_value}' (fallback)"
                }
        
        # Check for show commands
        if user_input == "show preferences":
            return {
                "tool_name": "show_preferences",  # We'll create this tool
                "parameters": {},
                "reasoning": "User wants to see current preferences (fallback)"
            }
        
        if user_input == "show learning":
            return {
                "tool_name": "show_learning",  # We'll create this tool
                "parameters": {},
                "reasoning": "User wants to see learning summary (fallback)"
            }
        
        # Check for directory listing commands
        if any(phrase in user_input for phrase in ["list files", "list directory", "what files", "ls", "dir", "files in"]):
            return {
                "tool_name": "list_directory",
                "parameters": {"path": "."},
                "reasoning": "User wants to list directory contents (fallback)"
            }
        
        # Check for git status
        elif any(phrase in user_input for phrase in ["git status", "status of git", "git repo"]):
            return {
                "tool_name": "git_status",
                "parameters": {},
                "reasoning": "User wants to check git status (fallback)"
            }
        
        # Check for project structure
        elif any(phrase in user_input for phrase in ["project structure", "show structure", "directory structure"]):
            return {
                "tool_name": "get_structure",
                "parameters": {"max_depth": 5},
                "reasoning": "User wants to see project structure (fallback)"
            }
        
        # Check for file reading commands - IMPROVED PATTERN
        elif any(phrase in user_input for phrase in ["read", "what's in", "show me", "display", "what is in", "cat", "view"]):
            # Extract file path - look for quoted strings or file-like patterns
            file_match = re.search(r'["\']([^"\']+)["\']|(\S+\.\S+)', user_input)
            if file_match:
                file_path = file_match.group(1) or file_match.group(2)
            else:
                # Try to find the last word that looks like a file
                words = user_input.split()
                for word in reversed(words):
                    if '.' in word:  # Simple heuristic for file names
                        file_path = word
                        break
                else:
                    file_path = "test.txt"  # Default to test.txt
            
            return {
                "tool_name": "read_file",
                "parameters": {"file_path": file_path},
                "reasoning": "User wants to read a file (fallback)"
            }
        
        # Default fallback
        return {
            "tool_name": "list_directory",
            "parameters": {"path": "."},
            "reasoning": "Default fallback response"
        }
    
    # Add this method to the Agent class in core.py
    def _handle_special_commands(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Handle special commands that don't require LLM reasoning"""
        user_input = user_input.lower().strip()
        
        # Handle set preference command
        if user_input.startswith("set preference"):
            parts = user_input.split("set preference", 1)[1].strip()
            if " " in parts:
                pref_name, pref_value = parts.split(" ", 1)
                pref_name = pref_name.strip()
                pref_value = pref_value.strip()
                
                # Convert boolean values
                if pref_value.lower() in ["true", "yes", "on"]:
                    pref_value = True
                elif pref_value.lower() in ["false", "no", "off"]:
                    pref_value = False
                
                # Set preference
                self.working_memory.set_user_preference(pref_name, pref_value)
                self.persistent_memory.store_preference(pref_name, pref_value, 0.8)
                
                return {
                    "success": True,
                    "message": f"Preference '{pref_name}' set to '{pref_value}'"
                }
        
        # Handle show preferences command
        elif user_input == "show preferences":
            preferences = {
                "verbosity": self.working_memory.get_user_preference("verbosity", "normal"),
                "auto_approve": self.working_memory.get_user_preference("auto_approve", False),
                "show_diffs": self.working_memory.get_user_preference("show_diffs", True),
                "communication_style": self.working_memory.get_user_preference("communication_style", "balanced")
            }
            
            return {
                "success": True,
                "preferences": preferences,
                "message": "Current user preferences"
            }
        
        # Handle show learning command
        elif user_input == "show learning":
            summary = self.learning_system.get_learning_summary()
            
            return {
                "success": True,
                "summary": summary,
                "message": "Learning summary"
            }
        
        return None

# Update the run method to check for special commands first:
    def run(self):
        self.interface.display_welcome()
        
        # Show learning summary if available
        learning_summary = self.learning_system.get_learning_summary()
        if learning_summary["memory_stats"]["interaction_history_count"] > 0:
            self.interface.display_response(
                f"Welcome back! I've learned from {learning_summary['memory_stats']['interaction_history_count']} previous interactions.",
                title="Learning Summary"
            )
        
        while True:
            try:
                user_input = self.interface.get_user_input()
                if user_input.lower() in ['exit', 'quit']:
                    break
                
                # Handle special commands first (no API call needed)
                special_result = self._handle_special_commands(user_input)
                if special_result:
                    if special_result["success"]:
                        self.interface.display_response(special_result["message"])
                        if "preferences" in special_result:
                            self.interface.display_response(
                                "\n".join(f"- {k}: {v}" for k, v in special_result["preferences"].items()),
                                title="Preferences"
                            )
                        elif "summary" in special_result:
                            # Format learning summary for display
                            summary = special_result["summary"]
                            summary_text = f"Learning Summary:\n"
                            summary_text += f"- Interactions analyzed: {summary['memory_stats'].get('interaction_history_count', 0)}\n"
                            summary_text += f"- Tools learned: {summary['learning_coverage'].get('tools_learned', 0)}\n"
                            summary_text += f"- Patterns discovered: {summary['learning_coverage'].get('patterns_discovered', 0)}\n"
                            summary_text += f"- Error patterns: {summary['learning_coverage'].get('error_patterns', 0)}"
                            self.interface.display_response(summary_text, title="Learning Summary")
                    else:
                        self.interface.display_error(special_result["message"])
                    continue
                
                # Rest of the existing run method remains the same...
                print(f"DEBUG: Processing user input: '{user_input}'")
                state = self.perceive(user_input)
                
                if self._is_multi_step_task(user_input):
                    self._handle_multi_step_task(state)
                else:
                    # Single-step interaction
                    action = self.reason(state)
                    print(f"DEBUG: Reasoned action: {action}")
                    result = self.act(action)
                    self.learn(state, action, result)
                    
                    if result["success"]:
                        self.interface.display_response(result["message"])
                        
                        # Always display file content if it's a read operation
                        if "content" in result and result["content"]:
                            # Clean up BOM if present
                            content = result["content"]
                            if content.startswith('\ufeff'):
                                content = content[1:]
                            elif content.startswith('ÿþ'):
                                # UTF-16 BOM - try to decode properly
                                try:
                                    content = content.encode('latin-1').decode('utf-16')
                                except:
                                    pass
                            
                            self.interface.display_response(content, title="File Content")
                        elif "items" in result:
                            self.interface.display_response("\n".join(result["items"]), title="Directory Contents")
                        elif "stdout" in result:
                            self.interface.display_response(result["stdout"], title="Command Output")
                    else:
                        self.interface.display_error(result["message"])
                        
                        # Show recovery suggestions
                        if "suggestions" in result:
                            self.interface.display_response(
                                "\n".join(f"- {suggestion}" for suggestion in result["suggestions"]),
                                title="Recovery Suggestions"
                            )
            
            except KeyboardInterrupt:
                self.interface.display_response("\nGoodbye!")
                break
            except Exception as e:
                self.interface.display_error(f"An error occurred: {str(e)}")
                import traceback
                print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        
        # End session and save summary
        session_summary = self.working_memory.end_session()
        if session_summary:
            self.interface.display_response(
                f"Session completed. Duration: {session_summary['duration']:.1f}s, "
                f"Interactions: {session_summary['stats']['total_interactions']}, "
                f"Success rate: {session_summary['stats']['successful_interactions']}/{session_summary['stats']['total_interactions']}",
                title="Session Summary"
            )
    
    def _show_learning_summary(self):
        """Show learning system summary"""
        summary = self.learning_system.get_learning_summary()
        
        # Create a formatted summary
        summary_text = f"""
Learning Summary:
- Interactions analyzed: {summary['memory_stats'].get('interaction_history_count', 0)}
- Tools learned: {summary['learning_coverage'].get('tools_learned', 0)}
- Patterns discovered: {summary['learning_coverage'].get('patterns_discovered', 0)}
- Error patterns identified: {summary['learning_coverage'].get('error_patterns', 0)}
User Preferences:
"""
        
        for pref, value in summary.get('user_preferences', {}).items():
            summary_text += f"- {pref}: {value}\n"
        
        self.interface.display_response(summary_text, title="Learning Summary")
    
    def _show_user_preferences(self):
        """Show current user preferences"""
        preferences = {
            "verbosity": self.working_memory.get_user_preference("verbosity", "normal"),
            "auto_approve": self.working_memory.get_user_preference("auto_approve", False),
            "show_diffs": self.working_memory.get_user_preference("show_diffs", True),
            "communication_style": self.working_memory.get_user_preference("communication_style", "balanced")
        }
        
        pref_text = "Current User Preferences:\n"
        for pref, value in preferences.items():
            pref_text += f"- {pref}: {value}\n"
        
        self.interface.display_response(pref_text, title="User Preferences")
    
    def _handle_preference_command(self, command: str):
        """Handle preference setting commands"""
        try:
            parts = command.split(" ", 3)
            if len(parts) >= 3:
                pref_name = parts[2]
                pref_value = parts[3].lower() if len(parts) > 3 else "true"
                
                # Convert string values to appropriate types
                if pref_value in ["true", "yes", "on"]:
                    pref_value = True
                elif pref_value in ["false", "no", "off"]:
                    pref_value = False
                
                # Set preference
                self.working_memory.set_user_preference(pref_name, pref_value)
                self.persistent_memory.store_preference(pref_name, pref_value, 0.8)
                
                self.interface.display_response(f"Preference '{pref_name}' set to '{pref_value}'", 
                                             title="Preference Updated")
            else:
                self.interface.display_response("Usage: set preference <name> <value>", 
                                             title="Invalid Command")
        except Exception as e:
            self.interface.display_error(f"Error setting preference: {str(e)}")