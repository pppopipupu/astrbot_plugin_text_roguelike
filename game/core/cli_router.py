from typing import Tuple, Generator
from ..models.state import set_user_id
from ..renderer import GameRenderer
from ..entities import ALL_CARDS
from .cli.base import ActionHandler, CommandHandler, split_by_comma_with_brackets
from . import cli

class CLIRouter:
    def __init__(self, save_manager, engine):
        self.save_manager = save_manager
        self.engine = engine
        self._action_handlers = ActionHandler.registry
        self._command_handlers = CommandHandler.registry

    def _execute_sub_action(self, user_id: str, run, parts: list[str]) -> Tuple[str, bool]:
        set_user_id(user_id)
        if not parts:
            return "", False
        state_stack = run.node_data.setdefault("state_stack", [])
        if run.node_type == "battle" and run.node_data.get("pending_discard"):
            run.node_data.pop("pending_discard", None)
            run.node_data.pop("pending_discard_source", None)
            state_stack.append({"type": "force_discard", "required_count": 1})
        if state_stack:
            top_state = state_stack[-1]
            stype = top_state.get("type")
            if stype == "force_discard":
                sub = parts[0]
                if sub.isdigit():
                    parts = ["选择"] + parts
                    sub = "选择"
                if sub not in ("选择", "c"):
                    return "❌ 你必须先丢弃一张卡牌。请输入：选择 <手牌序号>（如：选择 1）", False
                if len(parts) < 2:
                    return "❌ 请提供手牌序号，例如：选择 1", False
                try:
                    idx = int(parts[1])
                except ValueError:
                    return "❌ 序号必须是数字。", False
                p = run.player
                if idx < 1 or idx > len(p.hand):
                    return f"❌ 无效的手牌序号。你当前手牌有 {len(p.hand)} 张。", False
                cid = p.hand.pop(idx - 1)
                card_name = ALL_CARDS[cid].name if cid in ALL_CARDS else "未知卡牌"
                req_count = top_state.get("required_count", 1)
                discarded = top_state.setdefault("discarded", [])
                discarded.append(cid)
                agile_msg = self.engine._discard_card(run, cid)
                if len(discarded) >= req_count:
                    state_stack.pop()
                else:
                    top_state["required_count"] = req_count - len(discarded)
                    top_state["discarded"] = []
                self.save_manager.save_save(user_id, run)
                res = f"🧹 你丢弃了手牌中的【{card_name}】。"
                if agile_msg:
                    res += f"\n{agile_msg}"
                if self.engine.is_battle_won(run):
                    self.engine._handle_battle_win(run)
                    if run.node_type == "victory":
                        settle_msg = self.save_manager.settle_game_and_delete(user_id, run, is_victory=True)
                        boss_name = run.node_data.get("boss_name")
                        if not boss_name and run.enemies:
                            boss_name = run.enemies[0].name
                        if not boss_name:
                            boss_name = "最终BOSS"
                        return f"{res}\n🎉 恭喜你击败了{boss_name}，通关成功！\n{settle_msg}", True
                    else:
                        return f"{res}\n🎉 战斗胜利！你击败了敌方所有单位。", True
                return res, False
            elif stype == "awaiting_target":
                if parts and parts[0] in self._action_handlers:
                    state_stack.pop()
                    self.save_manager.save_save(user_id, run)
                else:
                    input_str = " ".join(parts).strip()
                    if input_str in ("取消", "cancel", "abandon", "放弃", "q"):
                        state_stack.pop()
                        self.save_manager.save_save(user_id, run)
                        return "❌ 取消使用操作。", False
                    def is_valid_target_format(text: str) -> bool:
                        text = text.strip().lower()
                        if not text:
                            return False
                        if text.isdigit():
                            return True
                        if text.startswith("p") and text[1:].isdigit():
                            return True
                        if text.startswith("e") and text[1:].isdigit():
                            return True
                        return False
                    if is_valid_target_format(input_str):
                        target = input_str
                        action_info = top_state.get("action")
                        if action_info == "play_card":
                            hand_idx = top_state.get("hand_idx")
                            state_stack.pop()
                            res = self.engine.play_card(run, hand_idx, target)
                            if run.player.hp <= 0:
                                settle_msg = self.save_manager.settle_game_and_delete(user_id, run, is_victory=False)
                                return f"{res}\n💀 你被击败了！当前进度已清空。\n{settle_msg}", True
                            if self.engine.is_battle_won(run):
                                self.engine._handle_battle_win(run)
                                if run.node_type == "victory":
                                    settle_msg = self.save_manager.settle_game_and_delete(user_id, run, is_victory=True)
                                    boss_name = run.node_data.get("boss_name")
                                    if not boss_name and run.enemies:
                                        boss_name = run.enemies[0].name
                                    if not boss_name:
                                        boss_name = "最终BOSS"
                                    return f"{res}\n🎉 恭喜你击败了{boss_name}，通关成功！\n{settle_msg}", True
                                else:
                                    return f"{res}\n🎉 战斗胜利！你击败了敌方所有单位。", True
                            return res, False
                        elif action_info == "minion_skill":
                            my_grid = top_state.get("my_grid")
                            skill_idx = top_state.get("skill_idx")
                            state_stack.pop()
                            res = self.engine.minion_skill(run, my_grid, skill_idx, target)
                            if run.player.hp <= 0:
                                settle_msg = self.save_manager.settle_game_and_delete(user_id, run, is_victory=False)
                                return f"{res}\n💀 你被击败了！当前进度已清空。\n{settle_msg}", True
                            if self.engine.is_battle_won(run):
                                self.engine._handle_battle_win(run)
                                if run.node_type == "victory":
                                    settle_msg = self.save_manager.settle_game_and_delete(user_id, run, is_victory=True)
                                    boss_name = run.node_data.get("boss_name")
                                    if not boss_name and run.enemies:
                                        boss_name = run.enemies[0].name
                                    if not boss_name:
                                        boss_name = "最终BOSS"
                                    return f"{res}\n🎉 恭喜你击败了{boss_name}，通关成功！\n{settle_msg}", True
                                else:
                                    return f"{res}\n🎉 战斗胜利！你击败了敌方所有单位。", True
                            return res, False
                    else:
                        state_stack.pop()
                        self.save_manager.save_save(user_id, run)
                        return "❌ 取消使用操作。", False
            elif stype == "discover_selection":
                input_str = " ".join(parts).strip()
                if input_str in ("取消", "cancel", "abandon", "放弃", "q"):
                    state_stack.pop()
                    self.save_manager.save_save(user_id, run)
                    return "❌ 取消发掘操作。", False
                sub = parts[0]
                if sub.isdigit():
                    parts = ["选择"] + parts
                    sub = "选择"
                if sub not in ("选择", "c"):
                    return "❌ 你必须从消耗堆中选择卡牌。请输入：选择 <卡牌序号>（如：选择 1），或输入 取消/q 放弃发掘。", False
                if len(parts) < 2:
                    return "❌ 请提供卡牌序号，例如：选择 1", False
                try:
                    idx = int(parts[1])
                except ValueError:
                    return "❌ 序号必须是数字。", False
                p = run.player
                if idx < 1 or idx > len(p.exhaust_pile):
                    return f"❌ 无效的消耗堆序号。当前消耗堆有 {len(p.exhaust_pile)} 张卡牌。", False
                cid = p.exhaust_pile.pop(idx - 1)
                p.hand.append(cid)
                card_name = ALL_CARDS[cid].name if cid in ALL_CARDS else "未知卡牌"
                top_state.setdefault("selected", []).append(cid)
                req_count = top_state.get("count", 1)
                if len(top_state["selected"]) < req_count and p.exhaust_pile:
                    self.save_manager.save_save(user_id, run)
                    exhaust_list = "\n".join(f"{i+1}. {ALL_CARDS[c].name}" for i, c in enumerate(p.exhaust_pile))
                    return f"✨ 你发掘了【{card_name}】并加入手牌。请继续选择第 {len(top_state['selected']) + 1} 张发掘卡牌：\n{exhaust_list}", False
                else:
                    state_stack.pop()
                    self.save_manager.save_save(user_id, run)
                    selected_cards_str = "，".join(ALL_CARDS[c].name for c in top_state["selected"])
                    return f"✨ 你完成了发掘，获得了【{selected_cards_str}】并加入手牌。", False
        if parts[0].isdigit():
            parts = ["选择"] + parts
        sub = parts[0]
        handler = self._action_handlers.get(sub)
        if handler:
            return handler.execute(self, user_id, run, parts)
        return f"🔮 未知操作：{parts}", False

    def _execute_queue(self, user_id: str, run, queue_content: str, results: list[str]) -> bool:
        content = queue_content.strip()
        if content.startswith("[") and content.endswith("]"):
            content = content[1:-1].strip()
        items = split_by_comma_with_brackets(content)
        for item in items:
            if not item:
                continue
            parts_sub = item.split()
            if not parts_sub:
                continue
            first_sub = parts_sub[0].lower()
            if first_sub in ("队列", "q", "queue"):
                sub_content = item[len(parts_sub[0]):].strip()
                term = self._execute_queue(user_id, run, sub_content, results)
                if term:
                    return True
            else:
                res, term = self._execute_sub_action(user_id, run, parts_sub)
                results.append(res)
                if term:
                    return True
        return False

    def handle_command(self, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        set_user_id(user_id)
        if not parts:
            run = self.save_manager.load_save(user_id)
            if run:
                yield GameRenderer.render_game(run)
            else:
                stats = self.save_manager.load_stats(user_id)
                yield GameRenderer.render_menu(stats)
            return
        run = self.save_manager.load_save(user_id)
        if run and run.node_data.get("state_stack"):
            res, term = self._execute_sub_action(user_id, run, parts)
            yield res
            return
        if parts[0].isdigit():
            parts = ["选择"] + parts
        sub = parts[0]
        handler = self._command_handlers.get(sub)
        if handler:
            yield from handler.execute(self, user_id, parts)
        else:
            yield "🔮 未知子命令。输入 /rogue 帮助 或 /rogue help 获取帮助。"
