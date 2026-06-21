import random
from typing import Optional
from ...models.state import GameRun, PlayerState, MinionState, Card, BuffState
from ...models.events import DamageCalculateEvent, MinionSummonEvent

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

class DuelCombatResolver:
    def __init__(self, engine):
        self.engine = engine

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

    def get_first_alive_enemy(self, run: GameRun) -> str:
        for idx, enemy in enumerate(run.enemies, 1):
            if enemy.hp > 0:
                return f"e{idx}"
        return "e1"

    def summon_minion(self, run: GameRun, minion_id: str, name: str, hp: int, atk: int, ba: int) -> Optional[str]:
        grid = self.get_free_grid(run.player)
        if grid:
            m = MinionState(minion_id, name, hp, hp, atk, 1, ba)
            evt = MinionSummonEvent(run, m, grid)
            self.engine.event_bus.dispatch(evt)
            run.player.minions[grid] = m
            return grid
        return None

    def add_buff_to(self, entity, buff_id: str, buff_name: str, desc: str, count: int = 1, count2: Optional[int] = None):
        for b in entity.buffs:
            if b.id == buff_id:
                b.stacks += count
                if count2 is not None:
                    if b.stacks2 is None:
                        b.stacks2 = 0
                    b.stacks2 += count2
                return
        entity.buffs.append(BuffState(buff_id, buff_name, count, count2, desc))

    def recall_dead_minion(self, run: GameRun, hp_limit: int) -> str:
        p = run.player
        try:
            from ...entities.cards.duel import ALL_DUEL_CARDS
        except ImportError:
            from game.entities.cards.duel import ALL_DUEL_CARDS
        eligible = []
        for cid in p.minion_graveyard:
            card = ALL_DUEL_CARDS.get(cid)
            if card and card.type == "minion":
                hp_val = getattr(card, "minion_hp", 999)
                if hp_val < hp_limit:
                    eligible.append(cid)
        if not eligible:
            return "墓地中没有符合条件的随从。"
        chosen_cid = random.choice(eligible)
        p.minion_graveyard.remove(chosen_cid)
        card = ALL_DUEL_CARDS[chosen_cid]
        hp_val = getattr(card, "minion_hp", 10)
        atk_val = getattr(card, "minion_atk", 1)
        grid = self.summon_minion(run, chosen_cid, card.name, hp_val, atk_val, 0)
        if grid:
            return f"从墓地召回了【{card.name}】（格子 [{grid}]）。"
        return "战场已满，召回失败。"
