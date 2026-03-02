from abc import ABC , abstractmethod

class IAStrategy(ABC):
    @abstractmethod
    def set_payload(self, message: str)-> dict:
        pass

class StrategyFastModel(IAStrategy):
    def set_payload(self, message: str)-> dict:
        return {
            "model": "minimax/minimax-m2.5",
            "temperature": 0.8,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant. your name is minimax"},
                {"role": "user", "content": message}
            ]

        }
    
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
