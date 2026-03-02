from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ToolsPort(ABC):
    """
    Contract for any tool provider injected into the system.
    """
    @abstractmethod
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        Returns the JSON schema that describes the available tools to the LLM.
        """
        pass
    @abstractmethod
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Executes the requested tool and returns the output as a string.
        """
        pass