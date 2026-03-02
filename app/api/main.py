from fastapi import FastAPI, HTTPException
from app.infra.client import OpenRouterClient
from app.core.domain.factory import IAStrategyFactory
from app.core.ports.observers_port import ConsoleTokenObserver
app = FastAPI()


ai_client = OpenRouterClient()
console_observer = ConsoleTokenObserver()
ai_client.subscribe(console_observer)

@app.get("/chat")
async def endpoint_chat(message:str, model_type: str = "fast"):
    client = OpenRouterClient()
    try:
        strategy = IAStrategyFactory.obtain_strategy(model_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    # Print the ID
    print(f"ID del cliente en memoria: {id(client)}")
    response = await client.generate_response(strategy=strategy, prompt=message)
    return {
        'message': message,
        'response': response
    }


@app.get("/chat/stream")
async def endpoint_chat_stream(message:str, model_type: str = "fast"):
    try:
        strategy = IAStrategyFactory.obtain_strategy(model_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # Llamamos al nuevo método de streaming
    await ai_client.generate_response_stream(strategy=strategy, prompt=message) 
    
    return {"status": "Mira tu terminal de Python para ver el resultado en tiempo real!"}