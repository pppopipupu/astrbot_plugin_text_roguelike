from ..models.state import GameRun
from ..cards import ALL_CARDS, MINION_SKILLS
from ..entities import get_relic_name, get_relic_desc
from ..data.buff_data import BUFF_CONFIG
from ..data.minion_data import MINION_CONFIG

def render_battle(run: GameRun) -> str:
    p = run.player
    will_buff = next((b for b in p.buffs if b.id == "iron_will"), None)
    will_stacks = will_buff.stacks if will_buff else 0
    cur_max = p.max_hp + will_stacks * 10
    relics_str = ""
    if p.relics:
        relics_str = "\n🎒 遗物：" + " ".join([f"【{get_relic_name(r)}】" for r in p.relics])
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        f"⚔️ 【第 {p.stage} 关：战斗阶段】",
        f"玩家：❤️ HP {p.hp}/{cur_max} | 🛡️ 护盾 {p.shield} | ⚡ 动作 {p.actions}A {p.bonus_actions}BA" + relics_str
    ]
    if p.buffs:
        buff_strs = []
        for b in p.buffs:
            if b.stacks > 1:
                buff_strs.append(f"{b.name} x{b.stacks}")
            else:
                buff_strs.append(f"{b.name}")
        lines.append("玩家Buff：" + " | ".join(buff_strs))
    lines.append("")
    lines.append("【我方战场】")
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
                    buff_desc = " | Buff: " + " ".join([f"{b.name} x{b.stacks}" if b.stacks > 1 else b.name for b in m.buffs])
                atk_val = m.atk + (1 if "whetstone" in p.relics else 0)
                lines.append(f" 格子 [{i}] 随从：{m.name} (❤️ HP {m.hp}/{m.max_hp} | ⚔️ 攻击 {atk_val} | ⚡ 动作 {m.actions}A {m.bonus_actions}BA {m.attack_actions}AA{skills_desc}{buff_desc})")
            elif key in p.amulets:
                a = p.amulets[key]
                lines.append(f" 格子 [{i}] 护符：{a.name} (⏳ 吟唱 {a.countdown}) - {a.desc}")
    lines.append("")
    lines.append("【敌方战场】")
    if not run.enemies:
        lines.append("（空无一物）")
    else:
        for idx, enemy in enumerate(run.enemies, 1):
            intent_parts = []
            if enemy.intent_a_desc:
                intent_parts.append(f"A: {enemy.intent_a_desc}")
            if enemy.intent_ba_desc:
                ba_desc = enemy.intent_ba_desc
                if enemy.intent_ba2_desc:
                    ba_desc += f" + {enemy.intent_ba2_desc}"
                intent_parts.append(f"BA: {ba_desc}")
            intent_str = f"({', '.join(intent_parts)})" if intent_parts else "无意图"
            shield_str = f" | 🛡️ 护盾 {enemy.shield}" if enemy.shield > 0 else ""
            buff_desc = ""
            if getattr(enemy, "buffs", None):
                buff_desc = " | Buff: " + " ".join([f"{b.name} x{b.stacks}" if b.stacks > 1 else b.name for b in enemy.buffs])
            lines.append(f" 格子 [{idx}] 敌人：{enemy.name} (❤️ HP {enemy.hp}/{enemy.max_hp}{shield_str}{buff_desc} | ⚡ 动作 {enemy.actions}A {enemy.bonus_actions}BA | ⚔️ 意图：{intent_str})")
    lines.append("")
    lines.append("【你的手牌】")
    if not p.hand:
        lines.append("（空空如也）")
    else:
        for idx, cid in enumerate(p.hand, 1):
            card = ALL_CARDS.get(cid)
            if card:
                color_ch = "🔵" if card.color == "wizard" else "⚪"
                cost_str = ""
                if card.cost_a > 0:
                    cost_str += f"{card.cost_a}A"
                if card.cost_ba > 0:
                    cost_str += f"{card.cost_ba}BA"
                cost_str = cost_str or "免费"
                rarity_map = {
                    "common": "普通",
                    "rare": "稀有",
                    "epic": "珍奇",
                    "legendary": "传奇",
                    "mythic": "神器"
                }
                rname = rarity_map.get(getattr(card, "rarity", "common"), "普通")
                lines.append(f" [{idx}] {color_ch} {card.name} <{rname}> (消耗: {cost_str}) - {card.desc}")
    if run.node_data.get("pending_discard"):
        lines.append("⚠️ 状态：请选择一张手牌丢弃！请输入：/rogue 选择 <手牌序号>")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
    else:
        lines.append("━━━━━━━━━━━━━━━━━━━━")
    if p.fold_guide:
        lines.append("💬 提示：操作指南已折叠。输入 /rogue 折叠 可展开。")
    else:
        lines.append("💬 战斗指令指南：")
        lines.append("• 使用卡牌：/rogue 使用 <手牌序号> [目标]")
        lines.append("• 指向目标：敌方 e1-eN (对应敌方格子) | 我方 p0-p6 (p0为自己，p1-p6为随从)")
        lines.append("• 队列打牌：/rogue 使用 [1, 2:e1, 3]")
        lines.append("• 随从指令：/rogue 随从 <我方格子> 攻击/技能 <目标格子/技能序号> [技能目标]")
        lines.append("• 结束回合：/rogue 结束")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)

