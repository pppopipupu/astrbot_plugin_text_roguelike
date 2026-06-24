import re
from .base import RelicImpl
from .registry import register_relic

class RustShackleRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.hp_loss = 4

    def on_battle_start(self, run, engine):
        p = run.player
        p.hp = max(1, p.hp - self.hp_loss)
        engine._log_event(run, f"🔒 [铁锈之锁] 触发：失去 {self.hp_loss} 点生命值。")

class BlindSpotRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.draw_penalty = 2

    def on_battle_start(self, run, engine):
        engine._log_event(run, f"👁️ [盲目之障] 触发：首回合少抽 {self.draw_penalty} 张牌。")

    def modify_initial_draw(self, run, draw_count: int, engine) -> int:
        return max(0, draw_count - self.draw_penalty)

class FoolOathRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.hp_reduction = 3

    def on_minion_summon(self, event, run, engine):
        m = event.minion_state
        m.hp = max(1, m.hp - self.hp_reduction)
        m.max_hp = max(1, m.max_hp - self.hp_reduction)

class WitherSeedRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)

    def on_heal(self, event, run, engine):
        if event.target == "p0":
            event.cancel()

class ShadowCurseRelic(RelicImpl):
    def on_card_played(self, event, run, engine):
        if event.card.type == "spell" and not event.card.id.startswith("demon_contract"):
            engine._damage_target(run, "p0", 2, source="shadow_curse", damage_type="true")
            engine._log_event(run, "🕸️ [影之诅咒] 触发：失去 2 点生命值。")

class GlacierChillRelic(RelicImpl):
    def on_turn_start(self, event, run, engine):
        if event.is_player:
            run.player.actions = max(0, run.player.actions - 1)
            engine._log_event(run, "❄️ [严寒侵袭] 触发：玩家本回合动作点 A 减少 1。")


for name, obj in list(globals().items()):
    if isinstance(obj, type) and issubclass(obj, RelicImpl) and obj is not RelicImpl:
        snake = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        if snake.endswith('_relic'):
            relic_id = snake[:-6]
            register_relic(relic_id)(obj)
