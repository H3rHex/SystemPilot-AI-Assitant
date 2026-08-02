import os
import sys

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings 

from app.chat.config import (
    WELCOME_BANNER,
    USER_PREFIX,
    ASSISTANT_PREFIX,
    EXIT_MESSAGE_CLEAN,
    EXIT_MESSAGE_INTERRUPT,
    STATUS_THINKING
)


class CommandLineInterface:
    def __init__(self) -> None:
        """Initialize the rich console and prompt_toolkit session engines."""
        self.console = Console()
        self.session = PromptSession()

    def print(self,text:str) -> None:
        '''Wrapper for printing using console'''
        self.console.print(text)

    def print_exit(self):
        self.print(EXIT_MESSAGE_CLEAN)

    def print_welcome(self):
        self.print(WELCOME_BANNER)

    def clear_console(self) -> None:
        """Clear the SO host terminal and reprint the central welcome banner."""
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')
            
    def get_input(self) -> str:
        """
        Capture user input from the terminal shell interface.
        Handles command history navigation and signals safely.
        """
        try:
            user_input = self.session.prompt(USER_PREFIX)
            return user_input.strip()

        except KeyboardInterrupt:
            current_buffer = getattr(self.session.app, "current_buffer", None)

            if current_buffer is not None and getattr(current_buffer, "text", ""):
                current_buffer.reset()
                current_buffer.text = ""
                current_buffer.cursor_position = 0
                return ""

            self.console.print(EXIT_MESSAGE_INTERRUPT)
            sys.exit(0)

        except EOFError:
            return 'exit'
        
    def print_markdown(self, text:str) -> None:
        """
        Render raw string response from the AI Agent using Markdown styling.
        """
        self.console.print(ASSISTANT_PREFIX)
        self.console.print(Markdown(text))
        self.console.print('\n' + '-' * 50)
    
    def print_stream(self, stream_generator) -> str:
        """Render status messages with Rich markup and model output as live Markdown."""
        self.console.print("\n[bold cyan]SystemPilot:[/bold cyan]")
        
        full_response = ""
        
        # First, process and render status messages directly to console
        # (they are short strings that end with a newline)
        for chunk in stream_generator:
            if chunk.startswith("[dim]"):
                self.console.print(chunk, end="")
            else:
                # Once status messages finish and LLM tokens start, collect the first chunk
                full_response += chunk
                break

        # Render only the model's actual response inside Live(Markdown)
        if full_response:
            with Live(console=self.console, refresh_per_second=12, auto_refresh=False) as live:
                # Render the first captured token
                live.update(Markdown(full_response), refresh=True)
                
                # Continue streaming the rest of the Markdown response
                for chunk in stream_generator:
                    full_response += chunk
                    live.update(Markdown(full_response), refresh=True)
                        
        self.console.print()
        return full_response
        

        
    