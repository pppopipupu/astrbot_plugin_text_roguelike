from typing import Tuple, Optional
from ...data.duel_template_data import DUEL_BROADCAST_TEMPLATES
from ...renderer.duel_renderer import render_duel_battle_public, render_duel_battle_private

class QueryManager:
    def __init__(self, save_manager):
        self.save_manager = save_manager

    def handle_query_cmd(self, router, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        if not args:
            return DUEL_BROADCAST_TEMPLATES["query_no_query"], False, None, None, None, None
            
        cmd = args[0].lower()
        if cmd in ("对决", "duel"):
            if len(args) > 1:
                args = args[1:]
                cmd = args[0].lower()
            else:
                return DUEL_BROADCAST_TEMPLATES["query_no_query"], False, None, None, None, None

        run = self.save_manager.load_duel_save(user_id)
        
        is_query_cmd = cmd in ("查询", "query", "info", "i")
        sub_query = None
        if is_query_cmd:
            if len(args) > 1:
                sub_query = " ".join(args[1:]).strip().lower()
            else:
                if run:
                    p1_id = run.node_data["player1_id"]
                    p2_id = run.node_data["player2_id"]
                    current_acting_id = run.user_id
                    
                    if current_acting_id == p1_id:
                        dm1 = render_duel_battle_private(run)
                        run.player, run.player2 = run.player2, run.player
                        run.user_id = p2_id
                        dm2 = render_duel_battle_private(run)
                        run.player, run.player2 = run.player2, run.player
                        run.user_id = p1_id
                    else:
                        dm2 = render_duel_battle_private(run)
                        run.player, run.player2 = run.player2, run.player
                        run.user_id = p1_id
                        dm1 = render_duel_battle_private(run)
                        run.player, run.player2 = run.player2, run.player
                        run.user_id = p2_id
                        
                    public_text = render_duel_battle_public(run)
                    public_text = router.engine._append_logs_to_res(run, public_text)
                    dm1 = router.engine._append_logs_to_res(run, dm1)
                    dm2 = router.engine._append_logs_to_res(run, dm2)
                    
                    return public_text, False, p1_id, dm1, p2_id, dm2
                else:
                    return DUEL_BROADCAST_TEMPLATES["query_not_in_battle"], False, None, None, None, None
        else:
            sub_query = cmd
            
        if sub_query:
            if sub_query in ("抽牌堆", "draw", "draw_pile", "弃牌堆", "discard", "discard_pile", "消耗堆", "exhaust", "exhaust_pile", "随从墓地", "minion_graveyard", "mg", "minion_grave"):
                if not run:
                    return DUEL_BROADCAST_TEMPLATES["query_not_in_battle_pile"].format(sub_query=sub_query), False, None, None, None, None
                
                try:
                    from ...renderer import GameRenderer
                except ImportError:
                    from ...renderer import GameRenderer
                    
                if sub_query in ("抽牌堆", "draw", "draw_pile"):
                    render_res = GameRenderer.render_draw_pile(run)
                elif sub_query in ("弃牌堆", "discard", "discard_pile"):
                    render_res = GameRenderer.render_discard_pile(run)
                elif sub_query in ("消耗堆", "exhaust", "exhaust_pile"):
                    render_res = GameRenderer.render_exhaust_pile(run)
                else:
                    render_res = GameRenderer.render_minion_graveyard(run)
                    
                return DUEL_BROADCAST_TEMPLATES["query_pile_sent_private"].format(sub_query=sub_query), False, user_id, render_res, None, None

            res_str = self.render_duel_query_info(sub_query)
            return res_str, False, None, None, None, None
            
        return DUEL_BROADCAST_TEMPLATES["query_unknown"], False, None, None, None, None

    def render_duel_query_info(self, query_str: str) -> str:
        q = query_str.strip().lower()
        if not q:
            return DUEL_BROADCAST_TEMPLATES["query_no_query"]
            
        try:
            from ...data.duel_card_data import DUEL_CARD_CONFIG, QUEST_CONFIGS
            from ...data.buff_data import BUFF_CONFIG
            from ...data.keyword_data import KEYWORD_CONFIG
        except ImportError:
            from ...data.duel_card_data import DUEL_CARD_CONFIG, QUEST_CONFIGS
            from ...data.buff_data import BUFF_CONFIG
            from ...data.keyword_data import KEYWORD_CONFIG
            
        lines = [DUEL_BROADCAST_TEMPLATES["query_title"].format(query_str=query_str)]
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
        
        for cid, val in DUEL_CARD_CONFIG.items():
            name = val.get("name", cid).replace("对决·", "")
            if q == cid.lower() or q == name.lower() or q in name.lower() or q in cid.lower():
                found = True
                rarity = val.get("rarity", "common")
                rarity_map = {
                    "common": "普通",
                    "rare": "稀有",
                    "epic": "珍奇",
                    "legendary": "传奇",
                    "mythic": "神话",
                    "artifact": "神器",
                    "curse": "诅咒"
                }
                rname = rarity_map.get(rarity, rarity)
                cost_a = val.get("cost_a", 0)
                cost_ba = val.get("cost_ba", 0)
                cost_str = ""
                if cost_a == -1:
                    cost_str += "X A "
                elif cost_a > 0:
                    cost_str += f"{cost_a}A "
                if cost_ba == -1:
                    cost_str += "X BA "
                elif cost_ba > 0:
                    cost_str += f"{cost_ba}BA "
                cost_str = cost_str.strip() or "0"
                
                lines.append(DUEL_BROADCAST_TEMPLATES["query_card_header"].format(name=name, rname=rname))
                lines.append(DUEL_BROADCAST_TEMPLATES["query_card_detail"].format(ctype=val.get('type', 'spell'), cost_str=cost_str, desc=val.get('desc', '')))
                
        for qid, val in QUEST_CONFIGS.items():
            name = val.get("name", qid)
            if q == qid.lower() or q == name.lower() or q in name.lower() or q in qid.lower():
                found = True
                rarity = val.get("rarity", "common")
                rname = {
                    "common": "普通", "rare": "稀有", "epic": "珍奇", 
                    "legendary": "传奇", "mythic": "神话", "artifact": "神器", "curse": "诅咒"
                }.get(rarity, rarity)
                cost_a = val.get("cost_a", 0)
                cost_ba = val.get("cost_ba", 0)
                cost_str = ""
                if cost_a > 0: cost_str += f"{cost_a}A "
                if cost_ba > 0: cost_str += f"{cost_ba}BA "
                cost_str = cost_str.strip() or "0"
                
                lines.append(DUEL_BROADCAST_TEMPLATES["query_quest_header"].format(name=name, rname=rname))
                lines.append(DUEL_BROADCAST_TEMPLATES["query_quest_detail"].format(ctype=val.get('type', 'spell'), cost_str=cost_str, desc=val.get('desc', '')))
                

        if not found:
            return DUEL_BROADCAST_TEMPLATES["query_no_match"].format(query_str=query_str)
            
        return "\n".join(lines).strip()
