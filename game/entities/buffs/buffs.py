from typing import List, Optional
from .registry import register_buff, BUFF_CLASS_REGISTRY
import re

def is_debuff(buff_id: str) -> bool:
    clean_id = buff_id[:-1] if buff_id.endswith("+") else buff_id
    if clean_id.startswith("minor_vulnerable_") or clean_id.startswith("vulnerable_"):
        return True
    from ...data.buff_data import BUFF_CONFIG
    cfg = BUFF_CONFIG.get(clean_id, {})
    return cfg.get("is_debuff", False)

class BuffImpl:
    auto_register = True
    def __init__(self, stacks: int):
        self.stacks = stacks
        self.upgraded = False

    def on_card_play(self, event, buff_state, entity):
        pass

    def on_card_played(self, event, buff_state, entity):
        pass

    def on_turn_start(self, event, buff_state, entity):
        pass

    def on_turn_end(self, event, buff_state, entity):
        pass

    def on_damage_calculate(self, event, buff_state, entity):
        pass

    def on_damage_calculate_defend(self, event, buff_state, entity):
        pass

    def on_damage_take_defend(self, event, buff_state, entity, engine):
        pass

    def on_heal(self, event, buff_state, entity):
        pass

    def on_heal_calculate(self, event, buff_state, entity):
        pass

    def on_shield_gain(self, event, buff_state, entity):
        pass

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
        num_echoes = min(10, max(0, stacks - 10 * played_count))
        if num_echoes > 0:
            res = ""
            for _ in range(num_echoes):
                if event.engine.is_battle_won(event.run):
                    break
                extra_res = event.engine._execute_card_effect(event.run, event.card, event.target)
                res += f" 🔁 [回响触发] {extra_res}"
                replay_val = getattr(event.card, "replay", 0)
                if replay_val > 0:
                    for _ in range(replay_val):
                        if event.engine.is_battle_won(event.run):
                            break
                        extra_res_rep = event.engine._execute_card_effect(event.run, event.card, event.target)
                        res += f" 🔁 [重放触发] {extra_res_rep}"
            event.feedback += res

    def on_card_played_legacy(self, run, card, target: str, engine) -> str:
        played_count = run.node_data.get("cards_played_this_turn", 0)
        stacks = self.stacks
        if card.id.startswith("echo_form"):
            stacks = max(0, stacks - 1)
        num_echoes = min(10, max(0, stacks - 10 * played_count))
        res = ""
        if num_echoes > 0:
            for _ in range(num_echoes):
                if engine.is_battle_won(run):
                    break
                extra_res = engine._execute_card_effect(run, card, target)
                res += f" 🔁 [回响触发] {extra_res}"
                replay_val = getattr(card, "replay", 0)
                if replay_val > 0:
                    for _ in range(replay_val):
                        if engine.is_battle_won(run):
                            break
                        extra_res_rep = engine._execute_card_effect(run, card, target)
                        res += f" 🔁 [重放触发] {extra_res_rep}"
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

    def on_heal_calculate(self, event, buff_state, entity):
        if event.target == "p0":
            val = 15 if self.upgraded else 10
            event.modified_max_hp = event.modified_max_hp + buff_state.stacks * val

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

    def on_enemy_sync_intents(self, event, buff_state, entity):
        from ...models.state import EnemyIntentState
        entity.actions = 0
        entity.bonus_actions = 0
        entity.intents = [
            EnemyIntentState(
                type="stun",
                val=0,
                desc="眩晕 (本回合无法行动)",
                cost_a=0,
                cost_ba=0
            )
        ]

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
    def on_damage_calculate(self, event, buff_state, entity):
        if entity == event.run.player and event.source == "p0":
            dtype_str = event.damage_type.value if hasattr(event.damage_type, "value") else str(event.damage_type)
            if dtype_str in ("slashing", "bludgeoning", "piercing"):
                mult = 1
                if event.card and event.card.id.startswith("heavy_blade"):
                    mult = 5 if event.card.upgraded else 3
                event.modified_damage += buff_state.stacks * mult

@register_buff("minor_vulnerable")
class GenericMinorVulnerableBuff(BuffImpl):
    def on_damage_calculate_defend(self, event, buff_state, entity):
        event.modified_damage = int(event.modified_damage * 1.5)

    def on_turn_end(self, event, buff_state, entity):
        if event.is_player == (entity == event.run.player):
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                entity.buffs.remove(buff_state)

@register_buff("vulnerable")
class GenericVulnerableBuff(BuffImpl):
    def on_damage_calculate_defend(self, event, buff_state, entity):
        event.modified_damage = int(event.modified_damage * 2)

    def on_turn_end(self, event, buff_state, entity):
        if event.is_player == (entity == event.run.player):
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                entity.buffs.remove(buff_state)

