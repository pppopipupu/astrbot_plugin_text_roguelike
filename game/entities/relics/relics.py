from typing import Dict, List, Optional
from ...data.relic_data import RELIC_CONFIG

class RelicImpl:
    def __init__(self, relic_id: str):
        self.id = relic_id

    def on_battle_start(self, run, engine):
        pass

    def on_battle_win(self, run, engine):
        pass

    def modify_initial_draw(self, run, draw_count: int, engine) -> int:
        return draw_count

class AncientPageRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.hp_loss = 4
        self.spark_count = 2

    def on_battle_start(self, run, engine):
        p = run.player
        p.hp = max(1, p.hp - self.hp_loss)
        engine._log_event(run, f"📖 [先古残页] 触发：失去 {self.hp_loss} 点生命值。")
        max_hand = 9 if "mask_of_void" in p.relics else 12
        spark_added = 0
        for _ in range(self.spark_count):
            if len(p.hand) < max_hand:
                p.hand.append("arcane_spark")
                spark_added += 1
        if spark_added > 0:
            engine._log_event(run, f"📖 [先古残页] 触发：将 {spark_added} 张【奥术星火】加入手牌。")

class HeavyArmorRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.shield_gain = 8

    def on_battle_start(self, run, engine):
        p = run.player
        p.shield += self.shield_gain
        engine._log_event(run, f"🛡️ [重装甲片] 触发：获得 {self.shield_gain} 点初始护盾。")

class LeatherArmorRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.shield_gain = 4

    def on_battle_start(self, run, engine):
        p = run.player
        p.shield += self.shield_gain
        engine._log_event(run, f"🛡️ [坚固皮革] 触发：获得 {self.shield_gain} 点初始护盾。")

class RustShackleRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.hp_loss = 4

    def on_battle_start(self, run, engine):
        p = run.player
        p.hp = max(1, p.hp - self.hp_loss)
        engine._log_event(run, f"🔒 [铁锈之锁] 触发：失去 {self.hp_loss} 点生命值。")

class GreedyContractRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.hp_loss = 3

    def on_battle_start(self, run, engine):
        p = run.player
        p.hp = max(1, p.hp - self.hp_loss)
        engine._log_event(run, f"🪙 [贪婪契约] 触发：失去 {self.hp_loss} 点生命值。")

class ReadyPackRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.draw_bonus = 1
        self.ba_bonus = 1

    def on_battle_start(self, run, engine):
        engine._log_event(run, f"🎒 [准备背包] 触发：本场战斗初始附赠动作（BA）+{self.ba_bonus}。")

    def modify_initial_draw(self, run, draw_count: int, engine) -> int:
        return draw_count + self.draw_bonus

class AncientEyeRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.draw_bonus = 2

    def on_battle_start(self, run, engine):
        engine._log_event(run, f"👁️ [先古之眼] 触发：初始抽牌数量 +{self.draw_bonus}。")

    def modify_initial_draw(self, run, draw_count: int, engine) -> int:
        return draw_count + self.draw_bonus

class BlindSpotRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.draw_penalty = 2

    def on_battle_start(self, run, engine):
        engine._log_event(run, f"👁️ [盲目之障] 触发：首回合少抽 {self.draw_penalty} 张牌。")

    def modify_initial_draw(self, run, draw_count: int, engine) -> int:
        return max(0, draw_count - self.draw_penalty)

class DragonBloodRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.heal_amount = 5

    def on_battle_win(self, run, engine):
        p = run.player
        p.hp = min(p.max_hp, p.hp + self.heal_amount)
        engine._log_event(run, f"🩸 [红龙之血] 触发：回复了 {self.heal_amount} 点生命值。")

class UnstableCrystalRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.spell_dmg_bonus = 1
        self.turn_ba_bonus = 1
        self.recoil_damage = 1

    def on_damage_calculate(self, event, run, engine):
        if event.damage_type == "spell" and event.source == "p0":
            event.modified_damage += self.spell_dmg_bonus

    def on_turn_start(self, event, run, engine):
        if event.is_player:
            run.player.bonus_actions += self.turn_ba_bonus

    def on_card_played(self, event, run, engine):
        if event.card.type == "spell":
            engine._damage_target(run, "p0", self.recoil_damage)
            engine._log_event(run, f"⚡ [不稳定水晶] 受到 {self.recoil_damage} 点法术反噬伤害。")

class VampiricTouchRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.heal_amount = 1

    def on_card_played(self, event, run, engine):
        if event.card.type == "spell" and event.card.id in (
            "dagger_throw", "fire_bolt", "fireball", "thunderwave",
            "magic_missile", "quick_strike", "arcane_spark", "doomsday_judgment", "meteor_swarm"
        ):
            old_hp = run.player.hp
            engine._heal_target(run, "p0", self.heal_amount)
            if run.player.hp > old_hp:
                engine._log_event(run, f"❤️ [吸血之触] 回复了 {self.heal_amount} 点生命值。")

class FoolOathRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.hp_reduction = 3

    def on_minion_summon(self, event, run, engine):
        m = event.minion_state
        m.hp = max(1, m.hp - self.hp_reduction)
        m.max_hp = max(1, m.max_hp - self.hp_reduction)

class WitherSeedRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)

    def on_heal(self, event, run, engine):
        if event.target == "p0":
            event.cancel()

class WhetstoneRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.attack_bonus = 1

    def on_damage_calculate(self, event, run, engine):
        if event.source.startswith("p") and event.source != "p0" and event.damage_type == "attack":
            event.modified_damage += self.attack_bonus

class ArcaneRuneRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.spell_bonus = 1

    def on_damage_calculate(self, event, run, engine):
        if event.damage_type == "spell" and event.source == "p0":
            event.modified_damage += self.spell_bonus

class MarkOfFuryRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.spell_bonus = 2

    def on_damage_calculate(self, event, run, engine):
        if event.damage_type == "spell" and event.source == "p0":
            event.modified_damage += self.spell_bonus

class EnergyCoreRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.action_bonus = 1

    def on_turn_start(self, event, run, engine):
        if event.is_player:
            run.player.actions += self.action_bonus

RELIC_IMPLS = {
    "ancient_page": AncientPageRelic,
    "heavy_armor": HeavyArmorRelic,
    "leather_armor": LeatherArmorRelic,
    "rust_shackle": RustShackleRelic,
    "greedy_contract": GreedyContractRelic,
    "ready_pack": ReadyPackRelic,
    "ancient_eye": AncientEyeRelic,
    "blind_spot": BlindSpotRelic,
    "dragon_blood": DragonBloodRelic,
    "unstable_crystal": UnstableCrystalRelic,
    "vampiric_touch": VampiricTouchRelic,
    "fool_oath": FoolOathRelic,
    "wither_seed": WitherSeedRelic,
    "whetstone": WhetstoneRelic,
    "arcane_rune": ArcaneRuneRelic,
    "mark_of_fury": MarkOfFuryRelic,
    "energy_core": EnergyCoreRelic,
}

def get_relic_impl(relic_id: str) -> Optional[RelicImpl]:
    cls = RELIC_IMPLS.get(relic_id)
    if cls:
        return cls(relic_id)
    return None

def get_relic_name(relic_id: str) -> str:
    return RELIC_CONFIG.get(relic_id, {}).get("name", relic_id)

def get_relic_desc(relic_id: str) -> str:
    return RELIC_CONFIG.get(relic_id, {}).get("desc", "")

def get_relic_rarity(relic_id: str) -> str:
    return RELIC_CONFIG.get(relic_id, {}).get("rarity", "common")

ALL_RELIC_IDS = list(RELIC_CONFIG.keys())
