from typing import List, Optional

def is_debuff(buff_id: str) -> bool:
    clean_id = buff_id[:-1] if buff_id.endswith("+") else buff_id
    if clean_id.startswith("minor_vulnerable_") or clean_id.startswith("vulnerable_"):
        return True
    from ...data.buff_data import BUFF_CONFIG
    cfg = BUFF_CONFIG.get(clean_id, {})
    return cfg.get("is_debuff", False)

class BuffImpl:
    def __init__(self, stacks: int):
        self.stacks = stacks
        self.upgraded = False

    def modify_heal_limit(self, run, target: str, current_max: int, engine) -> int:
        return current_max

    def modify_spell_cost_ba(self, run, card, cost_ba: int, engine) -> int:
        return cost_ba

    def modify_spell_damage(self, run, card, damage: int, engine) -> int:
        return damage

    def on_card_played(self, event, buff_state, entity):
        pass

    def on_player_turn_start(self, run, engine):
        pass

    def on_player_turn_end(self, run, buff_state, engine):
        pass

    def prevent_enemy_action(self, run, enemy, buff_state, engine, logs: list) -> bool:
        return False

class TacticalFocusBuff(BuffImpl):
    def on_player_turn_end(self, run, buff_state, engine):
        buff_state.stacks -= 1
        if buff_state.stacks <= 0:
            if buff_state in run.player.buffs:
                run.player.buffs.remove(buff_state)

    def on_turn_end(self, event, buff_state, entity):
        if entity == event.run.player and event.is_player:
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                if buff_state in event.run.player.buffs:
                    event.run.player.buffs.remove(buff_state)

class QuickenBuff(BuffImpl):
    def on_card_play(self, event, buff_state, entity):
        if entity == event.run.player and event.card.type == "spell":
            event.cost_ba = max(0, event.cost_ba - buff_state.stacks)

    def modify_spell_cost_ba(self, run, card, cost_ba: int, engine) -> int:
        if card.type == "spell":
            return max(0, cost_ba - self.stacks)
        return cost_ba

class SpellSurgeBuff(BuffImpl):
    def on_card_played(self, event, buff_state, entity):
        if entity == event.run.player and event.card.color == "wizard":
            event.engine._draw_cards(event.run.player, buff_state.stacks, event.run)

    def on_card_played_legacy(self, run, card, target: str, engine) -> str:
        if card.color == "wizard":
            engine._draw_cards(run.player, self.stacks, run)
        return ""

class ArcaneChargeBuff(BuffImpl):
    def on_damage_calculate(self, event, buff_state, entity):
        if entity == event.run.player and event.damage_type == "spell" and event.source == "p0":
            event.modified_damage += buff_state.stacks * 3

    def modify_spell_damage(self, run, card, damage: int, engine) -> int:
        return damage + self.stacks * 3

class EchoFormBuff(BuffImpl):
    def on_card_played(self, event, buff_state, entity):
        if entity != event.run.player:
            return
        played_count = event.run.node_data.get("cards_played_this_turn", 0)
        stacks = buff_state.stacks
        if event.card.id.startswith("echo_form"):
            stacks = max(0, stacks - 1)
        num_echoes = min(8, max(0, stacks - 8 * played_count))
        if num_echoes > 0:
            res = ""
            for _ in range(num_echoes):
                if event.engine.is_battle_won(event.run):
                    break
                extra_res = event.engine._execute_card_effect(event.run, event.card, event.target)
                res += f" 🔁 [回响触发] {extra_res}"
            event.feedback += res

    def on_card_played_legacy(self, run, card, target: str, engine) -> str:
        played_count = run.node_data.get("cards_played_this_turn", 0)
        stacks = self.stacks
        if card.id.startswith("echo_form"):
            stacks = max(0, stacks - 1)
        num_echoes = min(8, max(0, stacks - 8 * played_count))
        res = ""
        if num_echoes > 0:
            for _ in range(num_echoes):
                if engine.is_battle_won(run):
                    break
                extra_res = engine._execute_card_effect(run, card, target)
                res += f" 🔁 [回响触发] {extra_res}"
        return res

