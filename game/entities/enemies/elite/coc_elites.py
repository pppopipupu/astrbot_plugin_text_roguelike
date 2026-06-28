from typing import List
from ..base import EnemyTemplate, register_enemy
from ....data.enemy_data import ENEMY_CONFIG

@register_enemy("冷蛛")
class LengSpiderTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("冷蛛", {})
        intents = cfg.get("intents", [])
        res = []
        for _ in range(enemy.max_actions):
            chosen = random.choice(intents)
            res.append(EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0))
        for _ in range(enemy.max_bonus_actions):
            chosen = random.choice(intents)
            res.append(EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=0, cost_ba=1))
        return res

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
        if intent.type == "venom_bite":
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
        elif intent.type == "web_trap":
            enemy.shield += intent.val
            engine._add_buff_to(run.player, "discard_next_turn", "下回合弃牌", "在下一回合开始时，你将随机丢弃等同于此状态层数的手牌", 1)
            discard_msg = "，并使玩家在下一回合开始时将被迫随机丢弃 1 张手牌"
            logs.append(f"【{enemy.name}】编织蛛网，获得 {intent.val} 点护盾{discard_msg}。")
        elif intent.type == "spider_jump":
            val = intent.val
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            final_dmg = val + strength
            self._perform_attack(run, engine, enemy, final_dmg, logs)

@register_enemy("米·戈")
class MigoTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("米·戈", {})
        intents = cfg.get("intents", [])
        res = []
        for _ in range(enemy.max_actions):
            chosen = random.choice(intents)
            res.append(EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0))
        for _ in range(enemy.max_bonus_actions):
            chosen = random.choice(intents)
            res.append(EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=0, cost_ba=1))
        return res

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
        if intent.type == "electric_probe":
            val = intent.val
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            final_dmg = val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine.combat_resolver.damage_target(run, "p0", final_dmg, source=f"enemy:{enemy.name}", damage_type="lightning")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            run.node_data["draw_penalty_next_turn"] = run.node_data.get("draw_penalty_next_turn", 0) + 1
            logs.append(f"【{enemy.name}】使用电击探针。{dmg_msg}，使玩家下回合少抽 1 张牌。")
        elif intent.type == "brain_case":
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
            logs.append(f"【{enemy.name}】尝试提取你的大脑。{dmg_msg}")
        elif intent.type == "bio_shield":
            enemy.shield += intent.val
            negatives = {"stun", "weak", "vulnerable"}
            to_remove = None
            for b in enemy.buffs:
                if b.id in negatives or "vulnerable" in b.id or "weak" in b.id:
                    to_remove = b
                    break
            if to_remove:
                enemy.buffs.remove(to_remove)
                if to_remove.id == "stun":
                    engine._sync_enemy_intents(enemy)
                logs.append(f"【{enemy.name}】凝聚生物护盾，获得 {intent.val} 点护盾并净化了【{to_remove.name}】！")
            else:
                logs.append(f"【{enemy.name}】凝聚生物护盾，获得 {intent.val} 点护盾。")

@register_enemy("修格斯")
class ShoggothTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("修格斯", {})
        intents = cfg.get("intents", [])
        res = []
        for _ in range(enemy.max_actions):
            chosen = random.choice(intents)
            res.append(EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0))
        for _ in range(enemy.max_bonus_actions):
            chosen = random.choice(intents)
            res.append(EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=0, cost_ba=1))
        return res

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
        if intent.type == "acid_splash":
            val = intent.val
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            final_dmg = val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine.combat_resolver.damage_target(run, "p0", final_dmg, source=f"enemy:{enemy.name}", damage_type="acid")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(run.player, "drain_ba", "虚空纠缠", "在下一回合开始时，你将失去等同于此状态层数的附赠动作点 (BA)", 1)
            logs.append(f"【{enemy.name}】泼溅强酸。{dmg_msg}，使玩家在下一回合失去 1 个附赠动作点（BA）。")
        elif intent.type == "slime_cocoon":
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】分泌粘液茧，获得 {intent.val} 点护盾。")
        elif intent.type == "ooze_strike":
            val = intent.val
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            final_dmg = val + strength
            self._perform_attack(run, engine, enemy, final_dmg, logs)

@register_enemy("星之精")
class StarVampireTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("星之精", {})
        intents = cfg.get("intents", [])
        res = []
        for _ in range(enemy.max_actions):
            chosen = random.choice(intents)
            res.append(EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0))
        for _ in range(enemy.max_bonus_actions):
            chosen = random.choice(intents)
            res.append(EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=0, cost_ba=1))
        return res

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
        if intent.type == "blood_drain":
            val = intent.val
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            final_dmg = val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine.combat_resolver.damage_target(run, "p0", final_dmg, source=f"enemy:{enemy.name}", damage_type="necrotic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            heal = 8
            enemy.hp = min(enemy.max_hp, enemy.hp + heal)
            logs.append(f"【{enemy.name}】吸取你的鲜血。{dmg_msg}，并回复自身 {heal} 点生命。")
        elif intent.type == "invisible_stalker":
            enemy.shield += intent.val
            engine._add_buff_to(enemy, "strength", "力量", "造成的伤害增加", 4)
            logs.append(f"【{enemy.name}】隐形潜行，获得 {intent.val} 点护盾与 4 层【力量】！")
        elif intent.type == "talon_rend":
            val = intent.val
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            final_dmg = val + strength
            self._perform_attack(run, engine, enemy, final_dmg, logs)

@register_enemy("克苏鲁之星之眷族")
class StarspawnOfCthulhuTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("克苏鲁之星之眷族", {})
        intents = cfg.get("intents", [])
        res = []
        for _ in range(enemy.max_actions):
            chosen = random.choice(intents)
            res.append(EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0))
        for _ in range(enemy.max_bonus_actions):
            chosen = random.choice(intents)
            res.append(EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=0, cost_ba=1))
        return res

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
        if intent.type == "cosmic_blast":
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
            logs.append(f"【{enemy.name}】引导宇宙冲击。{dmg_msg}")
        elif intent.type == "cthulhu_gaze":
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
            run.node_data["drain_a"] = True
            logs.append(f"【{enemy.name}】投射克苏鲁之视。{dmg_msg}，使你下回合减少 1A。")
        elif intent.type == "star_regeneration":
            enemy.shield += intent.val
            heal = 10
            enemy.hp = min(enemy.max_hp, enemy.hp + heal)
            logs.append(f"【{enemy.name}】进行星光再生，获得 {intent.val} 点护盾并回复 {heal} 生命。")
