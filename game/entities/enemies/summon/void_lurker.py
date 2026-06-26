from typing import List
from ..base import EnemyTemplate, register_enemy

@register_enemy("虚空潜伏者")
class VoidLurkerTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        return [EnemyIntentState(type="void_strike", val=6, desc="虚空打击 (造成 6 点黯蚀伤害)", cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = intent
            from ....models.state import EnemyIntentState
            intent = EnemyIntentState(
                type=getattr(enemy, "intent_type", ""),
                val=getattr(enemy, "intent_val", 0),
                desc=getattr(enemy, "intent_desc", ""),
                cost_a=1,
                cost_ba=0
            )
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks
        val = intent.val + strength
        before_len = len(run.node_data.get("battle_logs", []))
        engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="necrotic")
        after_logs = run.node_data.get("battle_logs", [])
        dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
        logs.append(f"【{enemy.name}】对玩家进行虚空打击。{dmg_msg}")
