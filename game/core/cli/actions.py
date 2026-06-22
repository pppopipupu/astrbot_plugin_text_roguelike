from typing import Tuple
from .base import ActionHandler
from ...entities import ALL_CARDS

class UseAction(ActionHandler, actions=["使用", "p"]):
    def execute(self, router, user_id: str, run, parts: list[str]) -> Tuple[str, bool]:
        if len(parts) < 2:
            return "❌ 请提供手牌序号，例如：使用 1", False
        try:
            idx = int(parts[1])
        except ValueError:
            return "❌ 序号必须是数字。", False
        target = " ".join(parts[2:]) if len(parts) > 2 else None
        res = router.engine.play_card(run, idx, target)
        if run.player.hp <= 0:
            settle_msg = router.save_manager.settle_game_and_delete(user_id, run, is_victory=False)
            return f"{res}\n💀 你被击败了！当前进度已清空。\n{settle_msg}", True
        if router.engine.is_battle_won(run):
            router.engine._handle_battle_win(run)
            if run.node_type == "victory":
                settle_msg = router.save_manager.settle_game_and_delete(user_id, run, is_victory=True)
                boss_name = run.node_data.get("boss_name")
                if not boss_name and run.enemies:
                    boss_name = run.enemies[0].name
                if not boss_name:
                    boss_name = "最终BOSS"
                return f"{res}\n🎉 恭喜你击败了{boss_name}，通关成功！\n{settle_msg}", True
            else:
                return f"{res}\n🎉 战斗胜利！你击败了敌方所有单位。", True
        return res, False

class MinionAction(ActionHandler, actions=["随从", "m"]):
    def execute(self, router, user_id: str, run, parts: list[str]) -> Tuple[str, bool]:
        if len(parts) < 3:
            return "❌ 参数不足。用法：随从 <我方格子> 攻击/技能 <目标/序号>", False
        my_grid_raw = parts[1]
        action = parts[2]
        if my_grid_raw in ("all", "所有", "*"):
            grids = sorted(list(run.player.minions.keys()))
        else:
            grids = []
            for p_g in my_grid_raw.split(','):
                g = p_g.strip().replace("p", "")
                if g in run.player.minions:
                    grids.append(g)
        if not grids:
            return f"❌ 找不到我方随从格子 [{my_grid_raw}]。", False
        results = []
        for g in grids:
            if run.player.hp <= 0:
                return "\n".join(results) + "\n💀 你被击败了！当前进度已清空。", True
            if router.engine.is_battle_won(run):
                router.engine._handle_battle_win(run)
                if run.node_type == "victory":
                    settle_msg = router.save_manager.settle_game_and_delete(user_id, run, is_victory=True)
                    boss_name = run.node_data.get("boss_name")
                    if not boss_name and run.enemies:
                        boss_name = run.enemies[0].name
                    if not boss_name:
                        boss_name = "最终BOSS"
                    return "\n".join(results) + f"\n🎉 恭喜你击败了{boss_name}，通关成功！\n{settle_msg}", True
                else:
                    return "\n".join(results) + "\n🎉 战斗胜利！你击败了敌方所有单位。", True
            if action in ("攻击", "a", "attack"):
                opp_grid = parts[3] if len(parts) > 3 else None
                res = router.engine.minion_attack(run, g, opp_grid)
                results.append(res)
            elif action in ("技能", "s", "skill"):
                skill_idx = 1
                target = None
                if len(parts) > 3:
                    try:
                        skill_idx = int(parts[3])
                        if len(parts) > 4:
                            target = parts[4]
                    except ValueError:
                        target = parts[3]
                res = router.engine.minion_skill(run, g, skill_idx, target)
                results.append(res)
            else:
                return "❌ 未知的随从指令。", False
        res_combined = "\n".join(results)
        if run.player.hp <= 0:
            settle_msg = router.save_manager.settle_game_and_delete(user_id, run, is_victory=False)
            return f"{res_combined}\n💀 你被击败了！当前进度已清空。\n{settle_msg}", True
        if router.engine.is_battle_won(run):
            router.engine._handle_battle_win(run)
            if run.node_type == "victory":
                settle_msg = router.save_manager.settle_game_and_delete(user_id, run, is_victory=True)
                boss_name = run.node_data.get("boss_name")
                if not boss_name and run.enemies:
                    boss_name = run.enemies[0].name
                if not boss_name:
                    boss_name = "最终BOSS"
                return f"{res_combined}\n🎉 恭喜你击败了{boss_name}，通关成功！\n{settle_msg}", True
            else:
                return f"{res_combined}\n🎉 战斗胜利！你击败了敌方所有单位。", True
        return res_combined, False

