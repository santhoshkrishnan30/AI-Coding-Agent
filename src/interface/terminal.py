import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from typing import Optional, List, Dict, Any
import time
import threading

class TerminalInterface:
    def __init__(self):
        self.console = Console()
    
    def display_welcome(self):
        welcome_text = Panel(
            "[bold blue]AI Coding Agent[/bold blue]\n\nYour intelligent pair programming partner",
            title="Welcome",
            border_style="blue"
        )
        self.console.print(welcome_text)
    
    def get_user_input(self, prompt: str = "> ") -> str:
        return input(prompt)
    
    def display_response(self, response: str, title: Optional[str] = None):
        if title:
            response_panel = Panel(response, title=title, border_style="green")
            self.console.print(response_panel)
        else:
            self.console.print(response)
    
    def display_error(self, error: str):
        error_panel = Panel(error, title="Error", border_style="red")
        self.console.print(error_panel)