class IronWillBuff(BuffImpl):
    def on_heal(self, event, buff_state, entity):
        if event.target == "p0":
            if buff_state.stacks2 is not None and buff_state.stacks2 > 0:
                event.amount = event.amount * 2
            p = event.run.player
            val = 15 if self.upgraded else 10
            limit = p.max_hp + buff_state.stacks * val
            if p.hp + event.amount > limit:
                event.amount = max(0, limit - p.hp)

    def modify_heal_limit(self, run, target: str, current_max: int, engine) -> int:
        if target == "p0":
            val = 15 if self.upgraded else 10
            return current_max + self.stacks * val
        return current_max

    def on_turn_end(self, event, buff_state, entity):
        if entity == event.run.player and event.is_player:
            if buff_state.stacks2 is not None and buff_state.stacks2 > 0:
                buff_state.stacks2 -= 1

class MagicNetworkBuff(BuffImpl):
    def on_card_played(self, event, buff_state, entity):
        if entity == event.run.player and event.card.type == "spell":
            for idx, enemy in enumerate(list(event.run.enemies)):
                event.engine._damage_target(event.run, f"e{idx+1}", 3)
            event.run.player.shield += 3
            event.feedback += " ⚡ [魔网天成] 对所有敌人造成了 3 点伤害，获得了 3 点护盾。"

    def on_card_played_legacy(self, run, card, target: str, engine) -> str:
        res = ""
        if card.type == "spell":
            for enemy in list(run.enemies):
                engine._damage_target(run, f"e{run.enemies.index(enemy)+1}", 3)
            run.player.shield += 3
            res = " ⚡ [魔网天成] 对所有敌人造成了 3 点伤害，获得了 3 点护盾。"
        return res

    def on_player_turn_end(self, run, buff_state, engine):
        if buff_state in run.player.buffs:
            run.player.buffs.remove(buff_state)

    def on_turn_end(self, event, buff_state, entity):
        if entity == event.run.player:
            if buff_state in event.run.player.buffs:
                event.run.player.buffs.remove(buff_state)

class WishPowerBuff(BuffImpl):
    def on_damage_calculate(self, event, buff_state, entity):
        if entity == event.run.player and event.damage_type == "spell" and event.source == "p0":
            val = 6 if self.upgraded else 4
            event.modified_damage += buff_state.stacks * val

    def modify_spell_damage(self, run, card, damage: int, engine) -> int:
        val = 6 if self.upgraded else 4
        return damage + self.stacks * val

class StunBuff(BuffImpl):
    def on_turn_start(self, event, buff_state, entity):
        if not event.is_player and entity in event.run.enemies:
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                entity.buffs.remove(buff_state)
            entity.actions = 0
            entity.bonus_actions = 0
            event.engine._log_event(event.run, f"⚠️ 【{entity.name}】处于眩晕状态，本回合无法行动。")

    def prevent_enemy_action(self, run, enemy, buff_state, engine, logs: list) -> bool:
        buff_state.stacks -= 1
        if buff_state.stacks <= 0:
            enemy.buffs.remove(buff_state)
        logs.append(f"【{enemy.name}】处于眩晕状态，本回合无法行动。")
        return True

class BeatOfDeathBuff(BuffImpl):
    def __init__(self, stacks: int):
        super().__init__(stacks)
        self.damage_value = stacks

    def on_card_played(self, event, buff_state, entity):
        if event.run.node_data.get("extra_turns_left", 0) > 0 and event.run.node_data.get("time_stop_upgraded"):
            return
        p = event.run.player
        engine = event.engine
        dmg = self.damage_value
        engine._log_event(event.run, "💔 [死亡律动]")
        engine._damage_target(event.run, "p0", dmg, source="beat_of_death", damage_type="force")

class StrengthBuff(BuffImpl):
    pass

class FuryBuff(BuffImpl):
    def on_card_played(self, event, buff_state, entity):
        if event.card.rarity in ("rare", "legendary", "mythic", "artifact"):
            event.engine._add_buff_to(entity, "strength", "力量", "造成的伤害增加", buff_state.stacks)
            event.engine._log_event(event.run, f"🔥 【{entity.name}】的【愤怒】被玩家的【{event.card.name}】激怒，力量增加了 {buff_state.stacks} 点！")

