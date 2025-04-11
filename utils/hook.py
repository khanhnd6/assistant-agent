from agents import AgentHooks, RunContextWrapper, Agent, Tool
from typing import Any

class DebugAgentHooks(AgentHooks):
    def __init__(self, display_name: str):
        self.name = display_name

    async def on_start(self, context: RunContextWrapper, agent: Agent) -> None:
        print(f"({self.name}): nhận yêu cầu")

    async def on_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        print(f"({self.name}): kết thúc và trả về phản hồi \n\n")

    async def on_handoff(self, context: RunContextWrapper, agent: Agent, source: Agent) -> None:
        print(f"({self.name}): gọi tới Agent {agent.name}")

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        print(f"({self.name}): gọi hàm {tool.name}")

    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str) -> None:
        print(f"({self.name}): kết hàm {tool.name} và nhận kết quả '{result}'")