from abc import ABC, abstractmethod
from app.core.domain.strategies import IAStrategy
from app.core.ports.observers_port import TokenObserver

class IAProviderPort(ABC):
    
    @abstractmethod
    def subscribe(self, observer: TokenObserver):
        pass

    @abstractmethod
    async def generate_response_stream(self, strategy: IAStrategy, prompt: str):
        pass
        
    @abstractmethod
    async def generate_response(self, strategy: IAStrategy, prompt: str):
        pass