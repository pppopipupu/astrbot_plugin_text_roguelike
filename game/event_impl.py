from typing import Optional, List
from .data.event_data import EVENT_CONFIG

class EventOption:
    def __init__(self, text: str, action: str):
        self.text = text
        self.action = action

    def execute(self, run, engine) -> str:
        return ""

class DrinkFountainOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        cfg = EVENT_CONFIG["fountain"]["options"]["drink_fountain"]
        heal = cfg.get("heal_amount", 10)
        p.hp = min(p.max_hp, p.hp + heal)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return cfg["feedback"].format(heal_amount=heal)

class CoinFountainOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        cfg = EVENT_CONFIG["fountain"]["options"]["coin_fountain"]
        cost = cfg.get("gold_cost", 10)
        if p.gold < cost:
            return cfg.get("feedback_insufficient", "❌ 你的金币不足 10。")
        p.gold -= cost
        import random
        from .card_impl import ALL_CARDS
        wizards = [cid for cid, c in ALL_CARDS.items() if c.color == "wizard"]
        cid = random.choice(wizards)
        p.deck.append(cid)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return cfg["feedback"].format(gold_cost=cost, card_name=ALL_CARDS[cid].name)

class HelpKnightOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        cfg = EVENT_CONFIG["knight"]["options"]["help_knight"]
        consume = cfg.get("consume_card", "first_aid")
        reward = cfg.get("reward_card", "shield_guard")
        has_aid = False
        for idx, cid in enumerate(p.deck):
            if cid == consume:
                p.deck.pop(idx)
                has_aid = True
                break
        if not has_aid:
            return cfg.get("feedback_insufficient", "❌ 你的卡组中没有【绷带包扎】卡牌！")
        p.deck.append(reward)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return cfg["feedback"]

class RobKnightOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        cfg = EVENT_CONFIG["knight"]["options"]["rob_knight"]
        gain = cfg.get("gold_gain", 25)
        p.gold += gain
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return cfg["feedback"].format(gold_gain=gain)

class AbsorbAltarOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        cfg = EVENT_CONFIG["altar"]["options"]["absorb_altar"]
        reward = cfg.get("reward_card", "arcane_charge")
        p.deck.append(reward)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return cfg["feedback"]

class BreakAltarOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        cfg = EVENT_CONFIG["altar"]["options"]["break_altar"]
        gold_gain = cfg.get("gold_gain", 20)
        hp_loss = cfg.get("hp_loss", 4)
        p.gold += gold_gain
        p.hp -= hp_loss
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return cfg["feedback"].format(gold_gain=gold_gain, hp_loss=hp_loss)

class LeaveEventOption(EventOption):
    def __init__(self, text: str, action: str, event_id: str = "fountain"):
        super().__init__(text, action)
        self.event_id = event_id

    def execute(self, run, engine) -> str:
        cfg = EVENT_CONFIG.get(self.event_id, {}).get("options", {}).get("leave_event", {})
        feedback = cfg.get("feedback", "你决定不节外生枝，继续赶路。已前往下一关。")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return feedback

class EventTemplate:
    def __init__(self, id: str, description: str, options: List[EventOption]):
        self.id = id
        self.description = description
        self.options = options

ALL_EVENTS = [
    EventTemplate(
        "fountain",
        EVENT_CONFIG["fountain"]["description"],
        [
            DrinkFountainOption(EVENT_CONFIG["fountain"]["options"]["drink_fountain"]["text"], "drink_fountain"),
            CoinFountainOption(EVENT_CONFIG["fountain"]["options"]["coin_fountain"]["text"], "coin_fountain"),
            LeaveEventOption(EVENT_CONFIG["fountain"]["options"]["leave_event"]["text"], "leave_event", "fountain")
        ]
    ),
    EventTemplate(
        "knight",
        EVENT_CONFIG["knight"]["description"],
        [
            HelpKnightOption(EVENT_CONFIG["knight"]["options"]["help_knight"]["text"], "help_knight"),
            RobKnightOption(EVENT_CONFIG["knight"]["options"]["rob_knight"]["text"], "rob_knight"),
            LeaveEventOption(EVENT_CONFIG["knight"]["options"]["leave_event"]["text"], "leave_event", "knight")
        ]
    ),
    EventTemplate(
        "altar",
        EVENT_CONFIG["altar"]["description"],
        [
            AbsorbAltarOption(EVENT_CONFIG["altar"]["options"]["absorb_altar"]["text"], "absorb_altar"),
            BreakAltarOption(EVENT_CONFIG["altar"]["options"]["break_altar"]["text"], "break_altar"),
            LeaveEventOption(EVENT_CONFIG["altar"]["options"]["leave_event"]["text"], "leave_event", "altar")
        ]
    )
]

def get_option_by_action(action: str) -> Optional[EventOption]:
    mapping = {
        "drink_fountain": DrinkFountainOption(EVENT_CONFIG["fountain"]["options"]["drink_fountain"]["text"], "drink_fountain"),
        "coin_fountain": CoinFountainOption(EVENT_CONFIG["fountain"]["options"]["coin_fountain"]["text"], "coin_fountain"),
        "help_knight": HelpKnightOption(EVENT_CONFIG["knight"]["options"]["help_knight"]["text"], "help_knight"),
        "rob_knight": RobKnightOption(EVENT_CONFIG["knight"]["options"]["rob_knight"]["text"], "rob_knight"),
        "absorb_altar": AbsorbAltarOption(EVENT_CONFIG["altar"]["options"]["absorb_altar"]["text"], "absorb_altar"),
        "break_altar": BreakAltarOption(EVENT_CONFIG["altar"]["options"]["break_altar"]["text"], "break_altar"),
        "leave_event": LeaveEventOption(EVENT_CONFIG["leave_default"]["text"], "leave_event", "leave_default")
    }
    return mapping.get(action)
