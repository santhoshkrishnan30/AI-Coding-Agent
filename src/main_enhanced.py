#!/usr/bin/env python3
"""
Enhanced main entry point for the AI Coding Agent
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.core import Agent
from interface.enhanced_terminal import EnhancedTerminalInterface

def main():
    """Main entry point for the enhanced AI Coding Agent"""
    # Create enhanced terminal interface
    interface = EnhancedTerminalInterface()
    
    # Display welcome message
    interface.display_welcome()
    
    # Create agent
    try:
        agent = Agent()
        
        # Show learning summary if available
        try:
            learning_summary = agent.learning_system.get_learning_summary()
            if learning_summary["memory_stats"]["interaction_history_count"] > 0:
                interface.display_response(
                    f"Welcome back! I've learned from {learning_summary['memory_stats']['interaction_history_count']} previous interactions.",
                    title="Learning Summary"
                )
        except:
            pass
        
        # Main loop
        interface.display_markdown(
            "I'm ready to help you with your coding tasks. "
            "Type `help` for available commands or `exit` to quit.",
            title="Ready"
        )
        
        while True:
            try:
                user_input = interface.get_user_input("\n> ")
                
                # Handle special commands
                if user_input.lower() in ['exit', 'quit']:
                    interface.display_response("Goodbye!", title="Session Ended")
                    break
                
                elif user_input.lower() == 'help':
                    show_help(interface)
                    continue
                
                elif user_input.lower() == 'status':
                    show_status(agent, interface)
                    continue
                
                elif user_input.lower().startswith('set preference'):
                    handle_preference_command(agent, interface, user_input)
                    continue
                
                elif user_input.lower() == 'show preferences':
                    show_preferences(agent, interface)
                    continue
                
                elif user_input.lower() == 'show learning':
                    show_learning_summary(agent, interface)
                    continue
                
                # Process normal input
                print(f"DEBUG: Processing user input: '{user_input}'")
                
                # Check for multi-step task
                if is_multi_step_task(user_input):
                    handle_multi_step_task(agent, interface, user_input)
                else:
                    # Single-step interaction
                    handle_single_step_task(agent, interface, user_input)
                
            except KeyboardInterrupt:
                interface.display_response("\nGoodbye!", title="Interrupted")
                break
            except Exception as e:
                interface.display_error_with_suggestions(
                    f"An error occurred: {str(e)}",
                    [
                        "Check your input and try again",
                        "Type 'help' for available commands",
                        "If the problem persists, restart the agent"
                    ]
                )
        
        # End session and save summary
        try:
            session_summary = agent.working_memory.end_session()
            if session_summary:
                interface.display_response(
                    f"Session completed. Duration: {session_summary['duration']:.1f}s, "
                    f"Interactions: {session_summary['stats']['total_interactions']}, "
                    f"Success rate: {session_summary['stats']['successful_interactions']}/{session_summary['stats']['total_interactions']}",
                    title="Session Summary"
                )
        except:
            pass

    except Exception as e:
        interface.display_error(f"Fatal error: {str(e)}")

def show_help(interface):
    """Show help information"""
    try:
        help_content = """
## Available Commands

### General
- `help` - Show this help message
- `status` - Show current system status
- `exit` or `quit` - Exit the agent

### Preferences
- `set preference <name> <value>` - Set a user preference
- `show preferences` - Show current preferences
- `show learning` - Show learning summary

### Example Tasks
#### File Operations
- `What's in package.json?`
- `Create a new file called hello.py`
- `Find all TODO comments`

#### Git Operations
- `What's the git status?`
- `Create a commit with message "Fix bug"`
- `Show changes since last commit`

#### Code Analysis
- `Run linter on src directory`
- `Analyze dependencies`
- `Find references to main function`

#### Testing
- `Run all tests`
- `Generate tests for utils module`

