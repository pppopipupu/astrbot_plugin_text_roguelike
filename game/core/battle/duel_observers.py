from ...models.events import (
    TurnStartEvent, TurnEndEvent, CardPlayEvent, CardPlayedEvent,
    DamageCalculateEvent, DamageTakeEvent, HealEvent, MinionSummonEvent,
    ShieldGainEvent, ShieldDecayEvent, MinionDeathEvent, CardExhaustEvent,
    HealCalculateEvent, EnemyBeforeDeathEvent, EnemySyncIntentsEvent
)

class BuffTriggerHandler:
    def __init__(self, event_bus, engine):
        self.engine = engine
        event_bus.subscribe(TurnStartEvent, self.on_turn_start)
        event_bus.subscribe(TurnEndEvent, self.on_turn_end)
        event_bus.subscribe(CardPlayEvent, self.on_card_play)
        event_bus.subscribe(CardPlayedEvent, self.on_card_played)
        event_bus.subscribe(DamageCalculateEvent, self.on_damage_calculate)
        event_bus.subscribe(HealEvent, self.on_heal)
        event_bus.subscribe(ShieldGainEvent, self.on_shield_gain)
        event_bus.subscribe(DamageTakeEvent, self.on_damage_take)
        event_bus.subscribe(HealCalculateEvent, self.on_heal_calculate)
        event_bus.subscribe(EnemySyncIntentsEvent, self.on_enemy_sync_intents)

    def on_turn_start(self, event):
        from ...entities.buffs.duel_buffs import get_duel_buff_impl
        entities_with_buffs = []
        if event.is_player:
            entities_with_buffs.append((event.run.player, event.run.player))
        else:
            for enemy in list(event.run.enemies):
                entities_with_buffs.append((enemy, enemy))
        for entity, original in entities_with_buffs:
            for b in list(entity.buffs):
                impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                if impl and hasattr(impl, "on_turn_start"):
                    impl.on_turn_start(event, b, entity)

    def on_turn_end(self, event):
        from ...entities.buffs.duel_buffs import get_duel_buff_impl
        entities_with_buffs = []
        if event.is_player:
            entities_with_buffs.append((event.run.player, event.run.player))
        else:
            for enemy in list(event.run.enemies):
                entities_with_buffs.append((enemy, enemy))
        for entity, original in entities_with_buffs:
            for b in list(entity.buffs):
                impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                if impl and hasattr(impl, "on_turn_end"):
                    impl.on_turn_end(event, b, entity)

    def on_card_play(self, event):
        from ...entities.buffs.duel_buffs import get_duel_buff_impl
        for b in list(event.run.player.buffs):
            impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
            if impl and hasattr(impl, "on_card_play"):
                impl.on_card_play(event, b, event.run.player)

    def on_card_played(self, event):
        from ...entities.buffs.duel_buffs import get_duel_buff_impl
        for b in list(event.run.player.buffs):
            impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
            if impl and hasattr(impl, "on_card_played"):
                impl.on_card_played(event, b, event.run.player)
        for enemy in list(event.run.enemies):
            for b in list(enemy.buffs):
                impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                if impl and hasattr(impl, "on_card_played"):
                    impl.on_card_played(event, b, enemy)

    def on_damage_calculate(self, event):
        from ...entities.buffs.duel_buffs import get_duel_buff_impl
        if event.source.startswith("p"):
            for b in list(event.run.player.buffs):
                impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
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
                    impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                    if impl and hasattr(impl, "on_damage_calculate"):
                        impl.on_damage_calculate(event, b, enemy)

        if event.target == "p0":
            for b in list(event.run.player.buffs):
                impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
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
                    impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                    if impl and hasattr(impl, "on_damage_calculate_defend"):
                        impl.on_damage_calculate_defend(event, b, enemy)

    def on_heal(self, event):
        from ...entities.buffs.duel_buffs import get_duel_buff_impl
        if event.target == "p0":
            for b in list(event.run.player.buffs):
                impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                if impl and hasattr(impl, "on_heal"):
                    impl.on_heal(event, b, event.run.player)
        elif event.target.startswith("e"):
            try:
                idx = int(event.target[1:]) - 1
                if idx < 0: idx = 0
            except ValueError:
                idx = 0
            if 0 <= idx < len(event.run.enemies):
                enemy = event.run.enemies[idx]
                for b in list(enemy.buffs):
                    impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                    if impl and hasattr(impl, "on_heal"):
                        impl.on_heal(event, b, enemy)

    def on_shield_gain(self, event):
        from ...entities.buffs.duel_buffs import get_duel_buff_impl
        if event.target == "p0":
            for b in list(event.run.player.buffs):
                impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                if impl and hasattr(impl, "on_shield_gain"):
                    impl.on_shield_gain(event, b, event.run.player)
        elif event.target.startswith("e"):
            try:
                idx = int(event.target[1:]) - 1
                if idx < 0: idx = 0
            except ValueError:
                idx = 0
            if 0 <= idx < len(event.run.enemies):
                enemy = event.run.enemies[idx]
                for b in list(enemy.buffs):
                    impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                    if impl and hasattr(impl, "on_shield_gain"):
                        impl.on_shield_gain(event, b, enemy)

    def on_damage_take(self, event):
        from ...entities.buffs.duel_buffs import get_duel_buff_impl
        if event.target == "p0":
            for b in list(event.run.player.buffs):
                impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                if impl and hasattr(impl, "on_damage_take_defend"):
                    impl.on_damage_take_defend(event, b, event.run.player, self.engine)
        elif event.target.startswith("e"):
            try:
                idx = int(event.target[1:]) - 1
                if idx < 0: idx = 0
            except ValueError:
                idx = 0
            if 0 <= idx < len(event.run.enemies):
                enemy = event.run.enemies[idx]
                for b in list(enemy.buffs):
                    impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                    if impl and hasattr(impl, "on_damage_take_defend"):
                        impl.on_damage_take_defend(event, b, enemy, self.engine)

    def on_heal_calculate(self, event):
        from ...entities.buffs.duel_buffs import get_duel_buff_impl
        if event.target == "p0":
            for b in list(event.run.player.buffs):
                impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                if impl and hasattr(impl, "on_heal_calculate"):
                    impl.on_heal_calculate(event, b, event.run.player)
        elif event.target.startswith("e"):
            try:
                idx = int(event.target[1:]) - 1
                if idx < 0: idx = 0
            except ValueError:
                idx = 0
            if 0 <= idx < len(event.run.enemies):
                enemy = event.run.enemies[idx]
                for b in list(enemy.buffs):
                    impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                    if impl and hasattr(impl, "on_heal_calculate"):
                        impl.on_heal_calculate(event, b, enemy)

    def on_enemy_sync_intents(self, event):
        from ...entities.buffs.duel_buffs import get_duel_buff_impl
        for b in list(event.enemy.buffs):
            impl = get_duel_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
            if impl and hasattr(impl, "on_enemy_sync_intents"):
                impl.on_enemy_sync_intents(event, b, event.enemy)

