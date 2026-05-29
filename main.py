try:
    from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
    from astrbot.api.star import Context, Star, register
    from astrbot.api import logger
except ImportError:
    class Star:
        def __init__(self, context, config=None):
            self.context = context
            self.config = config or {}
    class Context:
        pass
    class AstrMessageEvent:
        pass
    class MessageEventResult:
        pass
    def register(*args, **kwargs):
        return lambda cls: cls
    class FilterDummy:
        def command(*args, **kwargs):
            return lambda func: func
        def regex(*args, **kwargs):
            return lambda func: func
    filter = FilterDummy()
    class DummyLogger:
        def info(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def debug(self, *args, **kwargs): pass
    logger = DummyLogger()

try:
    from .game.manager import SaveManager
    from .game.engine import GameEngine
    from .game.renderer import GameRenderer
except ImportError:
    from game.manager import SaveManager
    from game.engine import GameEngine
    from game.renderer import GameRenderer

try:
    from .game.models import current_user_id, set_user_id
except ImportError:
    from game.models import current_user_id, set_user_id

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

@register("helloworld", "YourName", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict | None = None):
        super().__init__(context, config)
        self.config = config or {}
        try:
            from astrbot.api.star import StarTools
            data_dir = str(StarTools.get_data_dir("astrbot_plugin_text_roguelike"))
        except Exception:
            data_dir = None
        self.save_manager = SaveManager(data_dir)
        self.engine = GameEngine(self.save_manager)

    async def initialize(self):
        pass

    async def terminate(self):
        pass

    @filter.command("rogue")
    async def rogue(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        message_str = event.message_str.strip()
        parts = message_str.split()
        if not parts:
            stats = self.save_manager.load_stats(user_id)
            yield event.plain_result(GameRenderer.render_menu(stats))
            return
        
        first = parts[0].lower()
        if first in ("rogue", "/rogue"):
            parts = parts[1:]
            
        async for res in self._handle_rogue_logic(event, parts):
            yield res

    @filter.regex(r".*")
    async def shortcut_rogue(self, event: AstrMessageEvent):
        enable = self.config.get("enable_shortcut", True)
        if not enable:
            return
        
        user_id = event.get_sender_id()
        stats = self.save_manager.load_stats(user_id)
        rogue_mode = stats.rogue_mode if stats else False
        
        prefix_config = self.config.get("shortcut_prefix", ".rogue")
        if isinstance(prefix_config, list):
            prefixes = prefix_config
        elif isinstance(prefix_config, str):
            prefixes = [prefix_config]
        else:
            prefixes = [".rogue"]
            
        message_str = event.message_str.strip()
        sorted_prefixes = sorted([p for p in prefixes if p], key=len, reverse=True)
        matched_prefix = None
        matched_idx = -1
        
        for p in sorted_prefixes:
            idx = message_str.find(p)
            if idx == -1:
                continue
            cmd_part = message_str[idx:]
            parts = cmd_part.split()
            if parts and parts[0].lower().startswith(p.lower()):
                matched_prefix = p
                matched_idx = idx
                break
                
        if matched_prefix is not None:
            event.stop_event()
            cmd_part = message_str[matched_idx:]
            parts = cmd_part.split()
            parts[0] = parts[0][len(matched_prefix):]
            if not parts[0]:
                parts = parts[1:]
            async for res in self._handle_rogue_logic(event, parts):
                yield res
            return
            
        if rogue_mode:
            parts = message_str.split()
            if parts:
                first_word = parts[0].lower()
                is_game_cmd = False
                valid_cmds = {
                    "开启", "start", "状态", "s", "牌组", "deck", "总览", "overview", 
                    "帮助", "help", "使用", "p", "随从", "m", "选择", "c", "特殊", "sa", 
                    "结束", "e", "折叠", "f", "fold", "队列", "q", "queue", "统计", "stat", 
                    "stats", "查询", "query", "info", "i", "放弃", "abandon", "mode", "模式",
                    "职业", "class", "商店", "shop"
                }
                if first_word in valid_cmds:
                    is_game_cmd = True
                elif first_word.isdigit():
                    run = self.save_manager.load_save(user_id)
                    if run is not None:
                        is_game_cmd = True
                if is_game_cmd:
                    event.stop_event()
                    async for res in self._handle_rogue_logic(event, parts):
                        yield res

    def _execute_sub_action(self, user_id, run, parts: list[str]) -> tuple[str, bool]:
        set_user_id(user_id)
        if not parts:
            return "", False
        if parts[0].isdigit():
            parts = ["选择"] + parts
        sub = parts[0]

        if run.node_type == "battle" and run.node_data.get("pending_discard"):
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
            try:
                from .game.card_impl import ALL_CARDS
            except ImportError:
                from game.card_impl import ALL_CARDS
            card_name = ALL_CARDS[cid].name if cid in ALL_CARDS else "未知卡牌"
            run.node_data.pop("pending_discard", None)
            run.node_data.pop("pending_discard_source", None)
            agile_msg = self.engine._discard_card(run, cid)
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

        if sub in ("使用", "p"):
            if len(parts) < 2:
                return "❌ 请提供手牌序号，例如：使用 1", False
            try:
                idx = int(parts[1])
            except ValueError:
                return "❌ 序号必须是数字。", False
            target = parts[2] if len(parts) > 2 else None
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

        return f"❓ 未知操作：{parts}", False

    async def _execute_queue(self, user_id, run, queue_content: str, results: list[str]) -> bool:
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
                term = await self._execute_queue(user_id, run, sub_content, results)
                if term:
                    return True
            else:
                res, term = self._execute_sub_action(user_id, run, parts_sub)
                results.append(res)
                if term:
                    return True
        return False

    async def _handle_rogue_logic(self, event: AstrMessageEvent, parts: list[str]):
        user_id = event.get_sender_id()
        set_user_id(user_id)
        if not parts:
            run = self.save_manager.load_save(user_id)
            if run:
                yield event.plain_result(GameRenderer.render_game(run))
            else:
                stats = self.save_manager.load_stats(user_id)
                yield event.plain_result(GameRenderer.render_menu(stats))
            return
            
        if parts[0].isdigit():
            parts = ["选择"] + parts
        sub = parts[0]
        
        if sub in ("开启", "start"):
            run = self.save_manager.load_save(user_id)
            if run:
                if len(parts) > 1 and parts[1] == "确认":
                    new_run = self.engine.start_new_game(user_id)
                    yield event.plain_result("已重新开始新的一局游戏。\n" + GameRenderer.render_game(new_run))
                else:
                    yield event.plain_result("⚠️ 你当前已有一局正在进行中的游戏。若要强制重新开始并覆盖存档，请输入：\n/rogue 开启 确认（或 /rogue start 确认）")
            else:
                new_run = self.engine.start_new_game(user_id)
                yield event.plain_result(GameRenderer.render_game(new_run))
                
        elif sub in ("状态", "s"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield event.plain_result("❌ 你当前没有正在进行的游戏。输入 /rogue 开启 开始新游戏。")
            else:
                yield event.plain_result(GameRenderer.render_game(run))
                
        elif sub in ("牌组", "deck"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield event.plain_result("❌ 你当前没有正在进行的游戏。输入 /rogue 开启 开始新游戏。")
            else:
                yield event.plain_result(GameRenderer.render_deck(run))
                
        elif sub in ("总览", "overview"):
            if len(parts) > 1 and parts[1] in ("遗物", "relic", "relics"):
                yield event.plain_result(GameRenderer.render_relic_library())
            else:
                yield event.plain_result(GameRenderer.render_card_library())
            
        elif sub in ("帮助", "help"):
            yield event.plain_result(GameRenderer.render_help())
            
        elif sub in ("mode", "模式"):
            stats = self.save_manager.load_stats(user_id)
            stats.rogue_mode = not stats.rogue_mode
            self.save_manager.save_stats(user_id, stats)
            status_str = "开启" if stats.rogue_mode else "关闭"
            yield event.plain_result(f"✨ 免前缀肉鸽模式已{status_str}！此设置仅对你个人生效。")
            
        elif sub in ("使用", "p"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield event.plain_result("❌ 你当前没有正在进行的游戏。")
                return
            if len(parts) < 2:
                yield event.plain_result("❌ 请提供手牌序号，例如：/rogue 使用 1")
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
                await self._execute_queue(user_id, run, queue_str, results)
                yield event.plain_result("\n".join(results) + "\n" + GameRenderer.render_game(run))
            else:
                res, term = self._execute_sub_action(user_id, run, parts)
                if term:
                    yield event.plain_result(res)
                else:
                    yield event.plain_result(res + "\n" + GameRenderer.render_game(run))
            
        elif sub in ("随从", "m"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield event.plain_result("❌ 你当前没有正在进行的游戏。")
                return
            if len(parts) < 2:
                yield event.plain_result("❌ 请提供随从指令，例如：/rogue 随从 1 攻击 e1")
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
                await self._execute_queue(user_id, run, queue_str, results)
                yield event.plain_result("\n".join(results) + "\n" + GameRenderer.render_game(run))
            else:
                res, term = self._execute_sub_action(user_id, run, parts)
                if term:
                    yield event.plain_result(res)
                else:
                    yield event.plain_result(res + "\n" + GameRenderer.render_game(run))
                
        elif sub in ("选择", "c"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield event.plain_result("❌ 你当前没有正在进行的游戏。")
                return
            res, term = self._execute_sub_action(user_id, run, parts)
            yield event.plain_result(res + "\n" + GameRenderer.render_game(run))
 
        elif sub in ("特殊", "sa"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield event.plain_result("❌ 你当前没有正在进行的游戏。")
                return
            res, term = self._execute_sub_action(user_id, run, parts)
            yield event.plain_result(res + "\n" + GameRenderer.render_game(run))
                    
        elif sub in ("结束", "e"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield event.plain_result("❌ 你当前没有正在进行的游戏。")
                return
            res, term = self._execute_sub_action(user_id, run, parts)
            if term:
                yield event.plain_result(res)
            else:
                yield event.plain_result(res + "\n" + GameRenderer.render_game(run))
                
        elif sub in ("放弃", "abandon"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield event.plain_result("❌ 你当前没有正在进行的游戏。")
                return
            if len(parts) > 1 and parts[1] in ("确认", "confirm"):
                settle_msg = self.save_manager.settle_game_and_delete(user_id, run, is_victory=False)
                yield event.plain_result(f"已放弃当前局内游戏，当前进度已清空。\n{settle_msg}")
            else:
                yield event.plain_result("⚠️ 确认放弃当前游戏？放弃后进度将无法恢复。确认请输入：\n/rogue 放弃 确认（或 /rogue abandon confirm）")

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
                yield event.plain_result("\n".join(lines))
            elif len(parts) >= 3 and parts[1] == "购买":
                yield event.plain_result("💡 请使用商店命令前往局外商店进行商品购买：/rogue 商店")
            elif len(parts) >= 3 and parts[1] == "选择":
                subclass_name = parts[2]
                if subclass_name in ("无", "取消"):
                    stats.selected_subclass = ""
                    self.save_manager.save_stats(user_id, stats)
                    yield event.plain_result("🔮 已取消子职业选择。当前以基础法师开始游戏。")
                    return
                if subclass_name not in ("时序法师", "塑能法师"):
                    yield event.plain_result("❌ 无效的子职业。可选：时序法师、塑能法师、无。")
                    return
                unlocked = getattr(stats, "unlocked_subclasses", [])
                if subclass_name not in unlocked:
                    yield event.plain_result(f"❌ 你尚未解锁【{subclass_name}】。需要消耗 2888 GP 购买，请使用：/rogue 商店")
                    return
                stats.selected_subclass = subclass_name
                self.save_manager.save_stats(user_id, stats)
                yield event.plain_result(f"🔮 已选择子职业为【{subclass_name}】。将在新的一局游戏中生效！")
            else:
                yield event.plain_result("❌ 格式错误。请使用 /rogue 职业、/rogue 职业 选择 <子职业|无>。")

        elif sub in ("商店", "shop"):
            stats = self.save_manager.load_stats(user_id)
            if len(parts) == 1:
                yield event.plain_result(GameRenderer.render_shop(stats))
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
                    yield event.plain_result("❌ 无效的商品。可选商品序号：1、2、3。")
                    return
                    
                if subclass_name in unlocked:
                    yield event.plain_result(f"❌ 你已经解锁了【{subclass_name}】。")
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
                    yield event.plain_result(f"❌ 你的 GP 不足。购买【{subclass_name}】需要 {price} GP，你当前只有 {gp} GP。\n🔮 神秘店主说：\n  {quote}")
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
                yield event.plain_result(f"🎉 购买成功！已成功解锁【{subclass_name}】。已扣除 {price} GP。\n🔮 神秘店主说：\n  {quote}")
            else:
                yield event.plain_result("❌ 格式错误。请使用 /rogue 商店 或 /rogue 商店 购买 <商品序号/商品名称>。")

        elif sub in ("折叠", "f", "fold"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield event.plain_result("❌ 你当前没有正在进行的游戏。")
                return
            res, term = self._execute_sub_action(user_id, run, parts)
            yield event.plain_result(res + "\n" + GameRenderer.render_game(run))

        elif sub in ("队列", "q", "queue"):
            run = self.save_manager.load_save(user_id)
            if not run:
                yield event.plain_result("❌ 你当前没有正在进行的游戏。")
                return
            if len(parts) < 2:
                yield event.plain_result("❌ 请提供队列操作，例如：/rogue 队列 [使用 1, 随从 1 技能 2, 结束]")
                return
            
            full_arg = " ".join(parts[1:])
            results = []
            await self._execute_queue(user_id, run, full_arg, results)
            
            if run.player.hp <= 0:
                yield event.plain_result("\n".join(results))
            else:
                yield event.plain_result("\n".join(results) + "\n" + GameRenderer.render_game(run))

        elif sub in ("统计", "stat", "stats"):
            stats = self.save_manager.load_stats(user_id)
            yield event.plain_result(GameRenderer.render_stats(stats))

        elif sub in ("查询", "query", "info", "i"):
            run = self.save_manager.load_save(user_id)
            if len(parts) > 1:
                query_str = " ".join(parts[1:]).strip()
                yield event.plain_result(GameRenderer.render_query_info(query_str))
            else:
                if not run:
                    yield event.plain_result("❌ 你当前没有正在进行的游戏。输入 /rogue 开启 开始新游戏。")
                elif run.node_type != "battle":
                    yield event.plain_result("❌ 只有在战斗中才能查询详细战斗信息。请输入想要查询的随从、遗物、Buff名称。")
                else:
                    yield event.plain_result(GameRenderer.render_detailed_battle(run))
                
        else:
            yield event.plain_result("❓ 未知子命令。输入 /rogue 帮助 或 /rogue help 获取帮助。")
