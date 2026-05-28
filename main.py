from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

try:
    from .game.manager import SaveManager
    from .game.engine import GameEngine
    from .game.renderer import GameRenderer
except ImportError:
    from game.manager import SaveManager
    from game.engine import GameEngine
    from game.renderer import GameRenderer

try:
    from .game.models import current_user_id
except ImportError:
    from game.models import current_user_id

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
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

    @filter.command("rogue")
    async def rogue(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        message_str = event.message_str.strip()
        parts = message_str.split()
        if not parts:
            yield event.plain_result(GameRenderer.render_menu())
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
        
        prefix = self.config.get("shortcut_prefix", ".rogue")
        message_str = event.message_str.strip()
        idx = message_str.find(prefix)
        if idx == -1:
            return
            
        event.stop_event()
        
        cmd_part = message_str[idx:]
        parts = cmd_part.split()
        if parts and parts[0].lower().startswith(prefix.lower()):
            parts[0] = parts[0][len(prefix):]
            if not parts[0]:
                parts = parts[1:]
                
        async for res in self._handle_rogue_logic(event, parts):
            yield res

    def _execute_sub_action(self, user_id, run, parts: list[str]) -> tuple[str, bool]:
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
                    return f"{res}\n🎉 恭喜你击败了远古红龙，通关成功！", True
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
                self.save_manager.delete_save(user_id)
                return f"{res}\n💀 你被击败了！当前进度已清空。", True
            if self.engine.is_battle_won(run):
                self.engine._handle_battle_win(run)
                if run.node_type == "victory":
                    return f"{res}\n🎉 恭喜你击败了远古红龙，通关成功！", True
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
                self.save_manager.delete_save(user_id)
                return f"{res_combined}\n💀 你被击败了！当前进度已清空。", True
                
            if self.engine.is_battle_won(run):
                self.engine._handle_battle_win(run)
                if run.node_type == "victory":
                    return f"{res_combined}\n🎉 恭喜你击败了远古红龙，通关成功！", True
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
        current_user_id.set(user_id)
        if not parts:
            run = self.save_manager.load_save(user_id)
            if run:
                yield event.plain_result(GameRenderer.render_game(run))
            else:
                yield event.plain_result(GameRenderer.render_menu())
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
                
        elif sub == "牌组":
            run = self.save_manager.load_save(user_id)
            if not run:
                yield event.plain_result("❌ 你当前没有正在进行的游戏。输入 /rogue 开启 开始新游戏。")
            else:
                yield event.plain_result(GameRenderer.render_deck(run))
                
        elif sub == "总览":
            yield event.plain_result(GameRenderer.render_card_library())
            
        elif sub in ("帮助", "help"):
            yield event.plain_result(GameRenderer.render_help())
            
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
                
        elif sub == "放弃":
            run = self.save_manager.load_save(user_id)
            if not run:
                yield event.plain_result("❌ 你当前没有正在进行的游戏。")
                return
            if len(parts) > 1 and parts[1] == "确认":
                self.save_manager.delete_save(user_id)
                yield event.plain_result("已放弃当前局内游戏，当前进度已清空。")
            else:
                yield event.plain_result("⚠️ 确认放弃当前游戏？放弃后进度将无法恢复。确认请输入：\n/rogue 放弃 确认")

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
