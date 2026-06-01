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

    def _execute_sub_action(self, user_id: str, run, parts: list[str]):
        return self.cli_router._execute_sub_action(user_id, run, parts)

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
            
        for res in self.cli_router.handle_command(user_id, parts):
            yield event.plain_result(res)

    @filter.command("rogueadmin")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def rogueadmin(self, event: AstrMessageEvent):
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
                "• 立即跳到某一层：/rogueadmin jump <层数> 或 /rogueadmin jump <玩家ID> <层数>"
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
        else:
            yield event.plain_result("❌ 错误：未知管理命令，请输入 /rogueadmin 查看帮助。")

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
            res_list = list(self.cli_router.handle_command(user_id, parts))
            if res_list:
                return event.plain_result("\n".join(res_list))
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
                    "职业", "class", "商店", "shop", "教程", "tutorial"
                }
                if first_word in valid_cmds:
                    is_game_cmd = True
                elif first_word.isdigit():
                    run = self.save_manager.load_save(user_id)
                    if run is not None:
                        is_game_cmd = True

                if is_game_cmd:
                    event.stop_event()
                    res_list = list(self.cli_router.handle_command(user_id, parts))
                    if res_list:
                        return event.plain_result("\n".join(res_list))
