# adapters/primary/cli_bot.py
import asyncio
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.domain.strategies import StrategyFastModel, StrategyCodeModel
from app.core.ports.ai_provider_port import IAProviderPort
from app.adapters.secondary.ai_clients.openrouter import OpenRouterClient
from app.adapters.secondary.tools.terminal import MacTerminalAdapter # 1. Import our tool adapter

async def start_agentic_bot(ai_client: IAProviderPort, terminal_tool: MacTerminalAdapter):
    print("="*50)
    print("🤖 Autonomous AI Agent (Hexagonal Architecture + Tool Use)")
    print("="*50)

    # 2. Inject the tools schema into our strategy so the AI knows it has hands
    strategy = StrategyFastModel(tools_schema=terminal_tool.get_tools_schema())

    while True:
        prompt = input("\n🧑 You: ")
        if prompt.lower() in ['salir', 'exit', 'quit']:
            break
        if not prompt.strip():
            continue

        current_prompt = prompt

        # --- THE AGENTIC LOOP (Think -> Act -> Observe) ---
        while True:
            print("⏳ [AI is thinking...]")
            
            # Send the current memory to the AI
            response_msg = await ai_client.generate_response(strategy=strategy, prompt=current_prompt)
            current_prompt = None # Clear prompt so we don't send it twice in the same loop
            
            # Did the AI decide to use a tool?
            if "tool_calls" in response_msg and response_msg["tool_calls"]:
                tool_call = response_msg["tool_calls"][0]
                tool_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])

                # MUST save the AI's tool request to history to maintain conversation flow
                strategy.add_message(response_msg)

                # Execute the tool safely (This will trigger your [y/N] prompt)
                result = terminal_tool.execute_tool(tool_name, arguments)
                print(f"⚙️  [System Result]:\n{result}")

                # Save the terminal's output back to the memory
                strategy.add_message({
                    "role": "tool",
                    "name": tool_name,
                    "content": result,
                    "tool_call_id": tool_call["id"]
                })
                
                # The loop restarts! The AI will read the result and decide what to do next.
                
            else:
                # The AI sent normal text, meaning it finished its task
                ai_text = response_msg.get("content", "")
                print(f"\n🤖 AI: {ai_text}")
                
                # Save final answer to memory
                strategy.add_message({"role": "assistant", "content": ai_text})
                break # Exit the agent loop, wait for the next user input

if __name__ == "__main__":
    # --- DEPENDENCY INJECTION ---
    openrouter_client = OpenRouterClient()
    mac_terminal = MacTerminalAdapter() # Instantiate the tool
    
    try:
        asyncio.run(start_agentic_bot(openrouter_client, mac_terminal))
    except KeyboardInterrupt:
        print("\n👋 Bot stopped.")