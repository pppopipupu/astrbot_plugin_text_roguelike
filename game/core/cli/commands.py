from typing import Generator
from .base import CommandHandler, split_by_comma_with_brackets
from ...renderer import GameRenderer
from ...entities import ALL_CARDS

class StartCommand(CommandHandler, names=["开启", "start"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if run:
            if len(parts) > 1 and parts[1] in ("确认", "confirm"):
                new_run = router.engine.start_new_game(user_id)
                yield "已重新开始新的一局游戏。\n" + GameRenderer.render_game(new_run)
            else:
                yield "⚠️ 你当前已有一局正在进行中的游戏。若要强制重新开始并覆盖存档，请输入：\n/rogue start confirm"
        else:
            new_run = router.engine.start_new_game(user_id)
            yield GameRenderer.render_game(new_run)

class StatusCommand(CommandHandler, names=["状态", "s"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            stats = router.save_manager.load_stats(user_id)
            yield GameRenderer.render_menu(stats)
        else:
            yield GameRenderer.render_game(run)

class DeckCommand(CommandHandler, names=["牌组", "deck"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            yield "❌ 你当前没有正在进行的游戏。输入 /rogue start 开始新游戏。"
        else:
            yield GameRenderer.render_deck(run)

class OverviewCommand(CommandHandler, names=["总览", "overview"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        stats = router.save_manager.load_stats(user_id)
        if len(parts) > 1 and parts[1] in ("遗物", "relic", "relics"):
            from game.renderer.menu import get_rogue_relic_library_items
            items = get_rogue_relic_library_items()
            stats.reader_title = "🎒 魔法肉鸽遗物总览"
        else:
            from game.renderer.menu import get_rogue_card_library_items
            items = get_rogue_card_library_items()
            stats.reader_title = "📜 魔法肉鸽卡牌总览"
        stats.reader_items = items
        stats.reader_page = 1
        stats.reader_active = True
        stats.reader_mode = "rogue"
        router.save_manager.save_stats(user_id, stats)
        from game.renderer.menu import render_reader_page
        yield render_reader_page(stats)

class HelpCommand(CommandHandler, names=["帮助", "help"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        yield GameRenderer.render_help()

class TutorialCommand(CommandHandler, names=["教程", "tutorial"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        yield GameRenderer.render_tutorial()


class ModeCommand(CommandHandler, names=["mode", "模式"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        stats = router.save_manager.load_stats(user_id)
        stats.rogue_mode = not stats.rogue_mode
        if stats.rogue_mode:
            stats.duel_mode = False
        router.save_manager.save_stats(user_id, stats)
        status_str = "开启" if stats.rogue_mode else "关闭"
        yield f"✨ 免前缀肉鸽模式已{status_str}！此设置仅对你个人生效。"

class UseCommand(CommandHandler, names=["使用", "p"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
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
            router._execute_queue(user_id, run, queue_str, results)
            yield "\n".join(results) + "\n" + GameRenderer.render_game(run)
        else:
            res, term = router._execute_sub_action(user_id, run, parts)
            if term:
                yield res
            else:
                yield res + "\n" + GameRenderer.render_game(run)

class MinionCommand(CommandHandler, names=["随从", "m"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
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
            router._execute_queue(user_id, run, queue_str, results)
            yield "\n".join(results) + "\n" + GameRenderer.render_game(run)
        else:
            res, term = router._execute_sub_action(user_id, run, parts)
            if term:
                yield res
            else:
                yield res + "\n" + GameRenderer.render_game(run)

class ChooseCommand(CommandHandler, names=["选择", "c"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            if len(parts) > 1:
                arg = parts[1].lower()
                if arg in ("wizard", "warrior", "wiz", "war", "法师", "战士", "1", "2", "3", "0", "选择", "时序法师", "塑能法师", "秘钥学者"):
                    yield "❌ 你当前没有正在进行的游戏。如需切换职业，请使用 /rogue class 命令。\n💡 选择命令 c 仅用于局内选项选择，无法用于选择职业。"
                    return
            yield "❌ 你当前没有正在进行的游戏。"
            return
        res, term = router._execute_sub_action(user_id, run, parts)
        yield res + "\n" + GameRenderer.render_game(run)

class SpecialCommand(CommandHandler, names=["特殊", "sa"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            yield "❌ 你当前没有正在进行的游戏。"
            return
        res, term = router._execute_sub_action(user_id, run, parts)
        yield res + "\n" + GameRenderer.render_game(run)

class EndTurnCommand(CommandHandler, names=["结束", "e"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            yield "❌ 你当前没有正在进行的游戏。"
            return
        res, term = router._execute_sub_action(user_id, run, parts)
        if term:
            yield res
        else:
            yield res + "\n" + GameRenderer.render_game(run)

class AbandonCommand(CommandHandler, names=["放弃", "abandon"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            yield "❌ 你当前没有正在进行的游戏。"
            return
        if len(parts) > 1 and parts[1] in ("确认", "confirm"):
            settle_msg = router.save_manager.settle_game_and_delete(user_id, run, is_victory=False)
            yield f"已放弃当前局内游戏，当前进度已清空。\n{settle_msg}"
        else:
            yield "⚠️ 确认放弃当前游戏？放弃后进度将无法恢复。确认请输入：\n/rogue abandon confirm"

class ClassCommand(CommandHandler, names=["职业", "class"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        stats = router.save_manager.load_stats(user_id)
        selected_class = getattr(stats, "selected_class", "法师")
        selected_subclass = getattr(stats, "selected_subclass", "") or "无"
        if len(parts) == 1:
            gp = getattr(stats, "gp", 0)
            unlocked = getattr(stats, "unlocked_subclasses", [])
            status_time = "已解锁" if "时序法师" in unlocked else "未解锁（2888 GP）"
            status_element = "已解锁" if "塑能法师" in unlocked else "未解锁（2888 GP）"
            status_key = "已解锁" if "秘钥学者" in unlocked else "未解锁（2888 GP）"
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
                "💡 如需购买子职业，请使用局外商店：/rogue shop",
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
                yield "💡 请使用商店命令前往局外商店进行商品购买：/rogue shop"
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
                    yield f"❌ 你尚未解锁【{subclass_name}】。需要消耗 2888 GP 购买，请使用：/rogue 商店 或 /rogue shop"
                    return
                stats.selected_subclass = subclass_name
                router.save_manager.save_stats(user_id, stats)
                yield f"🔮 已选择子职业为【{subclass_name}】。将在新的一局游戏中生效！"
            else:
                yield "❌ 格式错误。请使用 /rogue 职业 (/rogue class) 或 /rogue 职业 选择/c (/rogue class select) <职业名|子职业序号>。"

class SkillCommand(CommandHandler, names=["技能", "skill", "sk", "k"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run or run.node_type != "battle":
            yield "❌ 只有在战斗中才能使用职业技能。"
            return
        stats = router.save_manager.load_stats(user_id)
        p_class = getattr(stats, "selected_class", "法师")
        if p_class != "战士":
            yield "❌ 当前职业不是战士，无法使用【动作如潮】技能。"
            return
        skill_arg = parts[1].lower() if len(parts) >= 2 else "as"
        if skill_arg not in ("as", "action_surge", "动作如潮"):
            yield "💡 战士职业技能使用命令：/rogue 技能 as （或 /rogue sk as）"
            return
        uses = run.node_data.get("action_surge_uses", 0)
        if uses <= 0:
            yield "❌ 动作如潮在一场战斗中只能使用两次，本场战斗的使用次数已用尽！"
            return
        if run.node_data.get("action_surge_turn_used", False):
            yield "❌ 动作如潮每回合只能使用一次！"
            return
        run.node_data["action_surge_uses"] = uses - 1
        run.node_data["action_surge_turn_used"] = True
        p = run.player
        p.actions += 2
        p.bonus_actions += 1
        router.save_manager.save_save(user_id, run)
        yield f"🔥 战士发动了【动作如潮】！获得了额外的 2A 1BA 动作点！(本场战斗还可使用 {uses - 1} 次)\n当前行动点: {p.actions}A, {p.bonus_actions}BA"

class ShopCommand(CommandHandler, names=["商店", "shop"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        stats = router.save_manager.load_stats(user_id)
        if len(parts) == 1:
            yield GameRenderer.render_shop(stats)
        elif len(parts) >= 3 and parts[1] in ("购买", "buy"):
            target = parts[2]
            unlocked = getattr(stats, "unlocked_subclasses", [])
            gp = getattr(stats, "gp", 0)
            killed_icerainboww = getattr(stats, "killed_icerainboww", False)
            if hasattr(router.save_manager, "load_admin_config"):
                boss_cfg = router.save_manager.load_admin_config()
            else:
                boss_cfg = {}
            icerainboww_enabled = boss_cfg.get("icerainboww_enabled", True)
            is_gatekey = False
            if target in ("1", "时序法师", "chronomancer", "time"):
                subclass_name = "时序法师"
                price = 2888
            elif target in ("2", "塑能法师", "evoker", "elemental"):
                subclass_name = "塑能法师"
                price = 2888
            elif target in ("3", "秘钥学者", "arcanist", "key"):
                subclass_name = "秘钥学者"
                price = 2888
            elif target in ("4", "门之钥匙", "gatekey", "gate_key"):
                subclass_name = "门之钥匙"
                price = 3000
                is_gatekey = True
            elif target in ("5", "神秘物品", "mystery", "mystery_item"):
                subclass_name = "神秘物品"
                price = 66666
            elif target in ("6", "Icerainboww"):
                if not icerainboww_enabled:
                    yield "❌ 该商品已由管理员禁用，不可使用。"
                    return
                if killed_icerainboww:
                    yield "❌ 该商品已自动解锁，无需购买。"
                else:
                    yield "❌ 无法购买未知的隐藏商品。"
                return
            elif target in ("7", "尤格-索托斯", "Yog-Sothoth"):
                if getattr(stats, "killed_yog_sothoth", False):
                    yield "❌ 该商品已自动解锁，无需购买。"
                else:
                    yield "❌ 无法购买未知的隐藏商品。"
                return
            else:
                valid_ids = ["1", "2", "3", "4", "5"]
                if killed_icerainboww:
                    valid_ids.append("6")
                if getattr(stats, "killed_yog_sothoth", False):
                    valid_ids.append("7")
                valid_str = "、".join(valid_ids)
                yield f"❌ 无效的商品。可选商品序号：{valid_str}。"
                return

            if is_gatekey:
                if getattr(stats, "unlocked_gatekey", False):
                    yield "❌ 你已经解锁了【门之钥匙】。"
                    return
            else:
                if subclass_name in unlocked:
                    yield f"❌ 你已经解锁了【{subclass_name}】。"
                    return

            if gp < price:
                import random
                fail_quotes = [
                    "“呵呵，我的宝贝可概不赊账。多去地下城闯一闯，赚够了GP再来吧。”",
                    "“看来你的钱包 and 你的雄心壮志并不相符，旅者。”",
                    "“钱不够？那可不行。等你有了足够的GP，我随时在这儿等你。”",
                    "“GP不够可是买不到虚空造物的，去多打败一些强大的怪兽吧。”",
                    "“哦？想要空手套白狼？这可不是一个合格法师该有的行为。”",
                    "“即使是至高法皇，没钱也得从我这里老老实实地退出去，懂吗？”"
                ]
                quote = random.choice(fail_quotes)
                yield f"❌ 你的 GP 不足。购买【{subclass_name if not is_gatekey else '门之钥匙'}】需要 {price} GP，你当前只有 {gp} GP。\n🔮 神秘店主说：\n  {quote}"
                return

            stats.gp -= price
            if is_gatekey:
                stats.unlocked_gatekey = True
            else:
                stats.unlocked_subclasses.append(subclass_name)
            router.save_manager.save_stats(user_id, stats)
            import random
            success_quotes = [
                "“明智的选择，它现在属于你了。”",
                "“收您对应GP，拿好它，祝您好运，勇敢的旅者。”",
                "“呵呵，这股力量已经在虚空中沉睡了太久，希望你能配得上它。”",
                "“拿去吧，它会指指引你在接下来的地下城里改写宿命。”",
                "“噢……它离去时，连虚空的波动都微微震颤了一下。”",
                "“成交。记住，有些契约一经签订，便无法回头。”"
            ]
            quote = random.choice(success_quotes)
            yield f"🎉 购买成功！已成功解锁【{subclass_name if not is_gatekey else '门之钥匙'}】。已扣除 {price} GP。\n🔮 神秘店主说：\n  {quote}"
        else:
            yield "❌ 格式错误。请使用 /rogue 商店 (/rogue shop) 或 /rogue 商店 购买/buy (/rogue shop buy) <商品序号/商品名称>。"

class FoldCommand(CommandHandler, names=["折叠", "f", "fold"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            yield "❌ 你当前没有正在进行的游戏。"
            return
        res, term = router._execute_sub_action(user_id, run, parts)
        yield res + "\n" + GameRenderer.render_game(run)

class QueueCommand(CommandHandler, names=["队列", "q", "queue"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            yield "❌ 你当前没有正在进行的游戏。"
            return
        if len(parts) < 2:
            yield "❌ 请提供队列操作，例如：/rogue 队列 [使用 1, 随从 1 技能 2, 结束]"
            return
        full_arg = " ".join(parts[1:])
        results = []
        router._execute_queue(user_id, run, full_arg, results)
        if run.player.hp <= 0:
            yield "\n".join(results)
        else:
            yield "\n".join(results) + "\n" + GameRenderer.render_game(run)

class StatsCommand(CommandHandler, names=["统计", "stat", "stats"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        stats = router.save_manager.load_stats(user_id)
        yield GameRenderer.render_stats(stats)

class QueryCommand(CommandHandler, names=["查询", "query", "info", "i"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if len(parts) > 1:
            query_str = " ".join(parts[1:]).strip().lower()
            if query_str in ("抽牌堆", "draw", "draw_pile"):
                if not run:
                    yield "❌ 你当前没有正在进行的游戏。"
                elif run.node_type != "battle":
                    yield "❌ 只有在战斗中才能查询战斗牌堆。"
                else:
                    yield GameRenderer.render_draw_pile(run)
            elif query_str in ("弃牌堆", "discard", "discard_pile"):
                if not run:
                    yield "❌ 你当前没有正在进行的游戏。"
                elif run.node_type != "battle":
                    yield "❌ 只有在战斗中才能查询战斗牌堆。"
                else:
                    yield GameRenderer.render_discard_pile(run)
            elif query_str in ("消耗堆", "exhaust", "exhaust_pile"):
                if not run:
                    yield "❌ 你当前没有正在进行的游戏。"
                elif run.node_type != "battle":
                    yield "❌ 只有在战斗中才能查询战斗牌堆。"
                else:
                    yield GameRenderer.render_exhaust_pile(run)
            elif query_str in ("随从墓地", "mg", "minion_graveyard", "minion_grave"):
                if not run:
                    yield "❌ 你当前没有正在进行的游戏。"
                elif run.node_type != "battle":
                    yield "❌ 只有在战斗中才能查询战斗墓地。"
                else:
                    yield GameRenderer.render_minion_graveyard(run)
            elif query_str in ("敌人墓地", "eg", "enemy_graveyard", "enemy_grave"):
                if not run:
                    yield "❌ 你当前没有正在进行的游戏。"
                elif run.node_type != "battle":
                    yield "❌ 只有在战斗中才能查询战斗墓地。"
                else:
                    yield GameRenderer.render_enemy_graveyard(run)
            else:
                yield GameRenderer.render_query_info(" ".join(parts[1:]).strip())
        else:
            if not run:
                yield "❌ 你当前没有正在进行的游戏。输入 /rogue start 开始新游戏。\n💡 提示：你可以通过 /rogue i <名称>（如：/rogue i 力量）或 /rogue i buff 来查看相关效果描述。"
            elif run.node_type != "battle":
                yield "❌ 只有在战斗中才能查询详细战斗信息。请输入想要查询的随从、遗物、Buff名称。\n💡 提示：你可以通过 /rogue i <名称>（如：/rogue i 力量）或 /rogue i buff 来查看相关效果描述。"
            else:
                yield GameRenderer.render_detailed_battle(run)

class DrawCommand(CommandHandler, names=["抽牌堆", "draw", "draw_pile"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            yield "❌ 你当前没有正在进行的游戏。输入 /rogue start 开始新游戏。"
        elif run.node_type != "battle":
            yield "❌ 只有在战斗中才能查询战斗牌堆。"
        else:
            yield GameRenderer.render_draw_pile(run)

class DiscardCommand(CommandHandler, names=["弃牌堆", "discard", "discard_pile"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            yield "❌ 你当前没有正在进行的游戏。输入 /rogue start 开始新游戏。"
        elif run.node_type != "battle":
            yield "❌ 只有在战斗中才能查询战斗牌堆。"
        else:
            yield GameRenderer.render_discard_pile(run)

class ExhaustCommand(CommandHandler, names=["消耗堆", "exhaust", "exhaust_pile"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            yield "❌ 你当前没有正在进行的游戏。输入 /rogue start 开始新游戏。"
        elif run.node_type != "battle":
            yield "❌ 只有在战斗中才能查询战斗牌堆。"
        else:
            yield GameRenderer.render_exhaust_pile(run)

class MinionGraveyardCommand(CommandHandler, names=["随从墓地", "minion_graveyard", "mg"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            yield "❌ 你当前没有正在进行的游戏。输入 /rogue start 开始新游戏。"
        elif run.node_type != "battle":
            yield "❌ 只有在战斗中才能查询战斗墓地。"
        else:
            yield GameRenderer.render_minion_graveyard(run)

class EnemyGraveyardCommand(CommandHandler, names=["敌人墓地", "enemy_graveyard", "eg"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if not run:
            yield "❌ 你当前没有正在进行的游戏。输入 /rogue start 开始新游戏。"
        elif run.node_type != "battle":
            yield "❌ 只有在战斗中才能查询战斗墓地。"
        else:
            yield GameRenderer.render_enemy_graveyard(run)

class TownCommand(CommandHandler, names=["主城", "town"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        run = router.save_manager.load_save(user_id)
        if run:
            yield "❌ 游戏进行中，无法前往主城。请先通关或通过 放弃 结束当前游戏。"
            return
        stats = router.save_manager.load_stats(user_id)
        stats.in_town = True
        router.save_manager.save_stats(user_id, stats)
        yield router.town_engine.render_current_room(user_id, stats)
