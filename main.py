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
            for res in self.cli_router.handle_command(user_id, parts):
                event.plain_result(res)
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
                    for res in self.cli_router.handle_command(user_id, parts):
                        event.plain_result(res)
