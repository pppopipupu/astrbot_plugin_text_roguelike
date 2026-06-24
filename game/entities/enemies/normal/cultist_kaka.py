from typing import List
from ..base import EnemyTemplate, register_enemy
from ....data.enemy_data import ENEMY_CONFIG

@register_enemy("邪教徒咔咔")
class CultistKakaTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        cfg = ENEMY_CONFIG.get("邪教徒咔咔", {})
        intents = cfg.get("intents", [])
        has_ritual = any(b.id == "ritual" for b in enemy.buffs)
        if not has_ritual:
            caw_intent = next(it for it in intents if it["id"] == "caw")
            return [EnemyIntentState(type=caw_intent["id"], val=caw_intent["val"], desc=caw_intent["desc"], cost_a=1, cost_ba=0)]
        else:
            peck_intent = next(it for it in intents if it["id"] == "peck")
            return [EnemyIntentState(type=peck_intent["id"], val=peck_intent["val"], desc=peck_intent["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = intent
            from game.models.state import EnemyIntentState
            intent = EnemyIntentState(
                type=getattr(enemy, "intent_type", ""),
                val=getattr(enemy, "intent_val", 0),
                desc=getattr(enemy, "intent_desc", ""),
                cost_a=1,
                cost_ba=0
            )
        if intent.type == "caw":
            engine._add_buff_to(enemy, "ritual", "仪式", "每回合开始时，获得等同于此状态层数的力量", 1)
            logs.append(f"【{enemy.name}】大喊：“咔咔！”，开始施展神秘仪式！")
        elif intent.type == "peck":
            self._perform_attack(run, engine, enemy, intent.val, logs)
