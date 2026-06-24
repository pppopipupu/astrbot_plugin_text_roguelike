from typing import Generator
from ...base import CommandHandler
from .....renderer import GameRenderer

class DeckCommand(CommandHandler, names=["牌组", "deck"], allowed_states=["menu", "town", "explore", "battle"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            yield "❌ 你当前没有正在进行的游戏。输入 /rogue start 开始新游戏。"
        else:
            yield GameRenderer.render_deck(run)
