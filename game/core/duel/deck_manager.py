from typing import Optional, Tuple
import base64
import json
from ...data.duel_template_data import DUEL_BROADCAST_TEMPLATES

class DeckManager:
    def __init__(self, save_manager):
        self.save_manager = save_manager

    def get_user_active_deck(self, user_id: str) -> Tuple[Optional[str], list]:
        data = self.save_manager.load_duel_decks(user_id)
        active = data.get("active_deck")
        decks = data.get("decks", {})
        if not active or active not in decks:
            if decks:
                first = list(decks.keys())[0]
                return first, decks[first]
            return None, []
        return active, decks[active]

    def check_deck_validity(self, deck_list: list) -> Tuple[bool, str]:
        if len(deck_list) < 25 or len(deck_list) > 50:
            return False, DUEL_BROADCAST_TEMPLATES["deck_invalid_count"].format(len_cards=len(deck_list))
        try:
            from ...data.duel_card_data import DUEL_CARD_CONFIG
        except ImportError:
            from game.data.duel_card_data import DUEL_CARD_CONFIG
        counts = {}
        for cid in deck_list:
            base_id = cid.rstrip("+")
            counts[base_id] = counts.get(base_id, 0) + 1
            cfg = DUEL_CARD_CONFIG.get(base_id, {})
            name = cfg.get("name", base_id)
            rarity = cfg.get("rarity", "common")
            ctype = cfg.get("type", "spell")
            
            limit = 4
            if rarity == "mythic" or rarity == "artifact" or ctype == "artifact":
                limit = 1
            elif rarity == "legendary":
                limit = 2
                
            if counts[base_id] > limit:
                if limit == 1:
                    return False, DUEL_BROADCAST_TEMPLATES["deck_invalid_mythic_limit"].format(name=name)
                elif limit == 2:
                    return False, DUEL_BROADCAST_TEMPLATES["deck_invalid_legendary_limit"].format(name=name)
                else:
                    return False, DUEL_BROADCAST_TEMPLATES["deck_invalid_common_limit"].format(name=name)
        return True, "合法"

    def handle_deck_cmd(self, user_id: str, args: list) -> Tuple[str, bool]:
        data = self.save_manager.load_duel_decks(user_id)
        if "decks" not in data:
            data["decks"] = {}
        decks = data["decks"]
        
        if not args:
            lines = [DUEL_BROADCAST_TEMPLATES["deck_list_title"]]
            active = data.get("active_deck")
            if not decks:
                lines.append(DUEL_BROADCAST_TEMPLATES["deck_list_empty"])
            else:
                for idx, (name, cards) in enumerate(decks.items(), 1):
                    valid, _ = self.check_deck_validity(cards)
                    act_tag = "⭐ [当前选中]" if name == active else ""
                    valid_tag = "🟢 合法" if valid else "❌ 不合法"
                    lines.append(DUEL_BROADCAST_TEMPLATES["deck_list_item"].format(
                        idx=idx, name=name, len_cards=len(cards), valid_tag=valid_tag, act_tag=act_tag
                    ))
            return "\n".join(lines), False
            
        sub = args[0].lower()
        if sub in ("create", "c", "创建"):
            if len(args) < 2:
                return DUEL_BROADCAST_TEMPLATES["deck_create_no_name"], False
            name = args[1].strip()
            if not name:
                return DUEL_BROADCAST_TEMPLATES["deck_create_empty_name"], False
            if name in decks:
                return DUEL_BROADCAST_TEMPLATES["deck_create_exists"].format(name=name), False
            decks[name] = []
            data["active_deck"] = name
            self.save_manager.save_duel_decks(user_id, data)
            return DUEL_BROADCAST_TEMPLATES["deck_create_success"].format(name=name), False
            
        elif sub in ("select", "s", "选择"):
            if len(args) < 2:
                return DUEL_BROADCAST_TEMPLATES["deck_select_no_target"], False
            tgt = args[1].strip()
            if tgt.isdigit():
                idx = int(tgt) - 1
                keys = list(decks.keys())
                if 0 <= idx < len(keys):
                    name = keys[idx]
                else:
                    return DUEL_BROADCAST_TEMPLATES["deck_select_out_of_range"], False
            else:
                name = tgt
                if name not in decks:
                    return DUEL_BROADCAST_TEMPLATES["deck_select_not_found"].format(name=name), False
            data["active_deck"] = name
            self.save_manager.save_duel_decks(user_id, data)
            return DUEL_BROADCAST_TEMPLATES["deck_select_success"].format(name=name), False
            
        elif sub in ("info", "i", "详情"):
            name = data.get("active_deck")
            if len(args) >= 2:
                tgt = args[1].strip()
                if tgt.isdigit():
                    idx = int(tgt) - 1
                    keys = list(decks.keys())
                    if 0 <= idx < len(keys):
                        name = keys[idx]
                else:
                    name = tgt
            if not name or name not in decks:
                return DUEL_BROADCAST_TEMPLATES["deck_info_not_found"], False
                
            cards = decks[name]
            valid, reason = self.check_deck_validity(cards)
            status_str = "🟢 合法" if valid else f"❌ 不合法: {reason}"
            lines = [DUEL_BROADCAST_TEMPLATES["deck_info_title"].format(name=name, len_cards=len(cards), status_str=status_str)]
            
            if not cards:
                lines.append(DUEL_BROADCAST_TEMPLATES["deck_info_empty"])
            else:
                counts = {}
                for cid in cards:
                    counts[cid] = counts.get(cid, 0) + 1
                    
                sorted_cids = sorted(list(counts.keys()))
                try:
                    from ...entities.cards.duel import ALL_DUEL_CARDS
                except ImportError:
                    from game.entities.cards.duel import ALL_DUEL_CARDS
                for idx, cid in enumerate(sorted_cids, 1):
                    card = ALL_DUEL_CARDS.get(cid)
                    if card:
                        cost_a = card.cost_a
                        cost_str = f"{cost_a}A" if cost_a >= 0 else "X A"
                        lines.append(DUEL_BROADCAST_TEMPLATES["deck_info_item"].format(
                            idx=idx, card_name=card.name, cost_str=cost_str, count=counts[cid]
                        ))
            return "\n".join(lines), False
            
        elif sub in ("add", "a", "添加"):
            active = data.get("active_deck")
            if not active or active not in decks:
                return DUEL_BROADCAST_TEMPLATES["deck_add_no_active"], False
            if len(args) < 2:
                return DUEL_BROADCAST_TEMPLATES["deck_add_no_card"], False
            
            query = args[1].strip()
            count = 1
            if len(args) >= 3 and args[2].isdigit():
                count = int(args[2])
                if count < 1 or count > 4:
                    count = 1
                    
            try:
                from ...data.duel_card_data import DUEL_CARD_CONFIG
            except ImportError:
                from game.data.duel_card_data import DUEL_CARD_CONFIG
            matched = []
            q_clean = query.lower()
            for cid, val in DUEL_CARD_CONFIG.items():
                name = val.get("name", "").replace("对决·", "").lower()
                if q_clean in name or q_clean in cid.lower():
                    matched.append(cid)
                    
            if not matched:
                return DUEL_BROADCAST_TEMPLATES["deck_add_not_found"], False
            if len(matched) > 1:
                try:
                    from ...entities.cards.duel import ALL_DUEL_CARDS
                except ImportError:
                    from game.entities.cards.duel import ALL_DUEL_CARDS
                matches_str = "、".join([f"【{ALL_DUEL_CARDS[cid].name.replace('对决·', '')}】" for cid in matched[:5]])
                return DUEL_BROADCAST_TEMPLATES["deck_add_multiple_matches"].format(matches=matches_str), False
                
            cid = matched[0]
            base_id = cid.rstrip("+")
            cards = decks[active]
            
            if len(cards) + count > 50:
                return DUEL_BROADCAST_TEMPLATES["deck_add_full"], False
                
            cur_count = sum(1 for c in cards if c.rstrip("+") == base_id)
            cfg = DUEL_CARD_CONFIG.get(base_id, {})
            rarity = cfg.get("rarity", "common")
            ctype = cfg.get("type", "spell")
            
            limit = 4
            if rarity == "mythic" or rarity == "artifact" or ctype == "artifact":
                limit = 1
            elif rarity == "legendary":
                limit = 2
                
            if cur_count + count > limit:
                try:
                    from ...entities.cards.duel import ALL_DUEL_CARDS
                except ImportError:
                    from game.entities.cards.duel import ALL_DUEL_CARDS
                cname = ALL_DUEL_CARDS[cid].name.replace('对决·', '')
                if limit == 1:
                    return DUEL_BROADCAST_TEMPLATES["deck_add_mythic_limit"].format(cname=cname, cur_count=cur_count), False
                elif limit == 2:
                    return DUEL_BROADCAST_TEMPLATES["deck_add_legendary_limit"].format(cname=cname, cur_count=cur_count), False
                else:
                    return DUEL_BROADCAST_TEMPLATES["deck_add_common_limit"].format(cname=cname, cur_count=cur_count), False
                
            for _ in range(count):
                cards.append(cid)
            self.save_manager.save_duel_decks(user_id, data)
            try:
                from ...entities.cards.duel import ALL_DUEL_CARDS
            except ImportError:
                from game.entities.cards.duel import ALL_DUEL_CARDS
            cname = ALL_DUEL_CARDS[cid].name.replace('对决·', '')
            return DUEL_BROADCAST_TEMPLATES["deck_add_success"].format(active=active, count=count, cname=cname), False
            
        elif sub in ("remove", "r", "移除"):
            active = data.get("active_deck")
            if not active or active not in decks:
                return DUEL_BROADCAST_TEMPLATES["deck_remove_no_active"], False
            if len(args) < 2:
                return DUEL_BROADCAST_TEMPLATES["deck_remove_no_idx"], False
                
            tgt = args[1].strip()
            if not tgt.isdigit():
                return DUEL_BROADCAST_TEMPLATES["deck_remove_invalid_idx"], False
                
            idx = int(tgt) - 1
            cards = decks[active]
            
            counts = {}
            for cid in cards:
                counts[cid] = counts.get(cid, 0) + 1
            sorted_cids = sorted(list(counts.keys()))
            
            if idx < 0 or idx >= len(sorted_cids):
                return DUEL_BROADCAST_TEMPLATES["deck_remove_out_of_range"], False
                
            cid_to_rem = sorted_cids[idx]
            count = 1
            if len(args) >= 3 and args[2].isdigit():
                count = int(args[2])
                
            actual_rem = 0
            for _ in range(count):
                if cid_to_rem in cards:
                    cards.remove(cid_to_rem)
                    actual_rem += 1
                    
            self.save_manager.save_duel_decks(user_id, data)
            try:
                from ...entities.cards.duel import ALL_DUEL_CARDS
            except ImportError:
                from game.entities.cards.duel import ALL_DUEL_CARDS
            cname = ALL_DUEL_CARDS[cid_to_rem].name.replace('对决·', '')
            return DUEL_BROADCAST_TEMPLATES["deck_remove_success"].format(active=active, actual_rem=actual_rem, cname=cname), False
            
        elif sub in ("export", "exp", "导出"):
            name = data.get("active_deck")
            if len(args) >= 2:
                tgt = args[1].strip()
                if tgt.isdigit():
                    idx = int(tgt) - 1
                    keys = list(decks.keys())
                    if 0 <= idx < len(keys):
                        name = keys[idx]
                else:
                    name = tgt
            if not name or name not in decks:
                return DUEL_BROADCAST_TEMPLATES["deck_export_no_deck"], False
            cards = decks[name]
            try:
                payload = {"name": name, "cards": cards}
                dumped = json.dumps(payload, ensure_ascii=False)
                code = base64.b64encode(dumped.encode("utf-8")).decode("utf-8")
                return DUEL_BROADCAST_TEMPLATES["deck_export_success"].format(name=name, code=code), False
            except Exception as e:
                return DUEL_BROADCAST_TEMPLATES["deck_export_failed"].format(err=str(e)), False
            
        elif sub in ("import", "imp", "导入"):
            if len(args) < 2:
                return DUEL_BROADCAST_TEMPLATES["deck_import_no_code"], False
            code = args[1].strip()
            custom_name = args[2].strip() if len(args) >= 3 else None
            try:
                decoded_bytes = base64.b64decode(code.encode("utf-8"))
                dumped = decoded_bytes.decode("utf-8")
                payload = json.loads(dumped)
            except Exception as e:
                return DUEL_BROADCAST_TEMPLATES["deck_import_decode_failed"].format(err=str(e)), False
            
            if not isinstance(payload, dict) or "name" not in payload or "cards" not in payload:
                return DUEL_BROADCAST_TEMPLATES["deck_import_invalid_format"], False
            
            orig_name = payload["name"]
            cards = payload["cards"]
            if not isinstance(cards, list):
                return DUEL_BROADCAST_TEMPLATES["deck_import_invalid_cards"], False
            
            try:
                from ...data.duel_card_data import DUEL_CARD_CONFIG
            except ImportError:
                from game.data.duel_card_data import DUEL_CARD_CONFIG
                
            for cid in cards:
                if not isinstance(cid, str):
                    return DUEL_BROADCAST_TEMPLATES["deck_import_invalid_card_type"].format(ctype=type(cid)), False
                base_id = cid.rstrip("+")
                if base_id not in DUEL_CARD_CONFIG:
                    return DUEL_BROADCAST_TEMPLATES["deck_import_unknown_card"].format(cid=cid), False
            
            target_name = custom_name if custom_name else orig_name
            target_name = target_name.strip()
            if not target_name:
                target_name = "导入牌组"
            
            final_name = target_name
            suffix = 0
            while final_name in decks:
                suffix += 1
                final_name = f"{target_name}_导入{suffix}"
            
            decks[final_name] = cards
            data["active_deck"] = final_name
            self.save_manager.save_duel_decks(user_id, data)
            
            valid, reason = self.check_deck_validity(cards)
            status_msg = "🟢 合法" if valid else f"❌ 不合法 ({reason})"
            return DUEL_BROADCAST_TEMPLATES["deck_import_success"].format(final_name=final_name, len_cards=len(cards), status_msg=status_msg), False
            
        return DUEL_BROADCAST_TEMPLATES["duel_cmd_unknown"], False
