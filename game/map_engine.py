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

        if p.stage == 10:
            run.node_type = "battle"
            self.battle_engine._init_battle_node(run, "boss")
        else:
            run.node_type = "map_select"
            opts = []
            if p.stage == 1:
                opts = ["battle", "battle"]
            elif p.stage in (3, 6, 9):
                opts = ["rest", random.choice(["battle", "event", "elite"])]
            elif p.stage in (4, 7):
                opts = ["shop", random.choice(["battle", "event", "elite"])]
            else:
                pool = ["battle", "event", "shop", "elite"]
                num_opts = random.randint(2, 3)
                opts = random.sample(pool, num_opts)
            
            options_data = []
            desc_map = {
                "battle": "遭遇战 (遇到 1~3 个普通的敌人)",
                "elite": "精英战 (遭遇强力敌人，获胜金币更多)",
                "event": "神秘事件 (可能获得宝物或遭遇危险)",
                "shop": "奇妙商店 (购买强力卡牌或移除卡牌)",
                "rest": "篝火营地 (恢复生命值或冥想领悟卡牌)"
            }
            emoji_map = {
                "battle": "遭遇战",
                "elite": "精英战",
                "event": "神秘事件",
                "shop": "奇妙商店",
                "rest": "篝火营地"
            }
            for o in opts:
                options_data.append({
                    "node_type": o,
                    "desc": f"{emoji_map[o]} ({desc_map[o]})"
                })
            run.node_data = {"options": options_data}

    def choose_map_node(self, run: GameRun, option_idx: int) -> str:
        options = run.node_data.get("options", [])
        if option_idx < 1 or option_idx > len(options):
            return "❌ 无效的分支序号。"
        chosen = options[option_idx - 1]
        node_type = chosen["node_type"]
        run.node_type = node_type
        run.node_data.clear()
        
        if node_type == "battle":
            self.battle_engine._init_battle_node(run, "normal")
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
        card_pool = list(ALL_CARDS.keys())
        shop_cards = random.sample(card_pool, 3)
        items = []
        for cid in shop_cards:
            card = ALL_CARDS[cid]
            price = 15
            if card.color == "wizard":
                price += 10
            if card.type in ("ability", "minion"):
                price += 5
            items.append({
                "type": "card",
                "card_id": cid,
                "price": price,
                "sold": False
            })
        items.append({
            "type": "remove",
            "price": 30,
            "sold": False
        })
        items.append({
            "type": "leave",
            "price": 0,
            "sold": False
        })
        run.node_data = {"items": items}

    def choose_option(self, run: GameRun, option_idx: int) -> str:
        p = run.player
        if run.node_type == "battle":
            return "❌ 战斗中无法使用选择命令。"
        if run.node_type == "map_select":
            return self.choose_map_node(run, option_idx)

        if run.node_type == "reward":
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
                wizards = [cid for cid, c in ALL_CARDS.items() if c.color == "wizard" and c.type == "spell"]
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
        p.gold -= 30
        items = run.node_data.get("items", [])
        for item in items:
            if item.get("type") == "remove":
                item["sold"] = True
        self.save_manager.save_save(run.user_id, run)
        return f"已成功从你的卡组中移除了【{removed_name}】。"