class WeakBuff(BuffImpl):
    def on_damage_calculate(self, event, buff_state, entity):
        is_owner = False
        if entity == event.run.player:
            if event.source == "p0":
                is_owner = True
        elif entity in event.run.enemies:
            try:
                idx = event.run.enemies.index(entity)
                if event.source == f"e{idx+1}":
                    is_owner = True
            except ValueError:
                pass
        if is_owner:
            dtype_str = event.damage_type.value if hasattr(event.damage_type, "value") else str(event.damage_type)
            if dtype_str in ("slashing", "bludgeoning", "piercing"):
                event.modified_damage = max(0, event.modified_damage - buff_state.stacks * 3)

    def on_turn_end(self, event, buff_state, entity):
        if event.is_player == (entity == event.run.player):
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                entity.buffs.remove(buff_state)

class FlameBarrierBuff(BuffImpl):
    def on_damage_take_defend(self, event, buff_state, entity, engine):
        if entity == event.run.player and event.target == "p0" and event.source.startswith("e"):
            engine._damage_target(event.run, event.source, buff_state.stacks, damage_type="true")
            engine._log_event(event.run, f"🔥 [火焰屏障] 对攻击源造成了 {buff_state.stacks} 点反弹伤害。")

    def on_turn_end(self, event, buff_state, entity):
        if event.is_player == (entity == event.run.player):
            if buff_state in entity.buffs:
                entity.buffs.remove(buff_state)

class MetallicizeBuff(BuffImpl):
    def on_turn_end(self, event, buff_state, entity):
        if entity == event.run.player and event.is_player:
            shield_gain = buff_state.stacks
            event.engine._gain_shield(event.run, "p0", shield_gain)
            event.engine._log_event(event.run, f"🛡️ [金属化] 触发：玩家获得了 {shield_gain} 点额外护盾。")

class DemonFormBuff(BuffImpl):
    def on_turn_start(self, event, buff_state, entity):
        if entity == event.run.player and event.is_player:
            amount = buff_state.stacks
            event.engine._add_buff_to(entity, "strength", "力量", "造成的伤害增加", amount)
            event.engine._log_event(event.run, f"😈 [恶魔形态] 触发：玩家获得了 {amount} 点力量。")

class DoubleTapBuff(BuffImpl):
    def on_card_played(self, event, buff_state, entity):
        if entity == event.run.player:
            dtype = getattr(event.card, "damage_type", "spell")
            if dtype in ("slashing", "bludgeoning", "piercing"):
                stacks = buff_state.stacks
                res = ""
                for _ in range(stacks):
                    if event.engine.is_battle_won(event.run):
                        break
                    extra_res = event.engine._execute_card_effect(event.run, event.card, event.target)
                    res += f" 🔁 [双发触发] {extra_res}"
                event.feedback += res
                if buff_state in event.run.player.buffs:
                    event.run.player.buffs.remove(buff_state)

    def on_turn_end(self, event, buff_state, entity):
        if entity == event.run.player and event.is_player:
            if buff_state in event.run.player.buffs:
                event.run.player.buffs.remove(buff_state)

class FuryBuff(BuffImpl):
    def on_card_played(self, event, buff_state, entity):
        if event.card.rarity in ("rare", "legendary", "mythic", "artifact"):
            event.engine._add_buff_to(entity, "strength", "力量", "造成的伤害增加", buff_state.stacks)
            event.engine._log_event(event.run, f"🔥 【{entity.name}】的【愤怒】被玩家的【{event.card.name}】激怒，力量增加了 {buff_state.stacks} 点！")

class MinorVulnerableBuff(BuffImpl):
    auto_register = False
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
    auto_register = False
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
    auto_register = False
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
    auto_register = False
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

@register_buff("commander_aurora_emperor")
class AuroraEmperorBuff(BuffImpl):
    def on_damage_calculate(self, event, buff_state, entity):
        if event.source.startswith("p") and event.source != "p0" and event.damage_type == "attack":
            shield = 3 if self.upgraded else 2
            event.engine._gain_shield(event.run, "p0", shield)
            msg = f"🛡️ [极光圣域] 我方随从发起攻击，玩家获得 {shield} 点护盾。"
            if self.upgraded:
                event.engine._draw_cards(event.run.player, 1, event.run)
                msg = f"🛡️ [极光圣域+] 我方随从发起攻击，玩家获得 {shield} 点护盾并抽取 1 张牌。"
            event.engine._log_event(event.run, msg)

for name, obj in list(globals().items()):
    if isinstance(obj, type) and issubclass(obj, BuffImpl) and obj is not BuffImpl:
        if not getattr(obj, "auto_register", True):
            continue
        if obj not in BUFF_CLASS_REGISTRY.values():
            snake = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
            if snake.endswith('_buff'):
                buff_id = snake[:-5]
            else:
                buff_id = snake
            register_buff(buff_id)(obj)

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
    cls = BUFF_CLASS_REGISTRY.get(buff_id)
    if cls:
        inst = cls(stacks)
        inst.stacks2 = stacks2
        inst.upgraded = upgraded
        return inst
    return None
