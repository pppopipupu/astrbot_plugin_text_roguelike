from typing import List
from ..base import EnemyTemplate, register_enemy
from ....data.enemy_data import ENEMY_CONFIG

@register_enemy("幽灵大魔法师")
class GhostArchmageTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("幽灵大魔法师", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

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
        p = run.player
        import random
        if intent.type == "spell_burst":
            self._perform_attack(run, engine, enemy, intent.val, logs)
        elif intent.type == "mana_drain":
            self._perform_attack(run, engine, enemy, intent.val, logs)
            if p.hand:
                discarded = p.hand.pop(random.randint(0, len(p.hand) - 1))
                from ...cards import ALL_CARDS
                card_name = ALL_CARDS[discarded].name if discarded in ALL_CARDS else "未知卡牌"
                agile_msg = engine._discard_card(run, discarded)
                logs.append(f"【{enemy.name}】施展虹吸，迫使玩家随机丢弃了卡牌【{card_name}】。")
                if agile_msg:
                    logs.append(agile_msg)
