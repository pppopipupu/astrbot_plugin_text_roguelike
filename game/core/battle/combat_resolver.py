import random
from typing import Optional
from ...models.state import GameRun, PlayerState, EnemyState, MinionState, Card, BuffState
from ...models.events import (
    DamageCalculateEvent, DamageTakeEvent, HealEvent, MinionDeathEvent, MinionSummonEvent, ShieldGainEvent
)

DAMAGE_TYPE_NAMES = {
    "acid": "强酸",
    "bludgeoning": "钝击",
    "cold": "寒冷",
    "fire": "火焰",
    "force": "力场",
    "lightning": "闪电",
    "necrotic": "黯蚀",
    "piercing": "穿刺",
    "poison": "毒素",
    "psychic": "心灵",
    "radiant": "光耀",
    "slashing": "挥砍",
    "thunder": "雷鸣",
    "true": "真实",
    "attack": "物理",
    "effect": "效果",
    "spell": "法术"
}

class CombatResolver:
    def __init__(self, engine):
        self.engine = engine

    def get_target_name(self, run: GameRun, target: Optional[str]) -> str:
        if not target:
            return "无"
        if target == "p0":
            return "玩家"
        if target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if idx < 0: idx = 0
            except ValueError:
                idx = 0
            if 0 <= idx < len(run.enemies):
                return run.enemies[idx].name
            return "未知敌人"
        if target.startswith("p"):
            grid = target[1:]
            if grid in run.player.minions:
                return run.player.minions[grid].name
            return "我方随随从"
        return "未知"

    def get_first_alive_enemy(self, run: GameRun) -> str:
        for idx, enemy in enumerate(run.enemies, 1):
            if enemy.hp > 0:
                return f"e{idx}"
        return "e1"

    def get_free_grid(self, p: PlayerState) -> Optional[str]:
        for i in range(1, 7):
            s = str(i)
            if s not in p.minions and s not in p.amulets:
                return s
        return None

    def get_modified_spell_damage(self, run: GameRun, card: Card, damage: int) -> int:
        dtype = getattr(card, "damage_type", "spell")
        calc_evt = DamageCalculateEvent(run, card, "p0", "e1", dtype, damage, damage)
        self.engine.event_bus.dispatch(calc_evt)
        return calc_evt.modified_damage

    def add_buff_to(self, entity, buff_id: str, buff_name: str, desc: str, count: int = 1, count2: Optional[int] = None):
        for b in entity.buffs:
            if b.id == buff_id:
                b.stacks += count
                if count2 is not None:
                    if b.stacks2 is None:
                        b.stacks2 = 0
                    b.stacks2 += count2
                if buff_id == "stun" and isinstance(entity, EnemyState):
                    self.engine._sync_enemy_intents(entity)
                return
        entity.buffs.append(BuffState(buff_id, buff_name, count, count2, desc))
        if buff_id == "stun" and isinstance(entity, EnemyState):
            self.engine._sync_enemy_intents(entity)

    def gain_shield(self, run: GameRun, target: str, amount: int):
        evt = ShieldGainEvent(run, target, amount, amount)
        self.engine.event_bus.dispatch(evt)
        final_amount = evt.modified_amount
        if final_amount <= 0:
            return
        if target == "p0":
            run.player.shield += final_amount
        elif target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if idx < 0: idx = 0
            except ValueError:
                idx = 0
            if 0 <= idx < len(run.enemies):
                run.enemies[idx].shield += final_amount

    def heal_target(self, run: GameRun, target: str, heal: int):
        heal_evt = HealEvent(run, target, heal)
        self.engine.event_bus.dispatch(heal_evt)
        if heal_evt.cancelled:
            return
        heal = heal_evt.amount
        p = run.player
        if target == "p0":
            from ...entities.buffs.buffs import apply_modify_heal_limit
            cur_max_hp = apply_modify_heal_limit(run, "p0", p.max_hp, self.engine)
            p.hp = min(cur_max_hp, p.hp + heal)
        elif target.startswith("p"):
            grid = target[1:]
            if grid in p.minions:
                p.minions[grid].hp = min(p.minions[grid].max_hp, p.minions[grid].hp + heal)

    def recall_dead_minion(self, run: GameRun, hp_limit: int) -> str:
        p = run.player
        from ...entities.cards.base import ALL_CARDS
        eligible = []
        for cid in p.minion_graveyard:
            card = ALL_CARDS.get(cid)
            if card and card.type == "minion":
                hp_val = getattr(card, "minion_hp", 999)
                if hp_val < hp_limit:
                    eligible.append(cid)
        if not eligible:
            return "墓地中没有符合条件的随从。"
        chosen_cid = random.choice(eligible)
        p.minion_graveyard.remove(chosen_cid)
        card = ALL_CARDS[chosen_cid]
        hp_val = getattr(card, "minion_hp", 10)
        atk_val = getattr(card, "minion_atk", 1)
        grid = self.summon_minion(run, chosen_cid, card.name, hp_val, atk_val, 0)
        if grid:
            return f"从墓地召回了【{card.name}】（格子 [{grid}]）。"
        return "战场已满，召回失败。"

    def summon_minion(self, run: GameRun, minion_id: str, name: str, hp: int, atk: int, ba: int) -> Optional[str]:
        grid = self.get_free_grid(run.player)
        if grid:
            m = MinionState(minion_id, name, hp, hp, atk, 1, ba)
            evt = MinionSummonEvent(run, m, grid)
            self.engine.event_bus.dispatch(evt)
            run.player.minions[grid] = m
            return grid
        return None

    def damage_target(self, run: GameRun, target: str, dmg: int, source: str = "effect", damage_type: str = "effect", card: Optional[Card] = None):
        target_name = self.get_target_name(run, target)
        calc_evt = DamageCalculateEvent(run, card, source, target, damage_type, dmg, dmg)
        self.engine.event_bus.dispatch(calc_evt)
        final_dmg = max(0, calc_evt.modified_damage)
        p = run.player
        is_fatal = False
        is_true = False
        if damage_type == "true" or damage_type == "TRUE":
            is_true = True
        elif hasattr(damage_type, "value") and (damage_type.value == "true" or damage_type.value == "TRUE"):
            is_true = True
        shield_dmg = 0
        hp_dmg = 0
        if target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if idx < 0: idx = 0
            except ValueError:
                idx = 0
            if 0 <= idx < len(run.enemies):
                e = run.enemies[idx]
                if is_true:
                    hp_dmg = final_dmg
                    e.hp -= final_dmg
                else:
                    if e.shield >= final_dmg:
                        e.shield -= final_dmg
                        shield_dmg = final_dmg
                    else:
                        shield_dmg = e.shield
                        hp_dmg = final_dmg - e.shield
                        e.hp -= hp_dmg
                        e.shield = 0
                if e.hp <= 0:
                    if e.name == "虚空之门·尤格-索托斯":
                        e.name = "【觉醒】虚空之门·尤格-索托斯"
                        e.max_hp = 260
                        e.hp = 260
                        e.shield = 30
                        e.actions = 2
                        e.bonus_actions = 2
                        e.max_actions = 2
                        e.max_bonus_actions = 2
                        e.buffs.clear()
                        e.buffs.append(BuffState(id="end_gate_passive", name="终焉之门", stacks=1, desc="每回合开始时获得 15 点护盾，且清除自身所有负面效果，受到伤害时 30% 几率反弹 4 点真实伤害"))
                        run.node_data["yog_sothoth_phase"] = 2
                        run.node_data["yog_sothoth_turn"] = 0
                        e.intents.clear()
                        self.engine._log_event(run, "🌟 虚空之门·尤格-索托斯破裂了！狂暴的虚空能量从中倾泻而出，虚空之门在坍缩中重新觉醒！进入了觉醒形态！")
                    else:
                        is_fatal = True
                        p.enemy_graveyard.append(e.name)
                        run.enemies.pop(idx)
                        death_evt = MinionDeathEvent(run, e.name, target, e.name, True)
                        self.engine.event_bus.dispatch(death_evt)
                take_evt = DamageTakeEvent(run, source, target, final_dmg, is_fatal, damage_type)
                self.engine.event_bus.dispatch(take_evt)
        elif target == "p0":
            run.node_data["last_shield_before_dmg"] = p.shield
            if final_dmg > 0:
                run.node_data["player_damaged_this_turn"] = True
            if is_true:
                hp_dmg = final_dmg
                p.hp -= final_dmg
            else:
                if p.shield >= final_dmg:
                    p.shield -= final_dmg
                    shield_dmg = final_dmg
                else:
                    shield_dmg = p.shield
                    hp_dmg = final_dmg - p.shield
                    p.hp -= hp_dmg
                    p.shield = 0
            if p.hp <= 0:
                is_fatal = True
            take_evt = DamageTakeEvent(run, source, target, final_dmg, is_fatal, damage_type)
            self.engine.event_bus.dispatch(take_evt)
        elif target.startswith("p"):
            grid = target[1:]
            if grid in p.minions:
                m = p.minions[grid]
                hp_dmg = final_dmg
                m.hp -= final_dmg
                if m.hp <= 0:
                    is_fatal = True
                    p.minion_graveyard.append(m.id)
                    del p.minions[grid]
                    death_evt = MinionDeathEvent(run, m.id, target, m.name, False)
                    self.engine.event_bus.dispatch(death_evt)
                take_evt = DamageTakeEvent(run, source, target, final_dmg, is_fatal, damage_type)
                self.engine.event_bus.dispatch(take_evt)
        damage_type_str = damage_type.value if hasattr(damage_type, "value") else str(damage_type)
        type_name = DAMAGE_TYPE_NAMES.get(damage_type_str, "物理" if damage_type_str == "attack" else "特殊")
        log_msg = f"对【{target_name}】造成 {final_dmg} 点{type_name}伤害"
        if shield_dmg == 0 and hp_dmg == 0:
            log_msg += f"（但{target_name}免疫了这次攻击！）"
        else:
            if shield_dmg > 0:
                log_msg += f"，对护盾造成 {shield_dmg} 伤害"
            if hp_dmg > 0:
                log_msg += f"，对生命造成 {hp_dmg} 伤害"
        self.engine._log_event(run, log_msg)
