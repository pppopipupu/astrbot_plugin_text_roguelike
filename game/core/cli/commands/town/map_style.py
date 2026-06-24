from typing import Generator
from ...base import CommandHandler

class MapStyleCommand(CommandHandler, names=["地图", "map"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        stats = router.save_manager.load_stats(user_id)
        if not stats.in_town:
            yield "❌ 地图样式切换指令仅在主城模式下有效。"
            return
        current_style = stats.town_flags.get("map_style", "classic")
        target_style = None
        if len(parts) > 1:
            arg = parts[1].lower()
            if arg in ("经典", "classic", "c"):
                target_style = "classic"
            elif arg in ("雷达", "radar", "r"):
                target_style = "radar"
            else:
                yield "❌ 无效的地图样式。可选：经典/classic 或 雷达/radar"
                return
        else:
            target_style = "radar" if current_style == "classic" else "classic"
        stats.town_flags["map_style"] = target_style
        router.save_manager.save_stats(user_id, stats)
        style_desc = "经典全局大地图" if target_style == "classic" else "局部雷达十字小地图"
        yield f"✨ 已成功将主城小地图样式切换为：【{style_desc}】！\n\n" + router.town_engine.render_current_room(user_id, stats)
