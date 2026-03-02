import asyncio
from app.adapters.secondary.ai_clients.openrouter import OpenRouterClient
from app.core.domain.factory import IAStrategyFactory
from app.core.ports.observers_port import ConsoleTokenObserver


async def iniciar_bot_terminal():
    print("="*50)
    print("🤖 Bienvenido a tu AI Bot de Terminal (Estilo OpenClaw)")
    print("Escribe 'salir' para terminar el chat.")
    print("="*50)

    # 1. Preparamos nuestro Singleton y el Observador
    ai_client = OpenRouterClient()
    observador = ConsoleTokenObserver()
    ai_client.subscribe(observador) # Conectamos la consola para el streaming

    # 2. Bucle infinito para mantener el chat abierto
    while True:
        # Obtenemos el texto del usuario
        mensaje = input("\n🧑 Tú: ")
        
        # Condición de salida
        if mensaje.lower() in ['salir', 'exit', 'quit']:
            print("👋 ¡Hasta luego!")
            break
            
        # Evitar procesar mensajes vacíos
        if not mensaje.strip():
            continue

        # 3. Elegimos la estrategia (aquí la fijamos en 'fast', 
        # pero podrías hacer un menú para que el usuario elija)
        try:
            estrategia = IAStrategyFactory.obtain_strategy("fast")
        except ValueError as e:
            print(f"❌ Error: {e}")
            continue

        print("🤖 IA: ", end="")
        
        # 4. ¡Llamamos a nuestro motor!
        await ai_client.generate_response_stream(strategy=estrategia, prompt=mensaje)
        
        # Un salto de línea extra al terminar el stream para que se vea limpio
        print("\n")

# Punto de entrada del script
if __name__ == "__main__":
    # Ejecutamos nuestra función asíncrona principal
    try:
        asyncio.run(iniciar_bot_terminal())
    except KeyboardInterrupt:
        print("\n👋 Chat cerrado a la fuerza. ¡Nos vemos!")