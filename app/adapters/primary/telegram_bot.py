import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import CommandStart
from app.core.domain.factory import IAStrategyFactory
from app.core.ports.observers_port import TokenObserver
from app.core.ports.ai_provider_port import IAProviderPort
from app.adapters.secondary.ai_clients.openrouter import OpenRouterClient
from dotenv import load_dotenv

load_dotenv() 
# Telegram Bot Adapter
class TelegramTokenObserver(TokenObserver):
    def __init__(self, bot: Bot, chat_id: int, message_id: int):
        self.bot = bot
        self.chat_id = chat_id
        self.message_id = message_id
        self.buffer = ""
        self.token_count = 0

    async def on_token(self, token: str):
        self.buffer += token
        self.token_count += 1
        
        # Editamos el mensaje en Telegram cada 25 tokens para no saturar la API (Rate Limit)
        if self.token_count % 25 == 0:
            try:
                await self.bot.edit_message_text(
                    chat_id=self.chat_id,
                    message_id=self.message_id,
                    text=self.buffer + " ✍️..."
                )
            except Exception:
                # Telegram lanza error si intentamos editar el mensaje con el mismo texto
                pass


# BOT CONFIGURATION
router = Router()
ALLOWED_USER_ID = int(os.getenv("ALLOWED_TELEGRAM_ID", "0"))

router.message.filter(F.from_user.id == ALLOWED_USER_ID)  # Solo procesamos mensajes de texto no vacíos
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("🤖 ¡Hola! Soy tu AI bot con Arquitectura Hexagonal. Envíame un prompt de programación.")

# Capturamos todos los mensajes de texto
@router.message()
async def handle_chat(message: types.Message, ai_client: IAProviderPort, bot: Bot):
    """
    Fíjate en el parámetro `ai_client`. ¡Aiogram nos lo inyecta mágicamente 
    gracias a la configuración que hicimos en el Dispatcher más abajo!
    """
    # 1. Enviamos un mensaje inicial de "Pensando..." y guardamos su ID
    sent_msg = await message.answer("⏳ Pensando...")

    # 2. Elegimos la estrategia (puedes crear un menú luego para cambiarla)
    strategy = IAStrategyFactory.obtain_strategy("fast")

    # 3. Creamos el observador para este mensaje en particular y lo suscribimos
    observer = TelegramTokenObserver(bot, message.chat.id, sent_msg.message_id)
    ai_client.subscribe(observer)

    try:
        # 4. Dejamos que el cliente haga su magia en streaming
        await ai_client.generate_response_stream(strategy=strategy, prompt=message.text)
        
        # 5. Cuando termina, hacemos una actualización final para poner el texto completo
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=sent_msg.message_id,
            text=observer.buffer
        )
    finally:
        # 🚨 MUY IMPORTANTE: Desuscribimos a este observador para liberar memoria
        ai_client.unsubscribe(observer)

async def main():
    print("="*50)
    print("🚀 Iniciando Telegram Bot (Arquitectura Hexagonal)")
    print("="*50)

    # Reemplaza esto con tu token real o ponlo en el .env
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # --- INYECCIÓN DE DEPENDENCIAS ---
    # Instanciamos nuestra infraestructura
    openrouter_client = OpenRouterClient()
    
    # Aiogram permite inyectar variables a todos los handlers directamente así:
    dp["ai_client"] = openrouter_client

    # Iniciamos el bucle de eventos del bot
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot detenido.")