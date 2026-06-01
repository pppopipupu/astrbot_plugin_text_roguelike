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

    def on_damage_take(self, event, run, engine):
        pass

    def on_shield_decay(self, event, run, engine):
        pass

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

class ChemicalXRelic(RelicImpl):
    pass

class AncientCompassRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        for e in run.enemies:
            e.actions = max(0, e.actions - 1)
        engine._log_event(run, "🧭 [古老罗盘] 触发：所有敌人首回合动作点（A）减少 1。")

class PortalFragmentRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        import random
        p = run.player
        max_hand = 9 if "mask_of_void" in p.relics else 12
        if len(p.hand) < max_hand:
            chosen = random.choice(["key_resonance", "gate_guard", "master_key", "void_beacon", "ancient_wisdom"])
            p.hand.append(chosen)
            from ...data.card_data import CARD_CONFIG
            name = CARD_CONFIG.get(chosen, {}).get("name", chosen)
            engine._log_event(run, f"🌀 [门扉碎片] 触发：随机将一张中立牌【{name}】加入手牌。")

class AncientSigilRelic(RelicImpl):
    def on_card_played(self, event, run, engine):
        if getattr(event.card, "exhaust", False):
            import random
            if random.random() < 0.5:
                engine._heal_target(run, "p0", 3)
                engine._log_event(run, "✨ [先古印记] 触发：为玩家恢复 3 点生命值。")
            else:
                engine._gain_shield(run, "p0", 5)
                engine._log_event(run, "✨ [先古印记] 触发：为玩家获得 5 点护盾。")

class VoidLensRelic(RelicImpl):
    def on_damage_calculate(self, event, run, engine):
        if event.card and event.card.color == "neutral" and event.source == "p0":
            event.modified_damage += 2

    def on_shield_gain(self, event, run, engine):
        curr_cid = run.node_data.get("current_playing_card_id", "")
        if curr_cid:
            from ..cards.base import ALL_CARDS
            card = ALL_CARDS.get(curr_cid)
            if card and card.color == "neutral":
                event.modified_amount += 2

class AncientKeyringRelic(RelicImpl):
    pass

class AbyssGazeRelic(RelicImpl):
    def on_damage_calculate(self, event, run, engine):
        if event.damage_type == "spell" and event.source == "p0":
            event.modified_damage += 4

    def on_damage_take(self, event, run, engine):
        if event.target == "p0" and event.amount > 0 and event.source != "abyss_gaze":
            engine._damage_target(run, "p0", 2, source="abyss_gaze", damage_type="true")
            engine._log_event(run, "👁️ [深渊凝视] 触发：额外受到 2 点真实伤害。")

class GlacierArmorRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        run.player.shield += 12
        engine._log_event(run, "🛡️ [冰川装甲] 触发：获得 12 点初始护盾。")

class AbyssWhisperRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        if run.enemies:
            import random
            enemy = random.choice(run.enemies)
            engine._add_buff_to(enemy, "stun", "眩晕", "无法行动", 1)
            engine._log_event(run, f"👁️ [深渊低语] 触发：使【{enemy.name}】在首回合陷入眩晕！")

class FrostBladeRelic(RelicImpl):
    def on_damage_calculate(self, event, run, engine):
        dtype_str = event.damage_type.value if hasattr(event.damage_type, "value") else str(event.damage_type)
        if dtype_str == "cold" and event.source == "p0":
            event.modified_damage += 4

class ShadowCurseRelic(RelicImpl):
    def on_card_played(self, event, run, engine):
        if event.card.type == "spell" and not event.card.id.startswith("demon_contract"):
            engine._damage_target(run, "p0", 2, source="shadow_curse", damage_type="true")
            engine._log_event(run, "🕸️ [影之诅咒] 触发：失去 2 点生命值。")

class GlacierChillRelic(RelicImpl):
    def on_turn_start(self, event, run, engine):
        if event.is_player:
            run.player.actions = max(0, run.player.actions - 1)
            engine._log_event(run, "❄️ [严寒侵袭] 触发：玩家本回合动作点 A 减少 1。")

class AbyssContractRelic(RelicImpl):
    def on_damage_take(self, event, run, engine):
        dtype_str = event.damage_type.value if hasattr(event.damage_type, "value") else str(event.damage_type)
        if event.target == "p0" and dtype_str == "true" and event.amount > 0:
            engine._draw_cards(run.player, 1, run)
            engine._log_event(run, "📖 [深渊契约书] 触发：受到真实伤害，抽取 1 张卡牌。")

class GlacierCoreRelic(RelicImpl):
    def on_shield_decay(self, event, run, engine):
        if event.target == "p0" and event.amount > 0:
            lost = event.amount
            dmg = lost // 2
            if dmg > 0:
                feedback_parts = []
                for idx in range(len(run.enemies) - 1, -1, -1):
                    enemy = run.enemies[idx]
                    engine._damage_target(run, f"e{idx+1}", dmg, damage_type="cold", source="glacier_core")
                    feedback_parts.append(f"【{enemy.name}】受到 {dmg} 点冰霜伤害")
                if feedback_parts:
                    engine._log_event(run, "🏔️ [极寒之核] 触发：" + "，".join(feedback_parts) + "。")

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
    "chemical_x": ChemicalXRelic,
    "ancient_compass": AncientCompassRelic,
    "portal_fragment": PortalFragmentRelic,
    "ancient_sigil": AncientSigilRelic,
    "void_lens": VoidLensRelic,
    "ancient_keyring": AncientKeyringRelic,
    "abyss_gaze": AbyssGazeRelic,
    "glacier_armor": GlacierArmorRelic,
    "abyss_whisper": AbyssWhisperRelic,
    "frost_blade": FrostBladeRelic,
    "shadow_curse": ShadowCurseRelic,
    "glacier_chill": GlacierChillRelic,
    "abyss_contract": AbyssContractRelic,
    "glacier_core": GlacierCoreRelic,
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
