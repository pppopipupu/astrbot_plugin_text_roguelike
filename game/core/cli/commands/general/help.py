from typing import Generator
from ...base import CommandHandler
from .....renderer import GameRenderer

class HelpCommand(CommandHandler, names=["帮助", "help"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        yield GameRenderer.render_help()
