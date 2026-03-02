import os
import httpx
import json
from app.core.ports.ai_provider_port import IAProviderPort
from app.core.domain.strategies import IAStrategy
from app.core.ports.observers_port import TokenObserver
from app.adapters.secondary.cache.decorators import response_cache

class OpenRouterClient(IAProviderPort):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("Creating OpenRouter connection")
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.api_key = os.getenv('OPENROUTER_API_KEY')
            self.base_url = 'https://openrouter.ai/api/v1'
            self.http_client = httpx.AsyncClient(
                headers={'Authorization': f"Bearer {self.api_key}"}   
            )
            self._subscribers: list[TokenObserver] = []
            self.initialized = True 

    def subscribe(self, observer: TokenObserver):
        if observer not in self._subscribers:
            self._subscribers.append(observer)
            
    def unsubscribe(self, observer: TokenObserver):
        if observer in self._subscribers:
            self._subscribers.remove(observer)

    async def notify(self, token: str):
        for observer in self._subscribers:
            await observer.on_token(token)

    @response_cache
    async def generate_response(self, strategy: IAStrategy, prompt: str):
        payload = strategy.set_payload(prompt)
        response = await self.http_client.post(
            f"{self.base_url}/chat/completions",
            json=payload
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    async def generate_response_stream(self, strategy: IAStrategy, prompt: str):
        payload = strategy.set_payload(prompt)
        payload["stream"] = True

        async with self.http_client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    json_data = line[6:]
                    if json_data.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(json_data)
                        token = data["choices"][0]["delta"].get("content")
                        if token is not None and token != "":
                            await self.notify(token)
                    except json.JSONDecodeError:
                        pass