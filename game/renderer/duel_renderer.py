import os
from ..models.state import GameRun
from ..cards import ALL_CARDS, MINION_SKILLS
from .menu import get_card_cost_str

def get_p1_p2_states(run: GameRun):
    p1_id = run.node_data.get("player1_id")
    if run.user_id == p1_id:
        return run.player, run.player2
    else:
        return run.player2, run.player

def render_duel_battle_public(run: GameRun) -> str:
    p1_name = run.node_data.get("player1_name", "玩家1")
    p2_name = run.node_data.get("player2_name", "玩家2")
    p1, p2 = get_p1_p2_states(run)
    current_turn_id = run.node_data.get("current_turn_id")
    turn_name = p1_name if current_turn_id == run.node_data.get("player1_id") else p2_name
    p1_coins = run.node_data.get("p1_coins", 0)
    p2_coins = run.node_data.get("p2_coins", 0)
    p1_ev = run.node_data.get("p1_evolve_points", 4)
    p2_ev = run.node_data.get("p2_evolve_points", 4)
    
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "⚔️ 【对决模式：公开战局简报】",
        f"当前回合：⏳ {turn_name} 的回合 (回合数: {run.node_data.get('turn_count', 1)})",
        "",
        f"🔴 玩家一：{p1_name}",
        f"❤️ HP {p1.hp}/{p1.max_hp} | 🛡️ 护盾 {p1.shield} | ⚡ 能量 {p1.actions}A {p1.bonus_actions}BA",
        f"进化点: {p1_ev}/4 | 幸运币: {p1_coins} 个",
        "玩家一战场：",
    ]
    
    if not p1.minions and not p1.amulets:
        lines.append("  (空无随从/护符)")
    else:
        for i in range(1, 7):
            key = str(i)
            if key in p1.minions:
                m = p1.minions[key]
                skills_desc = ""
                if m.id in MINION_SKILLS:
                    skills_desc = " | 技能: " + " ".join([f"({idx}){s['name']}" for idx, s in enumerate(MINION_SKILLS[m.id], 1)])
                buff_desc = ""
                if getattr(m, "buffs", None):
                    minion_buff_strs = []
                    for b in m.buffs:
                        if b.stacks > 1:
                            minion_buff_strs.append(f"{b.name} x{b.stacks}")
                        else:
                            minion_buff_strs.append(f"{b.name}")
                    buff_desc = " | Buff: " + " ".join(minion_buff_strs)
                lines.append(f"  [{i}] 随从：{m.name} (❤️ HP {m.hp}/{m.max_hp} | ⚔️ 攻击 {m.atk} | ⚡ 动作 {m.actions}A {m.bonus_actions}BA {m.attack_actions}AA{skills_desc}{buff_desc})")
            elif key in p1.amulets:
                a = p1.amulets[key]
                lines.append(f"  [{i}] 护符：{a.name} (⏳ 吟唱 {a.countdown}) - {a.desc}")
                
    lines.append("")
    lines.append(f"🔵 玩家二：{p2_name}")
    lines.append(f"❤️ HP {p2.hp}/{p2.max_hp} | 🛡️ 护盾 {p2.shield} | ⚡ 能量 {p2.actions}A {p2.bonus_actions}BA")
    lines.append(f"进化点: {p2_ev}/4 | 幸运币: {p2_coins} 个")
    lines.append("玩家二战场：")
    
    if not p2.minions and not p2.amulets:
        lines.append("  (空无随从/护符)")
    else:
        for i in range(1, 7):
            key = str(i)
            if key in p2.minions:
                m = p2.minions[key]
                skills_desc = ""
                if m.id in MINION_SKILLS:
                    skills_desc = " | 技能: " + " ".join([f"({idx}){s['name']}" for idx, s in enumerate(MINION_SKILLS[m.id], 1)])
                buff_desc = ""
                if getattr(m, "buffs", None):
                    minion_buff_strs = []
                    for b in m.buffs:
                        if b.stacks > 1:
                            minion_buff_strs.append(f"{b.name} x{b.stacks}")
                        else:
                            minion_buff_strs.append(f"{b.name}")
                    buff_desc = " | Buff: " + " ".join(minion_buff_strs)
                lines.append(f"  [{i}] 随从：{m.name} (❤️ HP {m.hp}/{m.max_hp} | ⚔️ 攻击 {m.atk} | ⚡ 动作 {m.actions}A {m.bonus_actions}BA {m.attack_actions}AA{skills_desc}{buff_desc})")
            elif key in p2.amulets:
                a = p2.amulets[key]
                lines.append(f"  [{i}] 护符：{a.name} (⏳ 吟唱 {a.countdown}) - {a.desc}")
                
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)