class ChooseAction(ActionHandler, actions=["选择", "c"]):
    def execute(self, router, user_id: str, run, parts: list[str]) -> Tuple[str, bool]:
        if len(parts) < 2:
            return "❌ 请提供选项序号，例如：选择 1", False
        try:
            idx = int(parts[1])
        except ValueError:
            arg = parts[1].lower()
            if arg in ("取消", "cancel", "返回", "quit", "exit", "0"):
                if run.node_data.get("pending_remove"):
                    run.node_data["pending_remove"] = False
                    router.save_manager.save_save(user_id, run)
                    return "🧹 已取消卡牌移除操作。", False
                if run.node_data.get("pending_upgrade"):
                    run.node_data["pending_upgrade"] = False
                    router.save_manager.save_save(user_id, run)
                    return "🔨 已取消卡牌升级操作。", False
            if arg in ("wizard", "warrior", "wiz", "war", "法师", "战士", "选择", "时序法师", "塑能法师", "秘钥学者"):
                return "❌ 切换职业请在局外使用 /rogue class 命令。\n💡 选择命令 c 仅用于局内选项选择，无法用于选择职业。", False
            return "❌ 序号必须是数字。", False
        if run.node_data.get("pending_upgrade"):
            res = router.engine.upgrade_card_in_deck(run, idx)
            if run.player.hp <= 0:
                settle_msg = router.save_manager.settle_game_and_delete(user_id, run, is_victory=False)
                return f"{res}\n💀 你在荒野的意外中丧生了！当前进度已清空。\n{settle_msg}", True
            return res, False
        elif run.node_type == "shop" and run.node_data.get("pending_remove"):
            res = router.engine.remove_card_from_deck(run, idx)
            return res, False
        else:
            res = router.engine.choose_option(run, idx)
            if run.player.hp <= 0:
                settle_msg = router.save_manager.settle_game_and_delete(user_id, run, is_victory=False)
                return f"{res}\n💀 你在荒野的意外中丧生了！当前进度已清空。\n{settle_msg}", True
            if res == "REMOVE_FLOW":
                run.node_data["pending_remove"] = True
                router.save_manager.save_save(user_id, run)
                return "🧹 净化服务已启动。请查看你的卡组，并再次输入 c <卡牌序号> 来从卡组中移除该牌。可以通过 /rogue deck 查看卡牌序号。", False
            elif res == "UPGRADE_FLOW":
                run.node_data["pending_upgrade"] = True
                router.save_manager.save_save(user_id, run)
                return "🔨 卡牌升级强化已启动。请查看你的卡组，并输入 c <卡牌序号> 来使你的卡牌永久升级为带【+】的强力变体。可以通过 /rogue deck 查看卡牌序号。", False
            else:
                return res, False

class SpecialAction(ActionHandler, actions=["特殊", "sa"]):
    def execute(self, router, user_id: str, run, parts: list[str]) -> Tuple[str, bool]:
        if len(parts) < 2:
            return "❌ 请提供手牌序号，例如：sa 1", False
        try:
            idx = int(parts[1])
        except ValueError:
            return "❌ 序号必须是数字。", False
        target = parts[2] if len(parts) > 2 else None
        res = router.engine.play_special_action(run, idx, target)
        return res, False

class EndTurnAction(ActionHandler, actions=["结束", "e"]):
    def execute(self, router, user_id: str, run, parts: list[str]) -> Tuple[str, bool]:
        res = router.engine.end_turn(run)
        if "冒险结束" in res:
            return res, True
        return res, False

class FoldAction(ActionHandler, actions=["折叠", "f", "fold"]):
    def execute(self, router, user_id: str, run, parts: list[str]) -> Tuple[str, bool]:
        run.player.fold_guide = not run.player.fold_guide
        router.save_manager.save_save(user_id, run)
        state_str = "已折叠" if run.player.fold_guide else "已展开"
        return f"🔮 操作指南状态：【{state_str}】。", False
