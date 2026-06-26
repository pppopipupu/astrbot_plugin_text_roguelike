from typing import List
from ..base import EnemyTemplate, register_enemy
from ....data.enemy_data import ENEMY_CONFIG

@register_enemy("亡灵巫师")
class NecromancerTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("亡灵巫师", {})
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
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks
        val = intent.val + strength

        if intent.type == "shadow_bolt":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="necrotic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(run.player, "minor_vulnerable_necrotic", "轻度黯蚀易伤", "受到的黯蚀伤害增加 50%", 1)
            logs.append(f"【{enemy.name}】射出暗影箭。{dmg_msg}，并对玩家施加了 1 层【轻度黯蚀易伤】。")
        elif intent.type == "raise_dead":
            from ....models.state import EnemyState, EnemyIntentState
            new_skeleton = EnemyState(
                name="骷髅兵",
                hp=6,
                max_hp=6,
                shield=0,
                actions=1,
                bonus_actions=0,
                is_summon=True,
                max_actions=1,
                max_bonus_actions=0,
                intents=[EnemyIntentState(
                    type="attack",
                    val=2,
                    desc="攻击 (造成 2 物理伤害)",
                    cost_a=1,
                    cost_ba=0
                )]
            )
            run.enemies.append(new_skeleton)
            logs.append(f"【{enemy.name}】吟唱复苏法术，召唤了一只【骷髅兵】加入战场。")
        elif intent.type == "soul_drain":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="necrotic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            enemy.hp = min(enemy.max_hp, enemy.hp + 4)
            logs.append(f"【{enemy.name}】吸取玩家灵魂，恢复了 4 点生命值。{dmg_msg}")
