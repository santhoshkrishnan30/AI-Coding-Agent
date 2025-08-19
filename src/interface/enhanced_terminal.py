from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown
from typing import Optional, List, Dict, Any, Generator
import time
import threading
import difflib
from .terminal import TerminalInterface

class EnhancedTerminalInterface(TerminalInterface):
    def __init__(self):
        super().__init__()
        self.console = Console()
        self.streaming = False
        self.current_stream = None
        self.progress_bars = {}
    
    def display_welcome(self):
        welcome_text = Panel(
            "[bold blue]AI Coding Agent[/bold blue]\n\n"
            "Your intelligent pair programming partner\n"
            "[dim]Day 3: Enhanced Edition[/dim]",
            title="Welcome",
            border_style="blue",
            padding=(1, 2)
        )
        self.console.print(welcome_text)
    
    def display_streaming_response(self, response_generator, title: Optional[str] = None):
        """Display a streaming response with progress indicator"""
        self.streaming = True
        self.current_stream = ""
        
        def update_stream():
            for chunk in response_generator:
                self.current_stream += chunk
                time.sleep(0.03)  # Simulate streaming delay
        
        # Start streaming in a separate thread
        stream_thread = threading.Thread(target=update_stream)
        stream_thread.daemon = True
        stream_thread.start()
        
        # Display progress while streaming
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task("Processing...", total=100)
            
            while stream_thread.is_alive():
                progress.update(task, advance=1)
                time.sleep(0.1)
        
        # Display the final response
        if title:
            response_panel = Panel(
                Markdown(self.current_stream),
                title=title,
                border_style="green",
                padding=(1, 2)
            )
            self.console.print(response_panel)
        else:
            self.console.print(Markdown(self.current_stream))
        
        self.streaming = False
        self.current_stream = None
    
    def display_table(self, data: List[Dict[str, Any]], title: Optional[str] = None, 
                     columns: Optional[List[str]] = None):
        """Display data in a formatted table"""
        if not data:
            self.display_response("No data to display", title)
            return
        
        table = Table(title=title, show_header=True, header_style="bold magenta")
        
        # Use provided columns or infer from first row
        if columns:
            for col in columns:
                table.add_column(col.replace("_", " ").title())
        else:
            for key in data[0].keys():
                table.add_column(key.replace("_", " ").title())
        
        # Add rows
        for row in data:
            values = []
            for key in (columns if columns else data[0].keys()):
                value = str(row.get(key, ""))
                # Truncate long values
                if len(value) > 50:
                    value = value[:47] + "..."
                values.append(value)
            table.add_row(*values)
        
        self.console.print(table)
    
    def display_diff(self, old_content: str, new_content: str, title: Optional[str] = None):
        """Display a diff between two texts with syntax highlighting"""
        diff = difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile="Original",
            tofile="Modified",
            lineterm=""
        )
        
        diff_text = "".join(diff)
        
        # Try to detect file type for syntax highlighting
        if title and title.endswith('.py'):
            syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
        elif title and (title.endswith('.js') or title.endswith('.ts')):
            syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
        else:
            syntax = diff_text
        
        if title:
            diff_panel = Panel(
                syntax,
                title=title,
                border_style="yellow",
                padding=(1, 2)
            )
            self.console.print(diff_panel)
        else:
            self.console.print(syntax)
    
    def display_choices(self, choices: List[str], prompt: str = "Select an option:") -> int:
        """Display choices and get user selection"""
        choice_table = Table(title="Available Options", show_header=False)
        choice_table.add_column("No.", style="cyan", width=5)
        choice_table.add_column("Option", style="white")
        
        for i, choice in enumerate(choices, 1):
            choice_table.add_row(str(i), choice)
        
        self.console.print(choice_table)
        
        while True:
            try:
                selection = self.console.input(f"[bold green]{prompt} [/bold green]")
                selection = int(selection)
                if 1 <= selection <= len(choices):
                    return selection - 1
                else:
                    self.console.print(f"[red]Please enter a number between 1 and {len(choices)}[/red]")
            except ValueError:
                self.console.print("[red]Please enter a valid number[/red]")
    
    def display_progress(self, description: str, total: int = None) -> str:
        """Create and return a progress bar"""
        progress_id = str(time.time())
        
        if total:
            self.progress_bars[progress_id] = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                transient=True,
            )
            task = self.progress_bars[progress_id].add_task(description, total=total)
        else:
            self.progress_bars[progress_id] = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            )
            task = self.progress_bars[progress_id].add_task(description)
        
        return progress_id
    
    def update_progress(self, progress_id: str, advance: int = 1):
        """Update a progress bar"""
        if progress_id in self.progress_bars:
            self.progress_bars[progress_id].update(progress_id, advance=advance)
    
    def finish_progress(self, progress_id: str):
        """Finish and remove a progress bar"""
        if progress_id in self.progress_bars:
            self.progress_bars[progress_id].stop()
            del self.progress_bars[progress_id]
    
    def display_code(self, code: str, language: str = "python", title: Optional[str] = None):
        """Display code with syntax highlighting"""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        
        if title:
            code_panel = Panel(
                syntax,
                title=title,
                border_style="blue",
                padding=(1, 2)
            )
            self.console.print(code_panel)
        else:
            self.console.print(syntax)
    
    def display_markdown(self, content: str, title: Optional[str] = None):
        """Display markdown content"""
        if title:
            markdown_panel = Panel(
                Markdown(content),
                title=title,
                border_style="green",
                padding=(1, 2)
            )
            self.console.print(markdown_panel)
        else:
            self.console.print(Markdown(content))
    
    def display_error_with_suggestions(self, error: str, suggestions: List[str]):
        """Display error with recovery suggestions"""
        error_panel = Panel(
            f"[bold red]Error:[/bold red] {error}\n\n"
            f"[bold yellow]Suggestions:[/bold yellow]\n" + 
            "\n".join(f"• {s}" for s in suggestions),
            title="Error Occurred",
            border_style="red",
            padding=(1, 2)
        )
        self.console.print(error_panel)
    
    def display_success(self, message: str, details: Optional[str] = None):
        """Display success message"""
        if details:
            success_panel = Panel(
                f"[bold green]Success![/bold green] {message}\n\n"
                f"[dim]{details}[/dim]",
                title="Operation Completed",
                border_style="green",
                padding=(1, 2)
            )
            self.console.print(success_panel)
        else:
            self.console.print(f"[bold green]✓[/bold green] {message}")