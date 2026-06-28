from typing import List
from ..base import EnemyTemplate, register_enemy
from ....data.enemy_data import ENEMY_CONFIG

@register_enemy("黑曜石巨灵")
class ObsidianDjinnTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("黑曜石巨灵", {})
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
        p = run.player
        if intent.type == "quake":
            self._perform_attack(run, engine, enemy, intent.val, logs)
            engine._add_buff_to(run.player, "drain_ba", "虚空纠缠", "在下一回合开始时，你将失去等同于此状态层数的附赠动作点 (BA)", 1)
            logs.append(f"【{enemy.name}】引发地震，使玩家在下一回合失去 1 个附赠动作点 (BA)。")
        elif intent.type == "defend":
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】加固外壳，获得 {intent.val} 点护盾。")
