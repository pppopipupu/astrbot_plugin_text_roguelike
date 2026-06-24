from typing import Generator
from ...base import CommandHandler

class TownCommand(CommandHandler, names=["主城", "town"], allowed_states=["menu"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if run:
            yield "❌ 游戏进行中，无法前往主城。请先通关或通过 放弃 结束当前游戏。"
            return
        stats = router.save_manager.load_stats(user_id)
        stats.in_town = True
        router.save_manager.save_stats(user_id, stats)
        yield router.town_engine.render_current_room(user_id, stats)
