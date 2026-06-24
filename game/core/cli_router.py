from typing import Tuple, Generator
from ..models.state import set_user_id, UserStats, GameRun
from ..renderer import GameRenderer
from ..entities import ALL_CARDS
from .cli.base import ActionHandler, CommandHandler, split_by_comma_with_brackets
from . import cli
from .town_engine import TownEngine

class CLIRouter:
    def __init__(self, save_manager, engine):
        self.save_manager = save_manager
        self.engine = engine
        self._action_handlers = ActionHandler.registry
        self._command_handlers = CommandHandler.registry
        self.town_engine = TownEngine(save_manager, engine)

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

    def _handle_town_combat_settle(self, user_id: str, run: GameRun, original_res: str) -> str:
        latest_run = self.save_manager.load_save(user_id)
        zh_cn = self.town_engine._load_zh_cn()
        if not latest_run:
            stats = self.save_manager.load_stats(user_id)
            stats.in_town = True
            stats.town_pos = "range"
            self.save_manager.save_stats(user_id, stats)
            return original_res + "\n\n" + zh_cn.get("global", {}).get("combat_quit", "💀 你已退出了切磋，回到了靶场房间。") + "\n\n" + self.town_engine.render_current_room(user_id, stats)
        p = latest_run.player
        is_won = self.engine.is_battle_won(latest_run) or latest_run.node_type in ("reward", "victory")
        is_lost = p.hp <= 0
        if is_won or is_lost:
            self.save_manager.delete_save(user_id)
            stats = self.save_manager.load_stats(user_id)
            stats.in_town = True
            if is_lost:
                self.save_manager.save_stats(user_id, stats)
                return f"{original_res}\n\n" + zh_cn.get("global", {}).get("combat_lost", "💀 你被击败了！不过别担心，在主城的切磋不影响你的局外进度。你已回到了靶场房间。") + "\n\n" + self.town_engine.render_current_room(user_id, stats)
            npc_name = run.node_data.get("npc_name", "") or latest_run.node_data.get("npc_name", "")
            if npc_name == "NoobSlayer99" and stats.town_flags.get("quest_hammer_state") == "started":
                stats.town_flags["noob_coerced_hammer"] = True
            gp_gained = 0
            msg_bonus = ""
            if npc_name == "训练假人":
                msg_bonus = zh_cn.get("global", {}).get("combat_won_dummy", "训练假人已被摧毁！切磋完成。")
            else:
                if npc_name not in stats.defeated_town_npcs:
                    stats.defeated_town_npcs.append(npc_name)
                    if npc_name == "NoobSlayer99":
                        gp_gained = 100
                    elif npc_name == "xXx_SniperElite_xXx":
                        gp_gained = 150
                    elif npc_name == "Gate_Guardian":
                        gp_gained = 500
                    elif npc_name == "pppopipupu":
                        gp_gained = 1000
                    stats.gp += gp_gained
                    msg_bonus = zh_cn.get("global", {}).get("combat_won_first", "").format(name=npc_name, gp=gp_gained)
                else:
                    msg_bonus = zh_cn.get("global", {}).get("combat_won_repeat", "").format(name=npc_name)
            self.save_manager.save_stats(user_id, stats)
            return f"{original_res}\n\n" + zh_cn.get("global", {}).get("combat_won_banner", "🎉 战斗胜利！{bonus}").format(bonus=msg_bonus) + "\n\n" + self.town_engine.render_current_room(user_id, stats)
        return original_res

    def handle_command(self, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        for res in self._handle_command_raw(user_id, parts):
            yield res

    def _get_current_state(self, user_id: str, run) -> str:
        if run is not None:
            if getattr(run, "node_type", "") == "battle":
                return "battle"
            return "explore"
        stats = self.save_manager.load_stats(user_id)
        if stats is not None:
            if getattr(stats, "in_town", False):
                if stats.town_flags.get("current_dialog"):
                    return "dialog"
                return "town"
        return "menu"

    def _handle_command_raw(self, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        set_user_id(user_id)
        run = self.save_manager.load_save(user_id)
        curr_state = self._get_current_state(user_id, run)
        if parts:
            first_cmd = parts[0].lower()
            exempt_cmds = (
                "查询", "query", "info", "i",
                "背包", "bag", "inventory", "inv",
                "任务", "quest", "quests"
            )
            if first_cmd in exempt_cmds:
                handler = self._command_handlers.get(first_cmd)
                if handler:
                    if curr_state in getattr(handler, "allowed_states", []):
                        res_list = list(handler.execute(self, user_id, parts))
                        yield "\n".join(res_list)
                        return
                    else:
                        yield f"❌ 指令【{first_cmd}】在当前状态下不可用。"
                        return
        is_town_combat = run is not None and run.node_data.get("is_town_combat", False)
        if not parts:
            if run:
                yield GameRenderer.render_game(run)
            else:
                stats = self.save_manager.load_stats(user_id)
                if stats.in_town:
                    yield self.town_engine.render_current_room(user_id, stats)
                else:
                    yield GameRenderer.render_menu(stats)
            return
        if not run:
            stats = self.save_manager.load_stats(user_id)
            if stats.in_town:
                active_dialog = stats.town_flags.get("current_dialog")
                zh_cn = self.town_engine._load_zh_cn()
                if active_dialog:
                    input_str = " ".join(parts).strip()
                    yield self.town_engine.handle_dialog_input(user_id, input_str)
                    return
                cmd = parts[0].lower()
                if cmd in ("w", "a", "s", "d", "up", "down", "left", "right"):
                    yield self.town_engine.move(user_id, cmd)
                    return
                elif cmd in ("退出", "quit", "exit", "q"):
                    stats.in_town = False
                    self.save_manager.save_stats(user_id, stats)
                    yield zh_cn.get("global", {}).get("town_exit_success", "👋 你已退出主城，回到主菜单。") + "\n\n" + GameRenderer.render_menu(stats)
                    return
                elif cmd in ("回城", "home"):
                    stats.town_pos = "square"
                    self.save_manager.save_stats(user_id, stats)
                    yield self.town_engine.render_current_room(user_id, stats)
                    return
                elif cmd in ("拿取", "捡起", "take", "pick"):
                    if len(parts) < 2:
                        yield zh_cn.get("global", {}).get("take_missing_param", "❌ 请提供物品名字，例如：take 幸运硬币")
                    else:
                        yield self.town_engine.pick_item(user_id, " ".join(parts[1:]))
                    return
                elif cmd in ("使用", "use"):
                    if len(parts) < 2:
                        yield zh_cn.get("global", {}).get("use_missing_param", "❌ 请指定使用的物品，例如：use 遗失的笔记本")
                    else:
                        yield self.town_engine.use_item(user_id, " ".join(parts[1:]))
                    return
                elif cmd in ("交互", "talk", "interact", "inter", "talk_to"):
                    if len(parts) < 2:
                        yield zh_cn.get("global", {}).get("talk_missing_param", "❌ 请指定交互的目标，例如：talk 向导长老")
                    else:
                        yield self.town_engine.talk_npc(user_id, " ".join(parts[1:]))
                    return
                elif cmd in ("查询", "query", "info", "i", "统计", "stat", "stats", "帮助", "help", "地图", "map"):
                    pass
                else:
                    yield zh_cn.get("global", {}).get("town_help_prompt", "🔮 主城探索中。输入 退出/exit 回到主菜单，或输入 W/A/S/D 进行移动。输入 交互/talk <目标> 开启互动。")
                    return
        if run and run.node_data.get("state_stack"):
            res, term = self._execute_sub_action(user_id, run, parts)
            if is_town_combat:
                yield self._handle_town_combat_settle(user_id, run, res)
            else:
                yield res
            return
        if parts[0].isdigit():
            parts = ["选择"] + parts
        sub = parts[0]
        handler = self._command_handlers.get(sub)
        if handler:
            if curr_state in getattr(handler, "allowed_states", []):
                res_list = list(handler.execute(self, user_id, parts))
                res_text = "\n".join(res_list)
                if is_town_combat:
                    yield self._handle_town_combat_settle(user_id, run, res_text)
                else:
                    yield res_text
            else:
                yield f"❌ 指令【{sub}】在当前状态下不可用。"
        else:
            yield "🔮 未知子命令。输入 /rogue 帮助 或 /rogue help 获取帮助。"