class MinorVulnerableBuff(BuffImpl):
    def __init__(self, stacks: int, damage_type: str):
        super().__init__(stacks)
        self.damage_type = damage_type

    def on_damage_calculate_defend(self, event, buff_state, entity):
        dtype_str = event.damage_type.value if hasattr(event.damage_type, "value") else str(event.damage_type)
        if dtype_str == self.damage_type:
            event.modified_damage = int(event.modified_damage * 1.5)

    def on_turn_end(self, event, buff_state, entity):
        if event.is_player == (entity == event.run.player):
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                entity.buffs.remove(buff_state)

class VulnerableBuff(BuffImpl):
    def __init__(self, stacks: int, damage_type: str):
        super().__init__(stacks)
        self.damage_type = damage_type

    def on_damage_calculate_defend(self, event, buff_state, entity):
        dtype_str = event.damage_type.value if hasattr(event.damage_type, "value") else str(event.damage_type)
        if dtype_str == self.damage_type:
            event.modified_damage = int(event.modified_damage * 2)

    def on_turn_end(self, event, buff_state, entity):
        if event.is_player == (entity == event.run.player):
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                entity.buffs.remove(buff_state)

class FireGrowBuff(BuffImpl):
    def on_damage_calculate(self, event, buff_state, entity):
        if entity == event.run.player and event.damage_type == "fire" and event.source == "p0":
            event.modified_damage += buff_state.stacks

    def modify_spell_damage(self, run, card, damage: int, engine) -> int:
        if getattr(card, "damage_type", "") == "fire":
            return damage + self.stacks
        return damage

class ForgeBackfireBuff(BuffImpl):
    def on_damage_calculate(self, event, buff_state, entity):
        if entity == event.run.player and event.damage_type == "spell" and event.source == "p0":
            event.modified_damage = max(0, event.modified_damage - buff_state.stacks)

    def modify_spell_damage(self, run, card, damage: int, engine) -> int:
        return max(0, damage - self.stacks)

    def on_turn_end(self, event, buff_state, entity):
        if entity == event.run.player:
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                event.run.player.buffs.remove(buff_state)

class TimeWarpSpellBoostBuff(BuffImpl):
    def on_damage_calculate(self, event, buff_state, entity):
        if entity == event.run.player and event.damage_type == "spell" and event.source == "p0":
            event.modified_damage += buff_state.stacks * 2

    def modify_spell_damage(self, run, card, damage: int, engine) -> int:
        return damage + self.stacks * 2

    def on_turn_end(self, event, buff_state, entity):
        if entity == event.run.player:
            if buff_state in event.run.player.buffs:
                event.run.player.buffs.remove(buff_state)

class ShockBuff(BuffImpl):
    def on_damage_calculate_defend(self, event, buff_state, entity):
        dtype_str = event.damage_type.value if hasattr(event.damage_type, "value") else str(event.damage_type)
        if dtype_str in ("lightning", "thunder"):
            event.modified_damage += buff_state.stacks * 3

    def on_turn_end(self, event, buff_state, entity):
        if event.is_player == (entity == event.run.player):
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                if buff_state in entity.buffs:
                    entity.buffs.remove(buff_state)

class LightningShieldBuff(BuffImpl):
    def on_damage_calculate_defend(self, event, buff_state, entity):
        if event.source == "p0" and event.modified_damage > 0:
            run = event.run
            engine = event.engine
            engine._damage_target(run, "p0", 2 * buff_state.stacks, source=f"buff:{entity.name}", damage_type="lightning")
            engine._add_buff_to(run.player, "shock", "电击", "受到的闪电和雷鸣伤害每层增加 3 点", 1)

    def on_turn_start(self, event, buff_state, entity):
        if not event.is_player and entity in event.run.enemies:
            if buff_state in entity.buffs:
                entity.buffs.remove(buff_state)

