from typing import Generator
from ..cli.base import CommandHandler

class CommandRouter:
    def __init__(self, save_manager, engine):
        self.save_manager = save_manager
        self.engine = engine
        self._command_handlers = CommandHandler.registry

    def execute_command(self, router, user_id: str, parts: list[str], curr_state: str) -> Generator[str, None, None]:
        if not parts:
            return
        sub = parts[0].lower()
        handler = self._command_handlers.get(sub)
        if handler:
            if curr_state in getattr(handler, "allowed_states", []):
                yield from handler.execute(router, user_id, parts)
            else:
                yield f"❌ 指令【{sub}】在当前状态下不可用。"
