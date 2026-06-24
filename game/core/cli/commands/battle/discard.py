from typing import Generator
from ...base import CommandHandler
from .....renderer import GameRenderer

class DiscardCommand(CommandHandler, names=["弃牌堆", "discard", "discard_pile"], allowed_states=["battle"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            yield "❌ 你当前没有正在进行的游戏。输入 /rogue start 开始新游戏。"
        elif run.node_type != "battle":
            yield "❌ 只有在战斗中才能查询战斗牌堆。"
        else:
            yield GameRenderer.render_discard_pile(run)
