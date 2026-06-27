from .base import RelicImpl
from .registry import register_relic

@register_relic("infinite_hourglass")
class InfiniteHourglassRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        run.node_data["extra_turns_left"] = 1
        run.node_data["time_stop_upgraded"] = False
        engine._log_event(run, "⏳ [无限沙漏] 触发：时空凝固，你获得了 1 层时间停止状态。")

    def on_turn_start(self, event, run, engine):
        p = run.player
        p.bonus_actions += 1
        engine._log_event(run, "⏳ [无限沙漏] 触发：获得额外的 1BA。")
