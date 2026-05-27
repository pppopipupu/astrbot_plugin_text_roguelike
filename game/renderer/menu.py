from ..models import GameRun, UserStats
from ..cards import ALL_CARDS

def render_menu() -> str:
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "🔮 魔法肉鸽卡牌游戏 (DND 5.5E 法师篇)",
        "",
        "一款使用纯文字游玩的策略肉鸽卡牌游戏。",
        "每回合拥有 1 个动作 (A) 和 1 个附赠动作 (BA)。",
        "召唤随从和护符可帮助战斗。随从拥有独立的动作，需手动指挥！",
        "",
        "【开始游戏】",
        "👉 /rogue 开启  -- 开始一局新游戏",
        "",
        "【其他命令】",
        "👉 /rogue 总览  -- 查看全部卡牌信息",
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
