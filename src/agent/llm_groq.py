import os
import requests
from typing import Dict, Any, Optional, List

class GroqIntegration:
    def __init__(self, model: str = "llama3-8b-8192"):
        self.model = model
        self.api_key = os.getenv("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def generate_response(self, messages: List[Dict], temperature: float = 0.7) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 1000
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def generate_structured_response(self, messages: List[Dict], response_format: Dict) -> Dict:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1000,
                "response_format": response_format
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                try:
                    import json
                    return json.loads(content)
                except:
                    return {"content": content}
            else:
                return {"content": f"Error: {response.status_code}"}
        except Exception as e:
            return {"content": f"Error: {str(e)}"}
    
    def count_tokens(self, text: str) -> int:
        """Rough token count estimation"""
        return len(text.split())  # Simple word count as token estimate