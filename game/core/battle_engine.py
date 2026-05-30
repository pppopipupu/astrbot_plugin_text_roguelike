import random
from typing import Optional, List, Dict
import sys
from ..models.state import GameRun, PlayerState, EnemyState, MinionState, AmuletState, Card, BuffState, check_and_replace_fireball
from ..entities import (
    ALL_CARDS,
    ALL_MINIONS,
    ALL_AMULETS,
    get_enemy_template,
    get_relic_name,
    get_relic_impl,
    apply_modify_heal_limit,
    apply_modify_spell_cost_ba,
    apply_modify_spell_damage,
    apply_on_card_played,
    apply_on_player_turn_start,
    apply_on_player_turn_end,
    apply_prevent_enemy_action,
)
from ..models.events import (
    BattleStartEvent, BattleWinEvent, TurnStartEvent, TurnEndEvent,
    CardPlayEvent, CardPlayedEvent, DamageCalculateEvent, DamageTakeEvent,
    HealEvent, CardDiscardEvent, MinionDeathEvent, MinionSummonEvent,
    CardExhaustEvent, ShieldGainEvent
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

class BattleEngine:
    def __init__(self, save_manager):
        self.save_manager = save_manager
        self.event_bus = self._init_event_bus()
        orig_dispatch = self.event_bus.dispatch
        def decorated_dispatch(event, *args, **kwargs):
            event.engine = self
            return orig_dispatch(event, *args, **kwargs)
        self.event_bus.dispatch = decorated_dispatch

    def _init_event_bus(self):
        from .event_bus import EventBus
        bus = EventBus()
        bus.subscribe(BattleStartEvent, self._proxy_battle_start)
        bus.subscribe(BattleWinEvent, self._proxy_battle_win)
        bus.subscribe(TurnStartEvent, self._proxy_turn_start)
        bus.subscribe(TurnEndEvent, self._proxy_turn_end)
        bus.subscribe(CardPlayEvent, self._proxy_card_play)
        bus.subscribe(CardPlayedEvent, self._proxy_card_played)
        bus.subscribe(DamageCalculateEvent, self._proxy_damage_calculate)
        bus.subscribe(DamageTakeEvent, self._proxy_damage_take)
        bus.subscribe(HealEvent, self._proxy_heal)
        bus.subscribe(CardDiscardEvent, self._proxy_card_discard)
        bus.subscribe(MinionDeathEvent, self._proxy_minion_death)
        bus.subscribe(MinionSummonEvent, self._proxy_minion_summon)
        bus.subscribe(CardExhaustEvent, self._proxy_card_exhaust)
        bus.subscribe(ShieldGainEvent, self._proxy_shield_gain)
        return bus

    def _proxy_battle_start(self, event):
        from ..entities.relics.relics import get_relic_impl
        for r in list(event.run.player.relics):
            impl = get_relic_impl(r)
            if impl and hasattr(impl, "on_battle_start"):
                impl.on_battle_start(event.run, self)

    def _proxy_battle_win(self, event):
        from ..entities.relics.relics import get_relic_impl
        for r in list(event.run.player.relics):
            impl = get_relic_impl(r)
            if impl and hasattr(impl, "on_battle_win"):
                impl.on_battle_win(event.run, self)

    def _proxy_turn_start(self, event):
        from ..entities.relics.relics import get_relic_impl
        from ..entities.buffs.buffs import get_buff_impl
        if event.is_player:
            event.run.node_data["player_damaged_this_turn"] = False
            for r in list(event.run.player.relics):
                impl = get_relic_impl(r)
                if impl and hasattr(impl, "on_turn_start"):
                    impl.on_turn_start(event, event.run, self)
        entities_with_buffs = []
        if event.is_player:
            entities_with_buffs.append((event.run.player, event.run.player))
        else:
            for enemy in list(event.run.enemies):
                entities_with_buffs.append((enemy, enemy))
        for entity, original in entities_with_buffs:
            for b in list(entity.buffs):
                impl = get_buff_impl(b.id, b.stacks)
                if impl and hasattr(impl, "on_turn_start"):
                    impl.on_turn_start(event, b, entity)

    def _proxy_turn_end(self, event):
        from ..entities.buffs.buffs import get_buff_impl
        entities_with_buffs = []
        if event.is_player:
            entities_with_buffs.append((event.run.player, event.run.player))
        else:
            for enemy in list(event.run.enemies):
                entities_with_buffs.append((enemy, enemy))
        for entity, original in entities_with_buffs:
            for b in list(entity.buffs):
                impl = get_buff_impl(b.id, b.stacks)
                if impl and hasattr(impl, "on_turn_end"):
                    impl.on_turn_end(event, b, entity)

    def _proxy_card_play(self, event):
        from ..entities.buffs.buffs import get_buff_impl
        for b in list(event.run.player.buffs):
            impl = get_buff_impl(b.id, b.stacks)
            if impl and hasattr(impl, "on_card_play"):
                impl.on_card_play(event, b, event.run.player)

    def _proxy_card_played(self, event):
        from ..entities.relics.relics import get_relic_impl
        from ..entities.buffs.buffs import get_buff_impl
        from ..entities.amulets.amulets import ALL_AMULETS
        for r in list(event.run.player.relics):
            impl = get_relic_impl(r)
            if impl and hasattr(impl, "on_card_played"):
                impl.on_card_played(event, event.run, self)
        for b in list(event.run.player.buffs):
            impl = get_buff_impl(b.id, b.stacks)
            if impl and hasattr(impl, "on_card_played"):
                impl.on_card_played(event, b, event.run.player)
        for enemy in list(event.run.enemies):
            for b in list(enemy.buffs):
                impl = get_buff_impl(b.id, b.stacks)
                if impl and hasattr(impl, "on_card_played"):
                    impl.on_card_played(event, b, enemy)
        for ak, av in list(event.run.player.amulets.items()):
            base_id = av.id[:-1] if av.id.endswith("+") else av.id
            template = ALL_AMULETS.get(base_id)
            if template and hasattr(template, "on_spell_played") and event.card.type == "spell":
                template.on_spell_played(event.run, ak, event.card, self)

    def _proxy_damage_calculate(self, event):
        from ..entities.relics.relics import get_relic_impl
        from ..entities.buffs.buffs import get_buff_impl
        if event.source == "p0":
            for r in list(event.run.player.relics):
                impl = get_relic_impl(r)
                if impl and hasattr(impl, "on_damage_calculate"):
                    impl.on_damage_calculate(event, event.run, self)
        if event.source == "p0":
            for b in list(event.run.player.buffs):
                impl = get_buff_impl(b.id, b.stacks)
                if impl and hasattr(impl, "on_damage_calculate"):
                    impl.on_damage_calculate(event, b, event.run.player)
        if event.source.startswith("e"):
            try:
                idx = int(event.source[1:]) - 1
                if idx < 0: idx = 0
            except ValueError:
                idx = 0
            if 0 <= idx < len(event.run.enemies):
                enemy = event.run.enemies[idx]
                for b in list(enemy.buffs):
                    impl = get_buff_impl(b.id, b.stacks)
                    if impl and hasattr(impl, "on_damage_calculate"):
                        impl.on_damage_calculate(event, b, enemy)

        if event.target == "p0":
            for b in list(event.run.player.buffs):
                impl = get_buff_impl(b.id, b.stacks)
                if impl and hasattr(impl, "on_damage_calculate_defend"):
                    impl.on_damage_calculate_defend(event, b, event.run.player)
        elif event.target.startswith("e"):
            try:
                idx = int(event.target[1:]) - 1
                if idx < 0: idx = 0
            except ValueError:
                idx = 0
            if 0 <= idx < len(event.run.enemies):
                enemy = event.run.enemies[idx]
                for b in list(enemy.buffs):
                    impl = get_buff_impl(b.id, b.stacks)
                    if impl and hasattr(impl, "on_damage_calculate_defend"):
                        impl.on_damage_calculate_defend(event, b, enemy)

    def _proxy_damage_take(self, event):
        from ..entities.amulets.amulets import ALL_AMULETS
        if event.target == "p0" and event.amount > 0:
            for ak, av in list(event.run.player.amulets.items()):
                base_id = av.id[:-1] if av.id.endswith("+") else av.id
                template = ALL_AMULETS.get(base_id)
                if template and hasattr(template, "on_take_damage"):
                    msg = template.on_take_damage(event.run, ak, event.source, event.amount, self)
                    if msg:
                        self._log_event(event.run, msg)

    def _proxy_heal(self, event):
        from ..entities.relics.relics import get_relic_impl
        from ..entities.buffs.buffs import get_buff_impl
        if event.target == "p0":
            for r in list(event.run.player.relics):
                impl = get_relic_impl(r)
                if impl and hasattr(impl, "on_heal"):
                    impl.on_heal(event, event.run, self)
        if event.target == "p0":
            for b in list(event.run.player.buffs):
                impl = get_buff_impl(b.id, b.stacks)
                if impl and hasattr(impl, "on_heal"):
                    impl.on_heal(event, b, event.run.player)

    def _proxy_card_discard(self, event):
        pass

    def _proxy_minion_death(self, event):
        pass

    def _proxy_minion_summon(self, event):
        from ..entities.relics.relics import get_relic_impl
        for r in list(event.run.player.relics):
            impl = get_relic_impl(r)
            if impl and hasattr(impl, "on_minion_summon"):
                impl.on_minion_summon(event, event.run, self)

    def _proxy_card_exhaust(self, event):
        pass

    def _proxy_shield_gain(self, event):
        from ..entities.relics.relics import get_relic_impl
        from ..entities.buffs.buffs import get_buff_impl
        if event.target == "p0":
            for r in list(event.run.player.relics):
                impl = get_relic_impl(r)
                if impl and hasattr(impl, "on_shield_gain"):
                    impl.on_shield_gain(event, event.run, self)
            for b in list(event.run.player.buffs):
                impl = get_buff_impl(b.id, b.stacks)
                if impl and hasattr(impl, "on_shield_gain"):
                    impl.on_shield_gain(event, b, event.run.player)

    def _log_event(self, run: Optional[GameRun], msg: str):
        if run is None:
            return
        if "battle_logs" not in run.node_data:
            run.node_data["battle_logs"] = []
        run.node_data["battle_logs"].append(msg)

    def _append_logs_to_res(self, run: GameRun, res: str) -> str:
        if "battle_logs" in run.node_data:
            logs = run.node_data.pop("battle_logs", [])
            if logs:
                res = res.rstrip() + "\n" + "\n".join(logs)
        return res

    def is_battle_won(self, run: GameRun) -> bool:
        if not run.enemies:
            return True
        if all(e.hp <= 0 for e in run.enemies):
            return True
        alive_enemies = [e for e in run.enemies if e.hp > 0]
        if all(e.is_summon for e in alive_enemies):
            return True
        return False

    def _get_first_alive_enemy(self, run: GameRun) -> str:
        for idx, enemy in enumerate(run.enemies, 1):
            if enemy.hp > 0:
                return f"e{idx}"
        return "e1"

    def _get_target_name(self, run: GameRun, target: Optional[str]) -> str:
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

    def _damage_target(self, run: GameRun, target: str, dmg: int, source: str = "effect", damage_type: str = "effect", card: Optional[Card] = None):
        target_name = self._get_target_name(run, target)
        calc_evt = DamageCalculateEvent(run, card, source, target, damage_type, dmg, dmg)
        self.event_bus.dispatch(calc_evt)
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
                    is_fatal = True
                    p.enemy_graveyard.append(e.name)
                    run.enemies.pop(idx)
                    death_evt = MinionDeathEvent(run, e.name, target, e.name, True)
                    self.event_bus.dispatch(death_evt)
                take_evt = DamageTakeEvent(run, source, target, final_dmg, is_fatal)
                self.event_bus.dispatch(take_evt)
        elif target == "p0":
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
            take_evt = DamageTakeEvent(run, source, target, final_dmg, is_fatal)
            self.event_bus.dispatch(take_evt)
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
                    self.event_bus.dispatch(death_evt)
                take_evt = DamageTakeEvent(run, source, target, final_dmg, is_fatal)
                self.event_bus.dispatch(take_evt)
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
        self._log_event(run, log_msg)

    def _heal_target(self, run: GameRun, target: str, heal: int):
        heal_evt = HealEvent(run, target, heal)
        self.event_bus.dispatch(heal_evt)
        if heal_evt.cancelled:
            return
        heal = heal_evt.amount
        p = run.player
        if target == "p0":
            p.hp = min(p.max_hp, p.hp + heal)
        elif target.startswith("p"):
            grid = target[1:]
            if grid in p.minions:
                p.minions[grid].hp = min(p.minions[grid].max_hp, p.minions[grid].hp + heal)

    def _summon_minion(self, run: GameRun, minion_id: str, name: str, hp: int, atk: int, ba: int) -> Optional[str]:
        grid = self._get_free_grid(run.player)
        if grid:
            m = MinionState(minion_id, name, hp, hp, atk, 1, ba)
            evt = MinionSummonEvent(run, m, grid)
            self.event_bus.dispatch(evt)
            run.player.minions[grid] = m
            return grid
        return None

    def _gain_shield(self, run: GameRun, target: str, amount: int):
        evt = ShieldGainEvent(run, target, amount, amount)
        self.event_bus.dispatch(evt)
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

    def _sync_enemy_intents(self, enemy: EnemyState):
        from ..models.state import EnemyIntentState
        has_old_active = False
        old_intents = []
        if enemy.intent_a_desc and "已取消" not in enemy.intent_a_desc and "眩晕" not in enemy.intent_a_desc:
            old_intents.append(EnemyIntentState(type=enemy.intent_a_type, val=enemy.intent_a_val, desc=enemy.intent_a_desc, cost_a=1, cost_ba=0))
            has_old_active = True
        if getattr(enemy, "intent_a2_desc", None) and "已取消" not in enemy.intent_a2_desc:
            old_intents.append(EnemyIntentState(type=enemy.intent_a2_type, val=enemy.intent_a2_val, desc=enemy.intent_a2_desc, cost_a=1, cost_ba=0))
            has_old_active = True
        if enemy.intent_ba_desc and "已取消" not in enemy.intent_ba_desc:
            old_intents.append(EnemyIntentState(type=enemy.intent_ba_type, val=enemy.intent_ba_val, desc=enemy.intent_ba_desc, cost_a=0, cost_ba=1))
            has_old_active = True
        if getattr(enemy, "intent_ba2_desc", None) and "已取消" not in enemy.intent_ba2_desc:
            old_intents.append(EnemyIntentState(type=enemy.intent_ba2_type, val=enemy.intent_ba2_val, desc=enemy.intent_ba2_desc, cost_a=0, cost_ba=1))
            has_old_active = True

        if has_old_active:
            if not enemy.intents or len(enemy.intents) != len(old_intents) or any(
                enemy.intents[i].type != old_intents[i].type or enemy.intents[i].desc != old_intents[i].desc
                for i in range(min(len(enemy.intents), len(old_intents)))
            ):
                enemy.intents = old_intents

        has_stun = False
        if getattr(enemy, "buffs", None):
            for b in enemy.buffs:
                if b.id == "stun" and b.stacks > 0:
                    has_stun = True
                    break
        if has_stun:
            enemy.actions = 0
            enemy.bonus_actions = 0
            enemy.intents = [
                EnemyIntentState(
                    type="stun",
                    val=0,
                    desc="眩晕 (本回合无法行动)",
                    cost_a=0,
                    cost_ba=0
                )
            ]
        else:
            temp_a = enemy.actions
            temp_ba = enemy.bonus_actions
            for it in enemy.intents:
                it.cancelled = False
                it.cancelled_desc = ""
                if it.cost_a > 0:
                    if temp_a >= it.cost_a:
                        temp_a -= it.cost_a
                    else:
                        it.cancelled = True
                        it.cancelled_desc = "已取消 (动作点不足)"
                if it.cost_ba > 0:
                    if temp_ba >= it.cost_ba:
                        temp_ba -= it.cost_ba
                    else:
                        it.cancelled = True
                        it.cancelled_desc = "已取消 (动作点不足)"
        enemy.intent_a_type = ""
        enemy.intent_a_val = 0
        enemy.intent_a_desc = ""
        enemy.intent_a2_type = ""
        enemy.intent_a2_val = 0
        enemy.intent_a2_desc = ""
        enemy.intent_ba_type = ""
        enemy.intent_ba_val = 0
        enemy.intent_ba_desc = ""
        enemy.intent_ba2_type = ""
        enemy.intent_ba2_val = 0
        enemy.intent_ba2_desc = ""
        a_slots = []
        ba_slots = []
        for it in enemy.intents:
            desc = it.cancelled_desc if it.cancelled else it.desc
            itype = "" if (it.cancelled or it.type == "stun") else it.type
            val = 0 if it.cancelled else it.val
            if it.cost_ba > 0:
                ba_slots.append((itype, val, desc))
            else:
                a_slots.append((itype, val, desc))
        if len(a_slots) >= 1:
            enemy.intent_a_type, enemy.intent_a_val, enemy.intent_a_desc = a_slots[0]
        if len(a_slots) >= 2:
            enemy.intent_a2_type, enemy.intent_a2_val, enemy.intent_a2_desc = a_slots[1]
        if len(ba_slots) >= 1:
            enemy.intent_ba_type, enemy.intent_ba_val, enemy.intent_ba_desc = ba_slots[0]
        if len(ba_slots) >= 2:
            enemy.intent_ba2_type, enemy.intent_ba2_val, enemy.intent_ba2_desc = ba_slots[1]

    def _add_buff_to(self, entity, buff_id: str, buff_name: str, desc: str, count: int = 1):
        for b in entity.buffs:
            if b.id == buff_id:
                b.stacks += count
                if buff_id == "stun" and isinstance(entity, EnemyState):
                    self._sync_enemy_intents(entity)
                return
        entity.buffs.append(BuffState(buff_id, buff_name, count, desc))
        if buff_id == "stun" and isinstance(entity, EnemyState):
            self._sync_enemy_intents(entity)

    def _get_free_grid(self, p: PlayerState) -> Optional[str]:
        for i in range(1, 7):
            s = str(i)
            if s not in p.minions and s not in p.amulets:
                return s
        return None

    def _draw_cards(self, p: PlayerState, count: int, run: Optional[GameRun] = None):
        max_hand = 9 if "mask_of_void" in p.relics else 12
        drawn_cards = []
        reshuffled = False
        hand_full_logged = False
        for _ in range(count):
            if not p.draw_pile:
                if p.discard_pile:
                    p.draw_pile = p.discard_pile.copy()
                    random.shuffle(p.draw_pile)
                    p.discard_pile.clear()
                    reshuffled = True
            if p.draw_pile:
                if len(p.hand) < max_hand:
                    cid = p.draw_pile.pop()
                    p.hand.append(cid)
                    drawn_cards.append(cid)
                else:
                    if not hand_full_logged and run is not None:
                        self._log_event(run, "⚠️ 提示：手牌已达上限，无法抽取更多卡牌。")
                        hand_full_logged = True
        if run is not None:
            if reshuffled:
                self._log_event(run, "🔄 弃牌堆已重新洗入抽牌堆。")

    def _init_battle_node(self, run: GameRun, difficulty: str = "normal"):
        p = run.player
        p.hand.clear()
        p.draw_pile = p.deck.copy()
        random.shuffle(p.draw_pile)
        p.discard_pile.clear()
        p.exhaust_pile.clear()
        p.minion_graveyard.clear()
        p.enemy_graveyard.clear()
        p.minions.clear()
        p.amulets.clear()
        p.buffs.clear()
        p.actions = 2
        p.bonus_actions = 1
        p.shield = 0
        run.node_data["cards_played_this_turn"] = 0

        evt_start = BattleStartEvent(run)
        self.event_bus.dispatch(evt_start)

        if getattr(p, "subclass", "") == "时序法师":
            if random.random() < 0.25:
                p.bonus_actions += 1
                self._log_event(run, "⏳ [时序被动] 触发时间跳跃，初始额外获得 1 个附赠动作（BA）！")
        init_draw = 5
        for r in p.relics:
            impl = get_relic_impl(r)
            if impl:
                init_draw = impl.modify_initial_draw(run, init_draw, self)
        self._draw_cards(p, init_draw, run)
        run.node_data["difficulty"] = difficulty

        if difficulty == "boss":
            if p.stage == 20:
                boss_cfg = self.save_manager.load_admin_config()
                boss_setting = boss_cfg.get("final_boss", "random")
                if boss_setting == "random":
                    boss_name = random.choice(["腐化之心", "Icerainboww"])
                else:
                    boss_name = boss_setting

                if boss_name == "腐化之心":
                    run.enemies = [EnemyState(
                        name="腐化之心",
                        hp=120,
                        max_hp=120,
                        shield=0,
                        actions=1,
                        bonus_actions=2,
                        max_actions=1,
                        max_bonus_actions=2
                    )]
                    self._add_buff_to(run.enemies[0], "beat_of_death", "死亡律动", "玩家每使用一张牌，受到 1 点力场伤害。")
                    run.node_data["boss_name"] = "腐化之心"
                else:
                    run.enemies = [EnemyState(
                        name="Icerainboww",
                        hp=160,
                        max_hp=160,
                        shield=0,
                        actions=2,
                        bonus_actions=0,
                        max_actions=2,
                        max_bonus_actions=0
                    )]
                    run.node_data["boss_name"] = "Icerainboww"
                    run.node_data["icerainboww_turn"] = 1
            else:
                boss_name = random.choice(["远古红龙", "雷霆领主"])
                if boss_name == "远古红龙":
                    run.enemies = [EnemyState(
                        name="远古红龙",
                        hp=140,
                        max_hp=140,
                        shield=0,
                        actions=1,
                        bonus_actions=2,
                        max_actions=1,
                        max_bonus_actions=2
                    )]
                else:
                    run.enemies = [EnemyState(
                        name="雷霆领主",
                        hp=130,
                        max_hp=130,
                        shield=0,
                        actions=1,
                        bonus_actions=2,
                        max_actions=1,
                        max_bonus_actions=2
                    )]
                    run.node_data["thunder_lord_turn"] = 1
        elif difficulty == "elite":
            from ..data.enemy_data import ENEMY_CONFIG
            elite_pool = [
                "地精百夫长", "石像鬼祭司", "狂暴兽王",
                "黑曜石巨灵", "幽灵大魔法师", "暗影影魔",
                "末日守卫", "亡灵巫师"
            ]
            run.enemies = []
            base_name = random.choice(elite_pool)
            cfg = ENEMY_CONFIG.get(base_name, {})
            import re
            hp_str = cfg.get("hp", "30")
            base_hp = 30
            match = re.match(r"^(\d+)", hp_str)
            if match:
                base_hp = int(match.group(1))
            hp_final = base_hp + p.stage * 3

            actions_str = cfg.get("actions", "1A 1BA")
            act_match = re.search(r"(\d+)A", actions_str)
            ba_match = re.search(r"(\d+)BA", actions_str)
            actions = int(act_match.group(1)) if act_match else 1
            bonus_actions = int(ba_match.group(1)) if ba_match else 1

            run.enemies.append(EnemyState(
                name=base_name,
                hp=hp_final,
                max_hp=hp_final,
                shield=0,
                actions=actions,
                bonus_actions=bonus_actions,
                max_actions=actions,
                max_bonus_actions=bonus_actions
            ))
        else:
            from ..data.enemy_data import ENEMY_CONFIG
            normal_pool = [
                "地精突袭者", "石像鬼守卫", "堕落学徒", "狂暴野兽",
                "幽灵法师", "冰霜史莱姆", "骷髅弓箭手", "剧毒蜘蛛",
                "黑曜石巨人", "暗影刺客"
            ]
            run.enemies = []
            num_enemies = random.randint(1, 3)
            selected_names = [random.choice(normal_pool) for _ in range(num_enemies)]
            for i, base_name in enumerate(selected_names):
                cfg = ENEMY_CONFIG.get(base_name, {})
                import re
                hp_str = cfg.get("hp", "12")
                base_hp = 12
                match = re.match(r"^(\d+)", hp_str)
                if match:
                    base_hp = int(match.group(1))
                hp_final = base_hp + p.stage * 2

                actions_str = cfg.get("actions", "1A 0BA")
                act_match = re.search(r"(\d+)A", actions_str)
                ba_match = re.search(r"(\d+)BA", actions_str)
                actions = int(act_match.group(1)) if act_match else 1
                bonus_actions = int(ba_match.group(1)) if ba_match else 0

                name = f"{base_name} {chr(65 + i)}" if num_enemies > 1 else base_name
                run.enemies.append(EnemyState(
                    name=name,
                    hp=hp_final,
                    max_hp=hp_final,
                    shield=0,
                    actions=actions,
                    bonus_actions=bonus_actions,
                    max_actions=actions,
                    max_bonus_actions=bonus_actions
                ))

        evt_turn = TurnStartEvent(run, is_player=True)
        self.event_bus.dispatch(evt_turn)
        self._roll_enemy_intent(run)

    init_battle = _init_battle_node

    def play_card(self, run: GameRun, hand_idx: int, target: Optional[str] = None) -> str:
        initial_status = [(e.hp, e.shield) for e in run.enemies]
        p = run.player
        if run.node_type != "battle":
            return "❌ 只有在战斗中才能使用卡牌。"
        if hand_idx < 1 or hand_idx > len(p.hand):
            return "❌ 无效的手牌序号。"
        cid = p.hand[hand_idx - 1]
        card = ALL_CARDS.get(cid)
        if not card:
            return "❌ 卡牌不存在。"
        if getattr(card, "unplayable", False):
            return "❌ 该卡牌不能被打出。"

        if card.type == "spell":
            if target is None:
                if card.id in ("dagger_throw", "fire_bolt", "fireball", "thunderwave", "magic_missile", "quick_strike", "arcane_spark", "agile_strike", "fleeting_spark"):
                    target = self._get_first_alive_enemy(run)
                else:
                    target = "p0"
            if target == "0" or target == "e0":
                target = "e1"
            elif target == "p":
                target = "p0"
            if target.startswith("e"):
                try:
                    grid = int(target[1:]) - 1
                except ValueError:
                    grid = 0
                if grid < 0 or grid >= len(run.enemies):
                    return f"❌ 敌方格子 [{target}] 没有敌人。"
            elif target == "p0":
                pass
            elif target.startswith("p"):
                grid = target[1:]
                if grid not in p.minions:
                    return f"❌ 我方格子 [{grid}] 没有随从。"
            else:
                return "❌ 无效的目标选择。"

        if card.type in ("minion", "amulet") and self._get_free_grid(p) is None:
            return "❌ 你的战场格子已满，无法召唤随从或部署护符。"

        req_a = card.cost_a
        req_ba = card.cost_ba
        play_evt = CardPlayEvent(run, card, target, req_a, req_ba)
        self.event_bus.dispatch(play_evt)
        req_a = play_evt.cost_a
        req_ba = play_evt.cost_ba

        if p.actions < req_a or p.bonus_actions < req_ba:
            return f"❌ 你的动作资源不足（需要 {req_a}A {req_ba}BA，当前 {p.actions}A {p.bonus_actions}BA）。"

        p.actions -= req_a
        p.bonus_actions -= req_ba
        p.hand.pop(hand_idx - 1)
        if getattr(card, "fleeting", False):
            if cid in p.deck:
                p.deck.remove(cid)
        elif getattr(card, "exhaust", False):
            p.exhaust_pile.append(cid)
            self._log_event(run, f"✨ [消耗] 【{card.name}】已被移入消耗堆。")
            exhaust_evt = CardExhaustEvent(run, cid, "played")
            self.event_bus.dispatch(exhaust_evt)
        else:
            p.discard_pile.append(cid)

        res = self._execute_card_effect(run, card, target)
        played_count = run.node_data.get("cards_played_this_turn", 0)
        
        played_evt = CardPlayedEvent(run, card, target, res)
        self.event_bus.dispatch(played_evt)
        res = played_evt.feedback

        run.node_data["cards_played_this_turn"] = played_count + 1
        self.save_manager.save_save(run.user_id, run)
        
        has_damaged = False
        for idx, e in enumerate(run.enemies):
            if idx < len(initial_status):
                old_hp, old_shield = initial_status[idx]
                if e.hp < old_hp or e.shield < old_shield:
                    has_damaged = True
                    break
        if has_damaged and run.node_data.get("extra_turns_left", 0) > 0:
            end_turn_res = self.end_turn(run)
            res += f"\n⏳ [时间停止] 额外回合中对敌人造成了伤害，当前额外回合提前结束！\n{end_turn_res}"
        for enemy in run.enemies:
            self._sync_enemy_intents(enemy)
        return self._append_logs_to_res(run, res)

    def play_special_action(self, run: GameRun, hand_idx: int, target: Optional[str] = None) -> str:
        initial_status = [(e.hp, e.shield) for e in run.enemies]
        p = run.player
        if run.node_type != "battle":
            return "❌ 只有在战斗中才能使用卡牌的特殊行动。"
        if hand_idx < 1 or hand_idx > len(p.hand):
            return "❌ 无效的手牌序号。"
        cid = p.hand[hand_idx - 1]
        card = ALL_CARDS.get(cid)
        if not card:
            return "❌ 卡牌不存在。"
        if getattr(card, "unplayable", False):
            return "❌ 该卡牌不能被打出。"

        req_a = card.cost_a
        req_ba = card.cost_ba
        if p.actions < req_a or p.bonus_actions < req_ba:
            return f"❌ 你的动作资源不足（需要 {req_a}A {req_ba}BA，当前 {p.actions}A {p.bonus_actions}BA）。"

        if target is None:
            if card.id in ("dagger_throw", "fire_bolt", "fireball", "thunderwave", "magic_missile", "quick_strike", "arcane_spark", "agile_strike", "fleeting_spark"):
                target = self._get_first_alive_enemy(run)
            else:
                target = "p0"
        if target == "0" or target == "e0":
            target = "e1"
        elif target == "p":
            target = "p0"

        p.actions -= req_a
        p.bonus_actions -= req_ba
        p.hand.pop(hand_idx - 1)
        if getattr(card, "fleeting", False):
            if cid in p.deck:
                p.deck.remove(cid)
        else:
            p.discard_pile.append(cid)

        res = card.special_action(run, target)
        self.save_manager.save_save(run.user_id, run)
        has_damaged = False
        for idx, e in enumerate(run.enemies):
            if idx < len(initial_status):
                old_hp, old_shield = initial_status[idx]
                if e.hp < old_hp or e.shield < old_shield:
                    has_damaged = True
                    break
        if has_damaged and run.node_data.get("extra_turns_left", 0) > 0:
            end_turn_res = self.end_turn(run)
            res += f"\n⏳ [时间停止] 额外回合中对敌人造成了伤害，当前额外回合提前结束！\n{end_turn_res}"
        for enemy in run.enemies:
            self._sync_enemy_intents(enemy)
        return self._append_logs_to_res(run, res)

    def minion_attack(self, run: GameRun, my_grid: str, opp_grid: Optional[str] = None) -> str:
        initial_status = [(e.hp, e.shield) for e in run.enemies]
        p = run.player
        if run.node_type != "battle":
            return "❌ 只有在战斗中才能控制随从攻击。"
        if my_grid not in p.minions:
            return f"❌ 我方格子 [{my_grid}] 没有随从。"
        m = p.minions[my_grid]
        if m.attack_actions < 1:
            return "❌ 该随从本回合已经没有可用的攻击动作（AA）点。"

        if opp_grid is None:
            opp_grid = self._get_first_alive_enemy(run)

        m.attack_actions -= 1
        try:
            opp_idx = int(opp_grid.replace("e", "")) - 1
            if opp_idx < 0:
                opp_idx = 0
        except ValueError:
            opp_idx = 0

        if opp_idx < 0 or opp_idx >= len(run.enemies):
            return f"❌ 敌方格子 [{opp_grid}] 没有合法的敌人目标。"

        enemy = run.enemies[opp_idx]
        
        calc_evt = DamageCalculateEvent(run, None, f"p{my_grid}", f"e{opp_idx+1}", "attack", m.atk, m.atk)
        self.event_bus.dispatch(calc_evt)
        atk = calc_evt.modified_damage

        self._damage_target(run, opp_grid, atk, source=f"p{my_grid}", damage_type="attack")
        res = f"我方随从【{m.name}】攻击了敌人【{enemy.name}】。"

        self.save_manager.save_save(run.user_id, run)
        has_damaged = False
        for idx, e in enumerate(run.enemies):
            if idx < len(initial_status):
                old_hp, old_shield = initial_status[idx]
                if e.hp < old_hp or e.shield < old_shield:
                    has_damaged = True
                    break
        if has_damaged and run.node_data.get("extra_turns_left", 0) > 0:
            end_turn_res = self.end_turn(run)
            res += f"\n⏳ [时间停止] 额外回合中对敌人造成了伤害，当前额外回合提前结束！\n{end_turn_res}"
        for enemy in run.enemies:
            self._sync_enemy_intents(enemy)
        return self._append_logs_to_res(run, res)

    def minion_skill(self, run: GameRun, my_grid: str, skill_idx: int = 1, target: Optional[str] = None) -> str:
        initial_status = [(e.hp, e.shield) for e in run.enemies]
        p = run.player
        if run.node_type != "battle":
            return "❌ 只有在战斗中才能发动随从技能。"
        if my_grid not in p.minions:
            return f"❌ 我方格子 [{my_grid}] 没有随从。"
        m = p.minions[my_grid]
        if m.id not in ALL_MINIONS:
            return f"❌ 随从【{m.name}】没有任何可用技能。"

        template = ALL_MINIONS[m.id]
        skills_list = template.skills
        if skill_idx < 1 or skill_idx > len(skills_list):
            skills_desc = "\n".join([f" [{idx}] {s.name}: {s.desc}" for idx, s in enumerate(skills_list, 1)])
            return f"❌ 无效的技能序号。随从【{m.name}】的可用技能有：\n{skills_desc}"

        skill = skills_list[skill_idx - 1]
        cost_a = skill.cost_a
        cost_ba = skill.cost_ba
        if m.actions < cost_a or m.bonus_actions < cost_ba:
            return f"❌ 随从资源不足（需要 {cost_a}A {cost_ba}BA，当前 {m.actions}A {m.bonus_actions}BA）。"

        needs_target = False
        if m.id == "mercenary" and skill_idx == 1:
            needs_target = True
        elif m.id == "shield_guard" and skill_idx == 2:
            needs_target = True
        elif m.id == "water_elemental" and skill_idx == 2:
            needs_target = True

        if needs_target:
            if target is None:
                target = self._get_first_alive_enemy(run)
            if target == "0" or target == "e0":
                target = "e1"
            if target.startswith("e"):
                try:
                    idx = int(target[1:]) - 1
                except ValueError:
                    idx = 0
                if idx < 0 or idx >= len(run.enemies):
                    return f"❌ 敌方目标 [{target}] 不存在。"
            else:
                return "❌ 无效的目标。该技能只能对敌方目标释放。"

        m.actions -= cost_a
        m.bonus_actions -= cost_ba
        msg = f"随从【{m.name}】发动了技能【{skill.name}】！"
        effect_msg = skill.execute(run, my_grid, target, self)
        msg += effect_msg

        self.save_manager.save_save(run.user_id, run)
        has_damaged = False
        for idx, e in enumerate(run.enemies):
            if idx < len(initial_status):
                old_hp, old_shield = initial_status[idx]
                if e.hp < old_hp or e.shield < old_shield:
                    has_damaged = True
                    break
        if has_damaged and run.node_data.get("extra_turns_left", 0) > 0:
            end_turn_res = self.end_turn(run)
            msg += f"\n⏳ [时间停止] 额外回合中对敌人造成了伤害，当前额外回合提前结束！\n{end_turn_res}"
        for enemy in run.enemies:
            self._sync_enemy_intents(enemy)
        return self._append_logs_to_res(run, msg)

    def _execute_card_effect(self, run: GameRun, card: Card, target: Optional[str] = None) -> str:
        res = card.execute(run, target, self)
        return res

    def get_modified_spell_damage(self, run: GameRun, card: Card, damage: int) -> int:
        calc_evt = DamageCalculateEvent(run, card, "p0", "e1", "spell", damage, damage)
        self.event_bus.dispatch(calc_evt)
        return calc_evt.modified_damage

    def _discard_card(self, run: GameRun, cid: str) -> str:
        p = run.player
        card = ALL_CARDS.get(cid)
        
        discard_evt = CardDiscardEvent(run, cid, "manual")
        self.event_bus.dispatch(discard_evt)

        if not card:
            p.discard_pile.append(cid)
            return self._append_logs_to_res(run, "")

        if getattr(card, "agile", False):
            target = None
            if card.type == "spell":
                if card.id in ("dagger_throw", "fire_bolt", "fireball", "thunderwave", "magic_missile", "quick_strike", "arcane_spark", "agile_strike", "fleeting_spark"):
                    target = self._get_first_alive_enemy(run)
                else:
                    target = "p0"
                if target == "0" or target == "e0":
                    target = "e1"
            res = self._execute_card_effect(run, card, target)
            
            played_evt = CardPlayedEvent(run, card, target, res)
            self.event_bus.dispatch(played_evt)
            res = played_evt.feedback

            if getattr(card, "fleeting", False):
                if cid in p.deck:
                    p.deck.remove(cid)
            elif getattr(card, "exhaust", False):
                p.exhaust_pile.append(cid)
                self._log_event(run, f"✨ [消耗] 【{card.name}】已被移入消耗堆。")
                exhaust_evt = CardExhaustEvent(run, cid, "agile")
                self.event_bus.dispatch(exhaust_evt)
            else:
                p.discard_pile.append(cid)
            return self._append_logs_to_res(run, f"✨ 触发[灵巧]：丢弃【{card.name}】时自动打出！效果：{res}")
        else:
            p.discard_pile.append(cid)
            return self._append_logs_to_res(run, "")

    def end_turn(self, run: GameRun) -> str:
        if run.node_type != "battle":
            return "❌ 只有在战斗中才能结束回合。"
        p = run.player

        evt_end = TurnEndEvent(run, is_player=True)
        self.event_bus.dispatch(evt_end)

        retained = []
        temp_retains = list(run.node_data.get("temp_retain_cards", []))
        for cid in p.hand:
            card = ALL_CARDS.get(cid)
            if card and getattr(card, "retain", False):
                retained.append(cid)
            elif cid in temp_retains:
                retained.append(cid)
                temp_retains.remove(cid)
            elif card and getattr(card, "ethereal", False):
                p.exhaust_pile.append(cid)
                self._log_event(run, f"✨ [虚无] 【{card.name}】在回合结束时被消耗。")
                exhaust_evt = CardExhaustEvent(run, cid, "ethereal")
                self.event_bus.dispatch(exhaust_evt)
            else:
                p.discard_pile.append(cid)
        p.hand = retained
        run.node_data["temp_retain_cards"] = []

        for ak, av in list(p.amulets.items()):
            base_id = av.id[:-1] if av.id.endswith("+") else av.id
            template = ALL_AMULETS.get(base_id)
            if template:
                template.on_end_turn(run, ak, self)
            av.countdown -= 1
            if av.countdown <= 0:
                del p.amulets[ak]

        if self.is_battle_won(run):
            self._handle_battle_win(run)
            return self._append_logs_to_res(run, "战斗胜利！敌方单位已被全部击败。")

        extra_turns = run.node_data.get("extra_turns_left", 0)
        if extra_turns > 0:
            run.node_data["extra_turns_left"] = extra_turns - 1
            enemy_actions = f"⏳ [时间停止] 额外回合进行中（剩余 {extra_turns - 1} 个额外回合），敌人全部陷入静止。"
        else:
            enemy_actions = self._enemy_turn(run)

        if p.hp <= 0:
            settle_msg = self.save_manager.settle_game_and_delete(run.user_id, run, is_victory=False)
            return f"{enemy_actions}\n💀 冒险结束。你被击败了！存档已被清除。\n{settle_msg}"

        decay_msgs = []
        if p.shield > 0:
            lost = p.shield - (p.shield // 2)
            p.shield = p.shield // 2
            if lost > 0:
                decay_msgs.append(f"玩家失去 {lost} 点护盾")
        else:
            p.shield = 0

        decay_info = ""
        if decay_msgs:
            decay_info = "🛡️ 护盾流失：" + "，".join(decay_msgs) + "\n"

        p.actions = 2
        p.bonus_actions = 1
        if run.node_data.get("drain_ba"):
            p.bonus_actions = max(0, p.bonus_actions - 1)
            run.node_data.pop("drain_ba", None)
        if run.node_data.get("drain_a"):
            p.actions = max(0, p.actions - 1)
            run.node_data.pop("drain_a", None)
        
        evt_start = TurnStartEvent(run, is_player=True)
        self.event_bus.dispatch(evt_start)

        if getattr(p, "subclass", "") == "时序法师":
            if random.random() < 0.25:
                p.bonus_actions += 1
                self._log_event(run, "⏳ [时序被动] 触发时间跳跃，本回合额外获得 1 个附赠动作（BA）！")
        for mk, mv in p.minions.items():
            mv.actions += 1
            mv.bonus_actions += 1 if mv.id == "arcane_golem" else 0
            mv.attack_actions = 1
            if mv.id == "mercenary":
                mv.atk = 4
            elif mv.id == "arcane_golem":
                mv.atk = 6

        if run.enemies and any(e.name == "腐化之心" for e in run.enemies):
            run.node_data["heart_turn"] = run.node_data.get("heart_turn", 1) + 1
        if run.enemies and any(e.name == "Icerainboww" for e in run.enemies):
            run.node_data["icerainboww_turn"] = run.node_data.get("icerainboww_turn", 1) + 1
        if run.enemies and any(e.name == "雷霆领主" for e in run.enemies):
            run.node_data["thunder_lord_turn"] = run.node_data.get("thunder_lord_turn", 1) + 1

        self._draw_cards(p, 6, run)
        self._roll_enemy_intent(run)
        run.node_data["cards_played_this_turn"] = 0
        self.save_manager.save_save(run.user_id, run)
        return self._append_logs_to_res(run, f"{enemy_actions}\n{decay_info}进入玩家回合。已重置动作并抽取手牌。")

    def _enemy_turn(self, run: GameRun) -> str:
        logs = []
        decay_enemies = []
        for enemy in run.enemies:
            if enemy.hp > 0 and enemy.shield > 0:
                lost = enemy.shield - (enemy.shield // 2)
                enemy.shield = enemy.shield // 2
                if lost > 0:
                    decay_enemies.append(f"【{enemy.name}】失去 {lost} 点护盾")
            else:
                enemy.shield = 0
        if decay_enemies:
            logs.append("🛡️ 护盾流失：" + "，".join(decay_enemies))

        evt_turn = TurnStartEvent(run, is_player=False)
        self.event_bus.dispatch(evt_turn)

        active_enemies = list(run.enemies)
        for idx, enemy in enumerate(active_enemies):
            if enemy.hp <= 0:
                continue
            if enemy.actions == 0 and enemy.bonus_actions == 0:
                continue
            template = get_enemy_template(enemy.name)
            for it in list(enemy.intents):
                if enemy.hp <= 0:
                    break
                if it.cancelled:
                    continue
                if it.cost_a > 0 and enemy.actions < it.cost_a:
                    logs.append(f"⚠️ 【{enemy.name}】因动作点（A）不足，取消了意图【{it.desc}】。")
                    it.cancelled = True
                    it.cancelled_desc = "已取消 (动作点不足)"
                    continue
                if it.cost_ba > 0 and enemy.bonus_actions < it.cost_ba:
                    logs.append(f"⚠️ 【{enemy.name}】因附赠动作点（BA）不足，取消了意图【{it.desc}】。")
                    it.cancelled = True
                    it.cancelled_desc = "已取消 (动作点不足)"
                    continue
                enemy.actions = max(0, enemy.actions - it.cost_a)
                enemy.bonus_actions = max(0, enemy.bonus_actions - it.cost_ba)
                template.execute_intent(run, self, enemy, it, logs)

        evt_turn_end = TurnEndEvent(run, is_player=False)
        self.event_bus.dispatch(evt_turn_end)

        for enemy in run.enemies:
            enemy.actions = enemy.max_actions
            enemy.bonus_actions = enemy.max_bonus_actions
        return "\n".join(logs)

        evt_turn_end = TurnEndEvent(run, is_player=False)
        self.event_bus.dispatch(evt_turn_end)

        for enemy in run.enemies:
            enemy.actions = enemy.max_actions
            enemy.bonus_actions = enemy.max_bonus_actions
        return "\n".join(logs)

    def _handle_battle_win(self, run: GameRun):
        p = run.player
        p.buffs.clear()
        p.hp = min(p.max_hp, p.hp)

        evt_win = BattleWinEvent(run)
        self.event_bus.dispatch(evt_win)

        difficulty = run.node_data.get("difficulty", "normal")
        quest = run.node_data.get("quest")
        quest_bonus = ""
        if quest == "knight_cave":
            p.deck.append("shield_guard")
            p.relics.append("heavy_armor")
            quest_bonus = "\n🗡️ 任务完成！你帮奥术骑士夺回了长剑。作为谢礼，【盾卫】加入了你的卡组，你还获得了一个遗物【重装甲片】！"
        elif quest == "maze_fight":
            got_relic = random.choice(["whetstone", "ready_pack", "arcane_rune"])
            p.relics.append(got_relic)
            quest_bonus = f"\n🔥 任务完成！你击败了火元素守卫，在石门后获得稀有遗物【{get_relic_name(got_relic)}】！"
        if difficulty == "elite":
            reward_gold = 25 + random.randint(10, 20)
        else:
            reward_gold = 10 + random.randint(5, 15)
        p.gold += reward_gold
        if p.stage == 20:
            run.node_type = "victory"
            if run.node_data.get("boss_name") == "Icerainboww":
                stats = self.save_manager.load_stats(run.user_id)
                stats.killed_icerainboww = True
                self.save_manager.save_stats(run.user_id, stats)
        else:
            run.node_type = "reward"
            card_pool = list(ALL_CARDS.keys())
            normal_cards = [cid for cid in card_pool if ALL_CARDS[cid].rarity != "legendary" and not cid.startswith("curse_")]
            reward_cards = random.sample(normal_cards, 3)
            reward_cards = [check_and_replace_fireball(run, cid) for cid in reward_cards]
            run.node_data = {"cards": reward_cards, "quest_bonus": quest_bonus}
            self.save_manager.save_save(run.user_id, run)

    def _roll_enemy_intent(self, run: GameRun):
        for enemy in run.enemies:
            if enemy.hp <= 0:
                continue
            template = get_enemy_template(enemy.name)
            enemy.intents = template.roll_intents(run, self, enemy)
            self._sync_enemy_intents(enemy)
