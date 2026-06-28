from .base import BuffImpl
from .registry import register_buff

@register_buff("drain_ba")
class DrainBABuff(BuffImpl):
    def on_turn_start(self, event, buff_state, entity):
        if event.is_player and entity == event.run.player:
            entity.bonus_actions = max(0, entity.bonus_actions - buff_state.stacks)
            event.engine._log_event(event.run, f"⏳ [虚空纠缠] 触发！本回合失去 {buff_state.stacks} 个附赠动作点 (BA)。")
            if buff_state in entity.buffs:
                entity.buffs.remove(buff_state)

@register_buff("drain_a")
class DrainABuff(BuffImpl):
    def on_turn_start(self, event, buff_state, entity):
        if event.is_player and entity == event.run.player:
            entity.actions = max(0, entity.actions - buff_state.stacks)
            event.engine._log_event(event.run, f"⏳ [时间纠缠] 触发！本回合失去 {buff_state.stacks} 个动作点 (A)。")
            if buff_state in entity.buffs:
                entity.buffs.remove(buff_state)

@register_buff("discard_next_turn")
class DiscardNextTurnBuff(BuffImpl):
    pass
