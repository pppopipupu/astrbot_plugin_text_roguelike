from typing import Generator
from ...base import CommandHandler
from .....renderer import GameRenderer

class QueryCommand(CommandHandler, names=["查询", "query", "info", "i"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if len(parts) > 1:
            query_str = " ".join(parts[1:]).strip().lower()
            if query_str in ("抽牌堆", "draw", "draw_pile"):
                if not run:
                    yield "❌ 你当前没有正在进行的游戏。"
                elif run.node_type != "battle":
                    yield "❌ 只有在战斗中才能查询战斗牌堆。"
                else:
                    yield GameRenderer.render_draw_pile(run)
            elif query_str in ("弃牌堆", "discard", "discard_pile"):
                if not run:
                    yield "❌ 你当前没有正在进行的游戏。"
                elif run.node_type != "battle":
                    yield "❌ 只有在战斗中才能查询战斗牌堆。"
                else:
                    yield GameRenderer.render_discard_pile(run)
            elif query_str in ("消耗堆", "exhaust", "exhaust_pile"):
                if not run:
                    yield "❌ 你当前没有正在进行的游戏。"
                elif run.node_type != "battle":
                    yield "❌ 只有在战斗中才能查询战斗牌堆。"
                else:
                    yield GameRenderer.render_exhaust_pile(run)
            elif query_str in ("随从墓地", "mg", "minion_graveyard", "minion_grave"):
                if not run:
                    yield "❌ 你当前没有正在进行的游戏。"
                elif run.node_type != "battle":
                    yield "❌ 只有在战斗中才能查询战斗墓地。"
                else:
                    yield GameRenderer.render_minion_graveyard(run)
            elif query_str in ("敌人墓地", "eg", "enemy_graveyard", "enemy_grave"):
                if not run:
                    yield "❌ 你当前没有正在进行的游戏。"
                elif run.node_type != "battle":
                    yield "❌ 只有在战斗中才能查询战斗墓地。"
                else:
                    yield GameRenderer.render_enemy_graveyard(run)
            else:
                yield GameRenderer.render_query_info(" ".join(parts[1:]).strip())
        else:
            if not run:
                yield "❌ 你当前没有正在进行的游戏。输入 /rogue start 开始新游戏。\n💡 提示：你可以通过 /rogue i <名称>（如：/rogue i 力量）或 /rogue i buff 来查看相关效果描述。"
            elif run.node_type != "battle":
                yield "❌ 只有在战斗中才能查询详细战斗信息。请输入想要查询的随从、遗物、Buff名称。\n💡 提示：你可以通过 /rogue i <名称>（如：/rogue i 力量）或 /rogue i buff 来查看相关效果描述。"
            else:
                yield GameRenderer.render_detailed_battle(run)
