from ..models import GameRun, UserStats
from ..cards import ALL_CARDS

def render_menu() -> str:
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "🔮 魔法肉鸽卡牌游戏 (DND 5.5E 法师篇)",
        "",
        "一款使用纯文字游玩的策略肉鸽卡牌游戏。",
        "每回合拥有 2 个动作 (A) 和 1 个附赠动作 (BA)。",
        "召唤随从和护符可帮助战斗。随从拥有独立的动作，需手动指挥！",
        "",
        "【开始游戏】",
        "👉 /rogue 开启  -- 开始一局新游戏",
        "",
        "【其他命令】",
        "👉 /rogue 总览 [卡牌/遗物] -- 查看全部卡牌或遗物总览信息",
        "👉 /rogue 状态  -- 查看当前局内状态",
        "👉 /rogue 牌组  -- 查看当前拥有的卡组",
        "👉 /rogue 统计  -- 查看你的生涯统计数据",
        "👉 /rogue 放弃  -- 放弃当前局内游戏",
        "━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)

def render_card_library() -> str:
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "📜 魔法肉鸽卡牌总览",
        ""
    ]
    neutrals = []
    blue_spells = []
    for cid, card in ALL_CARDS.items():
        cost_str = ""
        if card.cost_a > 0:
            cost_str += f"{card.cost_a}A "
        if card.cost_ba > 0:
            cost_str += f"{card.cost_ba}BA "
        cost_str = cost_str.strip() or "免费"
        type_ch = ""
        if card.type == "spell":
            type_ch = "法术"
        elif card.type == "amulet":
            type_ch = f"护符(吟唱 {card.countdown})"
        elif card.type == "ability":
            type_ch = "能力"
        elif card.type == "minion":
            type_ch = "随从"
        rarity_map = {
            "common": "普通",
            "rare": "稀有",
            "epic": "珍奇",
            "legendary": "传奇",
            "mythic": "神器"
        }
        rname = rarity_map.get(getattr(card, "rarity", "common"), "普通")
        info = f"• {card.name} [{type_ch}] <{rname}> 消耗: {cost_str} - {card.desc}"
        if card.color == "neutral":
            neutrals.append(info)
        else:
            blue_spells.append(info)
    lines.append("【无色卡牌（中立）】")
    lines.extend(neutrals)
    lines.append("")
    lines.append("【蓝色卡牌（法师）】")
    lines.extend(blue_spells)
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)

def render_relic_library() -> str:
    from ..data.relic_data import RELIC_CONFIG
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "🎒 魔法肉鸽遗物总览",
        ""
    ]
    rarity_map = {
        "common": "普通",
        "rare": "稀有",
        "epic": "珍奇",
        "legendary": "传奇",
        "mythic": "神器"
    }
    commons = []
    rares = []
    epics = []
    for rid, relic in RELIC_CONFIG.items():
        r = relic.get("rarity", "common")
        rname = rarity_map.get(r, "普通")
        name = relic.get("name", rid)
        desc = relic.get("desc", "")
        price = relic.get("price", 0)
        info = f"• {name} <{rname}> 售价: {price}金币 - {desc}"
        if r == "common":
            commons.append(info)
        elif r == "rare":
            rares.append(info)
        else:
            epics.append(info)
    lines.append("【普通遗物】")
    lines.extend(commons)
    lines.append("")
    lines.append("【稀有遗物】")
    lines.extend(rares)
    lines.append("")
    lines.append("【珍奇遗物】")
    lines.extend(epics)
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)

def render_deck(run: GameRun) -> str:
    if not run or not run.player:
        return "❌ 你当前没有正在进行的游戏。输入 /rogue 开启 开始新游戏。"
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "📜 当前拥有的卡组 (共 %d 张)" % len(run.player.deck),
        ""
    ]
    counts = {}
    for cid in run.player.deck:
        counts[cid] = counts.get(cid, 0) + 1
    idx = 1
    for cid, count in sorted(counts.items()):
        card = ALL_CARDS.get(cid)
        if card:
            color_type = "🔵" if card.color == "wizard" else "⚪"
            rarity_map = {
                "common": "普通",
                "rare": "稀有",
                "epic": "珍奇",
                "legendary": "传奇",
                "mythic": "神器"
            }
            rname = rarity_map.get(getattr(card, "rarity", "common"), "普通")
            lines.append(f"{idx}. {color_type} {card.name} <{rname}> x{count} ({card.desc})")
            idx += 1
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)

def render_stats(stats: UserStats) -> str:
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "📊 魔法肉鸽卡牌生涯统计",
        "",
        f"💥 累计输出伤害：{stats.total_damage} 点",
        f"💀 累计击败怪物：{stats.total_kills} 只",
        f"🧗 累计游玩层数：{stats.total_stages} 层",
        "",
        "这些数据属于你的勇士生涯，不会随着放弃游戏而消失。",
        "━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)

def render_help() -> str:
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "🔮 魔法肉鸽卡牌游戏指令帮助",
        "",
        "输入 /rogue <子命令> 执行对应操作，主要指令及英文变体如下：",
        "",
        "【基础与非战斗指令】",
        "👉 开启 / start -- 开始一局新游戏（若有存档可输入 开启 确认）",
        "👉 帮助 / help -- 显示本帮助指令列表",
        "👉 状态 / s -- 查看当前的局内游戏界面与属性状态",
        "👉 牌组 -- 查看当前拥有的全部卡组及卡牌序号",
        "👉 总览 [卡牌/遗物] -- 查看全部卡牌或遗物总览信息（无参数默认只展示卡牌）",
        "👉 统计 / stat / stats -- 查看勇士生涯累计统计数据",
        "👉 放弃 -- 放弃当前战局（需输入 放弃 确认 彻底清空存档）",
        "",
        "【局内与战斗指令】",
        "👉 使用 / p <手牌序号> [目标] -- 使用或打出指定手牌。例如：使用 1",
        "👉 随从 / m <我方格子> <动作> <目标/序号> -- 指挥我方随从执行动作。例如：随从 1 攻击 e1",
        "   └─ 随从格子支持数字，以及 all 或 * 表示所有随从",
        "   └─ 动作支持 攻击 / a 或 技能 / s",
        "👉 选择 / c <序号> -- 选择事件分支、契约选项或商店商品（直接输入数字也可）。例如：选择 1",
        "👉 特殊 / sa <手牌序号> [目标] -- 释放对应手牌的特殊行动。例如：特殊 1",
        "👉 结束 / e -- 结束当前的战斗回合",
        "👉 折叠 / f / fold -- 切换是否折叠游戏底部的操作指南",
        "👉 队列 / q / queue <[指令1, 指令2...]> -- 顺序执行命令队列。例如：队列 [使用 1, 结束]",
        "👉 查询 / query / info / i [名称] -- 查询战斗快照，或模糊查询卡牌/遗物/Buff效果",
        "━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)
