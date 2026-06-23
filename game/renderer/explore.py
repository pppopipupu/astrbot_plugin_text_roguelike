from ..models.state import GameRun
from ..entities import get_relic_name, get_relic_desc
from ..cards import ALL_CARDS
from .menu import get_card_cost_str

def render_event(run: GameRun) -> str:
    p = run.player
    data = run.node_data
    relics_str = ""
    if p.relics:
        relics_str = "\n🎒 遗物：" + " ".join([f"【{get_relic_name(r)}】" for r in p.relics])
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        f"✨ 【第 {p.stage} 关：随机事件】",
        f"{run.player.name}：❤️ HP {p.hp}/{p.max_hp} | 🪙 金币 {p.gold}" + relics_str,
        "",
        data.get("description", "发生了一个神秘的事件。"),
        "",
        "请做出你的选择："
    ]
    options = data.get("options", [])
    for idx, opt in enumerate(options, 1):
        lines.append(f" [{idx}] {opt.get('text', '')}")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    if p.fold_guide:
        lines.append("💬 提示：操作指南已折叠。输入 /rogue 折叠 可展开。")
    else:
        lines.append("💬 选择指令：/rogue c <序号>")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)

def render_shop(run: GameRun) -> str:
    p = run.player
    data = run.node_data
    relics_str = ""
    if p.relics:
        relics_str = "\n🎒 遗物：" + " ".join([f"【{get_relic_name(r)}】" for r in p.relics])
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        f"🛒 【第 {p.stage} 关：奇妙商店】",
        f"{run.player.name}：❤️ HP {p.hp}/{p.max_hp} | 🪙 金币 {p.gold}" + relics_str,
        "",
        "一位旅商展示着他的精致收藏：",
        ""
    ]
    items = data.get("items", [])
    for idx, item in enumerate(items, 1):
        itype = item.get("type")
        price = item.get("price")
        sold = item.get("sold", False)
        if sold:
            lines.append(f" [{idx}] 【已售罄】")
            continue
        if itype == "card":
            card = ALL_CARDS.get(item.get("card_id"))
            if card:
                color_ch = "⚫" if card.color == "curse" else ("🔵" if card.color == "wizard" else "⚪")
                cost_str = get_card_cost_str(card)
                lines.append(f" [{idx}] {color_ch} {card.name} (卡牌 | 消耗: {cost_str}) - 🪙 {price}金币 | {card.desc}")
        elif itype == "relic":
            rid = item.get("relic_id")
            lines.append(f" [{idx}] 🎒 {get_relic_name(rid)} (遗物) - 🪙 {price}金币 | {get_relic_desc(rid)}")
        elif itype == "remove":
            lines.append(f" [{idx}] 🧹 净化服务 (移除卡组中任意一张牌) - 🪙 {price}金币")
        elif itype == "upgrade":
            lines.append(f" [{idx}] 🔨 强化服务 (将卡组中任意一张牌永久升级为带【+】的强力变体) - 🪙 {price}金币")
        elif itype == "leave":
            lines.append(f" [{idx}] 🚪 离开商店，继续冒险")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    if p.fold_guide:
        lines.append("💬 提示：操作指南已折叠。输入 /rogue 折叠 可展开。")
    else:
        lines.append("💬 购买/选择指令：/rogue c <商品序号>")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)

def render_rest(run: GameRun) -> str:
    p = run.player
    relics_str = ""
    if p.relics:
        relics_str = "\n🎒 遗物：" + " ".join([f"【{get_relic_name(r)}】" for r in p.relics])
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        f"🔥 【第 {p.stage} 关：篝火营地】",
        f"{run.player.name}：❤️ HP {p.hp}/{p.max_hp}" + relics_str,
        "",
        "温暖的篝火跳跃着，你感到有些疲惫。你可以选择：",
        " [1] 🍖 休息：恢复 50% 最大生命值",
        " [2] 🔮 冥想：获得一张随机蓝色法术牌并加入卡组",
        " [3] 🚪 离开：不做整顿直接出发",
        " [4] 🔨 强化：选择你卡组里的一张卡牌进行升级",
        "━━━━━━━━━━━━━━━━━━━━"
    ]
    if p.fold_guide:
        lines.append("💬 提示：操作指南已折叠。输入 /rogue 折叠 可展开。")
    else:
        lines.append("💬 选择指令：/rogue c <序号>")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)

