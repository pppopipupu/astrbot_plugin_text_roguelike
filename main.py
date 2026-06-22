import os
import sys

_curr_dir = os.path.dirname(os.path.abspath(__file__))
if _curr_dir not in sys.path:
    sys.path.insert(0, _curr_dir)

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
        def permission_type(*args, **kwargs):
            return lambda func: func
        class PermissionType:
            ADMIN = 1
    filter = FilterDummy()
    class DummyLogger:
        def info(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def debug(self, *args, **kwargs): pass
    logger = DummyLogger()

try:
    from .game.models.manager import SaveManager
    from .game.engine import GameEngine
    from .game.renderer import GameRenderer
    from .game.core.cli_router import CLIRouter
except ImportError:
    from game.models.manager import SaveManager
    from game.engine import GameEngine
    from game.renderer import GameRenderer
    from game.core.cli_router import CLIRouter

try:
    from .game.models.state import set_user_id
except ImportError:
    from game.models.state import set_user_id

try:
    from .game.core.duel_router import DuelRouter
except ImportError:
    from game.core.duel_router import DuelRouter

def resolve_card_id(card_input: str) -> str | None:
    card_input = card_input.strip()
    if not card_input:
        return None
    try:
        from .game.cards import ALL_CARDS
    except ImportError:
        from game.cards import ALL_CARDS
    if card_input in ALL_CARDS:
        return card_input
    card_input_lower = card_input.lower()
    for cid in list(ALL_CARDS.keys()):
        if cid.lower() == card_input_lower:
            return cid
    try:
        from .game.data.card_data import CARD_CONFIG
    except ImportError:
        from game.data.card_data import CARD_CONFIG
    for cid, cfg in CARD_CONFIG.items():
        name = cfg.get("name", "")
        if card_input == name or card_input_lower == name.lower():
            return cid
        if card_input == name + "+" or card_input_lower == (name + "+").lower():
            return cid + "+"
    if card_input.endswith("+"):
        base_input = card_input[:-1]
        base_id = resolve_card_id(base_input)
        if base_id:
            return base_id + "+"
    return None

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
        self.cli_router = CLIRouter(self.save_manager, self.engine)
        self.duel_router = DuelRouter(self.save_manager)

    def format_res(self, res: str, event: AstrMessageEvent) -> str:
        if not res:
            return res
        is_matrix = False
        try:
            platform_id = str(event.get_platform_id()).lower()
            if "matrix" in platform_id:
                is_matrix = True
        except Exception:
            pass
        try:
            if not is_matrix and hasattr(event, "message_obj") and event.message_obj:
                client_type = str(getattr(event.message_obj, "client_type", "")).lower()
                if "matrix" in client_type:
                    is_matrix = True
        except Exception:
            pass
            
        if is_matrix:
            if "\n" in res:
                if "━━━━━━━━━━━━━━━━━━━━" in res:
                    return f"```\n{res}\n```"
                elif res.count("\n") > 4:
                    lines = res.split("\n")
                    formatted_lines = []
                    for line in lines:
                        clean_line = line.replace("`", "")
                        if clean_line:
                            formatted_lines.append(f"`{clean_line}`  ")
                        else:
                            formatted_lines.append("  ")
                    return "\n".join(formatted_lines)
                else:
                    return res.replace("\n", "  \n")
        return res

    def _execute_sub_action(self, user_id: str, run, parts: list[str]):
        return self.cli_router._execute_sub_action(user_id, run, parts)

    async def send_dm(self, event, target_id: str, text: str):
        if not target_id or not text:
            return
        text = self.format_res(text, event)
        try:
            platform_id = event.unified_msg_origin.split(":")[0]
            if platform_id == "matrix" and not target_id.startswith("@") and not target_id.startswith("!"):
                target_id = "@" + target_id
            target_umo = f"{platform_id}:FriendMessage:{target_id}"
            try:
                from astrbot.api.event import MessageChain
            except ImportError:
                class MessageChain:
                    def __init__(self):
                        self.chain = []
                    def message(self, t):
                        self.chain.append(t)
                        return self
            chain = MessageChain().message(text)
            sent = await self.context.send_message(target_umo, chain)
            if sent:
                return
        except Exception:
            pass
        try:
            bot = getattr(event, "bot", None)
            if bot:
                if hasattr(bot, "call_api"):
                    try:
                        await bot.call_api("send_private_msg", user_id=int(target_id), message=text)
                    except:
                        try:
                            await bot.send_private_msg(user_id=int(target_id), message=text)
                        except:
                            pass
        except:
            pass

    async def process_duel_cmd(self, event, user_id: str, parts: list[str], message_str: str, force_duel: bool = False):
        if not parts:
            return False, None, None, None, None, None
        parts_lower = [p.lower() for p in parts]
        if parts_lower and parts_lower[0] in ("帮助", "help", "hp") and not force_duel:
            return False, None, None, None, None, None
        game_id = self.save_manager.get_duel_game_id(user_id)
        is_duel_related = False
        if force_duel or game_id:
            is_duel_related = True
        elif parts_lower and parts_lower[0] in ("对决", "duel"):
            is_duel_related = True
        if not is_duel_related:
            return False, None, None, None, None, None
        event.stop_event()
        sender_name = "玩家"
        try:
            if event:
                sender_name = event.get_sender_name()
                if not sender_name and hasattr(event, "message_obj") and event.message_obj:
                    sender_name = getattr(event.message_obj, "sender", {}).get("nickname", "玩家")
                if not sender_name:
                    sender_name = "玩家"
        except:
            pass
        opp_qq = None
        import re
        m = re.search(r"qq=([^\s\]]+)", message_str)
        if m:
            opp_qq = m.group(1)
        else:
            m = re.search(r"@([^\s]+)", message_str)
            if m:
                opp_qq = m.group(1)
            else:
                try:
                    if event and hasattr(event, "message_obj") and event.message_obj:
                        for seg in getattr(event.message_obj, "message", []):
                            if seg.get("type") == "at":
                                data = seg.get("data", {})
                                opp_qq = str(data.get("qq") or data.get("user_id") or data.get("id") or data.get("mxid") or data.get("target") or "")
                                if opp_qq:
                                    break
                except:
                    pass
        if opp_qq:
            for idx in range(len(parts)):
                if parts[idx].startswith("@") or parts[idx].startswith("[At:"):
                    parts[idx] = f"[At:qq={opp_qq}]"
                    break
        if game_id:
            run = self.save_manager.load_duel_save(user_id)
            if not run:
                return True, "❌ 未找到你的活跃对局存档。", None, None, None, None
            res_pub, _, p1, dm1, p2, dm2 = self.duel_router.route_in_game_action(run, user_id, sender_name, parts)
        else:
            res_pub, _, p1, dm1, p2, dm2 = self.duel_router.handle_duel_cmd(user_id, sender_name, parts)
        if p1 and dm1:
            await self.send_dm(event, p1, dm1)
        if p2 and dm2:
            await self.send_dm(event, p2, dm2)
        return True, res_pub, p1, dm1, p2, dm2

    async def initialize(self):
        pass

    async def terminate(self):
        pass

    @filter.command("duel")
    async def duel_cmd(self, event: AstrMessageEvent):
        original_plain_result = event.plain_result
        def patched_plain_result(res: str, *args, **kwargs):
            return original_plain_result(self.format_res(res, event), *args, **kwargs)
        event.plain_result = patched_plain_result

        user_id = event.get_sender_id()
        message_str = event.message_str.strip()
        parts = message_str.split()
        if not parts:
            help_text, _, _, _, _, _ = self.duel_router.handle_duel_cmd(user_id, "玩家", ["帮助"])
            yield event.plain_result(help_text)
            return
            
        first = parts[0].lower()
        if "duel" in first or "对决" in first:
            parts = parts[1:]

        is_duel, res_pub, p1, dm1, p2, dm2 = await self.process_duel_cmd(event, user_id, parts, message_str, force_duel=True)
        if is_duel:
            if res_pub:
                yield event.plain_result(res_pub)
            return

    @filter.command("rogue")
    async def rogue(self, event: AstrMessageEvent):
        original_plain_result = event.plain_result
        def patched_plain_result(res: str, *args, **kwargs):
            return original_plain_result(self.format_res(res, event), *args, **kwargs)
        event.plain_result = patched_plain_result

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

        for res in self.cli_router.handle_command(user_id, parts):
            yield event.plain_result(res)

    @filter.command("rogueadmin")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def rogueadmin(self, event: AstrMessageEvent):
        original_plain_result = event.plain_result
        def patched_plain_result(res: str, *args, **kwargs):
            return original_plain_result(self.format_res(res, event), *args, **kwargs)
        event.plain_result = patched_plain_result

        message_str = event.message_str.strip()
        parts = message_str.split()
        if len(parts) > 0 and parts[0].lower() in ("rogueadmin", "/rogueadmin"):
            parts = parts[1:]
            
        if not parts:
            yield event.plain_result(
                "💬 /rogueadmin 管理指令帮助：\n"
                "• 查看当前最终BOSS：/rogueadmin boss\n"
                "• 设置随机轮换：/rogueadmin boss set random\n"
                "• 固定最终BOSS：/rogueadmin boss set 腐化之心 或 Icerainboww\n"
                "• 开启/关闭 Icerainboww：/rogueadmin icerainboww <on/off>\n"
                "• 立即跳到某一层：/rogueadmin jump <层数> 或 /rogueadmin jump <玩家ID> <层数>\n"
                "• 向玩家牌组添加卡牌：/rogueadmin add_card <卡牌名称/ID> [玩家ID]"
            )
            return

        cmd = parts[0].lower()
        if cmd == "boss":
            if len(parts) == 1:
                cfg = self.save_manager.load_admin_config()
                boss = cfg.get("final_boss", "random")
                boss_zh = "随机轮换" if boss == "random" else boss
                yield event.plain_result(f"⚙️ 当前最终BOSS配置为：【{boss_zh}】")
                return
            elif len(parts) >= 3 and parts[1].lower() == "set":
                target_boss = parts[2]
                if target_boss.lower() in ("random", "随机", "轮换"):
                    self.save_manager.save_admin_config({"final_boss": "random"})
                    yield event.plain_result("⚙️ 最终BOSS已成功设置为：【随机轮换】")
                elif target_boss in ("腐化之心", "Icerainboww"):
                    self.save_manager.save_admin_config({"final_boss": target_boss})
                    yield event.plain_result(f"⚙️ 最终BOSS已成功固定为：【{target_boss}】")
                else:
                    yield event.plain_result("❌ 错误：无效的BOSS名称。可选值：random, 腐化之心, Icerainboww")
            else:
                yield event.plain_result("❌ 错误：无效指令。请使用 /rogueadmin boss set <random/腐化之心/Icerainboww>")
        elif cmd == "icerainboww":
            if len(parts) == 1:
                cfg = self.save_manager.load_admin_config()
                status = cfg.get("icerainboww_enabled", True)
                status_zh = "开启" if status else "关闭"
                yield event.plain_result(f"⚙️ 当前 icerainboww 相关内容配置状态为：【{status_zh}】")
                return
            elif len(parts) >= 2:
                target_status = parts[1].lower()
                cfg = self.save_manager.load_admin_config()
                if target_status in ("on", "开启", "enable", "true"):
                    cfg["icerainboww_enabled"] = True
                    self.save_manager.save_admin_config(cfg)
                    yield event.plain_result("⚙️ icerainboww 相关内容已成功【开启】！")
                elif target_status in ("off", "关闭", "disable", "false"):
                    cfg["icerainboww_enabled"] = False
                    self.save_manager.save_admin_config(cfg)
                    yield event.plain_result("⚙️ icerainboww 相关内容已成功【关闭】！所有 icerainboww 卡牌与 BOSS 已被禁用。")
                else:
                    yield event.plain_result("❌ 错误：无效的参数。可选值：on, off, 开启, 关闭")
            else:
                yield event.plain_result("❌ 错误：无效指令。请使用 /rogueadmin icerainboww <on/off>")
        elif cmd == "jump":
            if len(parts) == 2:
                target_user_id = event.get_sender_id()
                stage_str = parts[1]
            elif len(parts) >= 3:
                target_user_id = parts[1]
                stage_str = parts[2]
            else:
                yield event.plain_result("❌ 错误：无效指令。请使用 /rogueadmin jump <层数> 或 /rogueadmin jump <玩家ID> <层数>")
                return
            try:
                target_stage = int(stage_str)
            except ValueError:
                yield event.plain_result("❌ 错误：层数必须是整数")
                return
            if not (1 <= target_stage <= 25):
                yield event.plain_result("❌ 错误：层数范围必须在 1 到 25 之间")
                return
            run = self.save_manager.load_save(target_user_id)
            if not run:
                yield event.plain_result("❌ 错误：未找到该玩家的活跃游戏存档。")
                return
            msg = self.engine.jump_to_stage(run, target_stage)
            yield event.plain_result(f"⚙️ {msg}\n\n{GameRenderer.render_game(run)}")
        elif cmd == "add_card":
            if len(parts) == 2:
                card_input = parts[1]
                target_user_id = event.get_sender_id()
            elif len(parts) >= 3:
                card_input = parts[1]
                target_user_id = parts[2]
                resolved = resolve_card_id(card_input)
                if not resolved:
                    resolved_alt = resolve_card_id(parts[2])
                    if resolved_alt:
                        card_input = parts[2]
                        target_user_id = parts[1]
            else:
                yield event.plain_result("❌ 错误：无效指令。请使用 /rogueadmin add_card <卡牌名称/ID> [玩家ID]")
                return
            
            card_id = resolve_card_id(card_input)
            if not card_id:
                yield event.plain_result(f"❌ 错误：未找到卡牌【{card_input}】")
                return
            
            run = self.save_manager.load_save(target_user_id)
            if not run:
                yield event.plain_result("❌ 错误：未找到该玩家的活跃游戏存档。")
                return
            
            try:
                from .game.cards import ALL_CARDS
            except ImportError:
                from game.cards import ALL_CARDS
            
            card_obj = ALL_CARDS.get(card_id)
            card_name = card_obj.name if card_obj else card_id
            
            run.player.deck.append(card_id)
            in_battle = (run.node_type == "battle")
            if in_battle:
                run.player.hand.append(card_id)
                
            self.save_manager.save_save(target_user_id, run)
            
            if in_battle:
                msg = f"已成功将卡牌【{card_name}】添加到玩家【{target_user_id}】的牌组，且由于处于战斗中，该牌已直接加入手牌！"
            else:
                msg = f"已成功将卡牌【{card_name}】添加到玩家【{target_user_id}】的牌组！"
                
            yield event.plain_result(f"⚙️ {msg}\n\n{GameRenderer.render_game(run)}")
        else:
            yield event.plain_result("❌ 错误：未知管理命令，请输入 /rogueadmin 查看帮助。")

    @filter.regex(r".*")
    async def shortcut_rogue(self, event: AstrMessageEvent):
        enable = self.config.get("enable_shortcut", True)
        if not enable:
            return
            
        original_plain_result = event.plain_result
        def patched_plain_result(res: str, *args, **kwargs):
            return original_plain_result(self.format_res(res, event), *args, **kwargs)
        event.plain_result = patched_plain_result
        
        user_id = event.get_sender_id()
        stats = self.save_manager.load_stats(user_id)
        if stats and stats.reader_active:
            message_str = event.message_str.strip()
            clean_str = message_str
            prefix_config = self.config.get("shortcut_prefix", ".rogue")
            r_prefixes = prefix_config if isinstance(prefix_config, list) else [prefix_config] if isinstance(prefix_config, str) else [".rogue"]
            d_prefixes = [".duel", ".对决"]
            for p in sorted(r_prefixes + d_prefixes, key=len, reverse=True):
                if clean_str.lower().startswith(p.lower()):
                    clean_str = clean_str[len(p):].strip()
                    break
            parts = clean_str.split()
            if parts:
                cmd = parts[0].lower()
                if cmd in ("下一页", "n", "next", "上一页", "b", "back", "prev", "退出", "q", "quit", "exit"):
                    event.stop_event()
                    if cmd in ("退出", "q", "quit", "exit"):
                        stats.reader_active = False
                        self.save_manager.save_stats(user_id, stats)
                        return event.plain_result("🚪 已退出阅读器。")
                    elif cmd in ("下一页", "n", "next"):
                        total_items = len(stats.reader_items)
                        total_pages = (total_items + 9) // 10
                        if stats.reader_page >= total_pages:
                            return event.plain_result("⚠️ 已经是最后一页了。")
                        stats.reader_page += 1
                        self.save_manager.save_stats(user_id, stats)
                        from game.renderer.menu import render_reader_page
                        return event.plain_result(render_reader_page(stats))
                    elif cmd in ("上一页", "b", "back", "prev"):
                        if stats.reader_page <= 1:
                            return event.plain_result("⚠️ 已经是第一页了。")
                        stats.reader_page -= 1
                        self.save_manager.save_stats(user_id, stats)
                        from game.renderer.menu import render_reader_page
                        return event.plain_result(render_reader_page(stats))
                else:
                    stats.reader_active = False
                    self.save_manager.save_stats(user_id, stats)
        rogue_mode = stats.rogue_mode if stats else False
        duel_mode = stats.duel_mode if stats else False
        
        prefix_config = self.config.get("shortcut_prefix", ".rogue")
        if isinstance(prefix_config, list):
            r_prefixes = prefix_config
        elif isinstance(prefix_config, str):
            r_prefixes = [prefix_config]
        else:
            r_prefixes = [".rogue"]
            
        d_prefixes = [".duel", ".对决"]
        
        message_str = event.message_str.strip()
        
        all_prefixes = []
        for p in r_prefixes:
            all_prefixes.append((p, "rogue"))
        for p in d_prefixes:
            all_prefixes.append((p, "duel"))
            
        all_prefixes_sorted = sorted(all_prefixes, key=lambda x: len(x[0]), reverse=True)
        matched_p = None
        matched_type = None
        matched_idx = -1
        
        for p, ptype in all_prefixes_sorted:
            idx = message_str.find(p)
            if idx == -1:
                continue
            cmd_part = message_str[idx:]
            parts = cmd_part.split()
            if parts and parts[0].lower().startswith(p.lower()):
                matched_p = p
                matched_type = ptype
                matched_idx = idx
                break
                
        if matched_p is not None:
            event.stop_event()
            cmd_part = message_str[matched_idx:]
            parts = cmd_part.split()
            parts[0] = parts[0][len(matched_p):]
            if not parts[0]:
                parts = parts[1:]
                
            if matched_type == "duel":
                if not parts:
                    parts = ["帮助"]
                is_duel, res_pub, p1, dm1, p2, dm2 = await self.process_duel_cmd(event, user_id, parts, message_str, force_duel=True)
                if is_duel:
                    if res_pub:
                        return event.plain_result(res_pub)
                    return
                return event.plain_result("❌ 未知对决指令，请输入 .duel 帮助 获取指南。")
            else:
                res_list = list(self.cli_router.handle_command(user_id, parts))
                if res_list:
                    return event.plain_result("\n".join(res_list))
                return
                
        if duel_mode:
            parts = message_str.split()
            if parts:
                first_word = parts[0].lower()
                is_duel_cmd = False
                valid_duel_cmds = {
                    "帮助", "help", "hp", "牌组", "deck", "dk", "接受", "accept",
                    "放弃", "abandon", "confirm", "邀请", "invite", "iv", "模式", "mode",
                    "使用", "use", "u", "play", "p", "随从", "minion", "atk", "m", "结束", "end",
                    "进化", "evolve", "ev", "幸运币", "coin", "cn", "状态", "status", "s", "e", "查看", "overview", "总览"
                }
                if first_word in valid_duel_cmds:
                    is_duel_cmd = True
                elif first_word.isdigit():
                    game_id = self.save_manager.get_duel_game_id(user_id)
                    if game_id is not None:
                        is_duel_cmd = True
                
                if is_duel_cmd:
                    event.stop_event()
                    is_duel, res_pub, p1, dm1, p2, dm2 = await self.process_duel_cmd(event, user_id, parts, message_str, force_duel=True)
                    if is_duel:
                        if res_pub:
                            return event.plain_result(res_pub)
                        return
                    return
        elif rogue_mode:
            parts = message_str.split()
            if parts:
                first_word = parts[0].lower()
                is_game_cmd = False
                valid_cmds = {
                    "开启", "start", "状态", "s", "牌组", "deck", "总览", "overview", 
                    "帮助", "help", "使用", "p", "随从", "m", "选择", "c", "特殊", "sa", 
                    "结束", "e", "折叠", "f", "fold", "队列", "q", "queue", "统计", "stat", 
                    "stats", "查询", "query", "info", "i", "放弃", "abandon", "mode", "模式",
                    "职业", "class", "商店", "shop", "教程", "tutorial",
                    "技能", "skill", "sk", "k"
                }
                if first_word in valid_cmds:
                    is_game_cmd = True
                elif first_word.isdigit():
                    run = self.save_manager.load_save(user_id)
                    if run is not None and getattr(run, "node_type", "") != "duel":
                        is_game_cmd = True

                if is_game_cmd:
                    event.stop_event()
                    res_list = list(self.cli_router.handle_command(user_id, parts))
                    if res_list:
                        return event.plain_result("\n".join(res_list))
