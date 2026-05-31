import random
from .base import EventOption
from ...data.event_data import EVENT_CONFIG
from ..cards import ALL_CARDS

class DrinkFountainOption(EventOption, action="drink_fountain", text="饮用泉水"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.hp = min(p.max_hp, p.hp + 10)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你喝下了泉水，生命值回复了 10 点。已前往下一关。"

class CoinFountainOption(EventOption, action="coin_fountain", text="投入金币"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        if p.gold < 10:
            return "❌ 你的金币不足 10。"
        p.gold -= 10
        wizards = [cid for cid, c in ALL_CARDS.items() if c.color == "wizard" and c.rarity != "legendary"]
        reward_cards = random.sample(wizards, 3) if len(wizards) >= 3 else wizards
        run.node_type = "card_select"
        run.node_data = {
            "title": "许愿泉水：请选择你的回馈",
            "desc": "你在泉水中投入了 10 金币，泉水散发出耀眼的奥术涟漪，升起三张卡牌：",
            "cards": reward_cards
        }
        engine.save_manager.save_save(run.user_id, run)
        return "你在泉水中投入了 10 金币，开始选择泉水的回赠。"

class ObserveFountainOption(EventOption, action="observe_fountain", text="仔细观察泉底"):
    def _run_effect(self, run, engine) -> str:
        cfg = EVENT_CONFIG["fountain_observe"]
        run.node_data["event_id"] = "fountain_observe"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你凑近池塘向下观察..."

class TakeNecklaceOption(EventOption, action="take_necklace", text="冒险捞取项链"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        if random.random() < 0.5:
            p.relics.append("arcane_rune")
            res = "🍀 运气不错！你安全地解除了符文陷阱，成功捞出了【奥术项链】，获得遗物【奥术符文】！"
        else:
            p.deck.append("curse_dazed")
            res = "⚡ 糟糕！捞取项链时触发了爆裂电弧陷阱，你感到一阵晕眩（1张【晕眩】卡牌已加入卡组），且项链在电弧中化为了灰烬！"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return res
