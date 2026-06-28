from typing import Generator
from ...base import CommandHandler
from .....renderer import GameRenderer

class ChooseCommand(CommandHandler, names=["选择", "c"], allowed_states=["menu", "explore", "battle"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            if len(parts) > 1:
                arg = parts[1].lower()
                if arg in ("wizard", "warrior", "wiz", "war", "法师", "战士", "1", "2", "3", "0", "选择", "时序法师", "塑能法师", "秘钥学者"):
                    yield "❌ 你当前没有正在进行的游戏。如需切换职业，请使用 /rogue class 命令。\n💡 选择命令 c 仅用于局内选项选择，无法用于选择职业。"
                    return
            yield "❌ 你当前没有正在进行的游戏。"
            return
        res, term, success = router._execute_sub_action(user_id, run, parts)
        if term or (run and run.node_data.get("in_queue")):
            yield res
        else:
            yield res + "\n" + GameRenderer.render_game(run)
        return success
