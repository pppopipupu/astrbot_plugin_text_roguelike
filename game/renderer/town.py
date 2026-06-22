import os
import json
from typing import List, Dict, Any
from ..models.state import UserStats
from ..entities import ALL_CARDS

def _load_zh_cn() -> Dict[str, Any]:
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    zh_cn_path = os.path.join(current_dir, "data", "town", "zh_cn_town.json")
    if not os.path.exists(zh_cn_path):
        return {}
    try:
        with open(zh_cn_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def get_map_symbol(room_id: str, current_id: str, name: str) -> str:
    if room_id == current_id:
        return f"【{name}★】"
    return f"[{name}]"

def render_town_map(current_id: str, zh_cn: Dict[str, Any]) -> str:
    rooms_loc = zh_cn.get("rooms", {})
    t_wt = get_map_symbol("watch_tower", current_id, rooms_loc.get("watch_tower", {}).get("name", "Watch Tower"))
    t_wg = get_map_symbol("west_gate", current_id, rooms_loc.get("west_gate", {}).get("name", "West Gate"))
    t_rg = get_map_symbol("range", current_id, rooms_loc.get("range", {}).get("name", "Range"))
    t_ay = get_map_symbol("alley", current_id, rooms_loc.get("alley", {}).get("name", "Alley"))
    t_sq = get_map_symbol("square", current_id, rooms_loc.get("square", {}).get("name", "Square"))
    t_ft = get_map_symbol("fountain", current_id, rooms_loc.get("fountain", {}).get("name", "Fountain"))
    t_sp = get_map_symbol("shop", current_id, rooms_loc.get("shop", {}).get("name", "Shop"))
    t_mk = get_map_symbol("market", current_id, rooms_loc.get("market", {}).get("name", "Market"))
    t_tv = get_map_symbol("tavern", current_id, rooms_loc.get("tavern", {}).get("name", "Tavern"))
    t_vr = get_map_symbol("vip_room", current_id, rooms_loc.get("vip_room", {}).get("name", "VIP Room"))
    t_bs = get_map_symbol("blacksmith", current_id, rooms_loc.get("blacksmith", {}).get("name", "Blacksmith"))

    lines = [
        f"      {t_wt}",
        "        │",
        f"      {t_wg}",
        "        │",
        f"{t_rg} {t_ay} ── {t_sq} ── {t_ft} ── {t_sp}",
        "                    │                   │",
        f"                 {t_mk}            {t_tv} ── {t_vr}",
        "                    │",
        f"                 {t_bs}"
    ]
    return "\n".join(lines)

def render_town(stats: UserStats, room_data: Dict[str, Any]) -> str:
    zh_cn = _load_zh_cn()
    current_id = stats.town_pos
    map_str = render_town_map(current_id, zh_cn)

    name_key = room_data.get("name_key", current_id)
    room_loc = zh_cn.get("rooms", {}).get(name_key, {})
    room_name = room_loc.get("name", zh_cn.get("global", {}).get("unknown_room", "未知房间"))
    desc = room_loc.get("desc", "")

    title = zh_cn.get("global", {}).get("title_format", "✨ 先古主城 ── {name} ✨").format(name=room_name)

    entities_loc = zh_cn.get("interactive_entities", {})

    visible_npcs = []
    for npc_id in room_data.get("npcs", []):
        npc_name = entities_loc.get(npc_id, {}).get("name", npc_id)
        visible_npcs.append(npc_name)

    wandering_npcs_config = ["Gamer_Boy", "Crypto_Whale", "Lost_Bard", "Town_Guard", "Naughty_Child"]
    for npc_id in wandering_npcs_config:
        npc_pos = stats.town_flags.get(f"pos_{npc_id}", "square")
        if npc_pos == current_id:
            npc_name = entities_loc.get(npc_id, {}).get("name", npc_id)
            visible_npcs.append(npc_name)

    none_label = zh_cn.get("global", {}).get("none", "无")
    npc_str = "、".join(visible_npcs) if visible_npcs else none_label

    items_loc = zh_cn.get("items", {})
    visible_items = []
    for item_id in room_data.get("items", []):
        if not stats.town_flags.get(f"taken_{item_id}", 0):
            item_name = items_loc.get(item_id, [item_id])[0]
            visible_items.append(item_name)
    
    if current_id == "vip_room" and not stats.town_flags.get("box_opened", 0):
        chest_name = entities_loc.get("Chest", {}).get("name", "古老的铁宝箱")
        visible_items.append(chest_name)
    
    item_str = "、".join(visible_items) if visible_items else none_label

    exits_dict = room_data.get("exits", {})
    dir_names = zh_cn.get("global", {}).get("directions", {"w": "北", "s": "南", "a": "西", "d": "东"})
    exit_list = []
    for d, target in exits_dict.items():
        if d in dir_names:
            exit_list.append(f"{dir_names[d]}({d.upper()})")
    exit_str = "、".join(exit_list) if exit_list else none_label

    if current_id == "market":
        shelf = stats.town_flags.get("market_shelf", [])
        shelf_strs = []
        prices = [100, 300, 700]
        rarities = zh_cn.get("global", {}).get("rarities", ["普通", "稀有", "珍奇"])
        for idx, cid in enumerate(shelf):
            if not cid:
                shelf_strs.append(f"{idx+1}. " + zh_cn.get("global", {}).get("market_sold_out", "【已售罄】"))
            else:
                c_name = ALL_CARDS[cid].name if cid in ALL_CARDS else cid
                shelf_strs.append(zh_cn.get("global", {}).get("market_shelf_option", "").format(idx=idx+1, name=c_name, rarity=rarities[idx], price=prices[idx]))
        desc += zh_cn.get("global", {}).get("market_shelf_header", "\n\n🏷️ 今日货架商品：\n") + "\n".join(shelf_strs)
        desc += zh_cn.get("global", {}).get("market_shelf_footer", "\n（输入 交互/talk 卡牌商人 即可开启选购或锁定必带卡）")

    quest_str = ""
    quest_state = stats.town_flags.get("quest_town_tour_state", "unstarted")
    if quest_state == "started":
        visited = stats.town_flags.get("quest_town_tour_visited", [])
        if len(visited) >= 11:
            quest_str = zh_cn.get("global", {}).get("quest_tour_complete_ready", "")
        else:
            quest_str = zh_cn.get("global", {}).get("quest_tour_progress", "").format(visited=len(visited))
    elif quest_state == "completed":
        quest_str = zh_cn.get("global", {}).get("quest_tour_completed", "")
    else:
        quest_str = zh_cn.get("global", {}).get("quest_tour_none", "")

    town_inv = stats.town_inventory
    inv_display = []
    for item_id in town_inv:
        inv_display.append(items_loc.get(item_id, [item_id])[0])
    inv_str = "、".join(inv_display) if inv_display else zh_cn.get("global", {}).get("empty", "空")

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        title,
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        map_str,
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        zh_cn.get("global", {}).get("room_env", "环境：{desc}").format(desc=desc),
        zh_cn.get("global", {}).get("room_exits", "出口：{exits}").format(exits=exit_str),
        zh_cn.get("global", {}).get("room_npcs", "居民：{npcs}").format(npcs=npc_str),
        zh_cn.get("global", {}).get("room_items", "物品：{items}").format(items=item_str),
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        zh_cn.get("global", {}).get("room_inventory", "🎒 随身物品：{inv} | 💰 拥有 GP：{gp}").format(inv=inv_str, gp=stats.gp),
        quest_str,
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        zh_cn.get("global", {}).get("help_move", "💡 移动 (MOVE)：W(北/UP) / A(西/LEFT) / S(南/DOWN) / D(东/RIGHT)"),
        zh_cn.get("global", {}).get("help_take", "💡 拿取 (TAKE)：拿取/捡起/take/pick <物品>"),
        zh_cn.get("global", {}).get("help_use", "💡 使用 (USE)：使用/use <物品>"),
        zh_cn.get("global", {}).get("help_talk", "💡 交互 (TALK)：交互/talk/interact/talk_to <名字>"),
        zh_cn.get("global", {}).get("help_system", "💡 系统 (SYSTEM)：退出/exit/quit | 回城/home"),
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)
