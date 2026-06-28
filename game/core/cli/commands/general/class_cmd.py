from typing import Generator
from ...base import CommandHandler

class ClassCommand(CommandHandler, names=["职业", "class"], allowed_states=["menu", "town"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        stats = router.save_manager.load_stats(user_id)
        selected_class = getattr(stats, "selected_class", "法师")
        selected_subclass = getattr(stats, "selected_subclass", "") or "无"
        if len(parts) == 1:
            from .....data.shop_data import SHOP_ITEMS
            gp = getattr(stats, "gp", 0)
            unlocked = getattr(stats, "unlocked_subclasses", [])
            status_time = f"已解锁" if "时序法师" in unlocked else f"未解锁（{SHOP_ITEMS['时序法师']['price']} GP）"
            status_element = f"已解锁" if "塑能法师" in unlocked else f"未解锁（{SHOP_ITEMS['塑能法师']['price']} GP）"
            status_key = f"已解锁" if "秘钥学者" in unlocked else f"未解锁（{SHOP_ITEMS['秘钥学者']['price']} GP）"
            lines = [
                "━━━━━━━━━━━━━━━━━━━━",
                "🧙 魔法肉鸽卡牌职业系统",
                "",
                f"💰 我的 GP：{gp}",
                f"🧙 当前主职业：{selected_class}  🔮 当前子职业：{selected_subclass}",
                "",
                "【可用的主职业】",
                "1. 法师 (wizard)",
                "   └─ 使用蓝色法术牌和护符。可以使用子职业。初始生命 45。",
                "2. 战士 (warrior)",
                "   └─ 使用红色物理牌。无子职业。拥有被动“动作如潮”（/rogue sk 获得 2A，或者 /rogue k 直接触发，一场战斗限两次，初始生命 80）。",
                "",
                "【可用的子职业（仅法师可用）】",
                f"1. 时序法师 - 状态：[{status_time}]",
                "   └─ 操控时间。开局获得专属传奇卡牌“时间停止”（追加 3 个额外回合）。",
                f"2. 塑能法师 - 状态：[{status_element}]",
                "   └─ 元素爆发。所有法术伤害提升 15%，且抓取火球术时 40% 几率将火球术替换为流星爆。",
                f"3. 秘钥学者 - 状态：[{status_key}]",
                "   └─ 门扉共鸣。打出护符时回复 3 生命且获得 4 护盾。抓取卡牌时 35% 几率将普通法术替换为“秘钥共鸣”。",
                "",
                "【职业选择命令】",
                "👉 /rogue class wizard -- 切换到法师职业",
                "👉 /rogue class warrior -- 切换到战士职业",
                "👉 /rogue class 1 -- 装备时序法师子职业",
                "👉 /rogue class 2 -- 装备塑能法师子职业",
                "👉 /rogue class 3 -- 装备秘钥学者子职业",
                "👉 /rogue class 0 -- 取消装备子职业",
                "💡 如需购买子职业，请前往主城商店与神秘店主对话。",
                "━━━━━━━━━━━━━━━━━━━━"
            ]
            yield "\n".join(lines)
        else:
            action = None
            subclass_arg = None
            if len(parts) == 2:
                action = "选择"
                subclass_arg = parts[1]
            elif len(parts) >= 3:
                action = parts[1]
                subclass_arg = parts[2]
            if action in ("购买", "buy"):
                yield "💡 请前往主城商店与神秘店主对话以进行商品购买。"
            elif action in ("选择", "c", "choose", "select"):
                if subclass_arg in ("战士", "warrior", "war"):
                    stats.selected_class = "战士"
                    stats.selected_subclass = ""
                    router.save_manager.save_stats(user_id, stats)
                    yield "🔴 主职业已切换为【战士】。将在新的一局游戏中生效！"
                    return
                elif subclass_arg in ("法师", "wizard", "wiz"):
                    stats.selected_class = "法师"
                    router.save_manager.save_stats(user_id, stats)
                    yield "🧙 主职业已切换为【法师】。将在新的一局游戏中生效！"
                    return
                if selected_class == "战士":
                    yield "❌ 战士职业没有子职业，无法装备子职业。如需装备子职业，请先切换到法师职业。"
                    return
                if subclass_arg in ("1", "时序法师", "chronomancer", "time"):
                    subclass_name = "时序法师"
                elif subclass_arg in ("2", "塑能法师", "evoker", "elemental"):
                    subclass_name = "塑能法师"
                elif subclass_arg in ("3", "秘钥学者", "arcanist", "key"):
                    subclass_name = "秘钥学者"
                elif subclass_arg in ("0", "无", "取消", "none"):
                    subclass_name = ""
                else:
                    yield "❌ 无效的子职业。可选：1 (时序法师)、2 (塑能法师)、3 (秘钥学者)、0 (无)，或输入 法师/战士 切换主职业。"
                    return
                if subclass_name == "":
                    stats.selected_subclass = ""
                    router.save_manager.save_stats(user_id, stats)
                    yield "🔮 已取消子职业选择。当前以基础法师开始游戏。"
                    return
                unlocked = getattr(stats, "unlocked_subclasses", [])
                if subclass_name not in unlocked:
                    from .....data.shop_data import SHOP_ITEMS
                    price = SHOP_ITEMS.get(subclass_name, {}).get("price", 2888)
                    yield f"❌ 你尚未解锁【{subclass_name}】。需要消耗 {price} GP，请前往主城商店与神秘店主对话购买。"
                    return
                stats.selected_subclass = subclass_name
                router.save_manager.save_stats(user_id, stats)
                yield f"🔮 已选择子职业为【{subclass_name}】。将在新的一局游戏中生效！"
            else:
                yield "❌ 格式错误。请使用 /rogue 职业 (/rogue class) 或 /rogue 职业 选择/c (/rogue class select) <职业名|子职业序号>。"
