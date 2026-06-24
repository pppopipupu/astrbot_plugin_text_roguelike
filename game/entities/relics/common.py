import re
from .base import RelicImpl
from .registry import register_relic

class LeatherArmorRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.shield_gain = 4

    def on_battle_start(self, run, engine):
        p = run.player
        p.shield += self.shield_gain
        engine._log_event(run, f"🛡️ [坚固皮革] 触发：获得 {self.shield_gain} 点初始护盾。")

class AncientSigilRelic(RelicImpl):
    def on_card_played(self, event, run, engine):
        if getattr(event.card, "exhaust", False):
            import random
            if random.random() < 0.5:
                engine._heal_target(run, "p0", 3)
                engine._log_event(run, "✨ [先古印记] 触发：为玩家恢复 3 点生命值。")
            else:
                engine._gain_shield(run, "p0", 5)
                engine._log_event(run, "✨ [先古印记] 触发：为玩家获得 5 点护盾。")


for name, obj in list(globals().items()):
    if isinstance(obj, type) and issubclass(obj, RelicImpl) and obj is not RelicImpl:
        snake = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        if snake.endswith('_relic'):
            relic_id = snake[:-6]
            register_relic(relic_id)(obj)
