from typing import List
from ..base import EnemyTemplate, register_enemy
from ....data.enemy_data import ENEMY_CONFIG

@register_enemy("吉斯洋基海盗")
class GithyankiPirateTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("吉斯洋基海盗", {})
        intents = cfg.get("intents", [])
        
        extra_actions = 0
        speed_buff = next((b for b in enemy.buffs if b.id == "astral_speed"), None)
        if speed_buff:
            extra_actions = speed_buff.stacks
            enemy.buffs.remove(speed_buff)
            enemy.actions += extra_actions
            
        intents_list = []
        for _ in range(enemy.max_actions + extra_actions):
            chosen = random.choice(intents)
            intents_list.append(EnemyIntentState(
                type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0
            ))
        return intents_list

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
        from game.entities.enemies.trash_talk_actions import try_trash_talk
        try_trash_talk(run, enemy, logs)
        p = run.player
        if intent.type == "silver_sword":
            strength = 0
            for b in enemy.buffs:
                if b.id == "strength":
                    strength += b.stacks
            val = intent.val + strength
            
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="slashing")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            
            extra_msg = ""
            if p.shield > 0:
                extra_before = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, "p0", 4, source=f"enemy:{enemy.name}", damage_type="force")
                extra_after = run.node_data.get("battle_logs", [])
                if len(extra_after) > extra_before:
                    extra_msg = f" 银剑产生共鸣，对有盾的目标额外造成 4 点力场伤害！{extra_after.pop()}"
            
            logs.append(f"【{enemy.name}】使出银剑横扫劈向你。{dmg_msg}{extra_msg}")
        elif intent.type == "astral_step":
            enemy.shield += intent.val
            engine._add_buff_to(enemy, "astral_speed", "星界加速", "下回合开始时，获得 1 个额外动作点", 1)
            logs.append(f"【{enemy.name}】施展星界跃迁进行闪避与充能，获得 {intent.val} 点护盾与【星界加速】！")
        elif intent.type == "parry":
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】做出招架姿态，获得 {intent.val} 点护盾。")
