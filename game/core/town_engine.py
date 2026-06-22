import os
import json
import random
from typing import Optional, List, Dict, Any, Tuple
from ..models.state import UserStats, GameRun, PlayerState, EnemyState, BuffState
from ..entities import ALL_CARDS

class TownEngine:
    def __init__(self, save_manager, engine):
        self.save_manager = save_manager
        self.engine = engine

    def _load_zh_cn(self) -> Dict[str, Any]:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        zh_cn_path = os.path.join(os.path.dirname(current_dir), "data", "town", "zh_cn_town.json")
        if not os.path.exists(zh_cn_path):
            return {}
        try:
            with open(zh_cn_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def _load_room_data(self, room_id: str) -> Dict[str, Any]:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(os.path.dirname(current_dir), "data", "town", f"{room_id}.json")
        if not os.path.exists(data_path):
            return {"id": room_id, "name_key": room_id, "exits": {}, "npcs": [], "items": [], "interactive": {}}
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"id": room_id, "name_key": room_id, "exits": {}, "npcs": [], "items": [], "interactive": {}}

    def render_current_room(self, user_id: str, stats: UserStats) -> str:
        zh_cn = self._load_zh_cn()
        if stats.town_pos == "market":
            self._get_market_shelf(stats)
            self.save_manager.save_stats(user_id, stats)

        active_dialog = stats.town_flags.get("current_dialog")
        if active_dialog:
            return self._render_dialog_window(stats, active_dialog, zh_cn)

        from ..renderer.town import render_town
        room_data = self._load_room_data(stats.town_pos)
        return render_town(stats, room_data)

    def _render_dialog_window(self, stats: UserStats, npc_id: str, zh_cn: Dict[str, Any]) -> str:
        entities = zh_cn.get("interactive_entities", {})
        npc_data = entities.get(npc_id, {})
        npc_name = npc_data.get("name", npc_id)
        welcome_text = npc_data.get("welcome", "")

        options = []
        sub_menu = stats.town_flags.get("market_sub_menu")
        if npc_id == "Market_Merchant" and sub_menu == "buy":
            shelf = self._get_market_shelf(stats)
            prices = [100, 300, 700]
            rarities = zh_cn.get("global", {}).get("rarities", ["普通", "稀有", "珍奇"])
            for idx, cid in enumerate(shelf):
                if not cid:
                    options.append(f"{idx+1}. " + zh_cn.get("global", {}).get("market_sold_out", "【已售罄】"))
                else:
                    c_name = ALL_CARDS[cid].name if cid in ALL_CARDS else cid
                    options.append(zh_cn.get("global", {}).get("market_buy_option", "").format(idx=idx+1, name=c_name, rarity=rarities[idx], price=prices[idx]))
            options.append(f"{len(shelf)+1}. " + zh_cn.get("global", {}).get("back_to_previous", "返回上一级"))
        elif npc_id == "Market_Merchant" and sub_menu == "lock":
            options.append(zh_cn.get("global", {}).get("lock_instructions", "ℹ️ 请直接输入你想锁定的卡牌名称（例如输入 痛击 ）进行绑定。"))
            options.append(zh_cn.get("global", {}).get("back_to_previous_1", "1. 返回上一级"))
        elif npc_id == "Shopkeeper_Jack" and stats.town_flags.get("shop_sub_menu") == "buy_subclass":
            unlocked = getattr(stats, "unlocked_subclasses", [])
            has_gatekey = getattr(stats, "unlocked_gatekey", False)
            items_list = [
                ("时序法师", 2888, "时序法师" in unlocked),
                ("塑能法师", 2888, "塑能法师" in unlocked),
                ("秘钥学者", 2888, "秘钥学者" in unlocked),
                ("门之钥匙", 3000, has_gatekey),
                ("神秘物品", 66666, False)
            ]
            for idx, (name, price, is_unlocked) in enumerate(items_list):
                if is_unlocked:
                    options.append(f"{idx+1}. 购买 【{name}】 ({zh_cn.get('global', {}).get('unlocked_status', '已解锁')})")
                else:
                    options.append(f"{idx+1}. 购买 【{name}】 ({price} GP)")
            options.append(f"{len(items_list)+1}. " + zh_cn.get("global", {}).get("back_to_previous", "返回上一级"))
        else:
            if npc_id not in ("Chest", "Fountain", "West_Gate"):
                options.append(f"1. {npc_data.get('option_idle', zh_cn.get('global', {}).get('idle_talk_default', '闲聊'))}")
            if npc_id == "Guide_Elder":
                quest_state = stats.town_flags.get("quest_town_tour_state", "unstarted")
                if quest_state == "unstarted":
                    options.append(f"2. {npc_data.get('option_quest_accept')}")
                elif quest_state == "started":
                    visited = stats.town_flags.get("quest_town_tour_visited", [])
                    if len(visited) >= 11:
                        options.append(f"2. {npc_data.get('option_quest_complete')}")
                    else:
                        options.append(f"2. {npc_data.get('option_quest_status')}")
            elif npc_id == "Bartender_Jack":
                if "wine_glass" in stats.town_inventory and not stats.town_flags.get("jack_gift_given", 0):
                    options.append(f"2. {npc_data.get('option_gift_glass')}")
            elif npc_id == "Blacksmith_Ironclad":
                if "strange_ore" in stats.town_inventory and not stats.town_flags.get("ironclad_gift_given", 0):
                    options.append(f"2. {npc_data.get('option_gift_ore')}")
            elif npc_id == "Market_Merchant":
                options.append(f"2. {npc_data.get('option_buy_shelf')}")
                options.append(f"3. {npc_data.get('option_lock_card')}")
            elif npc_id == "Shopkeeper_Jack":
                options.append(f"2. {npc_data.get('option_buy_subclass', '购买新子职业/门之钥匙...')}")
            elif npc_id == "Chest":
                if "rusty_key" in stats.town_inventory and not stats.town_flags.get("box_opened", 0):
                    options.append(f"1. {npc_data.get('option_open')}")
            elif npc_id == "Fountain":
                if "lucky_coin" in stats.town_inventory:
                    options.append(f"1. {npc_data.get('option_wish')}")
            elif npc_id == "West_Gate":
                options.append(f"1. {npc_data.get('option_knock')}")
            elif npc_id in ("Dummy", "NoobSlayer99", "xXx_SniperElite_xXx", "pppopipupu"):
                options.append(f"2. {npc_data.get('option_challenge')}")

            leave_label = npc_data.get("option_leave", zh_cn.get("global", {}).get("leave_default", "离开"))
            options.append(f"{len(options)+1}. {leave_label}")

        menu_lines = "\n".join(options)
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            zh_cn.get("global", {}).get("dialog_title", "💬 与【{name}】对话中").format(name=npc_name),
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            welcome_text,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            menu_lines,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            zh_cn.get("global", {}).get("dialog_help", "💡 输入选项编号(如 1, 2)进行互动，输入 离开/exit/quit 结束交谈。"),
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
        return "\n".join(lines)

    def _get_market_shelf(self, stats: UserStats) -> List[str]:
        shelf = stats.town_flags.get("market_shelf")
        if shelf is not None:
            return shelf
        commons = []
        rares = []
        epics = []
        for cid, c in ALL_CARDS.items():
            rarity = getattr(c, "rarity", "common")
            color = getattr(c, "color", "")
            if rarity == "legendary" or color == "curse" or cid.startswith("curse_") or cid.startswith("duel_"):
                continue
            if rarity == "common":
                commons.append(cid)
            elif rarity == "rare":
                rares.append(cid)
            elif rarity == "epic":
                epics.append(cid)
        c_sel = random.choice(commons) if commons else "strike"
        r_sel = random.choice(rares) if rares else "first_aid"
        e_sel = random.choice(epics) if epics else "fireball"
        shelf = [c_sel, r_sel, e_sel]
        stats.town_flags["market_shelf"] = shelf
        return shelf

    def move(self, user_id: str, direction: str) -> str:
        stats = self.save_manager.load_stats(user_id)
        room_data = self._load_room_data(stats.town_pos)
        exits = room_data.get("exits", {})
        dir_map = {"up": "w", "down": "s", "left": "a", "right": "d"}
        dir_key = direction.lower()
        dir_key = dir_map.get(dir_key, dir_key)

        if dir_key not in exits:
            zh_cn = self._load_zh_cn()
            return zh_cn.get("global", {}).get("move_no_way", "").format(exits=', '.join(exits.keys()).upper())

        target_room = exits[dir_key]
        stats.town_pos = target_room

        quest_state = stats.town_flags.get("quest_town_tour_state", "unstarted")
        if quest_state == "started":
            visited = stats.town_flags.setdefault("quest_town_tour_visited", [])
            if target_room not in visited:
                visited.append(target_room)

        if random.random() < 0.5:
            wandering_npcs = ["Gamer_Boy", "Crypto_Whale", "Lost_Bard", "Town_Guard", "Naughty_Child"]
            wandering_rooms = ["square", "fountain", "shop", "tavern", "alley"]
            for npc in wandering_npcs:
                if random.random() < 0.5:
                    stats.town_flags[f"pos_{npc}"] = random.choice(wandering_rooms)

        self.save_manager.save_stats(user_id, stats)
        target_room_data = self._load_room_data(target_room)
        from ..renderer.town import render_town
        return render_town(stats, target_room_data)

    def talk_npc(self, user_id: str, target_name: str) -> str:
        stats = self.save_manager.load_stats(user_id)
        current_room = stats.town_pos
        room_data = self._load_room_data(current_room)
        zh_cn = self._load_zh_cn()

        visible_ids = []
        for n in room_data.get("npcs", []):
            visible_ids.append(n)

        wandering_npcs_config = ["Gamer_Boy", "Crypto_Whale", "Lost_Bard", "Town_Guard", "Naughty_Child"]
        for npc_id in wandering_npcs_config:
            npc_pos = stats.town_flags.get(f"pos_{npc_id}", "square")
            if npc_pos == current_room:
                visible_ids.append(npc_id)

        target_id = None
        target_lower = target_name.lower()
        entities = zh_cn.get("interactive_entities", {})
        for ent_id in visible_ids:
            ent_data = entities.get(ent_id, {})
            names = [ent_id.lower(), ent_data.get("name", "").lower()]
            if target_lower in names:
                target_id = ent_id
                break

        if not target_id:
            return zh_cn.get("global", {}).get("interact_not_found", "").format(target=target_name)

        stats.town_flags["current_dialog"] = target_id
        stats.town_flags.pop("market_sub_menu", None)
        self.save_manager.save_stats(user_id, stats)
        return self._render_dialog_window(stats, target_id, zh_cn)

    def handle_dialog_input(self, user_id: str, choice: str) -> str:
        stats = self.save_manager.load_stats(user_id)
        npc_id = stats.town_flags.get("current_dialog")
        zh_cn = self._load_zh_cn()
        if not npc_id:
            return zh_cn.get("global", {}).get("not_in_dialog", "❌ 没有处于交谈状态。")

        entities = zh_cn.get("interactive_entities", {})
        npc_data = entities.get(npc_id, {})
        choice_lower = choice.lower().strip()

        if choice_lower in ("离开", "退出", "返回", "exit", "quit", "q"):
            stats.town_flags.pop("current_dialog", None)
            stats.town_flags.pop("market_sub_menu", None)
            self.save_manager.save_stats(user_id, stats)
            return zh_cn.get("global", {}).get("dialog_exit", "").format(name=npc_data.get("name", npc_id)) + "\n\n" + self.render_current_room(user_id, stats)

        sub_menu = stats.town_flags.get("market_sub_menu")

        if npc_id == "Market_Merchant" and sub_menu == "lock":
            if choice_lower == "1":
                stats.town_flags.pop("market_sub_menu", None)
                self.save_manager.save_stats(user_id, stats)
                return self._render_dialog_window(stats, npc_id, zh_cn)
            target_cid = None
            for cid, cfg in ALL_CARDS.items():
                if cfg.name == choice:
                    target_cid = cid
                    break
            if not target_cid:
                return zh_cn.get("global", {}).get("card_lock_failed_not_found", "").format(name=choice)
            c_obj = ALL_CARDS[target_cid]
            if getattr(c_obj, "rarity", "common") == "legendary":
                return zh_cn.get("global", {}).get("card_lock_failed_legendary", "")
            if stats.gp < 1000:
                return zh_cn.get("global", {}).get("gp_insufficient", "").format(req=1000, owned=stats.gp)

            stats.gp -= 1000
            stats.guaranteed_card = target_cid
            stats.town_flags.pop("market_sub_menu", None)
            self.save_manager.save_stats(user_id, stats)
            res_msg = zh_cn.get("global", {}).get("card_lock_success", "").format(name=choice)
            return res_msg + "\n\n" + self._render_dialog_window(stats, npc_id, zh_cn)

        if npc_id == "Market_Merchant" and sub_menu == "buy":
            shelf = self._get_market_shelf(stats)
            prices = [100, 300, 700]
            if choice_lower == "4":
                stats.town_flags.pop("market_sub_menu", None)
                self.save_manager.save_stats(user_id, stats)
                return self._render_dialog_window(stats, npc_id, zh_cn)
            if choice_lower in ("1", "2", "3"):
                idx = int(choice_lower) - 1
                cid = shelf[idx]
                if not cid:
                    return zh_cn.get("global", {}).get("card_buy_not_on_shelf", "").format(name="")
                price = prices[idx]
                if stats.gp < price:
                    return zh_cn.get("global", {}).get("gp_insufficient", "").format(req=price, owned=stats.gp)
                
                c_name = ALL_CARDS[cid].name if cid in ALL_CARDS else cid
                stats.gp -= price
                stats.purchased_pool.append(cid)
                shelf[idx] = ""
                stats.town_flags["market_shelf"] = shelf
                self.save_manager.save_stats(user_id, stats)
                res_msg = zh_cn.get("global", {}).get("card_buy_success", "").format(price=price, name=c_name)
                return res_msg + "\n\n" + self._render_dialog_window(stats, npc_id, zh_cn)
            return zh_cn.get("global", {}).get("invalid_option", "")

        shop_sub = stats.town_flags.get("shop_sub_menu")
        if npc_id == "Shopkeeper_Jack" and shop_sub == "buy_subclass":
            if choice_lower == "6":
                stats.town_flags.pop("shop_sub_menu", None)
                self.save_manager.save_stats(user_id, stats)
                return self._render_dialog_window(stats, npc_id, zh_cn)
            if choice_lower in ("1", "2", "3", "4", "5"):
                unlocked = getattr(stats, "unlocked_subclasses", [])
                has_gatekey = getattr(stats, "unlocked_gatekey", False)
                subclass_map = {
                    "1": ("时序法师", 2888, False),
                    "2": ("塑能法师", 2888, False),
                    "3": ("秘钥学者", 2888, False),
                    "4": ("门之钥匙", 3000, True),
                    "5": ("神秘物品", 66666, False)
                }
                subclass_name, price, is_gatekey = subclass_map[choice_lower]
                if is_gatekey:
                    if has_gatekey:
                        return zh_cn.get("global", {}).get("already_unlocked_error", "❌ 你已经解锁了【{name}】。").format(name=subclass_name)
                else:
                    if subclass_name in unlocked:
                        return zh_cn.get("global", {}).get("already_unlocked_error", "❌ 你已经解锁了【{name}】。").format(name=subclass_name)
                if stats.gp < price:
                    return zh_cn.get("global", {}).get("gp_insufficient", "").format(req=price, owned=stats.gp)
                stats.gp -= price
                if is_gatekey:
                    stats.unlocked_gatekey = True
                else:
                    stats.unlocked_subclasses.append(subclass_name)
                self.save_manager.save_stats(user_id, stats)
                success_msg = zh_cn.get("global", {}).get("shop_buy_success", "").format(name=subclass_name, price=price)
                return success_msg + "\n\n" + self._render_dialog_window(stats, npc_id, zh_cn)
            return zh_cn.get("global", {}).get("invalid_option", "")

        options_map = {}
        opt_idx = 1
        options_map[str(opt_idx)] = "idle"
        opt_idx += 1

        if npc_id == "Guide_Elder":
            quest_state = stats.town_flags.get("quest_town_tour_state", "unstarted")
            if quest_state == "unstarted":
                options_map[str(opt_idx)] = "quest_accept"
                opt_idx += 1
            elif quest_state == "started":
                visited = stats.town_flags.get("quest_town_tour_visited", [])
                if len(visited) >= 11:
                    options_map[str(opt_idx)] = "quest_complete"
                else:
                    options_map[str(opt_idx)] = "quest_status"
                opt_idx += 1
        elif npc_id == "Bartender_Jack":
            if "wine_glass" in stats.town_inventory and not stats.town_flags.get("jack_gift_given", 0):
                options_map[str(opt_idx)] = "gift_glass"
                opt_idx += 1
        elif npc_id == "Blacksmith_Ironclad":
            if "strange_ore" in stats.town_inventory and not stats.town_flags.get("ironclad_gift_given", 0):
                options_map[str(opt_idx)] = "gift_ore"
                opt_idx += 1
        elif npc_id == "Market_Merchant":
            options_map[str(opt_idx)] = "buy_shelf"
            opt_idx += 1
            options_map[str(opt_idx)] = "lock_card"
            opt_idx += 1
        elif npc_id == "Shopkeeper_Jack":
            options_map[str(opt_idx)] = "buy_subclass"
            opt_idx += 1
        elif npc_id == "Chest":
            options_map = {}
            opt_idx = 1
            if "rusty_key" in stats.town_inventory and not stats.town_flags.get("box_opened", 0):
                options_map[str(opt_idx)] = "open_box"
                opt_idx += 1
        elif npc_id == "Fountain":
            options_map = {}
            opt_idx = 1
            if "lucky_coin" in stats.town_inventory:
                options_map[str(opt_idx)] = "wish"
                opt_idx += 1
        elif npc_id == "West_Gate":
            options_map = {}
            opt_idx = 1
            options_map[str(opt_idx)] = "knock"
            opt_idx += 1
        elif npc_id in ("Dummy", "NoobSlayer99", "xXx_SniperElite_xXx", "pppopipupu"):
            options_map[str(opt_idx)] = "challenge"
            opt_idx += 1

        options_map[str(opt_idx)] = "leave"

        if choice_lower not in options_map:
            return zh_cn.get("global", {}).get("invalid_option", "")

        action = options_map[choice_lower]
        if action == "leave":
            stats.town_flags.pop("current_dialog", None)
            stats.town_flags.pop("market_sub_menu", None)
            self.save_manager.save_stats(user_id, stats)
            return zh_cn.get("global", {}).get("dialog_exit", "").format(name=npc_data.get("name", npc_id)) + "\n\n" + self.render_current_room(user_id, stats)

        elif action == "idle":
            quotes = npc_data.get("idle_talk", [])
            q = random.choice(quotes) if quotes else "..."
            return q + "\n\n" + self._render_dialog_window(stats, npc_id, zh_cn)

        elif action == "quest_accept":
            stats.town_flags["quest_town_tour_state"] = "started"
            stats.town_flags["quest_town_tour_visited"] = ["square"]
            self.save_manager.save_stats(user_id, stats)
            return npc_data.get("quest_accepted", "") + "\n\n" + self._render_dialog_window(stats, npc_id, zh_cn)

        elif action == "quest_status":
            visited = stats.town_flags.get("quest_town_tour_visited", [])
            return npc_data.get("quest_doing", "").format(progress=len(visited)) + "\n\n" + self._render_dialog_window(stats, npc_id, zh_cn)

        elif action == "quest_complete":
            stats.town_flags["quest_town_tour_state"] = "completed"
            stats.gp += 2000
            self.save_manager.save_stats(user_id, stats)
            return npc_data.get("quest_completed_msg", "") + "\n\n" + self._render_dialog_window(stats, npc_id, zh_cn)

        elif action == "gift_glass":
            stats.town_inventory.remove("wine_glass")
            stats.town_flags["jack_gift_given"] = 1
            stats.gp += 150
            self.save_manager.save_stats(user_id, stats)
            return npc_data.get("gift_success", "") + "\n\n" + self._render_dialog_window(stats, npc_id, zh_cn)

        elif action == "gift_ore":
            stats.town_inventory.remove("strange_ore")
            stats.town_flags["ironclad_gift_given"] = 1
            stats.gp += 200
            self.save_manager.save_stats(user_id, stats)
            return npc_data.get("gift_success", "") + "\n\n" + self._render_dialog_window(stats, npc_id, zh_cn)

        elif action == "buy_shelf":
            stats.town_flags["market_sub_menu"] = "buy"
            self.save_manager.save_stats(user_id, stats)
            return self._render_dialog_window(stats, npc_id, zh_cn)

        elif action == "lock_card":
            stats.town_flags["market_sub_menu"] = "lock"
            self.save_manager.save_stats(user_id, stats)
            return self._render_dialog_window(stats, npc_id, zh_cn)

        elif action == "buy_subclass":
            stats.town_flags["shop_sub_menu"] = "buy_subclass"
            self.save_manager.save_stats(user_id, stats)
            return self._render_dialog_window(stats, npc_id, zh_cn)

        elif action == "open_box":
            stats.town_inventory.remove("rusty_key")
            stats.town_flags["box_opened"] = 1
            stats.gp += 300
            stats.guaranteed_card = "discover"
            self.save_manager.save_stats(user_id, stats)
            return npc_data.get("open_success", "") + "\n\n" + self._render_dialog_window(stats, npc_id, zh_cn)

        elif action == "wish":
            stats.town_inventory.remove("lucky_coin")
            effects = ["gp", "card", "hp"]
            choice = random.choice(effects)
            if choice == "gp":
                stats.gp += 200
                res = npc_data.get("wish_success_gp", "")
            elif choice == "card":
                stats.guaranteed_card = "discover"
                res = npc_data.get("wish_success_card", "")
            else:
                stats.town_health_bonus += 5
                res = npc_data.get("wish_success_hp", "")
            self.save_manager.save_stats(user_id, stats)
            return res + "\n\n" + self._render_dialog_window(stats, npc_id, zh_cn)

        elif action == "knock":
            count = stats.town_flags.get("knock_count", 0) + 1
            stats.town_flags["knock_count"] = count
            self.save_manager.save_stats(user_id, stats)
            if count == 3:
                if not stats.town_flags.get("west_gate_bonus_claimed", 0):
                    stats.town_flags["west_gate_bonus_claimed"] = 1
                    stats.gp += 100
                    self.save_manager.save_stats(user_id, stats)
                return npc_data.get("knock_bonus_3", "") + "\n\n" + self._render_dialog_window(stats, npc_id, zh_cn)
            elif count == 10:
                stats.town_flags.pop("current_dialog", None)
                self.save_manager.save_stats(user_id, stats)
                return self.challenge_npc(user_id, "Gate_Guardian")
            return npc_data.get("knock_normal", "").format(count=count) + "\n\n" + self._render_dialog_window(stats, npc_id, zh_cn)

        elif action == "challenge":
            stats.town_flags.pop("current_dialog", None)
            self.save_manager.save_stats(user_id, stats)
            return self.challenge_npc(user_id, npc_id)

        return zh_cn.get("global", {}).get("invalid_option", "")

    def pick_item(self, user_id: str, item_name: str) -> str:
        stats = self.save_manager.load_stats(user_id)
        current_room = stats.town_pos
        room_data = self._load_room_data(current_room)
        items = room_data.get("items", [])
        zh_cn = self._load_zh_cn()

        target_id = None
        target_lower = item_name.lower()
        items_config = zh_cn.get("items", {})
        for key, names in items_config.items():
            if target_lower in [x.lower() for x in names]:
                target_id = key
                break

        if not target_id or target_id not in items:
            return zh_cn.get("global", {}).get("take_not_found", "").format(target=item_name)
            
        if stats.town_flags.get(f"taken_{target_id}", 0):
            return zh_cn.get("global", {}).get("take_already_taken", "").format(target=item_name)

        stats.town_inventory.append(target_id)
        stats.town_flags[f"taken_{target_id}"] = 1
        self.save_manager.save_stats(user_id, stats)
        
        display_name = items_config[target_id][0]
        return zh_cn.get("global", {}).get("take_success", "").format(target=display_name)

    def use_item(self, user_id: str, item_name: str) -> str:
        stats = self.save_manager.load_stats(user_id)
        zh_cn = self._load_zh_cn()

        target_id = None
        target_lower = item_name.lower()
        items_config = zh_cn.get("items", {})
        for key, names in items_config.items():
            if target_lower in [x.lower() for x in names]:
                target_id = key
                break

        if not target_id or target_id not in stats.town_inventory:
            return zh_cn.get("global", {}).get("use_not_found", "").format(target=item_name)

        if target_id == "lost_notebook":
            return zh_cn.get("global", {}).get("lost_notebook_use_desc", "")

        return zh_cn.get("global", {}).get("use_cannot_use", "").format(target=item_name)

    def challenge_npc(self, user_id: str, npc_id: str) -> str:
        stats = self.save_manager.load_stats(user_id)
        zh_cn = self._load_zh_cn()
        npc_name = zh_cn.get("interactive_entities", {}).get(npc_id, {}).get("name", npc_id)

        selected_class = getattr(stats, "selected_class", "法师")
        if selected_class == "战士":
            hp = 80
            max_hp = 80
            deck = ["warrior_strike", "warrior_strike", "warrior_strike", "warrior_strike", "warrior_strike", "warrior_defend", "warrior_defend", "warrior_defend"]
        else:
            hp = 45
            max_hp = 45
            deck = ["fire_bolt", "fire_bolt", "fire_bolt", "fire_bolt", "fire_bolt", "first_aid", "first_aid", "first_aid"]
            
        if stats.guaranteed_card:
            deck.append(stats.guaranteed_card)
        if stats.purchased_pool:
            deck.extend(stats.purchased_pool)
            
        p_state = PlayerState(
            hp=hp,
            max_hp=max_hp,
            shield=0,
            gold=0,
            stage=1,
            deck=deck,
            draw_pile=list(deck),
            discard_pile=[],
            hand=[],
            actions=1,
            bonus_actions=1,
            minions={},
            amulets={},
            abilities=[],
            subclass="",
            selected_class=selected_class
        )

        if npc_id == "Dummy":
            enemy = EnemyState(name="训练假人", hp=200, max_hp=200, shield=0)
        elif npc_id == "NoobSlayer99":
            enemy = EnemyState(name="NoobSlayer99", hp=100, max_hp=100, shield=0)
        elif npc_id == "xXx_SniperElite_xXx":
            enemy = EnemyState(name="xXx_SniperElite_xXx", hp=120, max_hp=120, shield=0)
        elif npc_id == "pppopipupu":
            enemy = EnemyState(name="pppopipupu", hp=1, max_hp=1, shield=0)
        elif npc_id == "Gate_Guardian":
            enemy = EnemyState(name="Gate_Guardian", hp=300, max_hp=300, shield=0)
        else:
            return zh_cn.get("global", {}).get("cannot_challenge_unknown", "").format(name=npc_name)

        random.shuffle(p_state.draw_pile)
        for _ in range(min(5, len(p_state.draw_pile))):
            p_state.hand.append(p_state.draw_pile.pop(0))

        run = GameRun(
            user_id=user_id,
            node_type="battle",
            player=p_state,
            enemies=[enemy],
            node_data={"is_town_combat": True, "npc_name": npc_id}
        )
        self.engine.battle_engine.enemy_controller.roll_enemy_intent(run)
        self.save_manager.save_save(user_id, run)
        
        from ..renderer import GameRenderer
        render_res = GameRenderer.render_game(run)
        if npc_id == "Gate_Guardian":
            return zh_cn.get("global", {}).get("challenge_start_guardian", "").format(render_res=render_res)
        return zh_cn.get("global", {}).get("challenge_start_normal", "").format(name=npc_name, render_res=render_res)
