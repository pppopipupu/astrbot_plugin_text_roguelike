from typing import List
from ..base import EnemyTemplate, register_enemy
from ....data.enemy_data import ENEMY_CONFIG

@register_enemy("深潜者")
class DeepOneTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("深潜者", {})
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
        if intent.type == "tsunami_strike":
            val = intent.val
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            final_dmg = val + strength
            p = run.player
            extra_msg = ""
            if p.shield > 0:
                before_len = len(run.node_data.get("battle_logs", []))
                engine.combat_resolver.damage_target(run, "p0", 3, source=f"enemy:{enemy.name}", damage_type="true")
                after_logs = run.node_data.get("battle_logs", [])
                true_dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
                extra_msg = f"，且由于你拥有护盾，额外承受了 3 点真实伤害（{true_dmg_msg}）"
            
            before_len = len(run.node_data.get("battle_logs", []))
            self._perform_attack(run, engine, enemy, final_dmg, logs)
            if extra_msg and logs:
                logs[-1] += extra_msg
        elif intent.type == "defend":
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】凝聚潮汐之盾，获得 {intent.val} 点护盾。")

@register_enemy("食尸鬼")
class GhoulTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("食尸鬼", {})
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
        if intent.type == "rot_bite":
            val = intent.val
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            final_dmg = val + strength
            self._perform_attack(run, engine, enemy, final_dmg, logs)
            engine._add_buff_to(run.player, "minor_vulnerable", "轻度易伤", "受到的所有类型伤害增加 50%", 1)
            if logs:
                logs[-1] += "，并对你施加了 1 层【轻度易伤】"
        elif intent.type == "claw_slash":
            val = intent.val
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            final_dmg = val + strength
            self._perform_attack(run, engine, enemy, final_dmg, logs)

@register_enemy("夜魇")
class NightgauntTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("夜魇", {})
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
        if intent.type == "tickle_claw":
            val = intent.val
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            final_dmg = val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine.combat_resolver.damage_target(run, "p0", final_dmg, source=f"enemy:{enemy.name}", damage_type="psychic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"【{enemy.name}】使用搔痒爪。{dmg_msg}")
        elif intent.type == "void_glide":
            enemy.shield += intent.val
            engine._add_buff_to(enemy, "astral_speed", "星界加速", "下回合开始时，获得 1 个额外动作点", 1)
            logs.append(f"【{enemy.name}】施展虚空滑翔，获得 {intent.val} 点护盾与【星界加速】！")

@register_enemy("夏塔克鸟")
class ShantakTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("夏塔克鸟", {})
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
        if intent.type == "wind_buffet":
            val = intent.val
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            final_dmg = val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine.combat_resolver.damage_target(run, "p0", final_dmg, source=f"enemy:{enemy.name}", damage_type="force")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"【{enemy.name}】使用狂风拍击。{dmg_msg}")
        elif intent.type == "shriek":
            val = intent.val
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            final_dmg = val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine.combat_resolver.damage_target(run, "p0", final_dmg, source=f"enemy:{enemy.name}", damage_type="psychic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            
            engine._add_buff_to(run.player, "discard_next_turn", "下回合弃牌", "在下一回合开始时，你将随机丢弃等同于此状态层数的手牌", 1)
            discard_msg = "，并使玩家在下一回合开始时将被迫随机丢弃 1 张手牌"
            
            logs.append(f"【{enemy.name}】发出凄厉尖啸。{dmg_msg}{discard_msg}。")

@register_enemy("空鬼")
class DimensionalShamblerTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("空鬼", {})
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
        if intent.type == "phase_strike":
            val = intent.val
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            final_dmg = val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine.combat_resolver.damage_target(run, "p0", final_dmg, source=f"enemy:{enemy.name}", damage_type="true")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"【{enemy.name}】使用相位打击。{dmg_msg}")
        elif intent.type == "dimensional_shift":
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】进行维度偏移，获得 {intent.val} 点护盾。")