#### Multi-step Tasks
- `Create backup of package.json and add new dependency`
- `Run tests and fix any failures

### Tips
- Be specific in your requests
- Use multi-step commands for complex tasks
- The agent learns from your feedback
- All destructive operations show previews first
"""
        interface.display_markdown(help_content, title="Help")
    except Exception as e:
        interface.display_error(f"Could not display help: {str(e)}")

def show_status(agent, interface):
    """Show current system status"""
    try:
        status_info = {
            "LLM Provider": agent.llm.provider,
            "Model": agent.llm.model,
            "Current Directory": os.getcwd(),
            "Session ID": agent.working_memory.current_session_id,
            "Tools Registered": len(agent.tool_registry.list_tools()),
            "Memory Status": "Working" if agent.working_memory.current_session_id else "Inactive",
        }
        
        # Format as table
        table_data = []
        for key, value in status_info.items():
            table_data.append({"Aspect": key, "Status": str(value)})
        
        interface.display_table(table_data, title="System Status")
    except Exception as e:
        interface.display_error(f"Could not get status: {str(e)}")

def handle_preference_command(agent, interface, command):
    """Handle preference setting commands"""
    try:
        parts = command.split(" ", 3)
        if len(parts) >= 3:
            pref_name = parts[2]
            pref_value = parts[3] if len(parts) > 3 else ""
            
            # Convert boolean values
            if isinstance(pref_value, str):
                if pref_value.lower() in ["true", "yes", "on"]:
                    pref_value = True
                elif pref_value.lower() in ["false", "no", "off"]:
                    pref_value = False
            
            # Set preference
            agent.working_memory.set_user_preference(pref_name, pref_value)
            agent.persistent_memory.store_preference(pref_name, pref_value, 0.8)
            
            interface.display_success(
                f"Preference '{pref_name}' set to '{pref_value}'",
                "This preference will be remembered for future sessions."
            )
        else:
            interface.display_error("Usage: set preference <name> <value>")
    except Exception as e:
        interface.display_error(f"Could not set preference: {str(e)}")

def show_preferences(agent, interface):
    """Show current user preferences"""
    try:
        preferences = {
            "verbosity": agent.working_memory.get_user_preference("verbosity", "normal"),
            "auto_approve": agent.working_memory.get_user_preference("auto_approve", False),
            "show_diffs": agent.working_memory.get_user_preference("show_diffs", True),
            "communication_style": agent.working_memory.get_user_preference("communication_style", "balanced"),
        }
        
        # Format as table
        table_data = []
        for key, value in preferences.items():
            table_data.append({"Preference": key, "Value": str(value)})
        
        interface.display_table(table_data, title="User Preferences")
    except Exception as e:
        interface.display_error(f"Could not get preferences: {str(e)}")

def show_learning_summary(agent, interface):
    """Show learning system summary"""
    try:
        summary = agent.learning_system.get_learning_summary()
        
        # Create formatted summary
        summary_text = f"""## Learning Summary

### Interactions Analyzed
{summary['memory_stats'].get('interaction_history_count', 0)} interactions analyzed

### Tools Learned
{summary['learning_coverage'].get('tools_learned', 0)} tools with high effectiveness

### Patterns Discovered
{summary['learning_coverage'].get('patterns_discovered', 0)} successful patterns identified

### Error Patterns
{summary['learning_coverage'].get('error_patterns', 0)} error patterns recognized

### User Preferences
"""
        for pref, value in summary.get('user_preferences', {}).items():
            summary_text += f"- {pref}: {value}\n"
        
        interface.display_markdown(summary_text, title="Learning Summary")
    except Exception as e:
        interface.display_error(f"Could not get learning summary: {str(e)}")

def is_multi_step_task(user_input):
    """Check if the task is multi-step"""
    multi_step_keywords = [
        " and then ", " after that ", " followed by ", " then ", " next ",
        " first ", " second ", " third ", " finally "
    ]
    return any(keyword in user_input.lower() for keyword in multi_step_keywords)

def handle_multi_step_task(agent, interface, user_input):
    """Handle multi-step tasks"""
    try:
        steps = split_task_into_steps(user_input)
        
        interface.display_response(
            f"I'll break this down into {len(steps)} steps:",
            title="Multi-step Task"
        )
        
        for i, step in enumerate(steps, 1):
            interface.display_response(
                f"Step {i}: {step}",
                title=f"Step {i}"
            )
            
            # Create progress bar
            progress_id = interface.display_progress(f"Executing step {i}")
            
            # Execute step
            result = execute_step(agent, interface, step)
            
            interface.finish_progress(progress_id)
            
            if result.get("success", False):
                interface.display_success(
                    f"Step {i} completed successfully",
                    result.get("message", "")
                )
                
                # Display additional content if available
                if "content" in result:
                    interface.display_code(result["content"], title="Result")
                elif "items" in result:
                    interface.display_table(
                        [{"Item": item} for item in result["items"]],
                        title="Results"
                    )
                elif "stdout" in result:
                    interface.display_code(result["stdout"], "text", title="Output")
            else:
                interface.display_error_with_suggestions(
                    f"Step {i} failed: {result.get('message', 'Unknown error')}",
                    result.get("suggestions", ["Try a different approach", "Check your input"])
                )
                
                # Ask if user wants to continue
                response = interface.get_user_input("Do you want to continue with the next step? (y/n): ")
                if response.lower() not in ['y', 'yes']:
                    interface.display_response("Multi-step task cancelled.", title="Cancelled")
                    break
    except Exception as e:
        interface.display_error(f"Error in multi-step task: {str(e)}")

def split_task_into_steps(task):
    """Split a multi-step task into individual steps"""
    steps = []
    current_step = ""
    
    # Split on common delimiters
    delimiters = [
        " and then ", " after that ", " followed by ", " then ", " next ",
        " first ", " second ", " third ", " finally "
    ]
    
    for delimiter in delimiters:
        if delimiter in task.lower():
            parts = task.lower().split(delimiter)
            steps = [part.strip() for part in parts if part.strip()]
            break
    
    if not steps:
        steps = [task]
    
    return steps

def execute_step(agent, interface, step):
    """Execute a single step"""
    try:
        # Perceive
        state = agent.perceive(step)
        
        # Reason
        action = agent.reason(state)
        
        # Act
        result = agent.act(action)
        
        # Learn
        agent.learn(state, action, result)
        
        return result
    except Exception as e:
        return {
            "success": False,
            "message": f"Error executing step: {str(e)}",
            "suggestions": ["Check your input", "Try a different approach"]
        }

def handle_single_step_task(agent, interface, user_input):
    """Handle single-step tasks"""
    try:
        # Perceive
        state = agent.perceive(user_input)
        
        # Reason
        action = agent.reason(state)
        
        # Act
        result = agent.act(action)
        
        # Learn
        agent.learn(state, action, result)
        
        # Display result
        if result.get("success", False):
            interface.display_success(
                result.get("message", "Operation completed"),
                result.get("details", "")
            )
            
            # Display additional content based on result type
            if "content" in result:
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
                
                interface.display_code(content, title="Content")
            elif "items" in result:
                interface.display_table(
                    [{"Item": item} for item in result["items"]],
                    title="Results"
                )
            elif "stdout" in result:
                interface.display_code(result["stdout"], "text", title="Output")
            elif "diff" in result:
                interface.display_diff(
                    "Original content", 
                    result["diff"], 
                    title="Changes"
                )
        else:
            interface.display_error_with_suggestions(
                result.get("message", "Operation failed"),
                result.get("suggestions", ["Try again", "Check your input"])
            )
            
            # Show recovery suggestions if available
            if "recovery_suggestions" in result:
                interface.display_response(
                    "\n".join(f"• {s}" for s in result["recovery_suggestions"]),
                    title="Recovery Suggestions"
                )
    except Exception as e:
        interface.display_error_with_suggestions(
            f"An error occurred: {str(e)}",
            [
                "Check your input and try again",
                "Type 'help' for available commands",
                "If the problem persists, restart the agent"
            ]
        )

if __name__ == "__main__":
    main()
