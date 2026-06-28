from typing import Generator
from ...base import CommandHandler
from .....renderer import GameRenderer

class FoldCommand(CommandHandler, names=["折叠", "f", "fold"], allowed_states=["battle"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            yield "❌ 你当前没有正在进行的游戏。"
            return
        res, term, success = router._execute_sub_action(user_id, run, parts)
        yield res + "\n" + GameRenderer.render_game(run)
        return success
