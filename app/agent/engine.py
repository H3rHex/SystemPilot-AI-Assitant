from openai import OpenAI
from app.agent.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL_NAME

class AgentEngine:
    def __init__(self) -> None:
        """
        Initialize the LLM interaction engine utilizing environment-injected configurations.
        """
        self.base_url: str = LLM_BASE_URL or ""
        self.api_key: str = LLM_API_KEY or ""
        self.model_name: str = LLM_MODEL_NAME or ""

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
    
    def get_response(self, prompt: str) -> str:
        """
        Send the user prompt to the configured LLM endpoint and return the string content.
        """
        
        # Guard clause handling missing environment parameters safely
        if not self.api_key or not self.base_url or not self.model_name:
            return "[bold red]❌ Config Error:[/bold red] You must introduce your LLM credentials in the environment setup."
            
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,  # Pylance is happy now because self.model_name is strictly a 'str'
                messages=[
                    {
                        "role": "system", 
                        "content": "You are SystemPilot, a native system copilot for SO. Keep responses concise, clear, and focused on technical accuracy."
                    },
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content or ""
            
        except Exception as e:
            return f"[bold red]❌ LLM Engine Error:[/bold red] {str(e)}"