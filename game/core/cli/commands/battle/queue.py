from typing import Generator
from ...base import CommandHandler
from .....renderer import GameRenderer

class QueueCommand(CommandHandler, names=["队列", "q", "queue"], allowed_states=["battle"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            yield "❌ 你当前没有正在进行的游戏。"
            return
        if len(parts) < 2:
            yield "❌ 请提供队列操作，例如：/rogue 队列 [使用 1, 随从 1 技能 2, 结束]"
            return
        full_arg = " ".join(parts[1:])
        results = []
        router._execute_queue(user_id, run, full_arg, results)
        if run.player.hp <= 0:
            yield "\n".join(results)
        else:
            yield "\n".join(results) + "\n" + GameRenderer.render_game(run)