class ResistBuff(BuffImpl):
    def __init__(self, stacks: int, damage_type: str):
        super().__init__(stacks)
        self.damage_type = damage_type

    def on_damage_calculate_defend(self, event, buff_state, entity):
        dtype_str = event.damage_type.value if hasattr(event.damage_type, "value") else str(event.damage_type)
        if dtype_str == self.damage_type and dtype_str != "true":
            event.modified_damage = int(event.modified_damage * 0.5)

    def on_turn_end(self, event, buff_state, entity):
        if event.is_player == (entity == event.run.player):
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                if buff_state in entity.buffs:
                    entity.buffs.remove(buff_state)

class ImmuneBuff(BuffImpl):
    def __init__(self, stacks: int, damage_type: str):
        super().__init__(stacks)
        self.damage_type = damage_type

    def on_damage_calculate_defend(self, event, buff_state, entity):
        dtype_str = event.damage_type.value if hasattr(event.damage_type, "value") else str(event.damage_type)
        if dtype_str == self.damage_type and dtype_str != "true":
            event.modified_damage = 0

    def on_turn_end(self, event, buff_state, entity):
        if event.is_player == (entity == event.run.player):
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                if buff_state in entity.buffs:
                    entity.buffs.remove(buff_state)

class BurningBuff(BuffImpl):
    def on_turn_start(self, event, buff_state, entity):
        run = event.run
        engine = event.engine
        if entity == run.player:
            target = "p0"
        else:
            try:
                idx = run.enemies.index(entity)
                target = f"e{idx+1}"
            except ValueError:
                return
        damage = buff_state.stacks
        engine._log_event(run, f"🔥 【{entity.name}】受到燃烧造成的 {damage} 点火焰伤害！")
        engine._damage_target(run, target, damage, source="burning", damage_type="fire")
        if buff_state.stacks2 is not None:
            buff_state.stacks2 -= 1
            if buff_state.stacks2 <= 0:
                if buff_state in entity.buffs:
                    entity.buffs.remove(buff_state)

class KeyScholarPassiveBuff(BuffImpl):
    def on_card_played(self, event, buff_state, entity):
        if entity == event.run.player and event.card.type == "amulet":
            event.engine._heal_target(event.run, "p0", 3)
            event.engine._gain_shield(event.run, "p0", 4)
            event.feedback += " 🚪 [门扉共鸣] 回复了 3 点生命值并获得了 4 点护盾。"

class VoidWeaknessBuff(BuffImpl):
    def on_damage_calculate(self, event, buff_state, entity):
        if entity == event.run.player and event.damage_type == "spell" and event.source == "p0":
            event.modified_damage = max(0, event.modified_damage - buff_state.stacks * 3)

    def modify_spell_damage(self, run, card, damage: int, engine) -> int:
        return max(0, damage - self.stacks * 3)

    def on_turn_end(self, event, buff_state, entity):
        if entity == event.run.player and event.is_player:
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                event.run.player.buffs.remove(buff_state)

class AncientProtectionBuff(BuffImpl):
    def on_turn_start(self, event, buff_state, entity):
        if not event.is_player and entity.shield > 0:
            to_remove = []
            for b in entity.buffs:
                if is_debuff(b.id):
                    to_remove.append(b)
            for b in to_remove:
                entity.buffs.remove(b)
            event.engine._log_event(event.run, f"🛡️ 【{entity.name}】触发【先古庇护】：清除了所有负面效果！")

    def on_damage_calculate_defend(self, event, buff_state, entity):
        if event.modified_damage > 0:
            recoil_dmg = max(1, int(event.modified_damage * 0.20))
            event.engine._damage_target(event.run, "p0", recoil_dmg, source=f"buff:{entity.name}", damage_type="true")
            event.engine._log_event(event.run, f"⚡ 【{entity.name}】的反弹结界触发，对玩家反弹了 {recoil_dmg} 点真实伤害！")

class EndGatePassiveBuff(BuffImpl):
    def on_turn_start(self, event, buff_state, entity):
        if not event.is_player:
            entity.shield += 15
            to_remove = []
            for b in entity.buffs:
                if is_debuff(b.id):
                    to_remove.append(b)
            for b in to_remove:
                entity.buffs.remove(b)
            event.engine._log_event(event.run, f"🚪 【{entity.name}】触发【终焉之门】：获得 15 护盾并清除了所有负面效果！")

    def on_damage_calculate_defend(self, event, buff_state, entity):
        if event.modified_damage > 0:
            import random
            if random.random() < 0.30:
                event.engine._damage_target(event.run, "p0", 4, source=f"buff:{entity.name}", damage_type="true")
                event.engine._log_event(event.run, f"⚡ 【{entity.name}】的终焉结界触发，对玩家反弹了 4 点真实伤害！")

