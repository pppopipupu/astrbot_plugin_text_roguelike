from typing import List
from ..base import EnemyTemplate, register_enemy
from ....data.enemy_data import ENEMY_CONFIG

@register_enemy("地精百夫长")
class GoblinCenturionTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("地精百夫长", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

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
        if intent.type == "heavy_strike":
            self._perform_attack(run, engine, enemy, intent.val, logs)
        elif intent.type == "defend":
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】举起盾牌，获得 {intent.val} 点护盾。")
        elif intent.type == "command":
            enemy.actions += 1
            logs.append(f"【{enemy.name}】发出咆哮，获得 1 个额外动作点。")
