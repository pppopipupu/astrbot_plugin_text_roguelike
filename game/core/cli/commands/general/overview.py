from typing import Generator
from ...base import CommandHandler

class OverviewCommand(CommandHandler, names=["总览", "overview"], allowed_states=["menu", "town", "explore", "battle"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        stats = router.save_manager.load_stats(user_id)
        if len(parts) > 1 and parts[1] in ("遗物", "relic", "relics"):
            from .....renderer.menu import get_rogue_relic_library_items
            items = get_rogue_relic_library_items()
            stats.reader_title = "🎒 魔法肉鸽遗物总览"
        else:
            from .....renderer.menu import get_rogue_card_library_items
            items = get_rogue_card_library_items()
            stats.reader_title = "📜 魔法肉鸽卡牌总览"
        stats.reader_items = items
        stats.reader_page = 1
        stats.reader_active = True
        stats.reader_mode = "rogue"
        router.save_manager.save_stats(user_id, stats)
        from .....renderer.menu import render_reader_page
        yield render_reader_page(stats)
