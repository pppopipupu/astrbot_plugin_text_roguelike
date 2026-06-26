from typing import List
from ..base import EnemyTemplate, register_enemy
from ....data.enemy_data import ENEMY_CONFIG

@register_enemy("吉斯洋基至高指挥官")
class GithyankiSupremeCommanderTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("吉斯洋基至高指挥官", {})
        intents = cfg.get("intents", [])
        
        intents_list = []
        for _ in range(enemy.max_actions):
            valid_choices = [it for it in intents if it["id"] in ("silver_greatsword", "commanding_presence", "summon_hound")]
            chosen = random.choice(valid_choices)
            intents_list.append(EnemyIntentState(
                type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0
            ))
            
        for _ in range(enemy.max_bonus_actions):
            valid_choices = [it for it in intents if it["id"] in ("psionic_barrier", "commanding_presence")]
            chosen = random.choice(valid_choices)
            intents_list.append(EnemyIntentState(
                type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=0, cost_ba=1
            ))
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
        from ....entities.enemies.trash_talk_actions import try_trash_talk
        try_trash_talk(run, enemy, logs)
        p = run.player
        if intent.type == "silver_greatsword":
            strength = 0
            for b in enemy.buffs:
                if b.id == "strength":
                    strength += b.stacks
            val = intent.val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="slashing")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(p, "minor_vulnerable_slashing", "轻度挥砍易伤", "受到的挥砍伤害增加 50%", 1)
            logs.append(f"【{enemy.name}】高高跃起挥舞银光大剑重斩！{dmg_msg} 且你受到了【轻度挥砍易伤】！")
        elif intent.type == "commanding_presence":
            for other_e in run.enemies:
                if other_e.hp > 0:
                    engine._add_buff_to(other_e, "strength", "力量", "造成的伤害增加", 2)
            logs.append(f"【{enemy.name}】发出威严的指挥咆哮：“星界归一，斩灭诸敌！” 敌方全体获得了 2 层力量！")
        elif intent.type == "psionic_barrier":
            enemy.shield += intent.val
            engine._add_buff_to(enemy, "strength", "力量", "造成的伤害增加", 1)
            logs.append(f"【{enemy.name}】爆发灵能屏障，自身获得 {intent.val} 点护盾与 1 层力量！")
        elif intent.type == "summon_hound":
            from ....models.state import EnemyState, EnemyIntentState
            cfg = ENEMY_CONFIG.get("吉斯洋基至高指挥官", {})
            sh = cfg.get("summon_hound", {})
            new_hound = EnemyState(
                name=sh.get("name", "星界幼犬"),
                hp=sh.get("hp", 15),
                max_hp=sh.get("max_hp", 15),
                shield=0,
                actions=1,
                bonus_actions=0,
                is_summon=True,
                max_actions=1,
                max_bonus_actions=0,
                intents=[EnemyIntentState(
                    type="star_bite",
                    val=sh.get("intent_val", 3),
                    desc=sh.get("intent_desc", "星光撕咬 (造成 3 力场伤害)"),
                    cost_a=1,
                    cost_ba=0
                )]
            )
            run.enemies.append(new_hound)
            logs.append(f"【{enemy.name}】撕裂星界通道，召唤了一只【星界幼犬】加入战斗！")
