import sys

from app.chat.cli import CommandLineInterface

class ChatSession:
    def __init__(self) -> None:
        '''Initialize single ton session orchestrator linking UI and routing'''
        self.cli = CommandLineInterface()
        self.is_running = True

    def start(self):
        '''Execute the core application lifecycle state machine'''
        self.cli.clear_console()
        self.cli.print_welcome()

        while self.is_running == True:
            user_input = self.cli.get_input()

            if not user_input:
                continue
        
            self.handle_user_input(user_input)

    def handle_user_input(self, uinput:str) -> None:
        normalized_input = uinput.lower()

        if uinput in ['/exit', '/quit']:
            self._handle_exit()
            return

        if normalized_input == '/clear':
            self.cli.clear_console()
            return
        
        self._process_ai_request(uinput)

    def _handle_exit(self):
        self.cli.print_exit()
        sys.exit(0)

    def _process_ai_request(self, prompt: str) -> None:
      pass