import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from typing import Dict, Any, Optional, List
import os
import requests
import json
import re
import tiktoken
from dotenv import load_dotenv

# Try to import OpenAI
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    openai = None

load_dotenv()

class LLMIntegration:
    def __init__(self, model: str = "llama3.2:latest"):
        self.model = model
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.groq_base_url = "https://api.groq.com/openai/v1"
        
        # Model mapping for each provider
        self.model_mapping = {
            "openai": {
                "gpt-3.5-turbo": "gpt-3.5-turbo",
                "gpt-4": "gpt-4",
                "gpt-4-turbo": "gpt-4-turbo",
                "llama3.2:latest": "gpt-3.5-turbo"
            },
            "groq": {
                "gpt-3.5-turbo": "llama3-8b-8192",
                "gpt-4": "llama3-70b-8192",
                "llama3.2:latest": "llama3-8b-8192"
            },
            "ollama": {
                "gpt-3.5-turbo": "llama3.2:latest",
                "gpt-4": "llama3:latest",
                "llama3.2:latest": "llama3.2:latest"
            }
        }
        
        # Try providers in order: OpenAI -> Groq -> Ollama -> Fallback
        self.client = None
        self.provider = None
        self.available_models = []
        
        print(" Initializing provider cascade...")
        
        # Try OpenAI first
        if self.openai_api_key and HAS_OPENAI:
            try:
                print(" Trying OpenAI...")
                self.client = openai.OpenAI(api_key=self.openai_api_key)
                # Test the API key with a minimal request
                test_response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1
                )
                self.provider = "openai"
                self.model = self.model_mapping["openai"].get(model, "gpt-3.5-turbo")
                print(" Using OpenAI API")
                self._get_available_models()
                return  # Success, no need to try others
            except Exception as e:
                print(f" OpenAI API not working: {e}")
                self.client = None
        
        # Try Groq if OpenAI failed
        if not self.client and self.groq_api_key:
            try:
                print(" Trying Groq...")
                # Test Groq connectivity
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                
                # Map the requested model to a Groq model
                groq_model = self.model_mapping["groq"].get(model, "llama3-8b-8192")
                
                test_payload = {
                    "model": groq_model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                }
                response = requests.post(
                    f"{self.groq_base_url}/chat/completions",
                    headers=headers,
                    json=test_payload,
                    timeout=10
                )
                if response.status_code == 200:
                    self.provider = "groq"
                    self.model = groq_model
                    print(" Using Groq API")
                    self._get_available_models()
                    return  # Success, no need to try others
            except Exception as e:
                print(f" Groq API not available: {e}")
        
        # Try Ollama if both failed
        if not self.client:
            try:
                print(" Trying Ollama...")
                # Test Ollama connectivity
                response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    self.provider = "ollama"
                    # Map the requested model to an Ollama model
                    ollama_model = self.model_mapping["ollama"].get(model, "llama3.2:latest")
                    self.model = ollama_model
                    print(" Using Ollama (Local Models)")
                    self._get_available_models()
                    return  # Success, no need to try others
                else:
                    print(" Ollama responded with error")
            except Exception as e:
                print(f" Ollama not available: {e}")
        
        # If all else fails, use fallback mode
        if not self.client and self.provider != "ollama":
            self.provider = "fallback"
            print(" No API keys available. Using fallback mode.")
        
        # Initialize tiktoken for token counting
        try:
            self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except:
            # Fallback to a default encoding
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def _get_available_models(self):
        """Get list of available models from the current provider"""
        try:
            if self.provider == "openai":
                models = self.client.models.list()
                self.available_models = [model.id for model in models.data]
            elif self.provider == "groq":
                headers = {"Authorization": f"Bearer {self.groq_api_key}"}
                response = requests.get(f"{self.groq_base_url}/models", headers=headers)
                if response.status_code == 200:
                    models = response.json()
                    self.available_models = [model["id"] for model in models.get("data", [])]
            elif self.provider == "ollama":
                response = requests.get(f"{self.ollama_base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json()
                    self.available_models = [model["name"] for model in models.get("models", [])]
        except Exception as e:
            print(f"Warning: Could not get available models: {e}")
            self.available_models = []
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return self.available_models
    
    def generate_response(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Generate a response using the available provider with proper fallback"""
        # Try the current provider first
        try:
            if self.provider == "openai" and self.openai_api_key and HAS_OPENAI:
                return self._generate_openai_response(messages, temperature)
            elif self.provider == "groq" and self.groq_api_key:
                return self._generate_groq_response(messages, temperature)
            elif self.provider == "ollama":
                return self._generate_ollama_response(messages, temperature)
        except Exception as e:
            print(f"Current provider {self.provider} failed: {e}")
        
        # If current provider fails, try Ollama next (especially important for Groq rate limits)
        if self.provider != "ollama":
            try:
                print(" Trying Ollama as fallback...")
                return self._generate_ollama_response(messages, temperature)
            except Exception as e:
                print(f"Ollama fallback failed: {e}")
        
        # Then try other providers
        providers = ["openai", "groq"]
        for provider in providers:
            if provider == self.provider:
                continue  # Skip the one we just tried
                
            try:
                if provider == "openai" and self.openai_api_key and HAS_OPENAI:
                    return self._generate_openai_response(messages, temperature)
                elif provider == "groq" and self.groq_api_key:
                    return self._generate_groq_response(messages, temperature)
            except Exception as e:
                print(f"Provider {provider} failed: {e}")
                continue
        
        # All providers failed, use fallback
        return self._generate_fallback_response(messages)
    
    def generate_structured_response(self, messages: List[Dict], response_format: Dict) -> Dict:
        """Generate a structured response using the available provider with proper fallback"""
        # Try the current provider first
        try:
            if self.provider == "openai" and self.openai_api_key and HAS_OPENAI:
                return self._generate_openai_structured_response(messages, response_format)
            elif self.provider == "groq" and self.groq_api_key:
                return self._generate_groq_structured_response(messages, response_format)
            elif self.provider == "ollama":
                return self._generate_ollama_structured_response(messages, response_format)
        except Exception as e:
            print(f"Current provider {self.provider} failed for structured response: {e}")
        
        # If current provider fails, try Ollama next (especially important for Groq rate limits)
        if self.provider != "ollama":
            try:
                print(" Trying Ollama as fallback for structured response...")
                return self._generate_ollama_structured_response(messages, response_format)
            except Exception as e:
                print(f"Ollama fallback failed for structured response: {e}")
        
        # Then try other providers
        providers = ["openai", "groq"]
        for provider in providers:
            if provider == self.provider:
                continue  # Skip the one we just tried
                
            try:
                if provider == "openai" and self.openai_api_key and HAS_OPENAI:
                    return self._generate_openai_structured_response(messages, response_format)
                elif provider == "groq" and self.groq_api_key:
                    return self._generate_groq_structured_response(messages, response_format)
            except Exception as e:
                print(f"Provider {provider} failed for structured response: {e}")
                continue
        
        # All providers failed, use fallback
        content = self._generate_fallback_response(messages)
        return {"content": content}
    
    def _generate_openai_response(self, messages: List[Dict], temperature: float) -> str:
        """Generate response using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model if self.provider == "openai" else "gpt-3.5-turbo",
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            raise Exception(f"OpenAI API failed: {e}")
    
    def _generate_openai_structured_response(self, messages: List[Dict], response_format: Dict) -> Dict:
        """Generate structured response using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model if self.provider == "openai" else "gpt-3.5-turbo",
                messages=messages,
                response_format=response_format,
                temperature=0.3
            )
            return {"content": response.choices[0].message.content}
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            raise Exception(f"OpenAI API failed: {e}")
    
    def _generate_groq_response(self, messages: List[Dict], temperature: float) -> str:
        """Generate response using Groq"""
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 1000
            }
            
            response = requests.post(
                f"{self.groq_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                # Rate limit exceeded - don't wait, just fail so we can fallback to Ollama
                raise Exception(f"Groq API rate limit exceeded")
            else:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                raise Exception(f"Groq API error: {response.status_code} - {error_msg}")
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            raise Exception(f"Groq API failed: {e}")
    
    def _generate_groq_structured_response(self, messages: List[Dict], response_format: Dict) -> Dict:
        """Generate structured response using Groq"""
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1000,
                "response_format": response_format
            }
            
            response = requests.post(
                f"{self.groq_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                try:
                    import json
                    return json.loads(content)
                except:
                    return {"content": content}
            elif response.status_code == 429:
                # Rate limit exceeded - don't wait, just fail so we can fallback to Ollama
                raise Exception(f"Groq API rate limit exceeded")
            else:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                raise Exception(f"Groq API error: {response.status_code} - {error_msg}")
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            raise Exception(f"Groq API failed: {e}")
    
    # src/agent/llm_integration.py - Update the Ollama connection methods
   
    def _generate_ollama_response(self, messages: List[Dict], temperature: float) -> str:
        """Generate response using Ollama with better timeout handling"""
        try:
            # Check if Ollama is running first with a short timeout
            try:
                response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=2)
                if response.status_code != 200:
                    raise Exception(f"Ollama returned status {response.status_code}")
            except requests.exceptions.Timeout:
                raise Exception("Ollama connection timeout")
            except Exception as e:
                raise Exception(f"Ollama not accessible: {e}")
            
            # Build the prompt for Ollama
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                elif msg["role"] == "user":
                    user_messages.append(msg["content"])
                elif msg["role"] == "assistant":
                    user_messages.append(msg["content"])
            
            # Create a prompt that works well with Ollama
            prompt = system_message + "\n\n" if system_message else ""
            for i, msg in enumerate(user_messages):
                prompt += f"User: {msg}\n"
                if i < len(user_messages) - 1:
                    prompt += "Assistant: I understand.\n"
            prompt += "Assistant: "
            
            # Try with a very short prompt first for speed
            short_prompt = "What tool should I use for git status?"
            if len(prompt) > 200:
                print(" Using shortened prompt for faster Ollama response")
                prompt = short_prompt
            
            payload = {
                "model": "llama3.2:latest",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": 0.9,
                    "num_predict": 100,  # Even smaller for faster response
                    "num_ctx": 512,      # Smaller context window
                    "num_thread": 1     # Single thread for faster response
                }
            }
            
            # Try multiple times with increasing timeouts
            timeouts = [10, 20, 30]
            last_error = None
            
            for timeout in timeouts:
                try:
                    print(f" Trying Ollama with {timeout}s timeout...")
                    response = requests.post(
                        f"{self.ollama_base_url}/api/generate",
                        json=payload,
                        timeout=timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        response_text = result.get("response", "")
                        if response_text.strip():
                            print(f" Ollama response successful ({len(response_text)} chars)")
                            return response_text
                        else:
                            print(" Ollama returned empty response")
                            continue
                    else:
                        print(f" Ollama API error: {response.status_code}")
                        last_error = f"HTTP {response.status_code}"
                        
                except requests.exceptions.Timeout:
                    print(f" Ollama timeout with {timeout}s timeout")
                    last_error = "timeout"
                    continue
                except Exception as e:
                    print(f" Ollama error: {e}")
                    last_error = str(e)
                    continue
            
            # If all attempts failed, try with minimal prompt
            try:
                print(" Trying minimal Ollama prompt...")
                minimal_payload = {
                    "model": "llama3.2:latest",
                    "prompt": "git status",
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 20,
                        "num_ctx": 256
                    }
                }
                
                response = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json=minimal_payload,
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    if response_text.strip():
                        print(f" Minimal Ollama response successful")
                        return response_text
                        
            except Exception as e:
                print(f" Minimal Ollama prompt also failed: {e}")
            
            raise Exception(f"Ollama API failed after all attempts. Last error: {last_error}")
                
        except Exception as e:
            print(f"Error calling Ollama API: {e}")
            raise Exception(f"Ollama API failed: {e}")

    def _generate_ollama_structured_response(self, messages: List[Dict], response_format: Dict) -> Dict:
        """Generate structured response using Ollama"""
        try:
            # For structured responses, we need to modify the prompt to request JSON
            system_message = "You are an AI coding assistant. Respond only with valid JSON."
            
            # Find system message or add one
            if messages and messages[0]["role"] == "system":
                messages[0]["content"] = system_message + " " + messages[0]["content"]
            else:
                messages.insert(0, {"role": "system", "content": system_message})
            
            # Add JSON format instruction to the last user message
            if messages and messages[-1]["role"] == "user":
                messages[-1]["content"] += "\n\nRespond in JSON format only."
            
            # Generate response using the improved method
            response_text = self._generate_ollama_response(messages, 0.3)
            
            # Try to parse as JSON
            try:
                json_response = json.loads(response_text)
                return {"content": json.dumps(json_response)}
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from the response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        json_response = json.loads(json_match.group())
                        return {"content": json.dumps(json_response)}
                    except:
                        pass
                
                # If all else fails, create a simple JSON response
                return {"content": json.dumps({"response": response_text})}
                
        except Exception as e:
            print(f"Error generating structured Ollama response: {e}")
            raise Exception(f"Ollama API failed: {e}")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text (rough estimate)"""
        # Simple token count estimation
        return len(text.split()) // 0.75  # Rough estimate: ~1.33 chars per token
    
    def truncate_messages(self, messages: List[Dict], max_tokens: int = None) -> List[Dict]:
        """Truncate messages to fit within token limits"""
        if max_tokens is None:
            max_tokens = 4000  # Default token limit
        
        # Count tokens in each message
        token_counts = []
        for message in messages:
            content = message.get("content", "")
            token_counts.append(self.count_tokens(content))
        
        # Calculate total tokens
        total_tokens = sum(token_counts)
        
        # If we're under the limit, return as is
        if total_tokens <= max_tokens:
            return messages
        
        # Otherwise, truncate from the beginning (except system message)
        truncated_messages = []
        remaining_tokens = max_tokens
        
        # Always keep the system message
        if messages and messages[0].get("role") == "system":
            system_message = messages[0]
            system_tokens = token_counts[0]
            if system_tokens <= remaining_tokens:
                truncated_messages.append(system_message)
                remaining_tokens -= system_tokens
            else:
                # Truncate the system message if needed
                system_content = system_message.get("content", "")
                truncated_content = self.truncate_text(system_content, remaining_tokens)
                truncated_messages.append({
                    "role": "system",
                    "content": truncated_content
                })
                return truncated_messages
        
        # Add as many other messages as possible, starting from the end
        for i in range(len(messages) - 1, 0, -1):
            message = messages[i]
            message_tokens = token_counts[i]
            
            if message_tokens <= remaining_tokens:
                truncated_messages.insert(1, message)  # Insert after system message
                remaining_tokens -= message_tokens
            else:
                # Truncate the message if needed
                content = message.get("content", "")
                truncated_content = self.truncate_text(content, remaining_tokens)
                truncated_messages.insert(1, {
                    "role": message.get("role"),
                    "content": truncated_content
                })
                break
        
        return truncated_messages
    
    def truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit"""
        tokens = text.split()
        if len(tokens) <= max_tokens:
            return text
        
        truncated_tokens = tokens[:max_tokens]
        truncated_text = " ".join(truncated_tokens)
        
        # Try to end at a sentence boundary
        last_sentence_end = max(
            truncated_text.rfind('.'),
            truncated_text.rfind('!'),
            truncated_text.rfind('?')
        )
        
        if last_sentence_end > len(truncated_text) * 0.8:  # Only if we're not losing too much
            return truncated_text[:last_sentence_end + 1]
        
        return truncated_text + "..."  # Add ellipsis to indicate truncation
    
    def _generate_fallback_response(self, messages: List[Dict]) -> str:
        """Generate a fallback response when all providers fail"""
        # Get the user's message - find the last user message
        user_message = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                user_message = message.get("content", "")
                break
        
        print(f"DEBUG: Using fallback mode for: '{user_message}'")
        
        # Remove leading ">" if present (from command line)
        user_message = re.sub(r'^>\s*', '', user_message)
        
        # Simple pattern matching for common commands
        user_message = user_message.lower()
        
        # Check for directory listing commands
        if any(phrase in user_message for phrase in ["list files", "list directory", "what files", "ls", "dir", "files in"]):
            response = {
                "tool_name": "list_directory",
                "parameters": {"path": "."},
                "reasoning": "User wants to list directory contents (fallback)"
            }
            return json.dumps(response)
        
        # Check for git status
        elif any(phrase in user_message for phrase in ["git status", "status of git", "git repo"]):
            response = {
                "tool_name": "git_status",
                "parameters": {},
                "reasoning": "User wants to check git status (fallback)"
            }
            return json.dumps(response)
        
        # Check for project structure
        elif any(phrase in user_message for phrase in ["project structure", "show structure", "directory structure"]):
            response = {
                "tool_name": "get_structure",
                "parameters": {"max_depth": 5},
                "reasoning": "User wants to see project structure (fallback)"
            }
            return json.dumps(response)
        
        # Check for file reading commands
        elif any(phrase in user_message for phrase in ["read", "what's in", "show me", "display", "what is in", "cat", "view"]):
            # Extract file path - look for quoted strings or file-like patterns
            file_match = re.search(r'["\']([^"\']+)["\']|(\S+\.\S+)', user_message)
            if file_match:
                file_path = file_match.group(1) or file_match.group(2)
            else:
                # Try to find the last word that looks like a file
                words = user_message.split()
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
        response = {
            "tool_name": "list_directory",
            "parameters": {"path": "."},
            "reasoning": "Default fallback response"
        }
        return json.dumps(response)
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider"""
        return {
            "provider": self.provider,
            "model": self.model,
            "available_models": self.available_models,
            "has_openai": self.openai_api_key is not None and HAS_OPENAI,
            "has_groq": self.groq_api_key is not None,
            "has_ollama": self.provider == "ollama"
        }