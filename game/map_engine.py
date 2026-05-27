import random
from typing import Optional, List, Dict
from .models import GameRun, PlayerState, EnemyState, MinionState, AmuletState, Card

class MapEngine:
    def __init__(self, save_manager, battle_engine):
        self.save_manager = save_manager
        self.battle_engine = battle_engine

    def enter_next_stage(self, run: GameRun):
        p = run.player
        p.stage += 1
        p.shield = 0
        p.minions.clear()
        p.amulets.clear()
        p.abilities.clear()
        run.enemies.clear()
        run.node_data.clear()

        # 幸运硬币被动结算
        if "lucky_coin" in p.relics:
            p.gold += 5

        if p.stage == 1:
            run.node_type = "start_ancient"
            debuffs = ["rust_shackle", "fool_oath", "wither_seed"]
            legends = ["doomsday_judgment", "time_warp", "magic_network"]
            random.shuffle(debuffs)
            random.shuffle(legends)
            options = [
                {"type": "double", "relic": "mark_of_fury"},
                {"type": "double", "relic": "greedy_contract"},
                {"type": "double", "relic": "mask_of_void"},
                {"type": "contract", "relic": debuffs[0], "card": legends[0]},
                {"type": "contract", "relic": debuffs[1], "card": legends[1]},
                {"type": "contract", "relic": debuffs[2], "card": legends[2]}
            ]
            run.node_data = {"options": options}
        elif p.stage == 11:
            run.node_type = "ancient"
            legends_pool = ["doomsday_judgment", "time_warp", "magic_network"]
            relics_pool = ["ancient_eye", "gold_compass", "dragon_blood", "energy_core", "heavy_armor"]
            available_relics = [r for r in relics_pool if r not in p.relics]
            if not available_relics:
                available_relics = relics_pool.copy()
            random.shuffle(legends_pool)
            random.shuffle(available_relics)
            options = []
            for i in range(3):
                options.append({
                    "card": legends_pool[i % len(legends_pool)],
                    "relic": available_relics[i % len(available_relics)]
                })
            run.node_data = {"options": options}
        elif p.stage == 20:
            run.node_type = "battle"
            self.battle_engine._init_battle_node(run, "boss")
        else:
            if p.stage == 2:
                self._generate_map_network(run, 2, 10)
            elif p.stage == 12:
                self._generate_map_network(run, 12, 20)
            
            run.node_type = "map_select"
            nodes_layer = run.map_data.get("nodes", {}).get(str(p.stage), [])
            curr_id = run.map_data.get("current_node_id")
            
            opts = []
            if not curr_id:
                opts = nodes_layer
            else:
                nodes_dict = {}
                for layer in run.map_data.get("nodes", {}).values():
                    for node in layer:
                        nodes_dict[node["id"]] = node
                curr_node = nodes_dict.get(curr_id)
                if curr_node:
                    next_ids = curr_node.get("next", [])
                    opts = [nodes_dict[nid] for nid in next_ids if nid in nodes_dict]
            
            if not opts and nodes_layer:
                opts = nodes_layer
                
            options_data = []
            desc_map = {
                "battle": "遭遇战 (遇到 1~3 个普通的敌人)",
                "elite": "精英战 (遭遇强力敌人，获胜金币更多)",
                "event": "神秘事件 (可能获得宝物或遭遇危险)",
                "shop": "奇妙商店 (购买强力卡牌、遗物或移除卡牌)",
                "rest": "篝火营地 (恢复生命值或冥想领悟卡牌)",
                "treasure": "古老宝箱 (献祭卡牌以获取稀有遗物及宝藏)",
                "boss": "首领战 (击败守关的首领)"
            }
            emoji_map = {
                "battle": "遭遇战",
                "elite": "精英战",
                "event": "神秘事件",
                "shop": "奇妙商店",
                "rest": "篝火营地",
                "treasure": "古老宝箱",
                "boss": "首领战"
            }
            for o in opts:
                options_data.append({
                    "node_id": o["id"],
                    "node_type": o["type"],
                    "desc": f"{emoji_map.get(o['type'], o['type'])} ({desc_map.get(o['type'], o['type'])})"
                })
            run.node_data = {"options": options_data}

    def _generate_map_network(self, run: GameRun, start_s: int, end_s: int):
        nodes = {}
        for s in range(start_s, end_s + 1):
            nodes[str(s)] = []
        
        types_pool = ["battle", "event", "shop", "elite", "rest"]
        for s in range(start_s, end_s + 1):
            s_str = str(s)
            if s in (5, 15):
                nodes[s_str].append({
                    "id": f"{s}_0",
                    "type": "treasure",
                    "next": []
                })
            elif s in (10, 20):
                nodes[s_str].append({
                    "id": f"{s}_0",
                    "type": "boss",
                    "next": []
                })
            else:
                width = random.randint(2, 3)
                for i in range(width):
                    ntype = random.choice(types_pool)
                    nodes[s_str].append({
                        "id": f"{s}_{i}",
                        "type": ntype,
                        "next": []
                    })
        
        for s in range(start_s, end_s):
            curr_layer = nodes[str(s)]
            next_layer = nodes[str(s+1)]
            
            if len(next_layer) == 1:
                for cn in curr_layer:
                    cn["next"] = [next_layer[0]["id"]]
            elif len(curr_layer) == 1:
                curr_layer[0]["next"] = [nn["id"] for nn in next_layer]
            else:
                for i, cn in enumerate(curr_layer):
                    allowed = []
                    for offset in (-1, 0, 1):
                        idx = i + offset
                        if 0 <= idx < len(next_layer):
                            allowed.append(next_layer[idx]["id"])
                    cn["next"] = random.sample(allowed, min(len(allowed), random.randint(1, 2)))
                
                for nn in next_layer:
                    nn_id = nn["id"]
                    has_pre = False
                    for cn in curr_layer:
                        if nn_id in cn["next"]:
                            has_pre = True
                            break
                    if not has_pre:
                        best_i = min(len(curr_layer)-1, int(nn_id.split("_")[1]))
                        curr_layer[best_i]["next"].append(nn_id)
                        curr_layer[best_i]["next"] = list(set(curr_layer[best_i]["next"]))
                        
        run.map_data["nodes"] = nodes
        run.map_data["current_node_id"] = None

    def choose_map_node(self, run: GameRun, option_idx: int) -> str:
        options = run.node_data.get("options", [])
        if option_idx < 1 or option_idx > len(options):
            return "❌ 无效的分支序号。"
        chosen = options[option_idx - 1]
        node_type = chosen["node_type"]
        node_id = chosen["node_id"]
        
        run.node_type = node_type
        run.map_data["current_node_id"] = node_id
        run.node_data.clear()
        
        if node_type == "battle" or node_type == "boss":
            diff = "boss" if node_type == "boss" else "normal"
            self.battle_engine._init_battle_node(run, diff)
            name = run.enemies[0].name if run.enemies else "未知"
            num_enemies = len(run.enemies)
            self.save_manager.save_save(run.user_id, run)
            return f"你选择前往【{chosen['desc']}】。前方出现了 {num_enemies} 个敌人，领头的是【{name}】！进入战斗。"
        elif node_type == "elite":
            self.battle_engine._init_battle_node(run, "elite")
            name = run.enemies[0].name if run.enemies else "未知"
            num_enemies = len(run.enemies)
            self.save_manager.save_save(run.user_id, run)
            return f"你选择前往【{chosen['desc']}】。前方出现了 {num_enemies} 个强力精英，领头的是【{name}】！进入战斗。"
        elif node_type == "event":
            self._init_event_node(run)
            self.save_manager.save_save(run.user_id, run)
            return f"你选择前往【{chosen['desc']}】。你遇到了一个神秘事件..."
        elif node_type == "shop":
            self._init_shop_node(run)
            self.save_manager.save_save(run.user_id, run)
            return f"你选择前往【{chosen['desc']}】。你来到了奇妙商店，店主热情地向你招手。"
        elif node_type == "rest":
            self.save_manager.save_save(run.user_id, run)
            return f"你选择前往【{chosen['desc']}】。篝火在噼啪作响，你可以在此整顿休息。"
        elif node_type == "treasure":
            self._init_treasure_node(run)
            self.save_manager.save_save(run.user_id, run)
            return f"你选择前往【{chosen['desc']}】。你来到了古老宝箱前。"
        return "❌ 未知节点类型。"

    def _init_event_node(self, run: GameRun):
        from .event_impl import ALL_EVENTS
        event = random.choice(ALL_EVENTS)
        run.node_data = {
            "event_id": event.id,
            "description": event.description,
            "options": [{"text": opt.text, "action": opt.action} for opt in event.options]
        }

    def _init_shop_node(self, run: GameRun):
        from .card_impl import ALL_CARDS
        card_pool = [cid for cid, c in ALL_CARDS.items() if c.rarity != "legendary"]
        shop_cards = random.sample(card_pool, 3)
        items = []
        discount = 1.0
        if "gold_compass" in run.player.relics:
            discount *= 0.6
        if "greedy_contract" in run.player.relics:
            discount *= 0.8
            
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
            from .data.relic_data import RELIC_CONFIG
            r_cfg = RELIC_CONFIG[rid]
            r_price = int(r_cfg["price"] * discount)
            items.append({
                "type": "relic",
                "relic_id": rid,
                "price": r_price,
                "sold": False
            })
            
        items.append({
            "type": "remove",
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
        if run.node_type == "battle":
            return "❌ 战斗中无法使用选择命令。"
        if run.node_type == "map_select":
            return self.choose_map_node(run, option_idx)

        if run.node_type == "start_ancient":
            options = run.node_data.get("options", [])
            if option_idx < 1 or option_idx > len(options):
                return "❌ 无效的选择序号。"
            chosen = options[option_idx - 1]
            from .relic_impl import get_relic_name
            from .card_impl import ALL_CARDS
            
            rid = chosen["relic"]
            p.relics.append(rid)
            if rid == "mark_of_fury":
                p.max_hp = max(5, p.max_hp - 5)
                p.hp = min(p.hp, p.max_hp)
            
            bonus_str = f"获得了先古契约遗物：【{get_relic_name(rid)}】"
            if chosen["type"] == "contract":
                cid = chosen["card"]
                p.deck.append(cid)
                bonus_str += f" ➕ 传奇卡牌：【{ALL_CARDS[cid].name}】"
                
            self.enter_next_stage(run)
            self.save_manager.save_save(run.user_id, run)
            return f"🌌 契约达成！你{bonus_str}。冒险正式开始！"

        elif run.node_type == "ancient":
            options = run.node_data.get("options", [])
            if option_idx < 1 or option_idx > len(options):
                return "❌ 无效的选择序号。"
            chosen = options[option_idx - 1]
            from .relic_impl import get_relic_name
            from .card_impl import ALL_CARDS
            
            cid = chosen["card"]
            rid = chosen["relic"]
            p.deck.append(cid)
            p.relics.append(rid)
            
            self.enter_next_stage(run)
            self.save_manager.save_save(run.user_id, run)
            return f"🌟 先古赐福！你获得了传奇卡牌【{ALL_CARDS[cid].name}】与珍奇遗物【{get_relic_name(rid)}】！"

        elif run.node_type == "treasure":
            if run.node_data.get("state") == "pending_remove":
                if option_idx < 1 or option_idx > len(p.deck):
                    return "❌ 无效的卡牌序号。"
                from .card_impl import ALL_CARDS
                removed_name = ALL_CARDS[p.deck[option_idx - 1]].name
                p.deck.pop(option_idx - 1)
                
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
                        
                card_pool = [cid for cid, c in ALL_CARDS.items() if c.rarity == "epic"]
                got_card = random.choice(card_pool) if card_pool else "fireball"
                p.deck.append(got_card)
                
                from .relic_impl import get_relic_name
                relic_msg = f"与遗物【{get_relic_name(got_relic)}】" if got_relic else ""
                
                run.node_data = {
                    "state": "opened",
                    "text": f"🔓 宝箱上的锁链崩解脱落！你成功献祭了【{removed_name}】。\n宝箱缓缓开启，你获得了 🪙 {gold_gain}金币、一张珍奇卡牌【{ALL_CARDS[got_card].name}】{relic_msg}！"
                }
                self.save_manager.save_save(run.user_id, run)
                return "宝箱开启成功。"
            elif run.node_data.get("state") == "opened":
                if option_idx == 1:
                    self.enter_next_stage(run)
                    self.save_manager.save_save(run.user_id, run)
                    return "你整理了行装离开宝箱房，开启下一关。"
                return "❌ 无效的选择序号。"

        elif run.node_type == "reward":
            cards = run.node_data.get("cards", [])
            skip_idx = len(cards) + 1
            if option_idx < 1 or option_idx > skip_idx:
                return "❌ 无效的选择序号。"
            if option_idx == skip_idx:
                p.gold += 15
                self.enter_next_stage(run)
                self.save_manager.save_save(run.user_id, run)
                return "获得了 15 金币，开启下一关。"
            else:
                cid = cards[option_idx - 1]
                from .card_impl import ALL_CARDS
                card = ALL_CARDS.get(cid)
                p.deck.append(cid)
                self.enter_next_stage(run)
                self.save_manager.save_save(run.user_id, run)
                return f"已将卡牌【{card.name}】加入你的卡组，开启下一关。"

        elif run.node_type == "rest":
            if option_idx not in (1, 2, 3):
                return "❌ 无效的选择序号。"
            if option_idx == 1:
                heal = p.max_hp // 2
                p.hp = min(p.max_hp, p.hp + heal)
                self.enter_next_stage(run)
                self.save_manager.save_save(run.user_id, run)
                return f"你感到精力充沛，恢复了 {heal} 点生命值，开启下一关。"
            elif option_idx == 2:
                from .card_impl import ALL_CARDS
                wizards = [cid for cid, c in ALL_CARDS.items() if c.color == "wizard" and c.type == "spell" and c.rarity != "legendary"]
                cid = random.choice(wizards)
                p.deck.append(cid)
                self.enter_next_stage(run)
                self.save_manager.save_save(run.user_id, run)
                return f"你通过静坐冥想，领悟了【{ALL_CARDS[cid].name}】并加入卡组，开启下一关。"
            else:
                self.enter_next_stage(run)
                self.save_manager.save_save(run.user_id, run)
                return "你整理了行囊直接出发，开启下一关。"

        elif run.node_type == "event":
            options = run.node_data.get("options", [])
            if option_idx < 1 or option_idx > len(options):
                return "❌ 无效的选择序号。"
            opt = options[option_idx - 1]
            act = opt.get("action")
            
            from .event_impl import get_option_by_action
            option_executor = get_option_by_action(act)
            if option_executor:
                return option_executor.execute(run, self)
            else:
                self.enter_next_stage(run)
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
                from .card_impl import ALL_CARDS
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
                from .relic_impl import get_relic_name
                return f"购买成功！获得了遗物【{get_relic_name(rid)}】。"
            elif itype == "remove":
                return "REMOVE_FLOW"
            elif itype == "leave":
                self.enter_next_stage(run)
                self.save_manager.save_save(run.user_id, run)
                return "你离开了商店，继续冒险。已开启下一关。"
        return "未知的操作。"

    def remove_card_from_deck(self, run: GameRun, deck_idx: int) -> str:
        p = run.player
        if deck_idx < 1 or deck_idx > len(p.deck):
            return "❌ 无效的卡牌序号。"
        from .card_impl import ALL_CARDS
        removed_name = ALL_CARDS[p.deck[deck_idx - 1]].name
        p.deck.pop(deck_idx - 1)
        
        discount = 1.0
        if "gold_compass" in p.relics:
            discount *= 0.6
        if "greedy_contract" in p.relics:
            discount *= 0.8
        p.gold -= int(30 * discount)
        
        items = run.node_data.get("items", [])
        for item in items:
            if item.get("type") == "remove":
                item["sold"] = True
        self.save_manager.save_save(run.user_id, run)
        return f"已成功从你的卡组中移除了【{removed_name}】。"
