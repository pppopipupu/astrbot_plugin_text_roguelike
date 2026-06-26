from typing import List
from ..base import EnemyTemplate, register_enemy
from ....data.enemy_data import ENEMY_CONFIG

@register_enemy("星界猎犬")
class AstralHoundTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("星界猎犬", {})
        intents = cfg.get("intents", [])
        
        intents_list = []
        for _ in range(enemy.max_actions):
            chosen = random.choice(intents)
            intents_list.append(EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0))
        for _ in range(enemy.max_bonus_actions):
            chosen = random.choice(intents)
            intents_list.append(EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=0, cost_ba=1))
        return intents_list

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
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks
        val = intent.val + strength

        if intent.type == "star_bite":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="force")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"【{enemy.name}】进行星光撕咬。{dmg_msg}")
        elif intent.type == "phase_shift":
            enemy.shield += 12
            to_remove = next((b for b in enemy.buffs if b.id == "stun"), None)
            if to_remove:
                enemy.buffs.remove(to_remove)
                engine._sync_enemy_intents(enemy)
                logs.append(f"【{enemy.name}】施展相位转移，获得 12 护盾并清除了眩晕！")
            else:
                logs.append(f"【{enemy.name}】施展相位转移，获得 12 护盾。")
        elif intent.type == "star_fury":
            run.node_data["draw_penalty_next_turn"] = run.node_data.get("draw_penalty_next_turn", 0) + 1
            logs.append(f"【{enemy.name}】释放星光狂暴，使玩家下回合少抽 1 张牌。")
