from typing import Optional, List

class EventOption:
    def __init__(self, text: str, action: str):
        self.text = text
        self.action = action

    def execute(self, run, engine) -> str:
        return ""

class DrinkFountainOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        p.hp = min(p.max_hp, p.hp + 10)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你喝下了泉水，生命值回复了 10 点。已前往下一关。"

class CoinFountainOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        if p.gold < 10:
            return "❌ 你的金币不足 10。"
        p.gold -= 10
        import random
        from .card_impl import ALL_CARDS
        wizards = [cid for cid, c in ALL_CARDS.items() if c.color == "wizard"]
        cid = random.choice(wizards)
        p.deck.append(cid)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return f"你在泉水中投入了 10 金币，泉水闪烁，你获得了【{ALL_CARDS[cid].name}】。已前往下一关。"

class HelpKnightOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        has_aid = False
        for idx, cid in enumerate(p.deck):
            if cid == "first_aid":
                p.deck.pop(idx)
                has_aid = True
                break
        if not has_aid:
            return "❌ 你的卡组中没有【绷带包扎】卡牌！"
        p.deck.append("shield_guard")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你将绷带给予骑士治疗。为了答谢，【盾卫】加入了你的卡组。已前往下一关。"

class RobKnightOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        p.gold += 25
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你不顾骑士的反抗夺走了他的财物，获得 25 金币。已前往下一关。"

class AbsorbAltarOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        p.deck.append("arcane_charge")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你吸收了奥术波动的力量，将【奥术充能】加入卡组。已前往下一关。"

class BreakAltarOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        p.gold += 20
        p.hp -= 4
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你用法杖敲碎了祭坛上的水晶并收集了碎片（获得 20 金币），但被震荡的爆风伤及（失去 4 点生命值）。已前往下一关。"

class LeaveEventOption(EventOption):
    def execute(self, run, engine) -> str:
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你决定不节外生枝，继续赶路。已前往下一关。"

class EventTemplate:
    def __init__(self, id: str, description: str, options: List[EventOption]):
        self.id = id
        self.description = description
        self.options = options

ALL_EVENTS = [
    EventTemplate(
        "fountain",
        "你在荒野中发现了一座泛着蓝光的神秘喷泉。喷泉中央有一座双手捧杯 of 雕像。",
        [
            DrinkFountainOption("饮用泉水 (回复 10 生命值)", "drink_fountain"),
            CoinFountainOption("投入金币 (消耗 10 金币，获得一张随机蓝色卡牌)", "coin_fountain"),
            LeaveEventOption("悄悄离开 (什么都不发生)", "leave_event")
        ]
    ),
    EventTemplate(
        "knight",
        "一位受伤的奥术骑士靠在树旁，他的盔甲已经破损，正虚弱地向你求助。",
        [
            HelpKnightOption("施以援手 (消耗 1张 绷带包扎，获得 随从卡: 盾卫)", "help_knight"),
            RobKnightOption("趁火打劫 (获得 25 金币)", "rob_knight"),
            LeaveEventOption("置之不理 (继续赶路)", "leave_event")
        ]
    ),
    EventTemplate(
        "altar",
        "前方是一处古老的法师祭坛，祭坛上的水晶依然散发着狂暴的奥术波动。",
        [
            AbsorbAltarOption("汲取奥术 (获得一张能力卡: 奥术充能)", "absorb_altar"),
            BreakAltarOption("摧毁水晶 (获得 20 金币，但失去 4 点生命值)", "break_altar"),
            LeaveEventOption("绕道而行 (绕开祭坛)", "leave_event")
        ]
    )
]

def get_option_by_action(action: str) -> Optional[EventOption]:
    mapping = {
        "drink_fountain": DrinkFountainOption("饮用泉水 (回复 10 生命值)", "drink_fountain"),
        "coin_fountain": CoinFountainOption("投入金币 (消耗 10 金币，获得一张随机蓝色卡牌)", "coin_fountain"),
        "help_knight": HelpKnightOption("施以援手 (消耗 1张 绷带包扎，获得 随从卡: 盾卫)", "help_knight"),
        "rob_knight": RobKnightOption("趁火打劫 (获得 25 金币)", "rob_knight"),
        "absorb_altar": AbsorbAltarOption("汲取奥术 (获得一张能力卡: 奥术充能)", "absorb_altar"),
        "break_altar": BreakAltarOption("摧毁水晶 (获得 20 金币，但失去 4 点生命值)", "break_altar"),
        "leave_event": LeaveEventOption("离开事件", "leave_event")
    }
    return mapping.get(action)
