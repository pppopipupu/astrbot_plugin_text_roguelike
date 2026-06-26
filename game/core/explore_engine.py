import random
from typing import Optional, List, Dict
from ..models.state import GameRun, PlayerState
from ..entities import ALL_CARDS, get_relic_name
from ..entities.events import ALL_EVENTS, get_option_by_action

class ExploreEngine:
    def __init__(self, save_manager, map_engine):
        self.save_manager = save_manager
        self.map_engine = map_engine

    def _init_event_node(self, run: GameRun):
        stage = run.player.stage
        valid_events = [e for e in ALL_EVENTS if getattr(e, "min_stage", 2) <= stage <= getattr(e, "max_stage", 19)]
        if not valid_events:
            valid_events = ALL_EVENTS
        event = random.choice(valid_events)
        run.node_data = {
            "event_id": event.id,
            "description": event.description,
            "options": [{"text": opt.text, "action": opt.action} for opt in event.options]
        }

    def _init_shop_node(self, run: GameRun):
        allowed_colors = ("warrior", "neutral") if getattr(run.player, "selected_class", "法师") == "战士" else ("wizard", "neutral")
        unlocked_new = set()
        stats = None
        if hasattr(self.save_manager, "load_stats"):
            stats = self.save_manager.load_stats(run.user_id)
        from ..entities.cards.market import is_card_available
        card_pool = [
            cid for cid, c in ALL_CARDS.items()
            if c.rarity not in ("legendary", "mythic", "artifact")
            and getattr(c, "color", "") in allowed_colors
            and not cid.startswith("curse_")
            and not cid.startswith("duel_")
            and is_card_available(cid, stats)
        ]
        shop_cards = random.sample(card_pool, 3)
        from ..models.state import check_and_replace_fireball
        shop_cards = [check_and_replace_fireball(run, cid) for cid in shop_cards]
        items = []
        discount = 1.0
        if "gold_compass" in run.player.relics:
            discount *= 0.6
        if "greedy_contract" in run.player.relics:
            discount *= 0.6
            
        for cid in shop_cards:
            card = ALL_CARDS[cid]
            price = 15
            if card.color == "wizard":
                price += 10
            if card.type in ("ability", "minion"):
                price += 5
            price = int(price * discount)
            items.append({
                "type": "card",
                "card_id": cid,
                "price": price,
                "sold": False
            })
            
        available_relics = [rid for rid in ["lucky_coin", "red_bottle", "leather_armor", "whetstone", "ready_pack", "arcane_rune"] if rid not in run.player.relics]
        if available_relics:
            rid = random.choice(available_relics)
            from ..data.relic_data import RELIC_CONFIG
            r_cfg = RELIC_CONFIG[rid]
            r_price = int(r_cfg["price"] * discount)
            items.append({
                "type": "relic",
                "relic_id": rid,
                "price": r_price,
                "sold": False
            })
            
        from ..data.gem_data import GEM_CONFIG
        gem_pool = list(GEM_CONFIG.keys())
        shop_gems = random.sample(gem_pool, min(2, len(gem_pool)))
        for gid in shop_gems:
            g_cfg = GEM_CONFIG[gid]
            g_price = int(g_cfg["price"] * discount)
            items.append({
                "type": "gem",
                "gem_id": gid,
                "price": g_price,
                "sold": False
            })

        items.append({
            "type": "remove",
            "price": int(30 * discount),
            "sold": False
        })
        items.append({
            "type": "upgrade",
            "price": int(30 * discount),
            "sold": False
        })
        items.append({
            "type": "leave",
            "price": 0,
            "sold": False
        })
        run.node_data = {"items": items}

    def _init_treasure_node(self, run: GameRun):
        run.node_data = {
            "state": "pending_remove",
            "text": "你面前放着一个巨大的【古老宝箱】。宝箱上缠绕着锁链，上面刻着契约符文：‘欲获秘宝，必献此身部分知识。’\n请选择你想要献祭（移除）的卡牌序号（使用 选择 <卡牌序号>，可输入 /rogue 牌组 查看）："
        }

    def choose_option(self, run: GameRun, option_idx: int) -> str:
        p = run.player
        if run.node_type == "start_ancient":
            options = run.node_data.get("options", [])
            if option_idx < 1 or option_idx > len(options):
                return "❌ 无效的选择序号。"
            chosen = options[option_idx - 1]
            
            rid = chosen["relic"]
            p.relics.append(rid)
            if rid == "mark_of_fury":
                p.max_hp = max(5, p.max_hp - 5)
                p.hp = min(p.hp, p.max_hp)
            elif rid == "vampiric_touch":
                p.max_hp = max(5, p.max_hp - 4)
                p.hp = min(p.hp, p.max_hp)
            elif rid == "glacier_armor":
                p.max_hp = max(5, p.max_hp - 6)
                p.hp = min(p.hp, p.max_hp)
            
            bonus_str = f"获得了先古遗物：【{get_relic_name(rid)}】"
            if chosen["type"] == "contract":
                cid = chosen["card"]
                p.deck.append(cid)
                bonus_str += f" ➕ 先古卡牌：【{ALL_CARDS[cid].name}】"
                
            self.map_engine.enter_next_stage(run)
            self.save_manager.save_save(run.user_id, run)
            return f"🌌 契约达成！你{bonus_str}。冒险正式开始！"

        elif run.node_type == "ancient":
            options = run.node_data.get("options", [])
            if option_idx < 1 or option_idx > len(options):
                return "❌ 无效的选择序号。"
            chosen = options[option_idx - 1]
            
            cid = chosen["card"]
            rid = chosen["relic"]
            p.deck.append(cid)
            p.relics.append(rid)
            
            self.map_engine.enter_next_stage(run)
            self.save_manager.save_save(run.user_id, run)
            return f"🌟 先古赐福！你获得了传奇卡牌【{ALL_CARDS[cid].name}】与珍奇遗物【{get_relic_name(rid)}】！"

        elif run.node_type == "treasure":
            if run.node_data.get("state") == "pending_remove":
                counts = {}
                for c_id in p.deck:
                    counts[c_id] = counts.get(c_id, 0) + 1
                sorted_items = sorted(counts.items())
                if option_idx < 1 or option_idx > len(sorted_items):
                    return "❌ 无效的卡牌序号。"
                cid = sorted_items[option_idx - 1][0]
                removed_name = ALL_CARDS[cid].name
                p.deck.remove(cid)
                
                gold_gain = random.randint(20, 40)
                p.gold += gold_gain
                
                relics_pool = ["lucky_coin", "red_bottle", "leather_armor", "whetstone", "ready_pack", "arcane_rune", "ancient_eye", "gold_compass", "dragon_blood", "energy_core", "heavy_armor"]
                available_relics = [r for r in relics_pool if r not in p.relics]
                got_relic = ""
                if available_relics:
                    got_relic = random.choice(available_relics)
                    p.relics.append(got_relic)
                    if got_relic == "red_bottle":
                        p.max_hp += 5
                        p.hp += 5
                        
                allowed_colors = ("warrior", "neutral") if getattr(p, "selected_class", "法师") == "战士" else ("wizard", "neutral")
                stats = None
                if hasattr(self.save_manager, "load_stats"):
                    stats = self.save_manager.load_stats(run.user_id)
                from ..entities.cards.market import is_card_available
                card_pool = [
                    cid for cid, c in ALL_CARDS.items()
                    if c.rarity == "epic"
                    and getattr(c, "color", "") in allowed_colors
                    and not cid.startswith("curse_")
                    and not cid.startswith("duel_")
                    and is_card_available(cid, stats)
                ]
                reward_cards = random.sample(card_pool, 3) if len(card_pool) >= 3 else card_pool
                from ..models.state import check_and_replace_fireball
                reward_cards = [check_and_replace_fireball(run, cid) for cid in reward_cards]
                
                relic_msg = f"与遗物【{get_relic_name(got_relic)}】" if got_relic else ""
                
                from ..data.gem_data import GEM_CONFIG
                gift_gem_id = random.choice(list(GEM_CONFIG.keys()))
                gem_name = GEM_CONFIG[gift_gem_id]["name"]
                
                relic_msg = f"与遗物【{get_relic_name(got_relic)}】" if got_relic else ""
                
                next_node_data = {
                    "title": "古老宝箱：请选择你的秘宝",
                    "desc": f"🔓 宝箱上的锁链崩解脱落！你成功献祭了【{removed_name}】。\n宝箱缓缓开启，你获得了 🪙 {gold_gain}金币{relic_msg}，以及附赠的宝石【{gem_name}】！同时宝箱中露出了三张珍奇卡牌：",
                    "cards": reward_cards
                }
                
                self.start_gem_insert_flow(run, gift_gem_id, "card_select", next_node_data)
                return "宝箱开启成功。"

        elif run.node_type == "reward":
            if run.node_data.get("no_reward"):
                if option_idx != 1:
                    return "❌ 无效的选择序号。你只有选择 1 继续前进。"
                pending_gems = run.node_data.get("pending_gems", [])
                if pending_gems:
                    gem_id = pending_gems.pop(0)
                    run.node_data["pending_gems"] = pending_gems
                    self.start_gem_insert_flow(run, gem_id, "reward", {"no_reward": True, "pending_gems": pending_gems})
                    self.save_manager.save_save(run.user_id, run)
                    from ..entities import get_gem_name
                    return f"你开启了战斗中额外收获的宝石【{get_gem_name(gem_id)}】的强制镶嵌流程。"
                self.map_engine.enter_next_stage(run)
                self.save_manager.save_save(run.user_id, run)
                return "你确认了异界脱逃，空手离开了这片战场，开启下一关。"
            cards = run.node_data.get("cards", [])
            skip_idx = len(cards) + 1
            if option_idx < 1 or option_idx > skip_idx:
                return "❌ 无效的选择序号。"
            if option_idx == skip_idx:
                p.gold += 15
                msg = "获得了 15 金币。"
            else:
                cid = cards[option_idx - 1]
                card = ALL_CARDS.get(cid)
                p.deck.append(cid)
                msg = f"已将卡牌【{card.name}】加入你的卡组。"
            pending_gems = run.node_data.get("pending_gems", [])
            if pending_gems:
                gem_id = pending_gems.pop(0)
                run.node_data["pending_gems"] = pending_gems
                self.start_gem_insert_flow(run, gem_id, "reward", {"no_reward": True, "pending_gems": pending_gems})
                self.save_manager.save_save(run.user_id, run)
                from ..entities import get_gem_name
                return f"{msg}\n💎 另外，你开启了战斗中额外收获的宝石【{get_gem_name(gem_id)}】的强制镶嵌流程。"
            self.map_engine.enter_next_stage(run)
            self.save_manager.save_save(run.user_id, run)
            return f"{msg}开启下一关。"

        elif run.node_type == "card_select":
            cards = run.node_data.get("cards", [])
            skip_idx = len(cards) + 1
            if option_idx < 1 or option_idx > skip_idx:
                return "❌ 无效的选择序号。"
            if option_idx == skip_idx:
                self.map_engine.enter_next_stage(run)
                self.save_manager.save_save(run.user_id, run)
                return "已跳过卡牌选择，开启下一关。"
            else:
                cid = cards[option_idx - 1]
                card = ALL_CARDS.get(cid)
                p.deck.append(cid)
                self.map_engine.enter_next_stage(run)
                self.save_manager.save_save(run.user_id, run)
                return f"已将卡牌【{card.name}】加入你的卡组，开启下一关。"

        elif run.node_type == "rest":
            if option_idx not in (1, 2, 3, 4):
                return "❌ 无效的选择序号。"
            if option_idx == 1:
                heal = p.max_hp // 2
                p.hp = min(p.max_hp, p.hp + heal)
                self.map_engine.enter_next_stage(run)
                self.save_manager.save_save(run.user_id, run)
                return f"你感到精力充沛，恢复了 {heal} 点生命值，开启下一关。"
            elif option_idx == 2:
                class_color = "warrior" if getattr(p, "selected_class", "法师") == "战士" else "wizard"
                stats = None
                if hasattr(self.save_manager, "load_stats"):
                    stats = self.save_manager.load_stats(run.user_id)
                from ..entities.cards.market import is_card_available
                class_cards = [
                    cid for cid, c in ALL_CARDS.items()
                    if c.color == class_color
                    and c.type == "spell"
                    and c.rarity not in ("legendary", "mythic", "artifact")
                    and not cid.startswith("curse_")
                    and not cid.startswith("duel_")
                    and is_card_available(cid, stats)
                ]
                reward_cards = random.sample(class_cards, 3) if len(class_cards) >= 3 else class_cards
                from ..models.state import check_and_replace_fireball
                reward_cards = [check_and_replace_fireball(run, cid) for cid in reward_cards]
                run.node_type = "card_select"
                run.node_data = {
                    "title": "冥想感悟：请选择你想领悟的卡牌",
                    "desc": "你面对篝火静静冥想，脑海中浮现出了三道奥术灵光：",
                    "cards": reward_cards
                }
                self.save_manager.save_save(run.user_id, run)
                return "你开始冥想，寻找领悟。"
            elif option_idx == 4:
                run.node_data["upgrade_source"] = "rest"
                return "UPGRADE_FLOW"
            else:
                self.map_engine.enter_next_stage(run)
                self.save_manager.save_save(run.user_id, run)
                return "你整理了行囊直接出发，开启下一关。"

        elif run.node_type == "event":
            options = run.node_data.get("options", [])
            if option_idx < 1 or option_idx > len(options):
                return "❌ 无效的选择序号。"
            opt = options[option_idx - 1]
            act = opt.get("action")
            
            option_executor = get_option_by_action(act)
            if option_executor:
                return option_executor.execute(run, self.map_engine)
            else:
                self.map_engine.enter_next_stage(run)
                self.save_manager.save_save(run.user_id, run)
                return "你决定不节外生枝，继续赶路。已前往下一关。"

        elif run.node_type == "shop":
            items = run.node_data.get("items", [])
            if option_idx < 1 or option_idx > len(items):
                return "❌ 无效的商品序号。"
            item = items[option_idx - 1]
            if item.get("sold"):
                return "❌ 该商品已经售罄。"
            price = item.get("price")
            if p.gold < price:
                return f"❌ 你的金币不足，该商品售价为 {price} 金币（当前 {p.gold}）。"
            itype = item.get("type")
            if itype == "card":
                p.gold -= price
                cid = item.get("card_id")
                p.deck.append(cid)
                item["sold"] = True
                self.save_manager.save_save(run.user_id, run)
                return f"购买成功！已将【{ALL_CARDS[cid].name}】加入你的卡组。"
            elif itype == "relic":
                p.gold -= price
                rid = item.get("relic_id")
                p.relics.append(rid)
                item["sold"] = True
                if rid == "red_bottle":
                    p.max_hp += 5
                    p.hp += 5
                self.save_manager.save_save(run.user_id, run)
                return f"购买成功！获得了遗物【{get_relic_name(rid)}】。"
            elif itype == "gem":
                p.gold -= price
                gem_id = item.get("gem_id")
                item["sold"] = True
                shop_node_data = {"items": items}
                res = self.start_gem_insert_flow(run, gem_id, "shop", shop_node_data)
                return f"购买成功！{res}"
            elif itype == "remove":
                return "REMOVE_FLOW"
            elif itype == "upgrade":
                run.node_data["upgrade_price"] = price
                run.node_data["upgrade_source"] = "shop"
                return "UPGRADE_FLOW"
            elif itype == "leave":
                self.map_engine.enter_next_stage(run)
                self.save_manager.save_save(run.user_id, run)
                return "你离开了商店，继续冒险。已开启下一关。"
        return "未知的操作。"

    def remove_card_from_deck(self, run: GameRun, deck_idx: int) -> str:
        p = run.player
        counts = {}
        for c in p.deck:
            counts[c] = counts.get(c, 0) + 1
        sorted_items = sorted(counts.items(), key=lambda item: (item[0].id, item[0].upgraded))
        if deck_idx < 1 or deck_idx > len(sorted_items):
            return "❌ 无效的卡牌序号。"
        c_state = sorted_items[deck_idx - 1][0]
        removed_name = ALL_CARDS[c_state].name
        p.deck.remove(c_state)
        
        discount = 1.0
        if "gold_compass" in p.relics:
            discount *= 0.6
        if "greedy_contract" in p.relics:
            discount *= 0.6
        p.gold -= int(30 * discount)
        
        items = run.node_data.get("items", [])
        for item in items:
            if item.get("type") == "remove":
                item["sold"] = True
        run.node_data["pending_remove"] = False
        self.save_manager.save_save(run.user_id, run)
        return f"已成功从你的卡组中移除了【{removed_name}】。"

    def upgrade_card_in_deck(self, run: GameRun, deck_idx: int) -> str:
        p = run.player
        counts = {}
        for c in p.deck:
            counts[c] = counts.get(c, 0) + 1
        sorted_items = sorted(counts.items(), key=lambda item: (item[0].id, item[0].upgraded))
        
        if deck_idx < 1 or deck_idx > len(sorted_items):
            return "❌ 无效的卡牌序号。"
        
        c_state = sorted_items[deck_idx - 1][0]
        if c_state.upgraded:
            return "❌ 该卡牌已经升级过了，无法重复升级。"
            
        from ..data.card_upgrade_data import CARD_UPGRADE_CONFIG
        if c_state.id not in CARD_UPGRADE_CONFIG:
            return "❌ 该卡牌无法被升级。"
            
        import copy
        new_state = copy.copy(c_state)
        new_state.upgraded = True
        p.deck.remove(c_state)
        p.deck.append(new_state)
        
        source = run.node_data.get("upgrade_source", "rest")
        run.node_data["pending_upgrade"] = False
        
        old_card_name = ALL_CARDS[c_state].name
        new_card_name = ALL_CARDS[new_state].name
        
        if source in ("rest", "event"):
            self.map_engine.enter_next_stage(run)
            self.save_manager.save_save(run.user_id, run)
            return f"🔨 升级成功！你的【{old_card_name}】已成功升级为强力变体【{new_card_name}】。你离开此地继续赶路，开启下一关。"
        else:
            items = run.node_data.get("items", [])
            for item in items:
                if item.get("type") == "upgrade":
                    item["sold"] = True
            price = run.node_data.get("upgrade_price", 30)
            p.gold -= price
            self.save_manager.save_save(run.user_id, run)
            return f"🔨 升级成功！已将【{old_card_name}】永久升级为强力变体【{new_card_name}】。"

    def start_gem_insert_flow(self, run: GameRun, gem_id: str, next_node_type: str, next_node_data: dict) -> str:
        from ..data.gem_data import GEM_CONFIG
        gem_name = GEM_CONFIG[gem_id]["name"]
        gem_desc = GEM_CONFIG[gem_id]["desc"]
        run.node_type = "gem_insert"
        run.node_data = {
            "pending_gem": gem_id,
            "next_node_type": next_node_type,
            "next_node_data": next_node_data,
            "text": f"💎 你获得了宝石：【{gem_name}】（{gem_desc}）。\n当前无法将宝石放入行囊，必须立即进行强制镶嵌！\n请选择你要镶嵌的卡牌序号（输入 c <卡牌序号> 镶嵌，可输入 c 0 或是 c 取消 选择跳过镶嵌）："
        }
        self.save_manager.save_save(run.user_id, run)
        return f"你获得了宝石：【{gem_name}】。"

    def gem_insert_cancel(self, run: GameRun) -> str:
        next_type = run.node_data["next_node_type"]
        next_data = run.node_data["next_node_data"]
        run.node_type = next_type
        run.node_data = next_data
        self.save_manager.save_save(run.user_id, run)
        return "你决定不进行镶嵌，丢弃了该宝石。继续前进。"

    def gem_insert_choose(self, run: GameRun, deck_idx: int) -> str:
        p = run.player
        counts = {}
        for c_id in p.deck:
            counts[c_id] = counts.get(c_id, 0) + 1
        sorted_items = sorted(counts.items())
        if deck_idx < 1 or deck_idx > len(sorted_items):
            return "❌ 无效的卡牌序号。"
        cid = sorted_items[deck_idx - 1][0]
        from ..entities.cards.base import ALL_CARDS
        card_obj = ALL_CARDS.get(cid)
        if not card_obj:
            return "❌ 卡牌不存在。"
        from ..models.state import ensure_card_state
        cid = ensure_card_state(cid)
        old_gems = list(cid.gems)
        max_slots = card_obj.get_gem_slots_count()
        if len(old_gems) >= max_slots:
            return f"❌ 该卡牌的宝石插槽已满（当前槽位数：{max_slots}，已镶嵌：{len(old_gems)}），无法继续镶嵌。"
        gem_id = run.node_data["pending_gem"]
        from ..data.gem_data import GEM_CONFIG
        gem_name = GEM_CONFIG[gem_id]["name"]
        p.deck.remove(cid)
        import copy
        new_card_state = copy.copy(cid)
        new_card_state.gems = old_gems + [gem_id]
        p.deck.append(new_card_state)
        next_type = run.node_data["next_node_type"]
        next_data = run.node_data["next_node_data"]
        run.node_type = next_type
        run.node_data = next_data
        self.save_manager.save_save(run.user_id, run)
        return f"💎 镶嵌成功！已将【{gem_name}】成功镶嵌到了卡牌【{card_obj.name}】上。"