def render_detailed_battle(run: GameRun) -> str:
    p = run.player
    will_buff = next((b for b in p.buffs if b.id == "iron_will"), None)
    will_stacks = will_buff.stacks if will_buff else 0
    cur_max = p.max_hp + will_stacks * 10
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "⚔️ 【实时战斗详细情报】",
        "",
        "👤 【玩家领主】",
        f"  生命值：HP {p.hp}/{cur_max}",
        f"  护盾值：{p.shield}",
        f"  动作资源：{p.actions}A {p.bonus_actions}BA",
        f"  牌堆状态：手牌 {len(p.hand)}张 | 抽牌堆 {len(p.draw_pile)}张 | 弃牌堆 {len(p.discard_pile)}张 | 消耗堆 {len(p.exhaust_pile)}张",
    ]
    if p.relics:
        lines.append("  拥有遗物：")
        for r in p.relics:
            rname = get_relic_name(r)
            rdesc = get_relic_desc(r)
            lines.append(f"    • 【{rname}】: {rdesc}")
    else:
        lines.append("  拥有遗物：无")
    if p.buffs:
        lines.append("  当前Buff状态：")
        for b in p.buffs:
            bdesc = b.desc or BUFF_CONFIG.get(b.id, {}).get("desc", "无具体描述")
            lines.append(f"    • 【{b.name}】(层数: {b.stacks}): {bdesc}")
    else:
        lines.append("  当前Buff状态：无")
    lines.append("")
    lines.append("🦁 【我方战场】")
    if not p.minions and not p.amulets:
        lines.append("  （空无一物）")
    else:
        for i in range(1, 7):
            key = str(i)
            if key in p.minions:
                m = p.minions[key]
                atk_val = m.atk + (1 if "whetstone" in p.relics else 0)
                lines.append(f"  格子 [{i}] 随从：{m.name}")
                lines.append(f"    生命值：HP {m.hp}/{m.max_hp}")
                lines.append(f"    攻击力：⚔️ {atk_val}")
                lines.append(f"    剩余动作：{m.actions}A {m.bonus_actions}BA {m.attack_actions}AA")
                m_cfg = MINION_CONFIG.get(m.id, {})
                skills = m_cfg.get("skills", [])
                if skills:
                    lines.append("    技能列表：")
                    for idx, s in enumerate(skills, 1):
                        cost_str = ""
                        if s.get("cost_a", 0) > 0:
                            cost_str += f"{s['cost_a']}A "
                        if s.get("cost_ba", 0) > 0:
                            cost_str += f"{s['cost_ba']}BA "
                        cost_str = cost_str.strip() or "免费"
                        lines.append(f"      ({idx}) 【{s.get('name')}】(消耗: {cost_str}) - {s.get('desc')}")
                else:
                    lines.append("    技能列表：仅有普通攻击 (消耗 1A)")
                if getattr(m, "buffs", None):
                    lines.append("    随从Buff：")
                    for b in m.buffs:
                        bdesc = b.desc or BUFF_CONFIG.get(b.id, {}).get("desc", "无具体描述")
                        lines.append(f"      • 【{b.name}】(层数: {b.stacks}): {bdesc}")
            elif key in p.amulets:
                a = p.amulets[key]
                lines.append(f"  格子 [{i}] 护符：{a.name}")
                lines.append(f"    吟唱时间：⏳ 剩余 {a.countdown} 回合")
                lines.append(f"    效果：{a.desc}")
    lines.append("")
    lines.append("👿 【敌方战场】")
    if not run.enemies:
        lines.append("  （空无一物）")
    else:
        for idx, enemy in enumerate(run.enemies, 1):
            shield_str = f" | 🛡️ 护盾 {enemy.shield}" if enemy.shield > 0 else ""
            lines.append(f"  格子 [{idx}] 敌人：{enemy.name} (HP {enemy.hp}/{enemy.max_hp}{shield_str} | 动作 {enemy.actions}A {enemy.bonus_actions}BA)")
            intent_parts = []
            if enemy.intent_a_desc:
                intent_parts.append(f"动作(A)：{enemy.intent_a_desc}")
            if enemy.intent_ba_desc:
                ba_desc = enemy.intent_ba_desc
                if enemy.intent_ba2_desc:
                    ba_desc += f" + {enemy.intent_ba2_desc}"
                intent_parts.append(f"附赠动作(BA)：{ba_desc}")
            intent_str = " | ".join(intent_parts) if intent_parts else "无意图"
            lines.append(f"    行动意图：{intent_str}")
            if getattr(enemy, "buffs", None):
                lines.append("    敌人Buff：")
                for b in enemy.buffs:
                    bdesc = b.desc or BUFF_CONFIG.get(b.id, {}).get("desc", "无具体描述")
                    lines.append(f"      • 【{b.name}】(层数: {b.stacks}): {bdesc}")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)