def render_duel_battle_private(run: GameRun) -> str:
    p1_id = run.node_data.get("player1_id")
    p1_name = run.node_data.get("player1_name", "玩家1")
    p2_name = run.node_data.get("player2_name", "玩家2")
    
    if run.user_id == p1_id:
        my_name = p1_name
        opp_name = p2_name
        my_coins = run.node_data.get("p1_coins", 0)
        my_ev = run.node_data.get("p1_evolve_points", 4)
        opp_ev = run.node_data.get("p2_evolve_points", 4)
    else:
        my_name = p2_name
        opp_name = p1_name
        my_coins = run.node_data.get("p2_coins", 0)
        my_ev = run.node_data.get("p2_evolve_points", 4)
        opp_ev = run.node_data.get("p1_evolve_points", 4)
        
    p = run.player
    opp = run.player2
    
    current_turn_id = run.node_data.get("current_turn_id")
    is_my_turn = (current_turn_id == run.user_id)
    turn_status = "🟢 你的回合" if is_my_turn else "⏳ 对方回合中..."
    
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        f"⚔️ 【对决战局详情 ({turn_status})】",
        f"自己({my_name})：❤️ HP {p.hp}/{p.max_hp} | 🛡️ 护盾 {p.shield} | ⚡ 能量 {p.actions}A {p.bonus_actions}BA",
        f"进化点: {my_ev}/4 | 幸运币: {my_coins} 个",
        "",
        "【我方战场】",
    ]
    
    if not p.minions and not p.amulets:
        lines.append("（空无一物）")
    else:
        for i in range(1, 7):
            key = str(i)
            if key in p.minions:
                m = p.minions[key]
                skills_desc = ""
                if m.id in MINION_SKILLS:
                    skills_desc = " | 技能: " + " ".join([f"({idx}){s['name']}" for idx, s in enumerate(MINION_SKILLS[m.id], 1)])
                buff_desc = ""
                if getattr(m, "buffs", None):
                    minion_buff_strs = []
                    for b in m.buffs:
                        if b.stacks > 1:
                            minion_buff_strs.append(f"{b.name} x{b.stacks}")
                        else:
                            minion_buff_strs.append(f"{b.name}")
                    buff_desc = " | Buff: " + " ".join(minion_buff_strs)
                lines.append(f" 格子 [{i}] 随从：{m.name} (❤️ HP {m.hp}/{m.max_hp} | ⚔️ 攻击 {m.atk} | ⚡ 动作 {m.actions}A {m.bonus_actions}BA {m.attack_actions}AA{skills_desc}{buff_desc})")
            elif key in p.amulets:
                a = p.amulets[key]
                lines.append(f" 格子 [{i}] 护符：{a.name} (⏳ 吟唱 {a.countdown}) - {a.desc}")
                
    lines.append("")
    lines.append(f"对手({opp_name})：❤️ HP {opp.hp}/{opp.max_hp} | 🛡️ 护盾 {opp.shield} | ⚡ 能量 {opp.actions}A {opp.bonus_actions}BA")
    lines.append(f"对手进化点: {opp_ev}/4")
    lines.append("【敌方战场】")
    
    if not opp.minions and not opp.amulets:
        lines.append("（空无一物）")
    else:
        for i in range(1, 7):
            key = str(i)
            if key in opp.minions:
                m = opp.minions[key]
                buff_desc = ""
                if getattr(m, "buffs", None):
                    minion_buff_strs = []
                    for b in m.buffs:
                        if b.stacks > 1:
                            minion_buff_strs.append(f"{b.name} x{b.stacks}")
                        else:
                            minion_buff_strs.append(f"{b.name}")
                    buff_desc = " | Buff: " + " ".join(minion_buff_strs)
                lines.append(f" 格子 [{i}] 随从：{m.name} (❤️ HP {m.hp}/{m.max_hp} | ⚔️ 攻击 {m.atk} | ⚡ 动作 {m.actions}A {m.bonus_actions}BA{buff_desc})")
            elif key in opp.amulets:
                a = opp.amulets[key]
                lines.append(f" 格子 [{i}] 护符：{a.name} (⏳ 吟唱 {a.countdown}) - {a.desc}")
                
    lines.append("")
    lines.append("【你的手牌】")
    if not p.hand:
        lines.append("（空空如也）")
    else:
        for idx, cid in enumerate(p.hand, 1):
            card = ALL_CARDS.get(cid)
            if card:
                color_ch = "⚫" if card.color == "curse" else ("🔴" if card.color == "warrior" else ("🔵" if card.color == "wizard" else "⚪"))
                cost_str = get_card_cost_str(card)
                rarity_map = {
                    "common": "普通",
                    "rare": "稀有",
                    "epic": "珍奇",
                    "legendary": "传奇",
                    "mythic": "神话",
                    "artifact": "神器",
                    "curse": "诅咒"
                }
                rname = rarity_map.get(getattr(card, "rarity", "common"), "普通")
                lines.append(f" [{idx}] {color_ch} {card.name} <{rname}> (消耗: {cost_str}) - {card.desc}")
                
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    if is_my_turn:
        lines.append("💬 轮到你的回合，操作指南：")
        lines.append("• 使用手牌：/rogue 使用 <手牌序号> [目标格子]")
        lines.append("  (注：物理或法术直伤卡牌必须以敌方随从格子 e2-e7 为目标，除非卡牌说明可打脸)")
        lines.append("• 随从攻击：/rogue 随从 <我方格子> 攻击 [目标格子]")
        lines.append("  (注：第一个回合召唤失调，有冲锋/突进词条除外，未指定目标默认打敌方第一个存活的随从/领主)")
        lines.append("• 使用幸运币：/rogue 幸运币 (或 coin/cn)")
        lines.append("• 进化卡牌：/rogue 进化 <我方格子/手牌序号> (或 evolve/ev)")
        lines.append("• 结束回合：/rogue 结束 (或 end)")
    else:
        lines.append("💬 目前是对手的回合，请耐心等待对手进行操作。")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)
