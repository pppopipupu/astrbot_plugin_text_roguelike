from ..data.relic_data import RELIC_CONFIG
from ..data.buff_data import BUFF_CONFIG
from ..data.minion_data import MINION_CONFIG
from ..data.card_data import CARD_CONFIG
from ..data.enemy_data import ENEMY_CONFIG

def render_query_info(query_str: str) -> str:
    q = query_str.strip().lower()
    if not q:
        return "❌ 请输入具体的查询内容。"
    lines = ["━━━━━━━━━━━━━━━━━━━━", f"🔍 查询结果：{query_str}", ""]
    found = False
    for rid, cfg in RELIC_CONFIG.items():
        if q == rid.lower() or q in cfg.get("name", "").lower():
            found = True
            rname = cfg.get("name", rid)
            rarity = cfg.get("rarity", "common")
            rarity_map = {
                "common": "普通",
                "rare": "稀有",
                "epic": "珍奇"
            }
            rname_rarity = rarity_map.get(rarity, rarity)
            desc = cfg.get("desc", "")
            price = cfg.get("price", 0)
            lines.append(f"🎒 遗物：{rname} ({rname_rarity})")
            lines.append(f"效果：{desc}")
            lines.append(f"售价：{price} 金币")
            lines.append("")
    for bid, cfg in BUFF_CONFIG.items():
        if q == bid.lower() or q in cfg.get("name", "").lower():
            found = True
            bname = cfg.get("name", bid)
            desc = cfg.get("desc", "")
            lines.append(f"✨ 战斗效果 (Buff)：{bname}")
            lines.append(f"描述：{desc}")
            lines.append("")
    for mid, cfg in MINION_CONFIG.items():
        if q == mid.lower() or q in cfg.get("name", "").lower():
            found = True
            mname = cfg.get("name", mid)
            lines.append(f"🦁 随从：{mname}")
            card_cfg = CARD_CONFIG.get(mid)
            if card_cfg:
                hp = card_cfg.get("minion_hp", 0)
                atk = card_cfg.get("minion_atk", 0)
                lines.append(f"基础属性：生命值 {hp} | 攻击力 {atk}")
            skills = cfg.get("skills", [])
            if skills:
                lines.append("技能列表：")
                for s in skills:
                    cost_str = ""
                    if s.get("cost_a", 0) > 0:
                        cost_str += f"{s['cost_a']}A "
                    if s.get("cost_ba", 0) > 0:
                        cost_str += f"{s['cost_ba']}BA "
                    cost_str = cost_str.strip() or "免费"
                    lines.append(f"  • {s.get('name')} (消耗: {cost_str}) - {s.get('desc')}")
            else:
                lines.append("技能列表：仅有普通攻击 (消耗 1A)。")
            lines.append("")
    for cid, cfg in CARD_CONFIG.items():
        if q == cid.lower() or q in cfg.get("name", "").lower():
            found = True
            cname = cfg.get("name", cid)
            ctype = cfg.get("type", "")
            type_map = {
                "spell": "法术",
                "amulet": "护符",
                "ability": "能力",
                "minion": "随从"
            }
            ctype_ch = type_map.get(ctype, ctype)
            rarity = cfg.get("rarity", "common")
            rarity_map = {
                "common": "普通",
                "rare": "稀有",
                "epic": "珍奇",
                "legendary": "传奇",
                "mythic": "神器"
            }
            rname_rarity = rarity_map.get(rarity, rarity)
            cost_str = ""
            if cfg.get("cost_a", 0) > 0:
                cost_str += f"{cfg['cost_a']}A "
            if cfg.get("cost_ba", 0) > 0:
                cost_str += f"{cfg['cost_ba']}BA "
            cost_str = cost_str.strip() or "免费"
            desc = cfg.get("desc", "")
            lines.append(f"📜 卡牌：{cname} ({ctype_ch} | {rname_rarity})")
            lines.append(f"消耗：{cost_str}")
            lines.append(f"效果：{desc}")
            lines.append("")
    for eid, cfg in ENEMY_CONFIG.items():
        if q == eid.lower() or q in cfg.get("name", "").lower():
            found = True
            ename = cfg.get("name", eid)
            etype = cfg.get("type", "normal")
            type_map = {
                "normal": "普通",
                "elite": "精英",
                "boss": "领主",
                "summon": "召唤物"
            }
            etype_ch = type_map.get(etype, etype)
            ehp = cfg.get("hp", "未知")
            eact = cfg.get("actions", "1A 0BA")
            lines.append(f"👾 怪物：{ename} ({etype_ch})")
            lines.append(f"基础属性：生命值 {ehp} | 动作资源 {eact}")
            passive = cfg.get("passive")
            if passive:
                lines.append(f"特有效果：{passive}")
            intents = cfg.get("intents", [])
            if intents:
                lines.append("意图/行为列表：")
                for s in intents:
                    lines.append(f"  • {s.get('desc') or s.get('name') or s.get('id')}")
            cycle_info = cfg.get("cycle_info", [])
            if cycle_info:
                lines.append("行动循环列表：")
                for c in cycle_info:
                    lines.append(f"  • {c}")
            summon_goblin = cfg.get("summon_goblin")
            if summon_goblin:
                lines.append("关联召唤物：")
                s_name = summon_goblin.get("name", "未知")
                s_hp = summon_goblin.get("hp", 0)
                s_desc = summon_goblin.get("intent_desc", "")
                lines.append(f"  • {s_name} (生命值: {s_hp} | 动作资源: 1A 0BA) - {s_desc}")
            summon_hound = cfg.get("summon_hound")
            if summon_hound:
                lines.append("关联召唤物：")
                s_name = summon_hound.get("name", "未知")
                s_hp = summon_hound.get("hp", 0)
                s_desc = summon_hound.get("intent_desc", "")
                lines.append(f"  • {s_name} (生命值: {s_hp} | 动作资源: 1A 0BA) - {s_desc}")
            lines.append("")
    if not found:
        lines.append("❌ 未找到与该名称或 ID 匹配的随从、遗物、Buff、卡牌或怪物信息。")
        lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines).strip()
