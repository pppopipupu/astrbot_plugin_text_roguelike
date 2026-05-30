from ..models.state import GameRun, UserStats
from ..cards import ALL_CARDS

def render_menu(stats: UserStats = None) -> str:
    subclass_str = "无"
    gp_val = 0
    if stats:
        gp_val = getattr(stats, "gp", 0)
        subclass_str = getattr(stats, "selected_subclass", "") or "无"
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "🔮 魔法肉鸽卡牌游戏 (DND 5.5E 法师篇)",
        "",
        f"💰 我的 GP：{gp_val}",
        f"🧙 当前职业：法师  🔮 子职业：{subclass_str}",
        "",
        "一款使用纯文字游玩的策略肉鸽卡牌游戏。",
        "每回合拥有 2 个动作 (A) 和 1 个附赠动作 (BA)。",
        "召唤随从和护符可帮助战斗。随从拥有独立的动作，需手动指挥！",
        "",
        "【开始游戏】",
        "👉 /rogue 开启  -- 开始一局新游戏",
        "",
        "【其他命令】",
        "👉 /rogue 职业  -- 查看及选择子职业",
        "👉 /rogue 商店  -- 访问局外商店，使用 GP 购买商品",
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
            "mythic": "神器",
            "curse": "诅咒"
        }
        rname = rarity_map.get(getattr(card, "rarity", "common"), "普通")
        info = f"• {card.name} [{type_ch}] <{rname}> 消耗: {cost_str} - {card.desc}"
        
        up_card = ALL_CARDS.get(cid + "+")
        if up_card:
            up_cost_str = ""
            if up_card.cost_a > 0:
                up_cost_str += f"{up_card.cost_a}A "
            if up_card.cost_ba > 0:
                up_cost_str += f"{up_card.cost_ba}BA "
            up_cost_str = up_cost_str.strip() or "免费"
            info += f"\n  └─ 🔨 升级版：{up_card.name} | 消耗: {up_cost_str} | {up_card.desc}"
            
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
        "mythic": "神器",
        "curse": "诅咒"
    }
    commons = []
    rares = []
    epics = []
    curses = []
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
        elif r == "curse":
            curses.append(info)
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
    lines.append("")
    lines.append("【诅咒遗物】")
    lines.extend(curses)
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
                "mythic": "神器",
                "curse": "诅咒"
            }
            rname = rarity_map.get(getattr(card, "rarity", "common"), "普通")
            lines.append(f"{idx}. {color_type} {card.name} <{rname}> x{count} ({card.desc})")
            idx += 1
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)

def render_stats(stats: UserStats) -> str:
    mode_str = "开启" if getattr(stats, "rogue_mode", False) else "关闭"
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "📊 魔法肉鸽卡牌生涯统计",
        "",
        f"💥 累计输出伤害：{stats.total_damage} 点",
        f"💀 累计击败怪物：{stats.total_kills} 只",
        f"🧗 累计游玩层数：{stats.total_stages} 层",
        f"🎮 免前缀肉鸽模式：【{mode_str}】 (使用 /rogue mode 切换)",
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
        "👉 牌组 / deck -- 查看当前拥有的全部卡组及卡牌序号",
        "👉 总览 / overview [卡牌/遗物] -- 查看全部卡牌或遗物总览信息",
        "👉 统计 / stat / stats -- 查看勇士生涯累计统计数据",
        "👉 职业 / class -- 查看及选择子职业",
        "👉 商店 / shop -- 访问局外商店，使用 GP 购买子职业或神秘物品",
        "👉 放弃 / abandon -- 放弃当前战局（需输入 放弃 确认 彻底清空存档）",
        "👉 模式 / mode -- 切换个人免前缀快捷指令模式",
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
        "👉 查询 / query / info / i [名称] -- 查询战斗快照，或模糊查询卡牌/遗物/Buff/怪物信息",
        "",
        "💡 温馨提示：若已使用 模式/mode 开启免前缀肉鸽模式，你可以直接发送不带前缀的快捷指令（如直接发“结束”、“1”、“使用 1”）。此功能仅对你个人生效，不会对其他用户产生刷屏干扰。",
        "━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)

def render_shop(stats: UserStats) -> str:
    import random
    gp = getattr(stats, "gp", 0)
    unlocked = getattr(stats, "unlocked_subclasses", [])
    status_time = "已解锁" if "时序法师" in unlocked else "未解锁"
    status_element = "已解锁" if "塑能法师" in unlocked else "未解锁"
    status_mystery = "已解锁" if "神秘物品" in unlocked else "未解锁"
    
    welcome_quotes = [
        "“...嘘，悄悄看，我这儿可都是从无尽时空深处淘来的宝贝。”",
        "“又是你，旅者？只要GP足够，我这里的东西随时都可以归你。”",
        "“想要掌控时间，还是驾驭元素？或者……你对那件‘神秘物品’感兴趣？”",
        "“奥术的轨迹是有限的，但金钱 and 力量的秘密是无限的。”",
        "“有些东西并不存在于当下的时空，但在这里，一切皆有可能。”",
        "“外面的风暴越来越近了，或许你该准备点真正强力的武器？”"
    ]
    welcome_quote = random.choice(welcome_quotes)
    
    killed_icerainboww = getattr(stats, "killed_icerainboww", False)
    if killed_icerainboww:
        item4_title = " [4] Icerainboww - 状态：已解锁"
        item4_desc = "     └─ 击败最终BOSS Icerainboww解锁。"
    else:
        item4_title = " [4] ？？？ - 状态：未解锁"
        item4_desc = "     └─ 击败未知的最终BOSS解锁。"

    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "🏪 魔法肉鸽局外成长商店",
        "",
        "🔮 神秘店主说：",
        f"  {welcome_quote}",
        "",
        f"💰 我的 GP：{gp}",
        "",
        "【货架商品】",
        f" [1] 时序法师子职业 - 售价：2888 GP （状态：{status_time}）",
        "     └─ 操控时间。初始牌组中加入 1 张传奇卡牌“时间停止”（追加 3 个额外回合）。",
        f" [2] 塑能法师子职业 - 售价：2888 GP （状态：{status_element}）",
        "     └─ 元素爆发。所有法术伤害提升 15%，且抓取火球术时 40% 几率替换为流星爆。",
        f" [3] 神秘物品 - 售价：66666 GP （状态：{status_mystery}）",
        "     └─ 一件蕴藏着奇异力量的物件，购买后会永久保存在收藏中。",
        item4_title,
        item4_desc,
        "",
        "【购买指令】",
        "👉 /rogue 商店 购买 1 或 时序法师 -- 购买时序法师",
        "👉 /rogue 商店 购买 2 或 塑能法师 -- 购买塑能法师",
        "👉 /rogue 商店 购买 3 或 神秘物品 -- 购买神秘物品",
        "━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)
