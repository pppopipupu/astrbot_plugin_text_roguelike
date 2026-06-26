from typing import List
from ..base import EnemyTemplate, register_enemy
from ....data.enemy_data import ENEMY_CONFIG

@register_enemy("夺心魔")
class MindFlayerTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("夺心魔", {})
        intents = cfg.get("intents", [])
        
        has_grappled = any(b.id == "grappled" for b in run.player.buffs)
        
        intents_list = []
        for _ in range(enemy.max_actions):
            if has_grappled:
                if random.random() < 0.7:
                    chosen = next(it for it in intents if it["id"] == "extract_brain")
                else:
                    chosen = next(it for it in intents if it["id"] == "defend")
            else:
                valid_choices = [it for it in intents if it["id"] in ("tentacles", "mind_blast", "defend")]
                chosen = random.choice(valid_choices)
            intents_list.append(EnemyIntentState(
                type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0
            ))
            
        for _ in range(enemy.max_bonus_actions):
            valid_choices = [it for it in intents if it["id"] in ("tentacles", "defend")]
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
        if intent.type == "tentacles":
            strength = 0
            for b in enemy.buffs:
                if b.id == "strength":
                    strength += b.stacks
            val = intent.val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="psychic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(p, "grappled", "受擒", "你被夺心魔擒抱，每回合结束时层数减少 1", 1)
            logs.append(f"【{enemy.name}】伸出滑腻的触须缠绕过来。{dmg_msg} 且你陷入了【受擒】状态！")
        elif intent.type == "mind_blast":
            strength = 0
            for b in enemy.buffs:
                if b.id == "strength":
                    strength += b.stacks
            val = intent.val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="psychic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(p, "stun", "眩晕", "无法行动，回合开始时扣除一层恢复", 1)
            logs.append(f"【{enemy.name}】发出狂暴的心灵冲击波。{dmg_msg} 且你受到了【眩晕】！")
        elif intent.type == "extract_brain":
            has_grappled = any(b.id == "grappled" for b in p.buffs)
            if has_grappled:
                dmg_val = 25
                msg_prefix = f"【{enemy.name}】将触须插入你的颅骨，开始吞食你的脑髓！"
            else:
                dmg_val = 8
                msg_prefix = f"【{enemy.name}】由于你挣脱了擒抱，只能进行普通的脑部突刺！"
            
            strength = 0
            for b in enemy.buffs:
                if b.id == "strength":
                    strength += b.stacks
            val = dmg_val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="piercing")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"{msg_prefix}{dmg_msg}")
        elif intent.type == "defend":
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】凝聚心灵屏障，获得 {intent.val} 点护盾。")


@register_enemy("夺心魔奥术师")
class MindFlayerArcanistTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("夺心魔奥术师", {})
        intents = cfg.get("intents", [])
        
        has_grappled = any(b.id == "grappled" for b in run.player.buffs)
        
        intents_list = []
        for _ in range(enemy.max_actions):
            if has_grappled:
                if random.random() < 0.6:
                    chosen = next(it for it in intents if it["id"] == "extract_brain")
                else:
                    chosen = random.choice([it for it in intents if it["id"] in ("magic_missile", "shield_spell")])
            else:
                valid_choices = [it for it in intents if it["id"] in ("tentacles", "mind_blast", "magic_missile", "shield_spell")]
                chosen = random.choice(valid_choices)
            intents_list.append(EnemyIntentState(
                type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0
            ))
            
        for _ in range(enemy.max_bonus_actions):
            valid_choices = [it for it in intents if it["id"] in ("tentacles", "shield_spell")]
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
        if intent.type == "tentacles":
            strength = 0
            for b in enemy.buffs:
                if b.id == "strength":
                    strength += b.stacks
            val = intent.val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="psychic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(p, "grappled", "受擒", "你被夺心魔擒抱，每回合结束时层数减少 1", 1)
            logs.append(f"【{enemy.name}】伸出奥术触须缠绕过来。{dmg_msg} 且你陷入了【受擒】状态！")
        elif intent.type == "mind_blast":
            strength = 0
            for b in enemy.buffs:
                if b.id == "strength":
                    strength += b.stacks
            val = intent.val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="psychic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(p, "stun", "眩晕", "无法行动，回合开始时扣除一层恢复", 1)
            logs.append(f"【{enemy.name}】发出狂暴的心灵冲击波。{dmg_msg} 且你受到了【眩晕】！")
        elif intent.type == "extract_brain":
            has_grappled = any(b.id == "grappled" for b in p.buffs)
            if has_grappled:
                dmg_val = 25
                msg_prefix = f"【{enemy.name}】将触须插入你的颅骨，开始吞食你的脑髓！"
            else:
                dmg_val = 8
                msg_prefix = f"【{enemy.name}】由于你挣脱了擒抱，只能进行普通的脑部突刺！"
            
            strength = 0
            for b in enemy.buffs:
                if b.id == "strength":
                    strength += b.stacks
            val = dmg_val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="piercing")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"{msg_prefix}{dmg_msg}")
        elif intent.type == "magic_missile":
            strength = 0
            for b in enemy.buffs:
                if b.id == "strength":
                    strength += b.stacks
            single_val = intent.val + strength
            missile_logs = []
            for _ in range(3):
                before_len = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, "p0", single_val, source=f"enemy:{enemy.name}", damage_type="force")
                after_logs = run.node_data.get("battle_logs", [])
                if len(after_logs) > before_len:
                    missile_logs.append(after_logs.pop())
            logs.append(f"【{enemy.name}】吟唱奥术飞弹，连续射出 3 枚飞弹：{', '.join(missile_logs)}")
        elif intent.type == "shield_spell":
            enemy.shield += intent.val
            to_remove = next((b for b in enemy.buffs if b.id == "stun"), None)
            if not to_remove:
                neg_buffs = [b for b in enemy.buffs if b.id in ("minor_vulnerable_slashing", "minor_vulnerable_piercing", "minor_vulnerable_bludgeoning", "minor_vulnerable_fire", "minor_vulnerable_cold", "minor_vulnerable_lightning", "minor_vulnerable_thunder", "minor_vulnerable_necrotic", "minor_vulnerable_acid", "minor_vulnerable_poison", "minor_vulnerable_psychic", "minor_vulnerable_radiant", "minor_vulnerable_force")]
                if neg_buffs:
                    to_remove = neg_buffs[0]
            if to_remove:
                enemy.buffs.remove(to_remove)
                engine._sync_enemy_intents(enemy)
                logs.append(f"【{enemy.name}】施展护盾术，获得 {intent.val} 点护盾，并清除了【{to_remove.name}】负面效果！")
            else:
                logs.append(f"【{enemy.name}】施展护盾术，获得 {intent.val} 点护盾。")
