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

    def on_card_played(self, run, card, target: str, engine) -> str:
        return ""

    def on_player_turn_start(self, run, engine):
        pass

    def on_player_turn_end(self, run, buff_state, engine):
        pass

    def prevent_enemy_action(self, run, enemy, buff_state, engine, logs: list) -> bool:
        return False


class TacticalFocusBuff(BuffImpl):
    def on_player_turn_start(self, run, engine):
        run.player.bonus_actions += self.stacks


class QuickenBuff(BuffImpl):
    def modify_spell_cost_ba(self, run, card, cost_ba: int, engine) -> int:
        if card.type == "spell":
            return max(0, cost_ba - self.stacks)
        return cost_ba


class SpellSurgeBuff(BuffImpl):
    def on_card_played(self, run, card, target: str, engine) -> str:
        if card.color == "wizard":
            engine._draw_cards(run.player, self.stacks)
        return ""


class ArcaneChargeBuff(BuffImpl):
    def modify_spell_damage(self, run, card, damage: int, engine) -> int:
        return damage + self.stacks * 3


class EchoFormBuff(BuffImpl):
    def on_card_played(self, run, card, target: str, engine) -> str:
        played_count = run.node_data.get("cards_played_this_turn", 0)
        num_echoes = min(8, max(0, self.stacks - 8 * played_count))
        res = ""
        if num_echoes > 0:
            for _ in range(num_echoes):
                extra_res = engine._execute_card_effect(run, card, target)
                res += f" 🔁 [回响触发] {extra_res}"
        return res


class IronWillBuff(BuffImpl):
    def modify_heal_limit(self, run, target: str, current_max: int, engine) -> int:
        if target == "p0":
            return current_max + self.stacks * 10
        return current_max


class MagicNetworkBuff(BuffImpl):
    def on_card_played(self, run, card, target: str, engine) -> str:
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


class WishPowerBuff(BuffImpl):
    def modify_spell_damage(self, run, card, damage: int, engine) -> int:
        return damage + self.stacks * 4


class StunBuff(BuffImpl):
    def prevent_enemy_action(self, run, enemy, buff_state, engine, logs: list) -> bool:
        buff_state.stacks -= 1
        if buff_state.stacks <= 0:
            enemy.buffs.remove(buff_state)
        logs.append(f"【{enemy.name}】处于眩晕状态，本回合无法行动。")
        return True


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