class AncientWisdomBuff(BuffImpl):
    def on_card_played(self, event, buff_state, entity):
        if entity == event.run.player and event.card.color == "neutral":
            coef = 3 if self.upgraded else 2
            shield_gain = buff_state.stacks * coef
            event.engine._gain_shield(event.run, "p0", shield_gain)
            event.feedback += f" 🛡️ [古老智慧] 获得了 {shield_gain} 点护盾。"

class BufferBuff(BuffImpl):
    def on_damage_calculate_defend(self, event, buff_state, entity):
        if event.modified_damage > 0:
            event.modified_damage = 0
            buff_state.stacks -= 1
            name = "玩家" if entity == event.run.player else getattr(entity, "name", "未知")
            event.engine._log_event(event.run, f"🛡️ 【{name}】的【缓冲】消耗了 1 层，免疫了本次伤害。")
            if buff_state.stacks <= 0:
                if buff_state in entity.buffs:
                    entity.buffs.remove(buff_state)

class DemonContractBuff(BuffImpl):
    def on_card_played(self, event, buff_state, entity):
        if entity == event.run.player and event.card.type == "spell" and not event.card.id.startswith("demon_contract"):
            stacks = buff_state.stacks
            res = ""
            for _ in range(stacks):
                if event.engine.is_battle_won(event.run):
                    break
                extra_res = event.engine._execute_card_effect(event.run, event.card, event.target)
                res += f" 🔁 [契约回响] {extra_res}"
            event.feedback += res
            if buff_state in event.run.player.buffs:
                event.run.player.buffs.remove(buff_state)

    def on_turn_end(self, event, buff_state, entity):
        if entity == event.run.player and event.is_player:
            if buff_state in event.run.player.buffs:
                event.run.player.buffs.remove(buff_state)

class GlacierFortressBuff(BuffImpl):
    def on_turn_end(self, event, buff_state, entity):
        if entity == event.run.player and event.is_player:
            coef = 6 if self.upgraded else 4
            shield_gain = buff_state.stacks * coef
            event.engine._gain_shield(event.run, "p0", shield_gain)
            event.engine._log_event(event.run, f"🏔️ [冰川壁垒] 触发：玩家获得了 {shield_gain} 点额外护盾。")

class VoidExhaustionBuff(BuffImpl):
    def on_turn_end(self, event, buff_state, entity):
        if entity == event.run.player and event.is_player:
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                if buff_state in event.run.player.buffs:
                    event.run.player.buffs.remove(buff_state)

class ManaLeakBuff(BuffImpl):
    def on_card_play(self, event, buff_state, entity):
        if entity == event.run.player and event.card.type == "spell":
            event.cost_ba += buff_state.stacks

    def modify_spell_cost_ba(self, run, card, cost_ba: int, engine) -> int:
        if card.type == "spell":
            return cost_ba + self.stacks
        return cost_ba

    def on_damage_calculate(self, event, buff_state, entity):
        if entity == event.run.player and event.damage_type == "spell" and event.source == "p0":
            event.modified_damage = max(0, event.modified_damage - buff_state.stacks * 2)

    def modify_spell_damage(self, run, card, damage: int, engine) -> int:
        return max(0, damage - self.stacks * 2)

    def on_turn_end(self, event, buff_state, entity):
        if entity == event.run.player and event.is_player:
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                if buff_state in event.run.player.buffs:
                    event.run.player.buffs.remove(buff_state)

