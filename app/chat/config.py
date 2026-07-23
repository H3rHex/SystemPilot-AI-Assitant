# app/chat/config.py

# 1. Welcome Banner (Using Rich gradient simulation and sleek clean dividers)
WELCOME_BANNER = """
[bold cyan]┌────────────────────────────────────────────────────────┐[/bold cyan]
[bold cyan]│[/bold cyan]  [bold turquoise2]SystemPilot[/bold turquoise2] [bold white]Alpha[/bold white] [dim]|[/dim] [italic royal_blue1]Native SO Copilot[/italic royal_blue1]       [bold cyan]│[/bold cyan]
[bold cyan]└────────────────────────────────────────────────────────┘[/bold cyan]
 [dim]• Type[/dim] [bold red]/exit[/bold red] [dim]or[/dim] [bold red]/quit[/bold red] [dim]to terminate the session.[/dim]
 [dim]• Type[/dim] [bold spring_green3]/clear[/bold spring_green3] [dim]or press[/dim] [bold spring_green3]Ctrl+L[/bold spring_green3] [dim]to wipe the terminal screen.[/dim]
[dim]──────────────────────────────────────────────────────────[/dim]
"""

# 2. Prompts and Shell Layout Prefixes
USER_PREFIX = "user ❯❯ "
ASSISTANT_PREFIX = "\n[bold deep_pink4]assistant[/bold deep_pink4] [bold magenta]❯❯[/bold magenta] "
SYSTEM_PREFIX = "\n[bold grey50]system ❯❯[/bold grey50] "

# 3. Dynamic Process and Operations Status Indicators
STATUS_THINKING = "[bold blink purple4]Thinking...[/bold blink purple4] [dim]SystemPilot is computing your request[/dim]"
STATUS_EXECUTING = "[bold gold3]Executing...[/bold gold3] [dim]Running core system operation[/dim]"

# 4. Process Termination Messages
EXIT_MESSAGE_CLEAN = "\n[bold spring_green3]✔[/bold spring_green3] [bold white]Exiting SystemPilot.[/bold white] Goodbye!\n"
EXIT_MESSAGE_INTERRUPT = "\n\n[bold orange3]Session forcefully interrupted by user.[/bold orange3] Exiting application loop...\n"

# 5. Core Error Infrastructure Styling
ERROR_LLM_CONNECTION = "[bold red]Connection Error:[/bold red] Unable to establish bridge with the AI infrastructure provider."
ERROR_MCP_SERVER = "[bold red] Protocol Error:[/bold red] Model Context Protocol server handshake or response failed."
ERROR_COMMAND_FAILED = "[bold red] Execution Error:[/bold red] The requested subsystem operation returned a non-zero exit code."
ERROR_UNAUTHORIZED = "[bold red] Security Error:[/bold red] Access denied. Operation requires elevated system permissions."

# 6. AI Agent States & Interactive Prompts
AI_RESPONSE_SUCCESS = "[bold spring_green3]✔ Operation completed successfully.[/bold spring_green3]"
AI_RESPONSE_NO_TOOLS = "[bold yellow]⚠ Unhandled Intention:[/bold yellow] Request understood, but no local tools match this action matrix."
AI_RESPONSE_CONFIRMATION = "\n[bold sky_blue2]⚡ Critical Action:[/bold sky_blue2] Do you want me to proceed with this system modification? [dim](y/n)[/dim] ❯ "