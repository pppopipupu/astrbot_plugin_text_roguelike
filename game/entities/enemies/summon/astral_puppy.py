from typing import List
from ..base import EnemyTemplate, register_enemy

@register_enemy("星界幼犬")
class AstralPuppyTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        return [EnemyIntentState(type="star_bite", val=3, desc="星光撕咬 (造成 3 力场伤害)", cost_a=1, cost_ba=0)]

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
        engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="force")
        after_logs = run.node_data.get("battle_logs", [])
        dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
        logs.append(f"【{enemy.name}】张开虚空之口扑咬过来。{dmg_msg}")
