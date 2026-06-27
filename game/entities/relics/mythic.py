from .base import RelicImpl

class InfiniteHourglassRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        p = run.player
        p.actions += 1
        p.bonus_actions += 2
        engine._log_event(run, "⏳ [无限沙漏] 触发：额外获得了 1A 2BA 的时间控制权。")
