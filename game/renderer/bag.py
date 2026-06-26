import os
import json
from typing import Dict, Any
from ..models.state import UserStats
from ..entities import ALL_CARDS

def _load_zh_cn() -> Dict[str, Any]:
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    town_dir = os.path.join(current_dir, "data", "town")
    global_path = os.path.join(town_dir, "zh_cn_global.json")
    try:
        with open(global_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def render_bag(stats: UserStats) -> str:
    zh_cn = _load_zh_cn()
    items_loc = zh_cn.get("items", {})
    item_descs = zh_cn.get("item_descs", {})
    
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🎒 【先古主城 ── 冒险者随身背包】",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"💰 拥有 GP 资产：{stats.gp} GP",
        ""
    ]
    
    lines.append("🧱 【存放的冒险物品】")
    if stats.town_inventory:
        for item_id in stats.town_inventory:
            ch_name = items_loc.get(item_id, [item_id])[0]
            desc = item_descs.get(item_id, "一件主城里收集到的特殊物品，或许在与特定居民交谈时会派上用场。")
            lines.append(f"  • 【{ch_name}】 ({item_id})")
            lines.append(f"    描述：{desc}")
    else:
        lines.append("  • 你的背包空空如也，没有收集任何主城物品。")
    lines.append("")
    
    lines.append("🏷️ 【下局游戏定制（待带入）卡牌】")
    locked_list = getattr(stats, "locked_cards", []) or []
    p_pool = getattr(stats, "purchased_pool", [])
    
    has_custom = False
    if locked_list:
        has_custom = True
        locked_names = "、".join([f"【{ALL_CARDS[cid].name}】" if cid in ALL_CARDS else cid for cid in locked_list])
        lines.append(f"  📌 锁定必带卡牌：{locked_names}")
    if p_pool:
        has_custom = True
        p_names = "、".join([f"【{ALL_CARDS[cid].name}】" if cid in ALL_CARDS else cid for cid in p_pool])
        lines.append(f"  🛒 大卖场已购卡牌：{p_names}")
    if not has_custom:
        lines.append("  • 当前没有锁定或购买任何下局带入卡牌。")
    lines.append("")
    
    lines.append("🔓 【解锁的法师子职业与特殊特权】")
    unlocked = getattr(stats, "unlocked_subclasses", [])
    has_gatekey = getattr(stats, "unlocked_gatekey", False)
    
    privileges = []
    for sub in unlocked:
        privileges.append(f"子职业【{sub}】")
    if has_gatekey:
        privileges.append("特殊物品【门之钥匙】 (可开启西大门)")
        
    if privileges:
        lines.append("  • " + "、".join(privileges))
    else:
        lines.append("  • 当前尚未解锁任何法师子职业或大门特权。")
        
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 提示：输入 任务/quest 查看你的主城任务日志，输入 W/A/S/D 继续探索主城。")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)
