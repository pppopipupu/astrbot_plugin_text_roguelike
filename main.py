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

if __package__:
    from .game.core.headless_server import HeadlessGameServer
else:
    from game.core.headless_server import HeadlessGameServer

@register("astrbot_plugin_text_roguelike", "pppopipupu", "基于 DND 5.5E 背景的纯文字回合制肉鸽卡牌游戏插件，带有持久化存档等功能。", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict | None = None):
        super().__init__(context, config)
        self.config = config or {}
        try:
            from astrbot.api.star import StarTools
            data_dir = str(StarTools.get_data_dir("astrbot_plugin_text_roguelike"))
        except Exception:
            data_dir = None
        self.server = HeadlessGameServer(data_dir)
        self.save_manager = self.server.save_manager
        self.engine = self.server.engine
        self.cli_router = self.server.cli_router

    def _get_sender_name(self, event) -> str:
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
        return sender_name

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

    async def initialize(self):
        pass

    async def terminate(self):
        pass

    @filter.command("rogue")
    async def rogue(self, event: AstrMessageEvent):
        original_plain_result = event.plain_result
        def patched_plain_result(res: str, *args, **kwargs):
            return original_plain_result(self.format_res(res, event), *args, **kwargs)
        event.plain_result = patched_plain_result

        user_id = event.get_sender_id()
        sender_name = self._get_sender_name(event)
        message_str = event.message_str.strip()
        
        prefix_config = self.config.get("shortcut_prefix", ".rogue")
        r_prefixes = prefix_config if isinstance(prefix_config, list) else [prefix_config] if isinstance(prefix_config, str) else [".rogue"]
        
        res = await self.server.handle_rogue_message(
            user_id=user_id,
            sender_name=sender_name,
            message=message_str,
            shortcut_prefix=r_prefixes,
            enable_shortcut=self.config.get("enable_shortcut", True),
            force_execute=True
        )
        if res is not None:
            yield event.plain_result(res)

    @filter.command("rogueadmin")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def rogueadmin(self, event: AstrMessageEvent):
        event.stop_event()
        original_plain_result = event.plain_result
        def patched_plain_result(res: str, *args, **kwargs):
            return original_plain_result(self.format_res(res, event), *args, **kwargs)
        event.plain_result = patched_plain_result

        user_id = event.get_sender_id()
        message_str = event.message_str.strip()
        
        res = await self.server.handle_admin_message(user_id, message_str)
        yield event.plain_result(res)

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
        sender_name = self._get_sender_name(event)
        message_str = event.message_str.strip()
        
        prefix_config = self.config.get("shortcut_prefix", ".rogue")
        r_prefixes = prefix_config if isinstance(prefix_config, list) else [prefix_config] if isinstance(prefix_config, str) else [".rogue"]
        
        res = await self.server.handle_rogue_message(
            user_id=user_id,
            sender_name=sender_name,
            message=message_str,
            shortcut_prefix=r_prefixes,
            enable_shortcut=True
        )
        if res is not None:
            event.stop_event()
            return event.plain_result(res)
