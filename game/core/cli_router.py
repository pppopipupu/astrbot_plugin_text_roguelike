from typing import List, Tuple, Generator
from ..models.state import set_user_id
from ..renderer import GameRenderer
from ..entities import ALL_CARDS

def split_by_comma_with_brackets(s: str) -> list[str]:
    parts = []
    current = []
    bracket_depth = 0
    for char in s:
        if char == '[':
            bracket_depth += 1
            current.append(char)
        elif char == ']':
            bracket_depth -= 1
            current.append(char)
        elif char == ',' and bracket_depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        parts.append("".join(current).strip())
    return [p for p in parts if p]

class CLIRouter:
    def __init__(self, save_manager, engine):
        self.save_manager = save_manager
        self.engine = engine

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
                        return f"{res}\n🎉 恭喜你击败了腐化之心，通关成功！\n{settle_msg}", True
                    else:
                        return f"{res}\n🎉 战斗胜利！你击败了敌方所有单位。", True
                return res, False

            elif stype == "awaiting_target":
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
                                return f"{res}\n🎉 恭喜你击败了腐化之心，通关成功！\n{settle_msg}", True
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
                                return f"{res}\n🎉 恭喜你击败了腐化之心，通关成功！\n{settle_msg}", True
                            else:
                                return f"{res}\n🎉 战斗胜利！你击败了敌方所有单位。", True
                        return res, False
                else:
                    state_stack.pop()

        if parts[0].isdigit():
            parts = ["选择"] + parts
        sub = parts[0]

        if sub in ("使用", "p"):
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
                        self.save_manager.save_save(user_id, run)
                        return prompt_msg, False

            res = self.engine.play_card(run, idx, target)
            if run.player.hp <= 0:
                settle_msg = self.save_manager.settle_game_and_delete(user_id, run, is_victory=False)
                return f"{res}\n💀 你被击败了！当前进度已清空。\n{settle_msg}", True
            if self.engine.is_battle_won(run):
                self.engine._handle_battle_win(run)
                if run.node_type == "victory":
                    settle_msg = self.save_manager.settle_game_and_delete(user_id, run, is_victory=True)
                    return f"{res}\n🎉 恭喜你击败了腐化之心，通关成功！\n{settle_msg}", True
                else:
                    return f"{res}\n🎉 战斗胜利！你击败了敌方所有单位。", True
            return res, False

        elif sub in ("随从", "m"):
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
                if self.engine.is_battle_won(run):
                    return "\n".join(results) + "\n🎉 战斗胜利！", True

                if action in ("攻击", "a"):
                    opp_grid = parts[3] if len(parts) > 3 else None
                    res = self.engine.minion_attack(run, g, opp_grid)
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
                    if m.id == "mercenary" and skill_idx == 1:
                        needs_target = True
                    elif m.id == "shield_guard" and skill_idx == 2:
                        needs_target = True
                    elif m.id == "water_elemental" and skill_idx == 2:
                        needs_target = True
                        
                    if needs_target and target is None and len(run.enemies) > 1:
                        state_stack = run.node_data.setdefault("state_stack", [])
                        state_stack.append({
                            "type": "awaiting_target",
                            "action": "minion_skill",
                            "my_grid": g,
                            "skill_idx": skill_idx
                        })
                        self.save_manager.save_save(user_id, run)
                        return f"🎯 请选择敌方目标。当前战场有多个敌方单位，请输入敌方格子序号（如：e1, e2 或 1, 2）或输入取消：", False

                    res = self.engine.minion_skill(run, g, skill_idx, target)
                    results.append(res)
                else:
                    return "❌ 未知的随从指令。", False
                    
            res_combined = "\n".join(results)
            if run.player.hp <= 0:
                settle_msg = self.save_manager.settle_game_and_delete(user_id, run, is_victory=False)
                return f"{res_combined}\n💀 你被击败了！当前进度已清空。\n{settle_msg}", True
                
            if self.engine.is_battle_won(run):
                self.engine._handle_battle_win(run)
                if run.node_type == "victory":
                    settle_msg = self.save_manager.settle_game_and_delete(user_id, run, is_victory=True)
                    return f"{res_combined}\n🎉 恭喜你击败了腐化之心，通关成功！\n{settle_msg}", True
                else:
                    return f"{res_combined}\n🎉 战斗胜利！你击败了敌方所有单位。", True
            return res_combined, False

        elif sub in ("选择", "c"):
            if len(parts) < 2:
                return "❌ 请提供选项序号，例如：选择 1", False
            try:
                idx = int(parts[1])
            except ValueError:
                return "❌ 序号必须是数字。", False
            if run.node_type == "shop" and run.node_data.get("pending_remove"):
                res = self.engine.remove_card_from_deck(run, idx)
                return res, False
            else:
                res = self.engine.choose_option(run, idx)
                if res == "REMOVE_FLOW":
                    run.node_data["pending_remove"] = True
                    self.save_manager.save_save(user_id, run)
                    return "🧹 净化服务已启动。请查看你的卡组，并再次输入 选择 <卡牌序号> 来从卡组中移除该牌。可以通过 /rogue 牌组 查看卡牌序号。", False
                else:
                    return res, False

        elif sub in ("特殊", "sa"):
            if len(parts) < 2:
                return "❌ 请提供手牌序号，例如：特殊 1", False
            try:
                idx = int(parts[1])
            except ValueError:
                return "❌ 序号必须是数字。", False
            target = parts[2] if len(parts) > 2 else None
            res = self.engine.play_special_action(run, idx, target)
            return res, False

        elif sub in ("结束", "e"):
            res = self.engine.end_turn(run)
            if "冒险结束" in res:
                return res, True
            return res, False

        elif sub in ("折叠", "f", "fold"):
            run.player.fold_guide = not run.player.fold_guide
            self.save_manager.save_save(user_id, run)
            state_str = "已折叠" if run.player.fold_guide else "已展开"
            return f"🔮 操作指南状态：【{state_str}】。", False

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
            
        if parts[0].isdigit():
            parts = ["选择"] + parts
        sub = parts[0]
        
        if sub in ("开启", "start"):
            run = self.save_manager.load_save(user_id)
            if run:
                if len(parts) > 1 and parts[1] == "确认":
                    new_run = self.engine.start_new_game(user_id)
                    yield "已重新开始新的一局游戏。\n" + GameRenderer.render_game(new_run)
                else:
                    yield "⚠️ 你当前已有一局正在进行中的游戏。若要强制重新开始并覆盖存档，请输入：\n/rogue 开启 确认（或 /rogue start 确认）"
            else:
                new_run = self.engine.start_new_game(user_id)
                yield GameRenderer.render_game(new_run)
                
        elif sub in ("状态", "s"):
            run = self.save_manager.load_save(user_id)
            if not run:
                stats = self.save_manager.load_stats(user_id)
                yield GameRenderer.render_menu(stats)
            else:
                yield GameRenderer.render_game(run)
                
        elif sub in ("牌组", "deck"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield "❌ 你当前没有正在进行的游戏。输入 /rogue 开启 开始新游戏。"
            else:
                yield GameRenderer.render_deck(run)
                
        elif sub in ("总览", "overview"):
            if len(parts) > 1 and parts[1] in ("遗物", "relic", "relics"):
                yield GameRenderer.render_relic_library()
            else:
                yield GameRenderer.render_card_library()
            
        elif sub in ("帮助", "help"):
            yield GameRenderer.render_help()
            
        elif sub in ("mode", "模式"):
            stats = self.save_manager.load_stats(user_id)
            stats.rogue_mode = not stats.rogue_mode
            self.save_manager.save_stats(user_id, stats)
            status_str = "开启" if stats.rogue_mode else "关闭"
            yield f"✨ 免前缀肉鸽模式已{status_str}！此设置仅对你个人生效。"
            
        elif sub in ("使用", "p"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield "❌ 你当前没有正在进行的游戏。"
                return
            if len(parts) < 2:
                yield "❌ 请提供手牌序号，例如：/rogue 使用 1"
                return
            
            full_arg = " ".join(parts[1:])
            is_queue = False
            if full_arg.startswith("[") or "," in full_arg:
                is_queue = True
                
            if is_queue:
                clean_arg = full_arg.replace("[", "").replace("]", "").replace(" ", "")
                items = clean_arg.split(",")
                converted_items = []
                for item in items:
                    if not item:
                        continue
                    if ":" in item:
                        idx_str, target = item.split(":", 1)
                        converted_items.append(f"使用 {idx_str} {target}")
                    else:
                        converted_items.append(f"使用 {item}")
                queue_str = "[" + ", ".join(converted_items) + "]"
                
                results = []
                self._execute_queue(user_id, run, queue_str, results)
                yield "\n".join(results) + "\n" + GameRenderer.render_game(run)
            else:
                res, term = self._execute_sub_action(user_id, run, parts)
                if term:
                    yield res
                else:
                    yield res + "\n" + GameRenderer.render_game(run)
            
        elif sub in ("随从", "m"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield "❌ 你当前没有正在进行的游戏。"
                return
            if len(parts) < 2:
                yield "❌ 请提供随从指令，例如：/rogue 随从 1 攻击 e1"
                return
                
            full_arg = " ".join(parts[1:])
            is_queue = False
            if "," in full_arg:
                sub_parts = split_by_comma_with_brackets(full_arg)
                is_queue = True
                valid_parts_count = 0
                for sp in sub_parts:
                    sp_clean = sp.strip()
                    if not sp_clean:
                        continue
                    valid_parts_count += 1
                    words = sp_clean.split()
                    if len(words) < 2:
                        is_queue = False
                        break
                if valid_parts_count <= 1:
                    is_queue = False
                    
            if is_queue:
                items = split_by_comma_with_brackets(full_arg)
                converted_items = []
                for item in items:
                    item_str = item.strip()
                    if not item_str:
                        continue
                    if item_str.startswith("随从 ") or item_str.startswith("m "):
                        converted_items.append(item_str)
                    else:
                        converted_items.append(f"随从 {item_str}")
                queue_str = "[" + ", ".join(converted_items) + "]"
                
                results = []
                self._execute_queue(user_id, run, queue_str, results)
                yield "\n".join(results) + "\n" + GameRenderer.render_game(run)
            else:
                res, term = self._execute_sub_action(user_id, run, parts)
                if term:
                    yield res
                else:
                    yield res + "\n" + GameRenderer.render_game(run)
                
        elif sub in ("选择", "c"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield "❌ 你当前没有正在进行的游戏。"
                return
            res, term = self._execute_sub_action(user_id, run, parts)
            yield res + "\n" + GameRenderer.render_game(run)
 
        elif sub in ("特殊", "sa"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield "❌ 你当前没有正在进行的游戏。"
                return
            res, term = self._execute_sub_action(user_id, run, parts)
            yield res + "\n" + GameRenderer.render_game(run)
                    
        elif sub in ("结束", "e"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield "❌ 你当前没有正在进行的游戏。"
                return
            res, term = self._execute_sub_action(user_id, run, parts)
            if term:
                yield res
            else:
                yield res + "\n" + GameRenderer.render_game(run)
                
        elif sub in ("放弃", "abandon"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield "❌ 你当前没有正在进行的游戏。"
                return
            if len(parts) > 1 and parts[1] in ("确认", "confirm"):
                settle_msg = self.save_manager.settle_game_and_delete(user_id, run, is_victory=False)
                yield f"已放弃当前局内游戏，当前进度已清空。\n{settle_msg}"
            else:
                yield "⚠️ 确认放弃当前游戏？放弃后进度将无法恢复。确认请输入：\n/rogue 放弃 确认（或 /rogue abandon confirm）"

        elif sub in ("职业", "class"):
            stats = self.save_manager.load_stats(user_id)
            if len(parts) == 1:
                gp = getattr(stats, "gp", 0)
                selected_subclass = getattr(stats, "selected_subclass", "") or "无"
                unlocked = getattr(stats, "unlocked_subclasses", [])
                
                status_time = "已解锁" if "时序法师" in unlocked else "未解锁（2888 GP）"
                status_element = "已解锁" if "塑能法师" in unlocked else "未解锁（2888 GP）"
                
                lines = [
                    "━━━━━━━━━━━━━━━━━━━━",
                    "🧙 魔法肉鸽卡牌子职业系统",
                    "",
                    f"💰 我的 GP：{gp}",
                    f"🧙 当前职业：法师  🔮 子职业：{selected_subclass}",
                    "",
                    "【可用的子职业】",
                    f"1. 时序法师 - 状态：[{status_time}]",
                    "   └─ 操控时间。开局获得专属传奇卡牌“时间停止”（追加 3 个额外回合）。",
                    f"2. 塑能法师 - 状态：[{status_element}]",
                    "   └─ 元素爆发。所有法术伤害提升 15%，且抓取火球术时 40% 几率将火球术替换为流星爆。",
                    "",
                    "【职业命令】",
                    "👉 /rogue 职业 选择 时序法师 -- 装备时序法师子职业",
                    "👉 /rogue 职业 选择 塑能法师 -- 装备塑能法师子职业",
                    "👉 /rogue 职业 选择 无       -- 取消装备子职业",
                    "💡 如需购买子职业，请使用局外商店：/rogue 商店",
                    "━━━━━━━━━━━━━━━━━━━━"
                ]
                yield "\n".join(lines)
            elif len(parts) >= 3 and parts[1] == "购买":
                yield "💡 请使用商店命令前往局外商店进行商品购买：/rogue 商店"
            elif len(parts) >= 3 and parts[1] == "选择":
                subclass_name = parts[2]
                if subclass_name in ("无", "取消"):
                    stats.selected_subclass = ""
                    self.save_manager.save_stats(user_id, stats)
                    yield "🔮 已取消子职业选择。当前以基础法师开始游戏。"
                    return
                if subclass_name not in ("时序法师", "塑能法师"):
                    yield "❌ 无效的子职业。可选：时序法师、塑能法师、无。"
                    return
                unlocked = getattr(stats, "unlocked_subclasses", [])
                if subclass_name not in unlocked:
                    yield f"❌ 你尚未解锁【{subclass_name}】。需要消耗 2888 GP 购买，请使用：/rogue 商店"
                    return
                stats.selected_subclass = subclass_name
                self.save_manager.save_stats(user_id, stats)
                yield f"🔮 已选择子职业为【{subclass_name}】。将在新的一局游戏中生效！"
            else:
                yield "❌ 格式错误。请使用 /rogue 职业、/rogue 职业 选择 <子职业|无>。"

        elif sub in ("商店", "shop"):
            stats = self.save_manager.load_stats(user_id)
            if len(parts) == 1:
                yield GameRenderer.render_shop(stats)
            elif len(parts) >= 3 and parts[1] == "购买":
                target = parts[2]
                unlocked = getattr(stats, "unlocked_subclasses", [])
                gp = getattr(stats, "gp", 0)
                
                if target in ("1", "时序法师"):
                    subclass_name = "时序法师"
                    price = 2888
                elif target in ("2", "塑能法师"):
                    subclass_name = "塑能法师"
                    price = 2888
                elif target in ("3", "神秘物品"):
                    subclass_name = "神秘物品"
                    price = 66666
                else:
                    yield "❌ 无效的商品。可选商品序号：1、2、3。"
                    return
                    
                if subclass_name in unlocked:
                    yield f"❌ 你已经解锁了【{subclass_name}】。"
                    return
                if gp < price:
                    import random
                    fail_quotes = [
                        "“呵呵，我的宝贝可概不赊账。多去地下城闯一闯，赚够了GP再来吧。”",
                        "“看来你的钱包和你的雄心壮志并不相符，旅者。”",
                        "“钱不够？那可不行。等你有了足够的GP，我随时在这儿等你。”",
                        "“GP不够可是买不到虚空造物的，去多打败一些强大的怪兽吧。”",
                        "“哦？想要空手套白狼？这可不是一个合格法师该有的行为。”",
                        "“即使是至高法皇，没钱也得从我这里老老实实地退出去，懂吗？”"
                    ]
                    quote = random.choice(fail_quotes)
                    yield f"❌ 你的 GP 不足。购买【{subclass_name}】需要 {price} GP，你当前只有 {gp} GP。\n🔮 神秘店主说：\n  {quote}"
                    return
                    
                stats.gp -= price
                stats.unlocked_subclasses.append(subclass_name)
                self.save_manager.save_stats(user_id, stats)
                import random
                success_quotes = [
                    "“明智的选择，它现在属于你了。”",
                    "“收您对应GP，拿好它，祝您好运，勇敢的旅者。”",
                    "“呵呵，这股力量已经在虚空中沉睡了太久，希望你能配得上它。”",
                    "“拿去吧，它会指引你在接下来的地下城里改写宿命。”",
                    "“噢……它离去时，连虚空的波动都微微震颤了一下。”",
                    "“成交。记住，有些契约一经签订，便无法回头。”"
                ]
                quote = random.choice(success_quotes)
                yield f"🎉 购买成功！已成功解锁【{subclass_name}】。已扣除 {price} GP。\n🔮 神秘店主说：\n  {quote}"
            else:
                yield "❌ 格式错误。请使用 /rogue 商店 或 /rogue 商店 购买 <商品序号/商品名称>。"

        elif sub in ("折叠", "f", "fold"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield "❌ 你当前没有正在进行的游戏。"
                return
            res, term = self._execute_sub_action(user_id, run, parts)
            yield res + "\n" + GameRenderer.render_game(run)

        elif sub in ("队列", "q", "queue"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield "❌ 你当前没有正在进行的游戏。"
                return
            if len(parts) < 2:
                yield "❌ 请提供队列操作，例如：/rogue 队列 [使用 1, 随从 1 技能 2, 结束]"
                return
            
            full_arg = " ".join(parts[1:])
            results = []
            self._execute_queue(user_id, run, full_arg, results)
            
            if run.player.hp <= 0:
                yield "\n".join(results)
            else:
                yield "\n".join(results) + "\n" + GameRenderer.render_game(run)

        elif sub in ("统计", "stat", "stats"):
            stats = self.save_manager.load_stats(user_id)
            yield GameRenderer.render_stats(stats)

        elif sub in ("查询", "query", "info", "i"):
            run = self.save_manager.load_save(user_id)
            if len(parts) > 1:
                query_str = " ".join(parts[1:]).strip()
                yield GameRenderer.render_query_info(query_str)
            else:
                if not run:
                    yield "❌ 你当前没有正在进行的游戏。输入 /rogue 开启 开始新游戏。"
                elif run.node_type != "battle":
                    yield "❌ 只有在战斗中才能查询详细战斗信息。请输入想要查询的随从、遗物、Buff名称。"
                else:
                    yield GameRenderer.render_detailed_battle(run)
                
        else:
            yield "🔮 未知子命令。输入 /rogue 帮助 或 /rogue help 获取帮助。"
