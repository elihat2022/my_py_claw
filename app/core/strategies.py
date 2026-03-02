from abc import ABC , abstractmethod

class IAStrategy(ABC):
    @abstractmethod
    def set_payload(self, message: str)-> dict:
        pass

class StrategyFastModel(IAStrategy):
    def set_payload(self, message: str)-> dict:
        return {
            "model": "meta-llama/llama-3-8b-instruct",
            "temperature": 0.8,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message}
            ]

        }
    
class StrategyCodeModel(IAStrategy):
    def set_payload(self, message: str)-> dict:
        return {

            "model": "anthropic/claude-3.5-sonnet",
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": "You are a senior engineer. Only respond with clean code."},
                {"role": "user", "content": message}
            ]
        }
