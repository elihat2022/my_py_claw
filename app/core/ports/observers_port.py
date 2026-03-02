from abc import ABC, abstractmethod

# Contract for new observers
class TokenObserver(ABC):
    @abstractmethod
    async def on_token(self, token: str):
        pass
class ConsoleTokenObserver(TokenObserver):
    async def on_token(self, token: str):
        print(token, end="", flush=True)
