import asyncio
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from app.core.domain.factory import IAStrategyFactory
from app.core.ports.observers_port import TokenObserver
from app.core.ports.ai_provider_port import IAProviderPort
from app.adapters.secondary.ai_clients.openrouter import OpenRouterClient
from app.adapters.secondary.tools.terminal import MacTerminalAdapter
from dotenv import load_dotenv

load_dotenv() 

# --- GLOBAL STATE FOR APPROVALS ---
# This dictionary will hold the asyncio.Event for each chat
pending_approvals = {}


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
@router.message(F.text) # Ensures it only triggers on text messages
async def handle_chat(message: types.Message, ai_client: IAProviderPort, terminal_tool: MacTerminalAdapter, bot: Bot):
    status_msg = await message.answer("⏳ [Agent Started: Thinking...]")

    try:
        strategy = IAStrategyFactory.obtain_strategy("fast") # or "fast" if it supports tools
    except ValueError as e:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=f"❌ Error: {e}")
        return

    strategy.tools_schema = terminal_tool.get_tools_schema()
    current_prompt = message.text

    while True:
        response_msg = await ai_client.generate_response(strategy=strategy, prompt=current_prompt)
        current_prompt = None 

        if "tool_calls" in response_msg and response_msg["tool_calls"]:
            tool_call = response_msg["tool_calls"][0]
            tool_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])
            command_to_run = arguments.get("command", "Unknown")

            strategy.add_message(response_msg)

            # 1. Create Inline Buttons
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Approve", callback_data="approve_cmd"),
                    InlineKeyboardButton(text="❌ Deny", callback_data="deny_cmd")
                ]
            ])

            # 2. Ask for permission in Telegram
            await bot.edit_message_text(
                chat_id=message.chat.id, 
                message_id=status_msg.message_id, 
                text=f"⚠️ **[Security Alert]**\nThe AI wants to run:\n`{command_to_run}`\n\nDo you allow this?",
                parse_mode="Markdown",
                reply_markup=keyboard # Attach the buttons
            )

            # 3. PAUSE THE LOOP! Wait for the user to click a button
            approval_event = asyncio.Event()
            pending_approvals[message.chat.id] = {"event": approval_event, "approved": False}
            
            await approval_event.wait() # <--- Code stops executing here until button is clicked

            # 4. Check the user's decision
            is_approved = pending_approvals[message.chat.id]["approved"]
            del pending_approvals[message.chat.id] # Clean up memory

            if is_approved:
                await bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text="⚙️ [Executing command...]")
                result = terminal_tool.execute_tool(tool_name, arguments)
            else:
                result = "Error: The user explicitly denied the execution of this command. Stop and ask the user what to do next."

            # 5. Save result to memory and loop again
            strategy.add_message({
                "role": "tool",
                "name": tool_name,
                "content": result,
                "tool_call_id": tool_call["id"]
            })
            
            await bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text="🧠 [Analyzing terminal output...]")

        else:
            # AI is done
            ai_text = response_msg.get("content", "")
            try:
                await bot.edit_message_text(
                    chat_id=message.chat.id, 
                    message_id=status_msg.message_id, 
                    text=f"🤖 **Agent:**\n{ai_text}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                # Fallback if markdown formatting fails
                await bot.edit_message_text(
                    chat_id=message.chat.id, 
                    message_id=status_msg.message_id, 
                    text=f"🤖 Agent:\n{ai_text}"
                )
            strategy.add_message({"role": "assistant", "content": ai_text})
            break


# --- BUTTON CLICK HANDLER ---
@router.callback_query(F.data.in_(["approve_cmd", "deny_cmd"]))
async def handle_approval_buttons(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    
    # Check if this chat is currently waiting for an approval
    if chat_id in pending_approvals:
        # If data is 'approve_cmd', set True. Else, False.
        pending_approvals[chat_id]["approved"] = (callback.data == "approve_cmd")
        
        # WAKE UP THE LOOP! This signals the approval_event.wait() to proceed
        pending_approvals[chat_id]["event"].set()
        
        # Remove buttons so they can't be clicked twice
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass # Ignore if it was already modified or removed
        
        await callback.answer("Decision recorded!") 
    else:    
        # If the user clicks an old button from a past message
        await callback.answer("This request has expired.", show_alert=True)

async def main():
    print("="*50)
    print("🚀 Iniciando Telegram Bot (Agente Autónomo)")
    print("="*50)

    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # --- INYECCIÓN DE DEPENDENCIAS ---
    openrouter_client = OpenRouterClient()
    mac_terminal = MacTerminalAdapter() # 1. Creamos la herramienta
    
    dp["ai_client"] = openrouter_client
    dp["terminal_tool"] = mac_terminal # 2. La inyectamos en Aiogram para que llegue al handle_chat

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot detenido.")