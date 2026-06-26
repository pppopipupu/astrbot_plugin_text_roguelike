from typing import List
from ..base import EnemyTemplate, register_enemy
from ....data.enemy_data import ENEMY_CONFIG

@register_enemy("石像鬼祭司")
class GargoylePriestTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("石像鬼祭司", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = intent
            from astrbot_plugin_text_roguelike.game.models.state import EnemyIntentState
            intent = EnemyIntentState(
                type=getattr(enemy, "intent_type", ""),
                val=getattr(enemy, "intent_val", 0),
                desc=getattr(enemy, "intent_desc", ""),
                cost_a=1,
                cost_ba=0
            )
        if intent.type == "attack":
            self._perform_attack(run, engine, enemy, intent.val, logs)
        elif intent.type == "defend":
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】施展暗影护盾，获得 {intent.val} 点护盾。")
        elif intent.type == "drain":
            self._perform_attack(run, engine, enemy, intent.val, logs)
            if run.enemies:
                min_hp_enemy = min(run.enemies, key=lambda e: e.hp)
                min_hp_enemy.hp = min(min_hp_enemy.max_hp, min_hp_enemy.hp + 4)
                logs.append(f"【{enemy.name}】汲取生命，为【{min_hp_enemy.name}】恢复了 4 点生命值。")
