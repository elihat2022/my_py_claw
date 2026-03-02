from abc import ABC , abstractmethod
from typing import List, Dict, Any, Optional

class IAStrategy(ABC):
    @abstractmethod
    def set_payload(self, message: str)-> dict:
        pass

class StrategyFastModel(IAStrategy):
    def __init__(self, tools_schema: Optional[List[Dict[str, Any]]] = None):
        # We inject the tools schema into the strategy
        self.tools_schema = tools_schema or []

        # The agent's memory starts with the system prompt
        self.history = [
            {
                "role": "system", 
                "content": "You are a Senior AI Agent. You have access to the user's Mac terminal via the 'execute_terminal_command' tool. Use it to navigate, create files, and write code. Always verify your actions."
            }
        ]
    
    def add_message(self, message: dict):
        """Appends a message (from user, tool, or assistant) to the memory."""
        self.history.append(message)

    def set_payload(self, message: str)-> dict:
        if message:
            self.history.append({"role": "user", "content": message})
            


        payload =  {
            "model": "minimax/minimax-m2.5",
            "temperature": 0.8,
            "messages": 
                self.history
            

        }
        # If we have tools available, attach them to the OpenRouter payload
        if self.tools_schema:
            payload["tools"] = self.tools_schema
        return payload
    
class StrategyCodeModel(IAStrategy):
    def set_payload(self, message: str)-> dict:
        return {

            "model": "minimax/minimax-m2.5",
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": "You are a senior engineer. Only respond with clean code. your name is minimax"},
                {"role": "user", "content": message}
            ]
        }
