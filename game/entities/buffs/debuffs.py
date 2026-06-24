from typing import List, Optional
import re
from .base import BuffImpl
from .registry import register_buff

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

class StunBuff(BuffImpl):
    def on_turn_start(self, event, buff_state, entity):
        if not event.is_player and entity in event.run.enemies:
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                entity.buffs.remove(buff_state)
            entity.actions = 0
            entity.bonus_actions = 0
            event.engine._log_event(event.run, f"⚠️ 【{entity.name}】处于眩晕状态，本回合无法行动。")
        elif event.is_player and entity == event.run.player:
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                entity.buffs.remove(buff_state)
            entity.actions = 0
            entity.bonus_actions = 0
            event.engine._log_event(event.run, f"⚠️ 你处于眩晕状态，本回合无法行动。")

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

class GenericMinorVulnerableBuff(BuffImpl):
    def on_damage_calculate_defend(self, event, buff_state, entity):
        event.modified_damage = int(event.modified_damage * 1.5)

    def on_turn_start(self, event, buff_state, entity):
        if event.is_player == (entity == event.run.player):
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                entity.buffs.remove(buff_state)

class GenericVulnerableBuff(BuffImpl):
    def on_damage_calculate_defend(self, event, buff_state, entity):
        event.modified_damage = int(event.modified_damage * 2)

    def on_turn_start(self, event, buff_state, entity):
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

class MinorVulnerableBuff(BuffImpl):
    auto_register = False
    def __init__(self, stacks: int, damage_type: str):
        super().__init__(stacks)
        self.damage_type = damage_type

    def on_damage_calculate_defend(self, event, buff_state, entity):
        dtype_str = event.damage_type.value if hasattr(event.damage_type, "value") else str(event.damage_type)
        if dtype_str == self.damage_type:
            event.modified_damage = int(event.modified_damage * 1.5)

    def on_turn_start(self, event, buff_state, entity):
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

    def on_turn_start(self, event, buff_state, entity):
        if event.is_player == (entity == event.run.player):
            buff_state.stacks -= 1
            if buff_state.stacks <= 0:
                entity.buffs.remove(buff_state)

class ShockBuff(BuffImpl):
    def on_damage_calculate_defend(self, event, buff_state, entity):
        dtype_str = event.damage_type.value if hasattr(event.damage_type, "value") else str(event.damage_type)
        if dtype_str in ("lightning", "thunder"):
            event.modified_damage += buff_state.stacks * 1

    def on_turn_start(self, event, buff_state, entity):
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

class BleedBuff(BuffImpl):
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
        damage = 4
        engine._log_event(run, f"🩸 【{entity.name}】受到流血造成的 {damage} 点真实伤害！")
        engine._damage_target(run, target, damage, source="bleed", damage_type="true")
        buff_state.stacks -= 1
        if buff_state.stacks <= 0:
            if buff_state in entity.buffs:
                entity.buffs.remove(buff_state)


for name, obj in list(globals().items()):
    if isinstance(obj, type) and issubclass(obj, BuffImpl) and obj is not BuffImpl:
        if not getattr(obj, "auto_register", True):
            continue
        snake = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        if snake.endswith('_buff'):
            buff_id = snake[:-5]
        else:
            buff_id = snake
        register_buff(buff_id)(obj)
