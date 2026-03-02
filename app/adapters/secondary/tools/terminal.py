# app/adapters/secondary/tools/terminal.py
import subprocess
from typing import List, Dict, Any
from app.core.ports.tools_port import ToolsPort

class MacTerminalAdapter(ToolsPort):
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        return [{
            "type": "function",
            "function": {
                "name": "execute_terminal_command",
                "description": "Executes a bash command in the Mac terminal.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The bash command"}
                    },
                    "required": ["command"]
                }
            }
        }]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        command = arguments.get("command")
        if not command:
            return "Error: No command provided."

        # REMOVED the input() block. The Primary Adapter (Telegram) handles security now.
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, cwd="."
            )
            output = result.stdout if result.returncode == 0 else result.stderr
            return output if output else "Success: Command executed with no output."
        except Exception as e:
            return f"Critical error executing command: {str(e)}"