from typing import List
from ..base import EnemyTemplate, register_enemy
from ....data.enemy_data import ENEMY_CONFIG

@register_enemy("狂暴兽王")
class BeastMasterTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("狂暴兽王", {})
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
        if intent.type == "attack":
            self._perform_attack(run, engine, enemy, intent.val, logs)
        elif intent.type == "defend":
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】收缩防线，获得 {intent.val} 点护盾。")
        elif intent.type == "summon_beast":
            from ....models.state import EnemyState, EnemyIntentState
            cfg = ENEMY_CONFIG.get("狂暴兽王", {})
            sh = cfg.get("summon_hound", {})
            new_hound = EnemyState(
                name=sh.get("name", "狂暴猎犬"),
                hp=sh.get("hp", 8),
                max_hp=sh.get("max_hp", 8),
                shield=0,
                actions=1,
                bonus_actions=0,
                is_summon=True,
                max_actions=1,
                max_bonus_actions=0,
                intents=[EnemyIntentState(
                    type="attack",
                    val=sh.get("intent_val", 2),
                    desc=sh.get("intent_desc", "扑咬 (造成 2 伤害)"),
                    cost_a=1,
                    cost_ba=0
                )]
            )
            run.enemies.append(new_hound)
            logs.append(f"【{enemy.name}】召唤了一只【狂暴猎犬】加入战场。")