class AmuletTriggerHandler:
    def __init__(self, event_bus, engine):
        self.engine = engine
        event_bus.subscribe(TurnStartEvent, self.on_turn_start)

    def on_turn_start(self, event):
        if not event.is_player:
            return
        p = event.run.player
        triggered = []
        try:
            from ...data.amulet_data import AMULET_CONFIG
        except ImportError:
            from game.data.amulet_data import AMULET_CONFIG
        for ak, av in list(p.amulets.items()):
            av.countdown -= 1
            if av.countdown <= 0:
                del p.amulets[ak]
                p.minion_graveyard.append(av.id)
                base_id = av.id[:-1] if av.id.endswith("+") else av.id
                cfg = AMULET_CONFIG.get(base_id)
                if cfg:
                    lw_msg = ""
                    is_upgraded = av.id.endswith("+")
                    dmg_val = cfg.get("damage", 0)
                    if dmg_val > 0:
                        if is_upgraded:
                            dmg_val += 3
                        opp_target = self.engine._get_first_alive_enemy(event.run)
                        self.engine._damage_target(event.run, opp_target, dmg_val, damage_type="thunder")
                        lw_msg = f"对敌方造成了 {dmg_val} 点雷鸣伤害"
                    heal_val = cfg.get("heal", 0)
                    if heal_val > 0:
                        if is_upgraded:
                            heal_val += 2
                        self.engine._heal_target(event.run, "p0", heal_val)
                        lw_msg = f"玩家恢复了 {heal_val} 点生命值"
                    shield_val = cfg.get("shield", 0)
                    if shield_val > 0:
                        if is_upgraded:
                            shield_val += 2
                        self.engine._gain_shield(event.run, "p0", shield_val)
                        lw_msg = f"玩家获得了 {shield_val} 点护盾"
                    if lw_msg:
                        triggered.append(f"【{av.name}】:{lw_msg}")
        if triggered:
            self.engine._log_event(event.run, "🔔 护符谢幕触发：" + "，".join(triggered))

class MinionTriggerHandler:
    def __init__(self, event_bus, engine):
        self.engine = engine
        event_bus.subscribe(TurnStartEvent, self.on_turn_start)

    def on_turn_start(self, event):
        p = event.run.player
        p.minions = {k: v for k, v in p.minions.items() if v.hp > 0}