def render_reward(run: GameRun) -> str:
    p = run.player
    data = run.node_data
    if data.get("no_reward"):
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            "🎁 【离开遭遇战】",
            "",
            "🔮 你咏唱了【异界传送】，狼狈地穿过传送门逃离了战场。",
            "由于你半途脱逃，本场遭遇战你没有获得任何战利品与金币！",
            "",
            " [1] 🚪 确认并继续前进",
            "━━━━━━━━━━━━━━━━━━━━",
            "💬 继续指令：/rogue c 1",
            "━━━━━━━━━━━━━━━━━━━━"
        ]
        return "\n".join(lines)
    quest_bonus = data.get("quest_bonus", "")
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "🎁 【战斗胜利！请选择你的战利品】",
        ""
    ]
    if quest_bonus:
        lines.append(quest_bonus)
        lines.append("")
    cards = data.get("cards", [])
    for idx, cid in enumerate(cards, 1):
        card = ALL_CARDS.get(cid)
        if card:
            color_ch = "⚫" if card.color == "curse" else ("🔵" if card.color == "wizard" else "⚪")
            cost_str = get_card_cost_str(card)
            lines.append(f" [{idx}] {color_ch} {card.name} (消耗: {cost_str}) - {card.desc}")
    skip_idx = len(cards) + 1
    lines.append(f" [{skip_idx}] 🪙 跳过奖励卡牌 (获得 15 金币)")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    if p.fold_guide:
        lines.append("💬 提示：操作指南已折叠。输入 /rogue 折叠 可展开。")
    else:
        lines.append("💬 选择指令：/rogue c <序号>")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)

def render_treasure(run: GameRun) -> str:
    p = run.player
    data = run.node_data
    text = data.get("text", "")
    state = data.get("state", "pending_remove")
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        f"🎁 【第 {p.stage} 关：古老宝箱】",
        f"{run.player.name}：❤️ HP {p.hp}/{p.max_hp} | 🪙 金币 {p.gold}",
        "",
        text,
        ""
    ]
    if state == "opened":
        lines.append(" [1] 🚪 离开宝箱房，继续冒险")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    if state == "pending_remove":
        lines.append("💬 选择要献祭（移除）的卡牌序号指令：/rogue c <卡牌序号>")
    else:
        lines.append("💬 离开指令：/rogue c 1")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)

def render_card_select(run: GameRun) -> str:
    p = run.player
    data = run.node_data
    title = data.get("title", "选择你的卡牌奖励")
    relics_str = ""
    if p.relics:
        relics_str = "\n🎒 遗物：" + " ".join([f"【{get_relic_name(r)}】" for r in p.relics])
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        f"🎁 【{title}】",
        f"{run.player.name}：❤️ HP {p.hp}/{p.max_hp} | 🪙 金币 {p.gold}" + relics_str,
        ""
    ]
    desc = data.get("desc")
    if desc:
        lines.append(desc)
        lines.append("")
    cards = data.get("cards", [])
    for idx, cid in enumerate(cards, 1):
        card = ALL_CARDS.get(cid)
        if card:
            color_ch = "⚫" if card.color == "curse" else ("🔵" if card.color == "wizard" else "⚪")
            cost_str = get_card_cost_str(card)
            lines.append(f" [{idx}] {color_ch} {card.name} (消耗: {cost_str}) - {card.desc}")
    skip_idx = len(cards) + 1
    lines.append(f" [{skip_idx}] 🚪 跳过卡牌选择")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    if p.fold_guide:
        lines.append("💬 提示：操作指南已折叠。输入 /rogue 折叠 可展开。")
    else:
        lines.append("💬 选择指令：/rogue c <序号>")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)
