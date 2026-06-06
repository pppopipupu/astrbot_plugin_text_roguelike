from typing import Tuple, List
from .base import EnemyTemplate
from ...data.enemy_data import ENEMY_CONFIG

class GoblinCenturionTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("地精百夫长", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = intent
            from ...models.state import EnemyIntentState
            intent = EnemyIntentState(
                type=getattr(enemy, "intent_type", ""),
                val=getattr(enemy, "intent_val", 0),
                desc=getattr(enemy, "intent_desc", ""),
                cost_a=1,
                cost_ba=0
            )
        if intent.type == "heavy_strike":
            self._perform_attack(run, engine, enemy, intent.val, logs)
        elif intent.type == "defend":
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】举起盾牌，获得 {intent.val} 点护盾。")
        elif intent.type == "command":
            enemy.actions += 1
            logs.append(f"【{enemy.name}】发出咆哮，获得 1 个额外动作点。")

class GargoylePriestTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("石像鬼祭司", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = intent
            from ...models.state import EnemyIntentState
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
            logs.append(f"【{enemy.name}】施展暗影护盾，获得 {intent.val} 点护盾。")
        elif intent.type == "drain":
            self._perform_attack(run, engine, enemy, intent.val, logs)
            if run.enemies:
                min_hp_enemy = min(run.enemies, key=lambda e: e.hp)
                min_hp_enemy.hp = min(min_hp_enemy.max_hp, min_hp_enemy.hp + 4)
                logs.append(f"【{enemy.name}】汲取生命，为【{min_hp_enemy.name}】恢复了 4 点生命值。")

class BeastMasterTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("狂暴兽王", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = intent
            from ...models.state import EnemyIntentState
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
            from ...models.state import EnemyState, EnemyIntentState
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

class ObsidianDjinnTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("黑曜石巨灵", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = intent
            from ...models.state import EnemyIntentState
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
            p.bonus_actions = max(0, p.bonus_actions - 1)
            logs.append(f"【{enemy.name}】引发地震，剥夺了玩家 1 个附赠动作点 (BA)。")
        elif intent.type == "defend":
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】加固外壳，获得 {intent.val} 点护盾。")

class GhostArchmageTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("幽灵大魔法师", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = intent
            from ...models.state import EnemyIntentState
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
                from ..cards import ALL_CARDS
                card_name = ALL_CARDS[discarded].name if discarded in ALL_CARDS else "未知卡牌"
                agile_msg = engine._discard_card(run, discarded)
                logs.append(f"【{enemy.name}】施展虹吸，迫使玩家随机丢弃了卡牌【{card_name}】。")
                if agile_msg:
                    logs.append(agile_msg)

class ShadowFiendTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("暗影影魔", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = intent
            from ...models.state import EnemyIntentState
            intent = EnemyIntentState(
                type=getattr(enemy, "intent_type", ""),
                val=getattr(enemy, "intent_val", 0),
                desc=getattr(enemy, "intent_desc", ""),
                cost_a=1,
                cost_ba=0
            )
        p = run.player
        if intent.type == "shadow_strike":
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            dmg = intent.val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", dmg, source=f"enemy:{enemy.name}", damage_type="true")
            after_logs = run.node_data.get("battle_logs", [])
            if len(after_logs) > before_len:
                dmg_msg = after_logs.pop()
                logs.append(f"【{enemy.name}】施展影袭，直接对玩家造成生命伤害。{dmg_msg}")
        elif intent.type == "defend":
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】进入虚化，获得 {intent.val} 点护盾。")

class DoomguardTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("末日守卫", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = []
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks
        val = intent.val + strength

        if intent.type == "doom_strike":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="piercing")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(run.player, "minor_vulnerable_slashing", "轻度挥砍易伤", "受到的挥砍伤害增加 50%", 1)
            logs.append(f"【{enemy.name}】施展毁灭打击。{dmg_msg}")
        elif intent.type == "hellfire":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="fire")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(run.player, "minor_vulnerable_fire", "轻度火焰易伤", "受到的火焰伤害增加 50%", 1)
            logs.append(f"【{enemy.name}】施展地狱火。{dmg_msg}")
        elif intent.type == "sacrifice":
            enemy.shield += intent.val
            engine._damage_target(run, f"e{run.enemies.index(enemy)+1}", 2, source=f"enemy:{enemy.name}", damage_type="true")
            logs.append(f"【{enemy.name}】使用牺牲防御，获得 {intent.val} 点护盾，但自身受到 2 点真实伤害反噬。")

class NecromancerTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("亡灵巫师", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = []
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
            logs.append(f"【{enemy.name}】射出暗影箭。{dmg_msg}")
        elif intent.type == "raise_dead":
            from ...models.state import EnemyState, EnemyIntentState
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
            logs.append(f"【{enemy.name}】施展死者苏生，召唤了一只【骷髅兵】！")
        elif intent.type == "soul_drain":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="necrotic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            enemy.hp = min(enemy.max_hp, enemy.hp + 4)
            logs.append(f"【{enemy.name}】施展灵魂吸取，吸取了玩家生命值并为自身恢复了 4 点生命。{dmg_msg}")

class PortalGuardianTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("传送门守卫者", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = []
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks
        val = intent.val + strength

        if intent.type == "dimensional_tear":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="true")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"【{enemy.name}】施展空间撕裂。{dmg_msg}")
        elif intent.type == "void_shield":
            enemy.shield += intent.val
            neg_buff = next((b for b in enemy.buffs if b.id == "stun"), None)
            if neg_buff:
                neg_buff.stacks -= 1
                if neg_buff.stacks <= 0:
                    enemy.buffs.remove(neg_buff)
                engine._sync_enemy_intents(enemy)
                logs.append(f"【{enemy.name}】施展虚空屏障，获得 {intent.val} 护盾并解除了 1 层眩晕！")
            else:
                logs.append(f"【{enemy.name}】施展虚空屏障，获得 {intent.val} 护盾。")
        elif intent.type == "portal_instability":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="psychic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            p = run.player
            import random
            discard_msg = ""
            if p.hand:
                discarded = p.hand.pop(random.randint(0, len(p.hand) - 1))
                from ..cards import ALL_CARDS
                card_name = ALL_CARDS[discarded].name if discarded in ALL_CARDS else "未知"
                agile_msg = engine._discard_card(run, discarded)
                discard_msg = f"玩家被迫随机丢弃了卡牌【{card_name}】。"
                if agile_msg:
                    discard_msg += f" {agile_msg}"
            logs.append(f"【{enemy.name}】引发传送门不稳定！{discard_msg}{dmg_msg}")

class FireGuardTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("火元素守卫", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = []
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks
        val = intent.val + strength

        if intent.type == "fire_blast":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="fire")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(run.player, "minor_vulnerable_fire", "轻度火焰易伤", "受到的火焰伤害增加 50%", 1)
            logs.append(f"【{enemy.name}】释放烈焰爆轰。{dmg_msg}")
        elif intent.type == "fire_armor":
            enemy.shield += intent.val
            engine._damage_target(run, "p0", 2, source=f"enemy:{enemy.name}", damage_type="fire")
            logs.append(f"【{enemy.name}】凝聚火焰护甲，获得 {intent.val} 护盾，且火焰溅射对玩家造成 2 点火焰伤害。")
        elif intent.type == "heat_grow":
            engine._add_buff_to(enemy, "strength", "力量", "造成的伤害增加", 1)
            logs.append(f"【{enemy.name}】进行热力凝聚，力量提升了 1 点。")

class DemonServantTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("狂暴魔仆", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = []
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks
        val = intent.val + strength

        if intent.type == "rage_bite":
            if enemy.hp <= enemy.max_hp // 2:
                val *= 2
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="slashing")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"【{enemy.name}】发出狂暴撕咬。{dmg_msg}")
        elif intent.type == "evil_gaze":
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】投射邪恶凝视，获得 {intent.val} 护盾。")

class LightningOrbTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("雷影魔仆", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = []
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks
        val = intent.val + strength

        if intent.type == "lightning_strike":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="lightning")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(run.player, "shock", "电击", "受到的闪电和雷鸣伤害每层增加 1 点", 1)
            logs.append(f"【{enemy.name}】释放闪电击。{dmg_msg}")
        elif intent.type == "charge":
            engine._add_buff_to(enemy, "strength", "力量", "造成的伤害增加", 1)
            logs.append(f"【{enemy.name}】进行蓄能，力量提升了 1 点。")

class VoidWandererTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("虚空游荡者", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = []
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks
        val = intent.val + strength

        if intent.type == "void_bite":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="necrotic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(run.player, "minor_vulnerable_necrotic", "轻度黯蚀易伤", "受到的黯蚀伤害增加 50%", 1)
            logs.append(f"【{enemy.name}】施展虚空噬咬。{dmg_msg}")
        elif intent.type == "void_erosion":
            engine._add_buff_to(run.player, "void_weakness", "虚空虚弱", "造成的法术伤害减少 3 点，回合结束时层数减少 1", 2)
            logs.append(f"【{enemy.name}】施展虚空侵蚀，使玩家获得了 2 级【虚空虚弱】Buff。")

class AncientWardenTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("先古守卫", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = []
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks
        val = intent.val + strength

        if intent.type == "portal_smash":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="bludgeoning")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"【{enemy.name}】施展门扉重击。{dmg_msg}")
        elif intent.type == "ancient_charge":
            engine._add_buff_to(enemy, "strength", "力量", "造成的伤害增加", 3)
            logs.append(f"【{enemy.name}】进行先古充能，力量提升了 3 点。")
        elif intent.type == "space_lock":
            run.node_data["drain_a"] = True
            logs.append(f"【{enemy.name}】施展空间闭锁，玩家下回合将失去 1 个动作点（A）。")

class AstralHoundTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("星界猎犬", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = []
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
            logs.append(f"【{enemy.name}】星光撕咬玩家。{dmg_msg}")
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

class VoidLurkerTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        return [EnemyIntentState(type="void_strike", val=6, desc="虚空打击 (造成 6 点黯蚀伤害)", cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = []
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks
        val = intent.val + strength
        before_len = len(run.node_data.get("battle_logs", []))
        engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="necrotic")
        after_logs = run.node_data.get("battle_logs", [])
        dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
        logs.append(f"【{enemy.name}】对玩家进行虚空打击。{dmg_msg}")