BUFF_MAP = {
    "tactical_focus": TacticalFocusBuff,
    "quicken": QuickenBuff,
    "spell_surge": SpellSurgeBuff,
    "arcane_charge": ArcaneChargeBuff,
    "echo_form": EchoFormBuff,
    "iron_will": IronWillBuff,
    "magic_network": MagicNetworkBuff,
    "wish_power": WishPowerBuff,
    "stun": StunBuff,
    "beat_of_death": BeatOfDeathBuff,
    "strength": StrengthBuff,
    "fury": FuryBuff,
    "fire_grow": FireGrowBuff,
    "forge_backfire": ForgeBackfireBuff,
    "time_warp_spell_boost": TimeWarpSpellBoostBuff,
    "shock": ShockBuff,
    "lightning_shield": LightningShieldBuff,
    "burning": BurningBuff,
    "key_scholar_passive": KeyScholarPassiveBuff,
    "void_weakness": VoidWeaknessBuff,
    "ancient_protection": AncientProtectionBuff,
    "end_gate_passive": EndGatePassiveBuff,
    "ancient_wisdom_buff": AncientWisdomBuff,
    "buffer": BufferBuff,
    "demon_contract_buff": DemonContractBuff,
    "glacier_fortress_buff": GlacierFortressBuff,
    "void_exhaustion": VoidExhaustionBuff,
    "mana_leak": ManaLeakBuff,
}

def get_buff_impl(buff_id: str, stacks: int, stacks2: Optional[int] = None) -> Optional[BuffImpl]:
    upgraded = False
    if isinstance(buff_id, str) and buff_id.endswith("+"):
        upgraded = True
        buff_id = buff_id[:-1]
    if buff_id.startswith("minor_vulnerable_"):
        dtype = buff_id[len("minor_vulnerable_"):]
        inst = MinorVulnerableBuff(stacks, dtype)
        inst.stacks2 = stacks2
        inst.upgraded = upgraded
        return inst
    elif buff_id.startswith("vulnerable_"):
        dtype = buff_id[len("vulnerable_"):]
        inst = VulnerableBuff(stacks, dtype)
        inst.stacks2 = stacks2
        inst.upgraded = upgraded
        return inst
    elif buff_id.startswith("resist_"):
        dtype = buff_id[len("resist_"):]
        inst = ResistBuff(stacks, dtype)
        inst.stacks2 = stacks2
        inst.upgraded = upgraded
        return inst
    elif buff_id.startswith("immune_"):
        dtype = buff_id[len("immune_"):]
        inst = ImmuneBuff(stacks, dtype)
        inst.stacks2 = stacks2
        inst.upgraded = upgraded
        return inst
    cls = BUFF_MAP.get(buff_id)
    if cls:
        inst = cls(stacks)
        inst.stacks2 = stacks2
        inst.upgraded = upgraded
        return inst
    return None

def apply_modify_heal_limit(run, target: str, current_max: int, engine) -> int:
    limit = current_max
    for b in list(run.player.buffs):
        impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
        if impl:
            limit = impl.modify_heal_limit(run, target, limit, engine)
    return limit

def apply_modify_spell_cost_ba(run, card, cost_ba: int, engine) -> int:
    cost = cost_ba
    for b in list(run.player.buffs):
        impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
        if impl:
            cost = impl.modify_spell_cost_ba(run, card, cost, engine)
    return cost

def apply_modify_spell_damage(run, card, damage: int, engine) -> int:
    dmg = damage
    if getattr(run.player, "subclass", "") == "塑能法师" and getattr(card, "type", "") == "spell":
        dmg = int(dmg * 1.15)
    for b in list(run.player.buffs):
        impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
        if impl:
            dmg = impl.modify_spell_damage(run, card, dmg, engine)
    return dmg

def apply_on_card_played(run, card, target: str, engine) -> str:
    res = ""
    for b in list(run.player.buffs):
        impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
        if impl:
            extra = impl.on_card_played(run, card, target, engine)
            if extra:
                res += " " + extra
    return res

def apply_on_player_turn_start(run, engine):
    for b in list(run.player.buffs):
        impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
        if impl:
            impl.on_player_turn_start(run, engine)

def apply_on_player_turn_end(run, engine):
    for b in list(run.player.buffs):
        impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
        if impl:
            impl.on_player_turn_end(run, b, engine)

def apply_prevent_enemy_action(run, enemy, engine, logs: list) -> bool:
    prevented = False
    for b in list(enemy.buffs):
        impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
        if impl:
            if impl.prevent_enemy_action(run, enemy, b, engine, logs):
                prevented = True
    return prevented
