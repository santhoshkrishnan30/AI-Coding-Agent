import sys
import os
from typing import Dict, Any, Optional, List, Tuple
import tiktoken
from .llm_integration import LLMIntegration

class EnhancedLLMIntegration(LLMIntegration):
    def __init__(self, model: str = "llama3.2:latest"):
        super().__init__(model)
        self.tokenizer = None
        self.context_window = self._get_context_window_size()
        self.reserved_tokens = 500  # Reserve tokens for response
        self._initialize_tokenizer()
    
    def _get_context_window_size(self) -> int:
        """Get context window size for the current model"""
        model_windows = {
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "llama3.2:latest": 8192,
            "claude-3": 100000,
        }
        return model_windows.get(self.model, 4096)
    
    def _initialize_tokenizer(self):
        """Initialize tokenizer for the model"""
        try:
            if self.model.startswith("gpt"):
                self.tokenizer = tiktoken.encoding_for_model(self.model)
            else:
                # Use a fallback tokenizer for other models
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except:
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback: rough estimate
            return len(text.split()) * 1.3
    
    def truncate_messages(self, messages: List[Dict], max_tokens: int = None) -> List[Dict]:
        """Smart message truncation preserving important context"""
        if max_tokens is None:
            max_tokens = self.context_window - self.reserved_tokens
        
        # Calculate current token count
        current_tokens = sum(self.count_tokens(msg.get("content", "")) for msg in messages)
        
        if current_tokens <= max_tokens:
            return messages
        
        # Strategy: Always keep system message, then prioritize recent messages
        truncated_messages = []
        remaining_tokens = max_tokens
        
        # Always keep system message if present
        if messages and messages[0].get("role") == "system":
            system_msg = messages[0]
            system_tokens = self.count_tokens(system_msg.get("content", ""))
            
            if system_tokens <= remaining_tokens:
                truncated_messages.append(system_msg)
                remaining_tokens -= system_tokens
            else:
                # Truncate system message if too long
                truncated_content = self._truncate_text(
                    system_msg.get("content", ""), 
                    remaining_tokens
                )
                truncated_messages.append({
                    "role": "system",
                    "content": truncated_content
                })
                return truncated_messages
        
        # Add recent messages, working backwards
        for msg in reversed(messages[1:]):
            msg_tokens = self.count_tokens(msg.get("content", ""))
            
            if msg_tokens <= remaining_tokens:
                truncated_messages.insert(1, msg)  # Insert after system message
                remaining_tokens -= msg_tokens
            else:
                # Try to add a truncated version
                truncated_content = self._truncate_text(
                    msg.get("content", ""),
                    remaining_tokens
                )
                if truncated_content:
                    truncated_messages.insert(1, {
                        "role": msg.get("role"),
                        "content": truncated_content
                    })
                break
        
        return truncated_messages
    
    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text intelligently"""
        if self.tokenizer:
            tokens = self.tokenizer.encode(text)
            if len(tokens) <= max_tokens:
                return text
            
            # Truncate tokens
            truncated_tokens = tokens[:max_tokens]
            truncated_text = self.tokenizer.decode(truncated_tokens)
            
            # Try to end at a sentence boundary
            for i in range(len(truncated_text) - 1, max(0, len(truncated_text) - 100), -1):
                if truncated_text[i] in '.!?':
                    return truncated_text[:i+1]
            
            return truncated_text + "..."
        else:
            # Fallback: simple character truncation
            if len(text) <= max_tokens * 4:  # Rough estimate
                return text
            
            truncated = text[:max_tokens * 4]
            return truncated + "..."
    
    def optimize_context(self, messages: List[Dict], context: Dict[str, Any]) -> Tuple[List[Dict], Dict[str, Any]]:
        """Optimize context for better LLM performance"""
        # Extract key information from context
        optimized_context = {
            "current_directory": context.get("current_directory", ""),
            "git_status": context.get("git_status", {}),
            "recent_files": context.get("recent_files", [])[:5],  # Limit to 5 recent files
            "active_session": context.get("session_id", ""),
        }
        
        # Create a condensed system message if context is large
        if len(str(context)) > 2000:  # If context is very large
            condensed_system = {
                "role": "system",
                "content": (
                    "You are an AI coding agent. "
                    f"Current directory: {optimized_context['current_directory']}. "
                    f"Git status: {'dirty' if optimized_context['git_status'].get('is_dirty') else 'clean'}. "
                    "Focus on the user's most recent request."
                )
            }
            
            # Replace the original system message
            if messages and messages[0].get("role") == "system":
                messages[0] = condensed_system
            else:
                messages.insert(0, condensed_system)
        
        # Truncate messages if necessary
        optimized_messages = self.truncate_messages(messages)
        
        return optimized_messages, optimized_context
    
    def generate_response_with_context(self, messages: List[Dict], context: Dict[str, Any], 
                                     temperature: float = 0.7) -> str:
        """Generate response with optimized context"""
        # Optimize context
        optimized_messages, optimized_context = self.optimize_context(messages, context)
        
        # Add context to the last user message
        if optimized_messages and optimized_messages[-1].get("role") == "user":
            context_info = (
                f"\n\nContext:\n"
                f"- Directory: {optimized_context['current_directory']}\n"
                f"- Git: {'dirty' if optimized_context['git_status'].get('is_dirty') else 'clean'}\n"
            )
            optimized_messages[-1]["content"] += context_info
        
        # Generate response
        return self.generate_response(optimized_messages, temperature)
    
    def estimate_cost(self, messages: List[Dict]) -> Dict[str, float]:
        """Estimate API cost for the request"""
        total_tokens = sum(self.count_tokens(msg.get("content", "")) for msg in messages)
        
        # Rough cost estimates (adjust based on your provider)
        cost_per_1k_tokens = {
            "gpt-3.5-turbo": 0.002,
            "gpt-4": 0.06,
            "gpt-4-32k": 0.12,
        }
        
        model_cost = cost_per_1k_tokens.get(self.model, 0.01)
        estimated_cost = (total_tokens / 1000) * model_cost
        
        return {
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost,
            "model": self.model
        }