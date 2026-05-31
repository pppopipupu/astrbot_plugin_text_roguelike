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
        target = parts[2] if len(parts) > 2 else None
        p = run.player
        if 1 <= idx <= len(p.hand):
            cid = p.hand[idx - 1]
            card = ALL_CARDS.get(cid)
            if card and card.type == "spell" and target is None:
                is_ambiguous = False
                prompt_msg = ""
                if card.id in ("dagger_throw", "fire_bolt", "magic_missile", "quick_strike", "arcane_spark", "agile_strike", "fleeting_spark"):
                    if len(run.enemies) > 1:
                        is_ambiguous = True
                        prompt_msg = f"🎯 请选择敌方目标。当前战场有多个敌方单位，请输入敌方格子序号（如：e1, e2 或 1, 2）或输入取消："
                elif card.id == "first_aid":
                    if len(p.minions) > 0:
                        is_ambiguous = True
                        prompt_msg = f"💚 请选择治疗目标。请输入目标格子序号（如：p0 治疗自己，p1-p6 治疗对应随从）或输入取消："
                if is_ambiguous:
                    state_stack = run.node_data.setdefault("state_stack", [])
                    state_stack.append({
                        "type": "awaiting_target",
                        "action": "play_card",
                        "hand_idx": idx
                    })
                    router.save_manager.save_save(user_id, run)
                    return prompt_msg, False
        res = router.engine.play_card(run, idx, target)
        if run.player.hp <= 0:
            settle_msg = router.save_manager.settle_game_and_delete(user_id, run, is_victory=False)
            return f"{res}\n💀 你被击败了！当前进度已清空。\n{settle_msg}", True
        if router.engine.is_battle_won(run):
            router.engine._handle_battle_win(run)
            if run.node_type == "victory":
                settle_msg = router.save_manager.settle_game_and_delete(user_id, run, is_victory=True)
                return f"{res}\n🎉 恭喜你击败了腐化之心，通关成功！\n{settle_msg}", True
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
                return "\n".join(results) + "\n🎉 战斗胜利！", True
            if action in ("攻击", "a"):
                opp_grid = parts[3] if len(parts) > 3 else None
                res = router.engine.minion_attack(run, g, opp_grid)
                results.append(res)
            elif action in ("技能", "s"):
                skill_idx = 1
                target = None
                if len(parts) > 3:
                    try:
                        skill_idx = int(parts[3])
                        if len(parts) > 4:
                            target = parts[4]
                    except ValueError:
                        target = parts[3]
                p = run.player
                m = p.minions[g]
                needs_target = False
                base_id = m.id.rstrip("+")
                if base_id == "mercenary" and skill_idx == 1:
                    needs_target = True
                elif base_id == "shield_guard" and skill_idx == 2:
                    needs_target = True
                elif base_id == "water_elemental" and skill_idx == 2:
                    needs_target = True
                if needs_target and target is None and len(run.enemies) > 1:
                    state_stack = run.node_data.setdefault("state_stack", [])
                    state_stack.append({
                        "type": "awaiting_target",
                        "action": "minion_skill",
                        "my_grid": g,
                        "skill_idx": skill_idx
                    })
                    router.save_manager.save_save(user_id, run)
                    return f"🎯 请选择敌方目标。当前战场有多个敌方单位，请输入敌方格子序号（如：e1, e2 或 1, 2）或输入取消：", False
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
                return f"{res_combined}\n🎉 恭喜你击败了腐化之心，通关成功！\n{settle_msg}", True
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
                return "🧹 净化服务已启动。请查看你的卡组，并再次输入 选择 <卡牌序号> 来从卡组中移除该牌。可以通过 /rogue 牌组 查看卡牌序号。", False
            elif res == "UPGRADE_FLOW":
                run.node_data["pending_upgrade"] = True
                router.save_manager.save_save(user_id, run)
                return "🔨 卡牌升级强化已启动。请查看你的卡组，并输入 选择 <卡牌序号> 来使你的卡牌永久升级为带【+】的强力变体。可以通过 /rogue 牌组 查看卡牌序号。", False
            else:
                return res, False

class SpecialAction(ActionHandler, actions=["特殊", "sa"]):
    def execute(self, router, user_id: str, run, parts: list[str]) -> Tuple[str, bool]:
        if len(parts) < 2:
            return "❌ 请提供手牌序号，例如：特殊 1", False
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
