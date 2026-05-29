from typing import List, Optional

class BuffImpl:
    def __init__(self, stacks: int):
        self.stacks = stacks

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
    def on_turn_start(self, event, buff_state, entity):
        if event.is_player and entity == event.run.player:
            event.run.player.bonus_actions += buff_state.stacks

    def on_player_turn_start(self, run, engine):
        run.player.bonus_actions += self.stacks

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
        num_echoes = min(8, max(0, buff_state.stacks - 8 * played_count))
        if num_echoes > 0:
            res = ""
            for _ in range(num_echoes):
                extra_res = event.engine._execute_card_effect(event.run, event.card, event.target)
                res += f" 🔁 [回响触发] {extra_res}"
            event.feedback += res

    def on_card_played_legacy(self, run, card, target: str, engine) -> str:
        played_count = run.node_data.get("cards_played_this_turn", 0)
        num_echoes = min(8, max(0, self.stacks - 8 * played_count))
        res = ""
        if num_echoes > 0:
            for _ in range(num_echoes):
                extra_res = engine._execute_card_effect(run, card, target)
                res += f" 🔁 [回响触发] {extra_res}"
        return res

class IronWillBuff(BuffImpl):
    def on_heal(self, event, buff_state, entity):
        if event.target == "p0":
            p = event.run.player
            limit = p.max_hp + buff_state.stacks * 10
            if p.hp + event.amount > limit:
                event.amount = max(0, limit - p.hp)

    def modify_heal_limit(self, run, target: str, current_max: int, engine) -> int:
        if target == "p0":
            return current_max + self.stacks * 10
        return current_max

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
            event.modified_damage += buff_state.stacks * 4

    def modify_spell_damage(self, run, card, damage: int, engine) -> int:
        return damage + self.stacks * 4

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
        p = event.run.player
        engine = event.engine
        dmg = self.damage_value
        if p.shield >= dmg:
            p.shield -= dmg
            engine._log_event(event.run, f"💔 [死亡律动] 玩家受到 {dmg} 点伤害（由护盾吸收）。")
        else:
            take = dmg - p.shield
            p.hp -= take
            p.shield = 0
            engine._log_event(event.run, f"💔 [死亡律动] 玩家受到 {take} 点生命伤害。")

class StrengthBuff(BuffImpl):
    pass

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
}

def get_buff_impl(buff_id: str, stacks: int) -> Optional[BuffImpl]:
    cls = BUFF_MAP.get(buff_id)
    if cls:
        return cls(stacks)
    return None

def apply_modify_heal_limit(run, target: str, current_max: int, engine) -> int:
    limit = current_max
    for b in list(run.player.buffs):
        impl = get_buff_impl(b.id, b.stacks)
        if impl:
            limit = impl.modify_heal_limit(run, target, limit, engine)
    return limit

def apply_modify_spell_cost_ba(run, card, cost_ba: int, engine) -> int:
    cost = cost_ba
    for b in list(run.player.buffs):
        impl = get_buff_impl(b.id, b.stacks)
        if impl:
            cost = impl.modify_spell_cost_ba(run, card, cost, engine)
    return cost

def apply_modify_spell_damage(run, card, damage: int, engine) -> int:
    dmg = damage
    if getattr(run.player, "subclass", "") == "塑能法师" and getattr(card, "type", "") == "spell":
        dmg = int(dmg * 1.15)
    for b in list(run.player.buffs):
        impl = get_buff_impl(b.id, b.stacks)
        if impl:
            dmg = impl.modify_spell_damage(run, card, dmg, engine)
    return dmg

def apply_on_card_played(run, card, target: str, engine) -> str:
    res = ""
    for b in list(run.player.buffs):
        impl = get_buff_impl(b.id, b.stacks)
        if impl:
            extra = impl.on_card_played(run, card, target, engine)
            if extra:
                res += " " + extra
    return res

def apply_on_player_turn_start(run, engine):
    for b in list(run.player.buffs):
        impl = get_buff_impl(b.id, b.stacks)
        if impl:
            impl.on_player_turn_start(run, engine)

def apply_on_player_turn_end(run, engine):
    for b in list(run.player.buffs):
        impl = get_buff_impl(b.id, b.stacks)
        if impl:
            impl.on_player_turn_end(run, b, engine)

def apply_prevent_enemy_action(run, enemy, engine, logs: list) -> bool:
    prevented = False
    for b in list(enemy.buffs):
        impl = get_buff_impl(b.id, b.stacks)
        if impl:
            if impl.prevent_enemy_action(run, enemy, b, engine, logs):
                prevented = True
    return prevented
