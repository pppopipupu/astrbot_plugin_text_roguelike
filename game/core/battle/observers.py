from ...models.events import (
    BattleStartEvent, BattleWinEvent, TurnStartEvent, TurnEndEvent,
    CardPlayEvent, CardPlayedEvent, DamageCalculateEvent, DamageTakeEvent,
    HealEvent, MinionSummonEvent, ShieldGainEvent, ShieldDecayEvent
)

class RelicTriggerHandler:
    def __init__(self, event_bus, engine):
        self.engine = engine
        event_bus.subscribe(BattleStartEvent, self.on_battle_start)
        event_bus.subscribe(BattleWinEvent, self.on_battle_win)
        event_bus.subscribe(TurnStartEvent, self.on_turn_start)
        event_bus.subscribe(CardPlayedEvent, self.on_card_played)
        event_bus.subscribe(DamageCalculateEvent, self.on_damage_calculate)
        event_bus.subscribe(MinionSummonEvent, self.on_minion_summon)
        event_bus.subscribe(ShieldGainEvent, self.on_shield_gain)
        event_bus.subscribe(HealEvent, self.on_heal)
        event_bus.subscribe(DamageTakeEvent, self.on_damage_take)
        event_bus.subscribe(ShieldDecayEvent, self.on_shield_decay)

    def on_battle_start(self, event):
        from ...entities.relics.relics import get_relic_impl
        for r in list(event.run.player.relics):
            impl = get_relic_impl(r)
            if impl and hasattr(impl, "on_battle_start"):
                impl.on_battle_start(event.run, self.engine)

    def on_battle_win(self, event):
        from ...entities.relics.relics import get_relic_impl
        for r in list(event.run.player.relics):
            impl = get_relic_impl(r)
            if impl and hasattr(impl, "on_battle_win"):
                impl.on_battle_win(event.run, self.engine)

    def on_turn_start(self, event):
        from ...entities.relics.relics import get_relic_impl
        if event.is_player:
            event.run.node_data["player_damaged_this_turn"] = False
            for r in list(event.run.player.relics):
                impl = get_relic_impl(r)
                if impl and hasattr(impl, "on_turn_start"):
                    impl.on_turn_start(event, event.run, self.engine)

    def on_card_played(self, event):
        from ...entities.relics.relics import get_relic_impl
        for r in list(event.run.player.relics):
            impl = get_relic_impl(r)
            if impl and hasattr(impl, "on_card_played"):
                impl.on_card_played(event, event.run, self.engine)

    def on_damage_calculate(self, event):
        from ...entities.relics.relics import get_relic_impl
        if event.source == "p0":
            for r in list(event.run.player.relics):
                impl = get_relic_impl(r)
                if impl and hasattr(impl, "on_damage_calculate"):
                    impl.on_damage_calculate(event, event.run, self.engine)

    def on_minion_summon(self, event):
        from ...entities.relics.relics import get_relic_impl
        for r in list(event.run.player.relics):
            impl = get_relic_impl(r)
            if impl and hasattr(impl, "on_minion_summon"):
                impl.on_minion_summon(event, event.run, self.engine)

    def on_shield_gain(self, event):
        from ...entities.relics.relics import get_relic_impl
        if event.target == "p0":
            for r in list(event.run.player.relics):
                impl = get_relic_impl(r)
                if impl and hasattr(impl, "on_shield_gain"):
                    impl.on_shield_gain(event, event.run, self.engine)

    def on_heal(self, event):
        from ...entities.relics.relics import get_relic_impl
        if event.target == "p0":
            for r in list(event.run.player.relics):
                impl = get_relic_impl(r)
                if impl and hasattr(impl, "on_heal"):
                    impl.on_heal(event, event.run, self.engine)

    def on_damage_take(self, event):
        from ...entities.relics.relics import get_relic_impl
        for r in list(event.run.player.relics):
            impl = get_relic_impl(r)
            if impl and hasattr(impl, "on_damage_take"):
                impl.on_damage_take(event, event.run, self.engine)

    def on_shield_decay(self, event):
        from ...entities.relics.relics import get_relic_impl
        for r in list(event.run.player.relics):
            impl = get_relic_impl(r)
            if impl and hasattr(impl, "on_shield_decay"):
                impl.on_shield_decay(event, event.run, self.engine)

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

    def on_turn_start(self, event):
        from ...entities.buffs.buffs import get_buff_impl
        entities_with_buffs = []
        if event.is_player:
            entities_with_buffs.append((event.run.player, event.run.player))
        else:
            for enemy in list(event.run.enemies):
                entities_with_buffs.append((enemy, enemy))
        for entity, original in entities_with_buffs:
            for b in list(entity.buffs):
                impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                if impl and hasattr(impl, "on_turn_start"):
                    impl.on_turn_start(event, b, entity)

    def on_turn_end(self, event):
        from ...entities.buffs.buffs import get_buff_impl
        entities_with_buffs = []
        if event.is_player:
            entities_with_buffs.append((event.run.player, event.run.player))
        else:
            for enemy in list(event.run.enemies):
                entities_with_buffs.append((enemy, enemy))
        for entity, original in entities_with_buffs:
            for b in list(entity.buffs):
                impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                if impl and hasattr(impl, "on_turn_end"):
                    impl.on_turn_end(event, b, entity)

    def on_card_play(self, event):
        from ...entities.buffs.buffs import get_buff_impl
        for b in list(event.run.player.buffs):
            impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
            if impl and hasattr(impl, "on_card_play"):
                impl.on_card_play(event, b, event.run.player)

    def on_card_played(self, event):
        from ...entities.buffs.buffs import get_buff_impl
        for b in list(event.run.player.buffs):
            impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
            if impl and hasattr(impl, "on_card_played"):
                impl.on_card_played(event, b, event.run.player)
        for enemy in list(event.run.enemies):
            for b in list(enemy.buffs):
                impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                if impl and hasattr(impl, "on_card_played"):
                    impl.on_card_played(event, b, enemy)

    def on_damage_calculate(self, event):
        from ...entities.buffs.buffs import get_buff_impl
        if event.source == "p0":
            for b in list(event.run.player.buffs):
                impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
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
                    impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                    if impl and hasattr(impl, "on_damage_calculate"):
                        impl.on_damage_calculate(event, b, enemy)

        if event.target == "p0":
            for b in list(event.run.player.buffs):
                impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
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
                    impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                    if impl and hasattr(impl, "on_damage_calculate_defend"):
                        impl.on_damage_calculate_defend(event, b, enemy)

    def on_heal(self, event):
        from ...entities.buffs.buffs import get_buff_impl
        if event.target == "p0":
            for b in list(event.run.player.buffs):
                impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                if impl and hasattr(impl, "on_heal"):
                    impl.on_heal(event, b, event.run.player)

    def on_shield_gain(self, event):
        from ...entities.buffs.buffs import get_buff_impl
        if event.target == "p0":
            for b in list(event.run.player.buffs):
                impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                if impl and hasattr(impl, "on_shield_gain"):
                    impl.on_shield_gain(event, b, event.run.player)

    def on_damage_take(self, event):
        from ...entities.buffs.buffs import get_buff_impl
        if event.target == "p0":
            for b in list(event.run.player.buffs):
                impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                if impl and hasattr(impl, "on_damage_take_defend"):
                    impl.on_damage_take_defend(event, b, event.run.player, self.engine)
        elif event.target.startswith("e"):
            try:
                idx = int(event.target[1:]) - 1
            except ValueError:
                idx = -1
            if 0 <= idx < len(event.run.enemies):
                enemy = event.run.enemies[idx]
                for b in list(enemy.buffs):
                    impl = get_buff_impl(b.id, b.stacks, getattr(b, "stacks2", None))
                    if impl and hasattr(impl, "on_damage_take_defend"):
                        impl.on_damage_take_defend(event, b, enemy, self.engine)

class AmuletTriggerHandler:
    def __init__(self, event_bus, engine):
        self.engine = engine
        event_bus.subscribe(CardPlayedEvent, self.on_card_played)
        event_bus.subscribe(DamageTakeEvent, self.on_damage_take)

    def on_card_played(self, event):
        from ...entities.amulets.amulets import ALL_AMULETS
        for ak, av in list(event.run.player.amulets.items()):
            base_id = av.id[:-1] if av.id.endswith("+") else av.id
            template = ALL_AMULETS.get(base_id)
            if template and hasattr(template, "on_spell_played") and event.card.type == "spell":
                template.on_spell_played(event.run, ak, event.card, self.engine)

    def on_damage_take(self, event):
        from ...entities.amulets.amulets import ALL_AMULETS
        if event.target == "p0" and event.amount > 0:
            for ak, av in list(event.run.player.amulets.items()):
                base_id = av.id[:-1] if av.id.endswith("+") else av.id
                template = ALL_AMULETS.get(base_id)
                if template and hasattr(template, "on_take_damage"):
                    msg = template.on_take_damage(event.run, ak, event.source, event.amount, self.engine)
                    if msg:
                        self.engine._log_event(event.run, msg)
