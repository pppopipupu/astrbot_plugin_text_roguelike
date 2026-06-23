from ..data.relic_data import RELIC_CONFIG
from ..data.buff_data import BUFF_CONFIG
from ..data.minion_data import MINION_CONFIG
from ..data.card_data import CARD_CONFIG
from ..data.enemy_data import ENEMY_CONFIG
from ..data.keyword_data import KEYWORD_CONFIG
from .menu import get_card_cost_str

def render_query_info(query_str: str) -> str:
    from ..models.manager import SaveManager
    boss_cfg = SaveManager().load_admin_config()
    icerainboww_enabled = boss_cfg.get("icerainboww_enabled", True)
    q = query_str.strip().lower()
    if not q:
        return "❌ 请输入具体的查询内容。"
    lines = ["━━━━━━━━━━━━━━━━━━━━", f"🔍 查询结果：{query_str}", ""]
    found = False
    if q in ("buff", "buffs", "状态", "战斗效果", "效果"):
        found = True
        lines.append("✨ 【全体战斗效果 (Buff) 一览】")
        for bid, cfg in BUFF_CONFIG.items():
            bname = cfg.get("name", bid)
            desc = cfg.get("desc", "")
            lines.append(f"  • 【{bname}】: {desc}")
        lines.append("")
    if q in ("keyword", "keywords", "词条", "机制"):
        found = True
        lines.append("🧩 【全体卡牌词条与机制一览】")
        for kid, cfg in KEYWORD_CONFIG.items():
            kname = cfg.get("name", kid)
            desc = cfg.get("desc", "")
            lines.append(f"  • 【{kname}】: {desc}")
        lines.append("")
    for rid, cfg in RELIC_CONFIG.items():
        if q == rid.lower() or q in cfg.get("name", "").lower():
            found = True
            rname = cfg.get("name", rid)
            rarity = cfg.get("rarity", "common")
            rarity_map = {
                "common": "普通",
                "rare": "稀有",
                "epic": "珍奇",
                "legendary": "传奇",
                "mythic": "神话",
                "artifact": "神器",
                "curse": "诅咒"
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
    for kid, cfg in KEYWORD_CONFIG.items():
        if q == kid.lower() or q in cfg.get("name", "").lower():
            found = True
            kname = cfg.get("name", kid)
            desc = cfg.get("desc", "")
            lines.append(f"🧩 词条/机制：{kname}")
            lines.append(f"描述：{desc}")
            lines.append("")
    for mid, cfg in MINION_CONFIG.items():
        if not icerainboww_enabled and (mid == "minion_icerainboww" or mid == "minion_icerainboww+" or "icerainboww" in mid.lower() or "icerainboww" in cfg.get("name", "").lower()):
            continue
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
        if not icerainboww_enabled and (cid == "minion_icerainboww" or cid == "minion_icerainboww+" or "icerainboww" in cid.lower() or "icerainboww" in cfg.get("name", "").lower()):
            continue
        q_clean = q[:-1] if q.endswith("+") else q
        if q_clean and (q_clean == cid.lower() or q_clean == cfg.get("name", "").lower() or q_clean in cid.lower() or q_clean in cfg.get("name", "").lower()):
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
                "mythic": "神话",
                "artifact": "神器",
                "curse": "诅咒"
            }
            rname_rarity = rarity_map.get(rarity, rarity)
            from ..cards import ALL_CARDS
            card_obj = ALL_CARDS.get(cid)
            cost_str = get_card_cost_str(card_obj) if card_obj else "免费"
            desc = cfg.get("desc", "")
            lines.append(f"📜 卡牌：{cname} ({ctype_ch} | {rname_rarity})")
            lines.append(f"消耗：{cost_str}")
            lines.append(f"效果：{desc}")
            lines.append("")
            
            from ..data.card_upgrade_data import CARD_UPGRADE_CONFIG
            if cid in CARD_UPGRADE_CONFIG:
                up_card = ALL_CARDS.get(cid + "+")
                if up_card:
                    up_cost_str = get_card_cost_str(up_card)
                    lines.append(f"🔨 升级变体：{up_card.name} ({ctype_ch} | {rname_rarity})")
                    lines.append(f"升级消耗：{up_cost_str}")
                    lines.append(f"升级效果：{up_card.desc}")
                    lines.append("")
    for eid, cfg in ENEMY_CONFIG.items():
        if not icerainboww_enabled and (eid == "Icerainboww" or "icerainboww" in eid.lower() or "icerainboww" in cfg.get("name", "").lower()):
            continue
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

    from .town import _load_zh_cn
    town_data = _load_zh_cn()
    if town_data:
        items_map = town_data.get("items", {})
        item_descs = town_data.get("item_descs", {})
        for item_id, aliases in items_map.items():
            if q == item_id.lower() or any(q == alias.lower() or q in alias.lower() for alias in aliases):
                found = True
                ch_name = aliases[0]
                desc = item_descs.get(item_id, "一件主城的特殊物品。")
                lines.append(f"🎒 物品：{ch_name} ({item_id})")
                lines.append(f"描述：{desc}")
                lines.append("")

        npcs_map = town_data.get("interactive_entities", {})
        for npc_id, npc_cfg in npcs_map.items():
            npc_name = npc_cfg.get("name", npc_id)
            if q == npc_id.lower() or q == npc_name.lower() or q in npc_name.lower():
                found = True
                desc = npc_cfg.get("desc", "先古主城的一位普通居民。")
                lines.append(f"👤 居民：{npc_name} ({npc_id})")
                lines.append(f"介绍：{desc}")
                
                idle_talks = npc_cfg.get("idle_talk", [])
                if idle_talks:
                    lines.append("闲聊语录：")
                    for t in idle_talks:
                        lines.append(f"  • {t}")
                lines.append("")

    if not found:
        lines.append("❌ 未找到与该名称或 ID 匹配的随从、遗物、Buff、卡牌、怪物、主城居民或物品信息。")
        lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines).strip()
