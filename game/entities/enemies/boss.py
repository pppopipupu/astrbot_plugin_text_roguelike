from typing import Tuple, List
from .base import EnemyTemplate, register_enemy
from ...data.enemy_data import ENEMY_CONFIG

@register_enemy("远古红龙")
class BossRedDragonTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("远古红龙", {})
        intents = cfg.get("intents", [])
        intents_list = []
        for _ in range(enemy.max_actions):
            chosen = random.choice(intents)
            intents_list.append(EnemyIntentState(
                type=chosen["id"],
                val=chosen["val"],
                desc=chosen["desc"],
                cost_a=1,
                cost_ba=0
            ))
        for _ in range(enemy.max_bonus_actions):
            chosen = random.choice(intents)
            intents_list.append(EnemyIntentState(
                type=chosen["id"],
                val=chosen["val"],
                desc=chosen["desc"],
                cost_a=0,
                cost_ba=1
            ))
        return intents_list

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
        if intent.type == "attack":
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            dmg = intent.val + strength
            self._perform_attack(run, engine, enemy, dmg, logs)
        elif intent.type == "defend":
            enemy.shield += intent.val
            logs.append(f"敌方领主【{enemy.name}】进行防守，获得 {intent.val} 点护盾。")
        elif intent.type == "summon":
            from ...models.state import EnemyState, EnemyIntentState
            cfg = ENEMY_CONFIG.get("远古红龙", {})
            sg = cfg.get("summon_goblin", {})
            new_goblin = EnemyState(
                name=sg.get("name", "魔仆"),
                hp=sg.get("hp", 5),
                max_hp=sg.get("max_hp", 5),
                shield=0,
                actions=1,
                bonus_actions=0,
                is_summon=True,
                max_actions=1,
                max_bonus_actions=0,
                intents=[EnemyIntentState(
                    type="attack",
                    val=sg.get("intent_val", 1),
                    desc=sg.get("intent_desc", "准备攻击 (造成 1 伤害)"),
                    cost_a=1,
                    cost_ba=0
                )]
            )
            run.enemies.append(new_goblin)
            logs.append(f"敌方领主【{enemy.name}】召唤了一个【魔仆】。")
        elif intent.type == "attack_all":
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            dmg = intent.val + strength
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", dmg, source=f"enemy:{enemy.name}", damage_type="bludgeoning")
            after_logs = run.node_data.get("battle_logs", [])
            if len(after_logs) > before_len:
                dmg_msg = after_logs.pop()
                logs.append(f"敌方领主【{enemy.name}】扫尾攻击玩家。{dmg_msg}")
            for mk in list(p.minions.keys()):
                if mk not in p.minions:
                    continue
                m_name = p.minions[mk].name
                before_len = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, f"p{mk}", dmg, source=f"enemy:{enemy.name}", damage_type="bludgeoning")
                after_logs = run.node_data.get("battle_logs", [])
                if len(after_logs) > before_len:
                    dmg_msg = after_logs.pop()
                    logs.append(f"我方随从【{m_name}】受到扫尾波及。{dmg_msg}")
        return "\n".join(logs)

@register_enemy("腐化之心")
class BossCorruptedHeartTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        turn = run.node_data.get("heart_turn", 1)
        cycle = (turn - 1) % 4 + 1
        intents_list = []
        
        if cycle == 1:
            itype, val, desc = "debuff", 0, "邪恶之语 (将晕眩与苦恼放入玩家牌组)"
        elif cycle == 2:
            itype, val, desc = "multi_attack", 2, "血弹喷射 (造成 2 点伤害，重复 8 次)"
        elif cycle == 3:
            itype, val, desc = "big_attack", 20, "毁灭之痛 (造成 20 点伤害)"
        else:
            itype, val, desc = "strength_buff", 2, "充能 (获得 2 层力量，使后续伤害增加 2)"
        intents_list.append(EnemyIntentState(type=itype, val=val, desc=desc, cost_a=1, cost_ba=0))
        
        if cycle == 1:
            itype, val, desc = "defend_large", 15, "暗影护盾 (获得 15 护盾)"
        elif cycle == 2:
            itype, val, desc = "defend_normal", 10, "护盾 (获得 10 护盾)"
        elif cycle == 3:
            itype, val, desc = "defend_normal", 10, "护盾 (获得 10 护盾)"
        else:
            itype, val, desc = "defend_large", 20, "暗影护盾 (获得 20 护盾)"
        intents_list.append(EnemyIntentState(type=itype, val=val, desc=desc, cost_a=0, cost_ba=1))
        
        if cycle == 1:
            itype, val, desc = "drain_ba", 1, "虚空之歌 (使玩家下回合失去 1BA)"
        elif cycle == 2:
            itype, val, desc = "heart_strike", 4, "心跳重击 (造成 4 伤害)"
        elif cycle == 3:
            itype, val, desc = "gaze_discard", 1, "虚无凝视 (迫使玩家随机丢弃 1 张手牌)"
        else:
            itype, val, desc = "heart_heal", 10, "回潮 (恢复 10 生命)"
        intents_list.append(EnemyIntentState(type=itype, val=val, desc=desc, cost_a=0, cost_ba=1))
        
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
        
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks

        if intent.type == "debuff":
            p.draw_pile.append("curse_dazed")
            p.draw_pile.append("curse_agony")
            random.shuffle(p.draw_pile)
            logs.append(f"【{enemy.name}】施放了【邪恶之语】，将【晕眩】与【苦恼】放入了玩家的抽牌堆并进行了洗牌。")
            
        elif intent.type == "multi_attack":
            dmg = intent.val + strength
            logs.append(f"【{enemy.name}】释放【血弹喷射】，发动 8 次攻击（每次 {dmg} 伤害）：")
            for _ in range(8):
                if enemy.hp <= 0:
                    break
                self._perform_attack(run, engine, enemy, dmg, logs)
                
        elif intent.type == "big_attack":
            dmg = intent.val + strength
            self._perform_attack(run, engine, enemy, dmg, logs)
            
        elif intent.type == "strength_buff":
            engine._add_buff_to(enemy, "strength", "力量", f"造成的伤害增加 {intent.val} 点", intent.val)
            logs.append(f"【{enemy.name}】进行【充能】，力量提升了 {intent.val} 点。")
            
        elif intent.type in ("defend_large", "defend_normal"):
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】获得 {intent.val} 点护盾。")
            
        elif intent.type == "drain_ba":
            run.node_data["drain_ba"] = True
            logs.append(f"【{enemy.name}】吟唱【虚空之歌】，玩家将在下一回合失去 1 个附赠动作点 (BA)。")
            
        elif intent.type == "heart_strike":
            dmg = intent.val + strength
            self._perform_attack(run, engine, enemy, dmg, logs)
            
        elif intent.type == "gaze_discard":
            engine._add_buff_to(run.player, "discard_next_turn", "下回合弃牌", "在下一回合开始时，你将随机丢弃等同于此状态层数的手牌", 1)
            logs.append(f"【{enemy.name}】虚无凝视，使玩家在下一回合开始时将被迫随机丢弃 1 张手牌。")
                
        elif intent.type == "heart_heal":
            enemy.hp = min(enemy.max_hp, enemy.hp + intent.val)
            logs.append(f"【{enemy.name}】自我回潮，恢复了 {intent.val} 点生命值。")
        return "\n".join(logs)

@register_enemy("Icerainboww")
class BossIcerainbowwTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        turn = run.node_data.get("icerainboww_turn", 1)
        cycle = (turn - 1) % 4 + 1
        intents_list = []
        
        if cycle == 1:
            itype, val, desc = "icerain_shoot", 2, "冰雨弓射击 (造成 2 寒冷伤害，使玩家下回合失去 1A)"
        elif cycle == 2:
            itype, val, desc = "winter_gaze", 4, "寒冬凝视 (造成 4 心灵伤害，并使玩家受到轻度寒冷易伤)"
        elif cycle == 3:
            itype, val, desc = "smash_attack", 10, "粉碎攻击 (造成 10 寒冷伤害，并使玩家受到轻度寒冷易伤)"
        else:
            itype, val, desc = "frost_blast", 6, "冰霜爆震 (对玩家与所有我方随从造成 6 寒冷伤害)"
        intents_list.append(EnemyIntentState(type=itype, val=val, desc=desc, cost_a=1, cost_ba=0))
        
        if cycle == 1:
            itype, val, desc = "fury", 1, "愤怒 (获得 1 层愤怒buff，被打出珍奇或传奇卡牌激怒时自身增伤)"
        elif cycle == 2:
            itype, val, desc = "aurora_shield", 12, "极光屏障 (获得 12 护盾并净化 1 负面 Buff，无负面时额外获得 4 护盾)"
        elif cycle == 3:
            itype, val, desc = "icerain_shoot", 2, "冰雨弓射击 (造成 2 寒冷伤害，使玩家下回合失去 1A)"
        else:
            itype, val, desc = "fury", 1, "愤怒 (获得 1 层愤怒buff，被打出珍奇或传奇卡牌激怒时自身增伤)"
        intents_list.append(EnemyIntentState(type=itype, val=val, desc=desc, cost_a=1, cost_ba=0))
        
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
        
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks
 
        val = intent.val + strength
 
        if intent.type == "icerain_shoot":
            if p.minions and random.random() < 0.5:
                target_key = random.choice(list(p.minions.keys()))
                target = p.minions[target_key]
                m_name = target.name
                before_len = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, f"p{target_key}", val, source=f"enemy:{enemy.name}", damage_type="cold")
                after_logs = run.node_data.get("battle_logs", [])
                if len(after_logs) > before_len:
                    dmg_msg = after_logs.pop()
                    logs.append(f"【{enemy.name}】用冰雨弓攻击了我方随从【{m_name}】。{dmg_msg}")
            else:
                before_len = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="cold")
                after_logs = run.node_data.get("battle_logs", [])
                if len(after_logs) > before_len:
                    dmg_msg = after_logs.pop()
                    logs.append(f"【{enemy.name}】用冰雨弓攻击玩家。{dmg_msg}")
            run.node_data["drain_a"] = True
            logs.append(f"【{enemy.name}】射出冰雨弓，使玩家在下一回合失去 1 个动作点 (A)。")
 
        elif intent.type == "fury":
            engine._add_buff_to(enemy, "fury", "愤怒", "玩家使用珍奇或传奇卡牌时，该怪物获得等同于愤怒层数的力量", 1)
            logs.append(f"【{enemy.name}】获得了 1 层【愤怒】Buff！")
 
        elif intent.type == "smash_attack":
            if p.minions and random.random() < 0.5:
                target_key = random.choice(list(p.minions.keys()))
                target = p.minions[target_key]
                m_name = target.name
                before_len = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, f"p{target_key}", val, source=f"enemy:{enemy.name}", damage_type="cold")
                after_logs = run.node_data.get("battle_logs", [])
                if len(after_logs) > before_len:
                    dmg_msg = after_logs.pop()
                    logs.append(f"【{enemy.name}】对随从【{m_name}】施展粉碎攻击。{dmg_msg}")
            else:
                before_len = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="cold")
                after_logs = run.node_data.get("battle_logs", [])
                if len(after_logs) > before_len:
                    dmg_msg = after_logs.pop()
                    logs.append(f"【{enemy.name}】对玩家施展粉碎攻击。{dmg_msg}")
            engine._add_buff_to(p, "minor_vulnerable_cold", "轻度寒冷易伤", "受到的寒冷伤害增加 50%", 2)
            logs.append(f"【{enemy.name}】的粉碎攻击使玩家获得了 2 层【轻度寒冷易伤】状态。")
 
        elif intent.type == "aurora_shield":
            neg_buff = next((b for b in enemy.buffs if b.id == "stun"), None)
            shield_gain = intent.val
            if neg_buff:
                neg_name = neg_buff.name
                neg_buff.stacks -= 1
                if neg_buff.stacks <= 0:
                    enemy.buffs.remove(neg_buff)
                engine._sync_enemy_intents(enemy)
                logs.append(f"【{enemy.name}】施展【极光屏障】，获得 {shield_gain} 点护盾，并解除了自身的负面状态【{neg_name}】！")
            else:
                shield_gain += 4
                logs.append(f"【{enemy.name}】施展【极光屏障】，由于没有负面状态，额外获得了 4 点护盾，总计获得 {shield_gain} 点护盾。")
            enemy.shield += shield_gain
 
        elif intent.type == "winter_gaze":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="psychic")
            after_logs = run.node_data.get("battle_logs", [])
            if len(after_logs) > before_len:
                dmg_msg = after_logs.pop()
                logs.append(f"【{enemy.name}】投射【寒冬凝视】。{dmg_msg}")
            engine._add_buff_to(p, "minor_vulnerable_cold", "轻度寒冷易伤", "受到的寒冷伤害增加 50%", 1)
            logs.append(f"【{enemy.name}】的寒冬凝视使玩家获得了 1 层【轻度寒冷易伤】状态。")
 
        elif intent.type == "frost_blast":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="cold")
            after_logs = run.node_data.get("battle_logs", [])
            if len(after_logs) > before_len:
                dmg_msg = after_logs.pop()
                logs.append(f"【{enemy.name}】释放【冰霜爆震】对玩家造成伤害。{dmg_msg}")
            for mk in list(p.minions.keys()):
                if mk not in p.minions:
                    continue
                m_name = p.minions[mk].name
                before_len = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, f"p{mk}", val, source=f"enemy:{enemy.name}", damage_type="cold")
                after_logs = run.node_data.get("battle_logs", [])
                if len(after_logs) > before_len:
                    dmg_msg = after_logs.pop()
                    logs.append(f"我方随从【{m_name}】受到冰霜爆震波及。{dmg_msg}")
        return "\n".join(logs)

@register_enemy("雷霆领主")
class BossThunderLordTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        if run.node_data.get("thunder_lord_overloaded"):
            enemy.actions = max(0, enemy.actions - 1)
            run.node_data["thunder_lord_overloaded"] = False
        turn = run.node_data.get("thunder_lord_turn", 1)
        cycle = (turn - 1) % 4 + 1
        intents_list = []
        if cycle == 1:
            itype, val, desc = "thunder_strike", 8, "雷鸣重击 (造成 8 雷鸣伤害，并对玩家施加 2 层电击)"
        elif cycle == 2:
            itype, val, desc = "lightning_shield", 12, "闪电护壳 (获得 12 护盾并获得闪电护体)"
        elif cycle == 3:
            itype, val, desc = "storm_summon", 0, "呼唤雷云 (召唤一只雷影魔仆)"
        else:
            itype, val, desc = "electric_overload", 6, "电能超载 (获得 2 层力量，造成 6 闪电伤害，下回合失去 1A)"
        intents_list.append(EnemyIntentState(type=itype, val=val, desc=desc, cost_a=1, cost_ba=0))

        if cycle == 1:
            itype, val, desc = "lightning_shield", 10, "闪电护壳 (获得 10 护盾并获得闪电护体)"
        elif cycle == 2:
            itype, val, desc = "thunder_strike", 6, "雷鸣重击 (造成 6 雷鸣伤害，并对玩家施加 2 层电击)"
        elif cycle == 3:
            itype, val, desc = "defend", 8, "聚能防护 (获得 8 护盾)"
        else:
            itype, val, desc = "thunder_strike", 8, "雷鸣重击 (造成 8 雷鸣伤害，并对玩家施加 2 层电击)"
        intents_list.append(EnemyIntentState(type=itype, val=val, desc=desc, cost_a=0, cost_ba=1))

        if cycle == 1:
            itype, val, desc = "defend", 6, "聚能防护 (获得 6 护盾)"
        elif cycle == 2:
            itype, val, desc = "defend", 6, "聚能防护 (获得 6 护盾)"
        elif cycle == 3:
            itype, val, desc = "thunder_strike", 6, "雷鸣重击 (造成 6 雷鸣伤害，并对玩家施加 2 层电击)"
        else:
            itype, val, desc = "defend", 10, "聚能防护 (获得 10 护盾)"
        intents_list.append(EnemyIntentState(type=itype, val=val, desc=desc, cost_a=0, cost_ba=1))
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
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks
        val = intent.val + strength

        if intent.type == "thunder_strike":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="thunder")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(run.player, "shock", "电击", "受到的闪电和雷鸣伤害每层增加 1 点", 2)
            logs.append(f"【{enemy.name}】施展雷鸣重击。{dmg_msg}")
        elif intent.type == "lightning_shield":
            enemy.shield += intent.val
            engine._add_buff_to(enemy, "lightning_shield", "闪电护体", "受到伤害时反弹 2 点闪电伤害并施加 1 层电击", 1)
            logs.append(f"【{enemy.name}】施展闪电护壳，获得 {intent.val} 点护盾并获得闪电护体。")
        elif intent.type == "storm_summon":
            from ...models.state import EnemyState, EnemyIntentState
            new_minion = EnemyState(
                name="雷影魔仆",
                hp=12,
                max_hp=12,
                shield=0,
                actions=1,
                bonus_actions=0,
                is_summon=True,
                max_actions=1,
                max_bonus_actions=0,
                intents=[EnemyIntentState(
                    type="lightning_strike",
                    val=4,
                    desc="闪电击 (造成 4 闪电伤害，并施加 1 层电击)",
                    cost_a=1,
                    cost_ba=0
                )]
            )
            run.enemies.append(new_minion)
            logs.append(f"【{enemy.name}】呼唤雷云，召唤了一只【雷影魔仆】加入战场。")
        elif intent.type == "electric_overload":
            engine._add_buff_to(enemy, "strength", "力量", "造成的伤害增加", 2)
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="lightning")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            run.node_data["thunder_lord_overloaded"] = True
            logs.append(f"【{enemy.name}】释放电能超载。{dmg_msg}")
        elif intent.type == "defend":
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】凝聚雷电防护，获得 {intent.val} 点护盾。")
        return "\n".join(logs)

@register_enemy("虚空之门·尤格-索托斯")
class BossYogSothothTemplate(EnemyTemplate):
    def on_enemy_before_death(self, run, enemy, event, engine):
        if enemy.name == "虚空之门·尤格-索托斯":
            event.cancel()
            enemy.name = "【觉醒】虚空之门·尤格-索托斯"
            enemy.max_hp = 260
            enemy.hp = 260
            enemy.shield = 30
            enemy.actions = 2
            enemy.bonus_actions = 2
            enemy.max_actions = 2
            enemy.max_bonus_actions = 2
            enemy.buffs.clear()
            from ...models.state import BuffState
            enemy.buffs.append(BuffState(id="end_gate_passive", name="终焉之门", stacks=1, desc="每回合开始时获得 15 点护盾，且清除自身所有负面效果，受到伤害时 30% 几率反弹 4 点真实伤害"))
            run.node_data["yog_sothoth_phase"] = 2
            run.node_data["yog_sothoth_turn"] = 0
            enemy.intents.clear()
            engine._log_event(run, "🌟 虚空之门·尤格-索托斯破裂了！狂暴的虚空能量从中倾泻而出，虚空之门在坍缩中重新觉醒！进入了觉醒形态！")

    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        phase = run.node_data.get("yog_sothoth_phase", 1)
        turn = run.node_data.get("yog_sothoth_turn", 1)
        run.node_data["yog_sothoth_turn"] = turn + 1
        cycle = (turn - 1) % 4 + 1
        intents_list = []
        if phase == 1:
            if cycle == 1:
                intents_list.append(EnemyIntentState(type="gate_gaze", val=12, desc="门之凝视 (造成 12 点心灵伤害，对随机随从造成 8 点力场伤害，玩家下回合无法抽牌)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="void_corruption", val=8, desc="虚空腐蚀 (造成 8 点强酸伤害并施加 1 层虚空虚弱)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="void_exhaust", val=1, desc="虚空耗竭 (使玩家获得 1 层虚空耗竭 Buff)", cost_a=0, cost_ba=1))
            elif cycle == 2:
                intents_list.append(EnemyIntentState(type="void_storm", val=10, desc="虚空风暴 (对玩家与所有我方随从造成 10 点力场伤害)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="gravity_press", val=10, desc="重力压迫 (造成 10 点钝击伤害，如果玩家身上有护盾，额外损失 5 点护盾；对随机随从造成 6 点钝击伤害)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="decay_whisper", val=2, desc="衰退低语 (使玩家获得 2 层虚空虚弱 Buff)", cost_a=0, cost_ba=1))
            elif cycle == 3:
                intents_list.append(EnemyIntentState(type="ancient_resonance", val=20, desc="先古共鸣 (获得 20 点护盾，且下回合获得 2 层力量)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="void_storm", val=8, desc="虚空风暴 (对玩家与所有我方随从造成 8 点力场伤害)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="mana_block", val=1, desc="魔力阻断 (使玩家获得 1 层魔力泄漏 Buff)", cost_a=0, cost_ba=1))
            else:
                intents_list.append(EnemyIntentState(type="gate_gaze", val=12, desc="门之凝视 (造成 12 点心灵伤害，对随机随从造成 8 点力场伤害，玩家下回合无法抽牌)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="gravity_press", val=10, desc="重力压迫 (造成 10 点钝击伤害，如果玩家身上有护盾，额外损失 5 点护盾；对随机随从造成 6 点钝击伤害)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="dimensional_distortion", val=15, desc="维度扭曲 (获得 15 点护盾)", cost_a=0, cost_ba=1))
        else:
            if cycle == 1:
                intents_list.append(EnemyIntentState(type="time_collapse", val=14, desc="时空坍缩 (造成 14 点力场伤害，玩家下回合动作减少 1A 1BA，且洗入 2 张空间撕裂)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="chaos_beam", val=10, desc="混乱光束 (造成 10 点光耀伤害，对所有随从造成 6 点光耀伤害)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="void_shield_large", val=20, desc="虚空大盾 (获得 20 点护盾并净化自身 1 负面 Buff)", cost_a=0, cost_ba=1))
                intents_list.append(EnemyIntentState(type="abyss_exhaust", val=1, desc="深渊耗竭 (使玩家获得 1 层虚空耗竭 Buff)", cost_a=0, cost_ba=1))
            elif cycle == 2:
                intents_list.append(EnemyIntentState(type="all_gates_open", val=20, desc="万门齐开 (召唤 2 个虚空潜伏者，敌方全体获得 2 层力量；若格子满则造成 20 点心灵伤害)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="abyss_gaze", val=12, desc="深渊凝视 (造成 12 点心灵伤害，使玩家下回合少抽 2 张牌)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="strength_infuse", val=2, desc="力量注入 (敌方全体获得 2 层力量)", cost_a=0, cost_ba=1))
                intents_list.append(EnemyIntentState(type="end_whisper", val=6, desc="终焉低语 (造成 6 点心灵伤害，且迫使玩家随机丢弃 1 张手牌)", cost_a=0, cost_ba=1))
            elif cycle == 3:
                intents_list.append(EnemyIntentState(type="doomsday_tide", val=12, desc="灭世之潮 (对玩家与所有随从造成 12 点真实伤害，穿透护盾，并恢复自身 15 点生命值)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="time_collapse", val=10, desc="时空坍缩 (造成 10 点力场伤害，玩家下回合动作减少 1A 1BA，且洗入 2 张空间撕裂)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="mana_block", val=1, desc="魔力阻断 (使玩家获得 1 层魔力泄漏 Buff)", cost_a=0, cost_ba=1))
                intents_list.append(EnemyIntentState(type="reality_shatter", val=8, desc="现实碎裂 (造成 8 点真实伤害)", cost_a=0, cost_ba=1))
            else:
                intents_list.append(EnemyIntentState(type="chaos_beam", val=12, desc="混乱光束 (造成 12 点光耀伤害，对所有随从造成 6 点光耀伤害)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="doomsday_tide", val=10, desc="灭世之潮 (对玩家与所有随从造成 10 点真实伤害，穿透护盾，并恢复自身 15 点生命值)", cost_a=1, cost_ba=0))
                intents_list.append(EnemyIntentState(type="strength_infuse", val=2, desc="力量注入 (敌方全体获得 2 层力量)", cost_a=0, cost_ba=1))
                intents_list.append(EnemyIntentState(type="void_shield_large", val=20, desc="虚空大盾 (获得 20 点护盾并净化自身 1 负面 Buff)", cost_a=0, cost_ba=1))
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
        p = run.player
        import random
        from ..buffs import is_debuff

        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks
        val = intent.val + strength

        if intent.type == "gate_gaze":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="psychic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"【{enemy.name}】对玩家施展门之凝视。{dmg_msg}")
            if p.minions:
                target_key = random.choice(list(p.minions.keys()))
                m_name = p.minions[target_key].name
                before_len = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, f"p{target_key}", 8, source=f"enemy:{enemy.name}", damage_type="force")
                after_logs = run.node_data.get("battle_logs", [])
                dmg_msg_m = after_logs.pop() if len(after_logs) > before_len else ""
                logs.append(f"随从【{m_name}】受到波及。{dmg_msg_m}")
            engine._add_buff_to(run.player, "tactical_focus", "无法抽牌", "本回合无法再抽牌", 1)
            logs.append(f"【{enemy.name}】的心灵波动使玩家在下一回合【无法抽牌】。")

        elif intent.type == "void_storm":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="force")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"【{enemy.name}】引发虚空风暴。{dmg_msg}")
            for mk in list(p.minions.keys()):
                if mk not in p.minions:
                    continue
                m_name = p.minions[mk].name
                before_len = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, f"p{mk}", val, source=f"enemy:{enemy.name}", damage_type="force")
                after_logs = run.node_data.get("battle_logs", [])
                dmg_msg_m = after_logs.pop() if len(after_logs) > before_len else ""
                logs.append(f"我方随从【{m_name}】受到虚空风暴波及。{dmg_msg_m}")

        elif intent.type == "ancient_resonance":
            enemy.shield += intent.val
            engine._add_buff_to(enemy, "strength", "力量", "造成的伤害增加", 2)
            logs.append(f"【{enemy.name}】进行先古共鸣，获得 {intent.val} 点护盾，且攻击力量提升 2 点。")

        elif intent.type == "void_corruption":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="acid")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(run.player, "void_weakness", "虚空虚弱", "造成的法术伤害减少 3 点，回合结束时层数减少 1", 1)
            logs.append(f"【{enemy.name}】引发虚空腐蚀对玩家造成酸蚀。{dmg_msg}")
            logs.append(f"玩家获得了 1 层【虚空虚弱】状态。")

        elif intent.type == "gravity_press":
            lost_shield_msg = ""
            if p.shield > 0:
                lost_amount = min(5, p.shield)
                p.shield -= lost_amount
                lost_shield_msg = f"（重力场额外压碎了玩家 {lost_amount} 点护盾）"
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="bludgeoning")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"【{enemy.name}】施展重力压迫。{dmg_msg}{lost_shield_msg}")
            if p.minions:
                target_key = random.choice(list(p.minions.keys()))
                m_name = p.minions[target_key].name
                before_len = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, f"p{target_key}", 6, source=f"enemy:{enemy.name}", damage_type="bludgeoning")
                after_logs = run.node_data.get("battle_logs", [])
                dmg_msg_m = after_logs.pop() if len(after_logs) > before_len else ""
                logs.append(f"我方随从【{m_name}】受到重力余波打击。{dmg_msg_m}")

        elif intent.type in ("void_exhaust", "abyss_exhaust"):
            engine._add_buff_to(run.player, "void_exhaustion", "虚空耗竭", "本回合内打出的所有非随从和护符卡牌都会在结算后被强制消耗移入消耗堆", 1)
            logs.append(f"【{enemy.name}】引动了虚空耗竭，玩家被施加了 1 层【虚空耗竭】状态！")

        elif intent.type == "decay_whisper":
            engine._add_buff_to(run.player, "void_weakness", "虚空虚弱", "造成的法术伤害减少 3 点，回合结束时层数减少 1", 2)
            logs.append(f"【{enemy.name}】低吟起衰退歌谣，使玩家获得了 2 层【虚空虚弱】状态。")

        elif intent.type == "mana_block":
            engine._add_buff_to(run.player, "mana_leak", "魔力泄漏", "你打出的法术卡牌需要额外消耗 1BA，且造成的法术伤害减少 2 点", 1)
            logs.append(f"【{enemy.name}】施加魔力阻断，使玩家获得了 1 层【魔力泄漏】状态。")

        elif intent.type == "dimensional_distortion":
            enemy.shield += intent.val
            logs.append(f"【{enemy.name}】扭曲周围的维度，获得了 {intent.val} 点护盾。")

        elif intent.type == "time_collapse":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="force")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            run.node_data["drain_a"] = True
            run.node_data["drain_ba"] = True
            p.draw_pile.append("curse_dimensional_tear")
            p.draw_pile.append("curse_dimensional_tear")
            random.shuffle(p.draw_pile)
            logs.append(f"【{enemy.name}】施展时空坍缩，使玩家下回合减少 1A 1BA，且洗入 2 张【空间撕裂】。{dmg_msg}")

        elif intent.type == "chaos_beam":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="radiant")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"【{enemy.name}】射出混乱光束。{dmg_msg}")
            for mk in list(p.minions.keys()):
                if mk not in p.minions:
                    continue
                m_name = p.minions[mk].name
                before_len = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, f"p{mk}", 6, source=f"enemy:{enemy.name}", damage_type="radiant")
                after_logs = run.node_data.get("battle_logs", [])
                dmg_msg_m = after_logs.pop() if len(after_logs) > before_len else ""
                logs.append(f"我方随从【{m_name}】受到混乱光束穿透。{dmg_msg_m}")

        elif intent.type == "void_shield_large":
            enemy.shield += intent.val
            neg_buff = next((b for b in enemy.buffs if is_debuff(b.id)), None)
            if neg_buff:
                neg_name = neg_buff.name
                neg_buff.stacks -= 1
                if neg_buff.stacks <= 0:
                    enemy.buffs.remove(neg_buff)
                engine._sync_enemy_intents(enemy)
                logs.append(f"【{enemy.name}】施展虚空大盾，获得 {intent.val} 点护盾，并解除了 1 层自身的负面状态【{neg_name}】！")
            else:
                logs.append(f"【{enemy.name}】施展虚空大盾，获得 {intent.val} 点护盾。")

        elif intent.type == "all_gates_open":
            empty_slots = 6 - len(run.enemies)
            summon_count = min(2, empty_slots)
            from ...models.state import EnemyState, EnemyIntentState
            for _ in range(summon_count):
                new_minion = EnemyState(
                    name="虚空潜伏者",
                    hp=20,
                    max_hp=20,
                    shield=0,
                    actions=1,
                    bonus_actions=0,
                    is_summon=True,
                    max_actions=1,
                    max_bonus_actions=0,
                    intents=[EnemyIntentState(
                        type="void_strike",
                        val=6,
                        desc="虚空打击 (造成 6 点黯蚀伤害)",
                        cost_a=1,
                        cost_ba=0
                    )]
                )
                run.enemies.append(new_minion)
            for e in run.enemies:
                engine._add_buff_to(e, "strength", "力量", "造成的伤害增加", 2)
            logs.append(f"【{enemy.name}】开启了万门，召唤了 {summon_count} 个【虚空潜伏者】，且敌方全体力量提升了 2 点。")
            if summon_count < 2:
                before_len = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, "p0", 20, source=f"enemy:{enemy.name}", damage_type="psychic")
                after_logs = run.node_data.get("battle_logs", [])
                dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
                logs.append(f"由于传送门受阻，虚空能量直接冲击玩家。{dmg_msg}")

        elif intent.type == "abyss_gaze":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="psychic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            run.node_data["draw_penalty_next_turn"] = 2
            logs.append(f"【{enemy.name}】投射深渊凝视，玩家下回合少抽 2 张牌。{dmg_msg}")

        elif intent.type == "strength_infuse":
            for e in run.enemies:
                engine._add_buff_to(e, "strength", "力量", "造成的伤害增加", 2)
            logs.append(f"【{enemy.name}】进行力量注入，敌方全体力量提升 2 点。")

        elif intent.type == "end_whisper":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="psychic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(run.player, "discard_next_turn", "下回合弃牌", "在下一回合开始时，你将随机丢弃等同于此状态层数的手牌", 1)
            logs.append(f"【{enemy.name}】发出终焉低语。{dmg_msg}，且使玩家在下一回合开始时将被迫随机丢弃 1 张手牌。")

        elif intent.type == "doomsday_tide":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="true")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"【{enemy.name}】释放了灭世之潮！造成真实伤害。{dmg_msg}")
            for mk in list(p.minions.keys()):
                if mk not in p.minions:
                    continue
                m_name = p.minions[mk].name
                before_len = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, f"p{mk}", val, source=f"enemy:{enemy.name}", damage_type="true")
                after_logs = run.node_data.get("battle_logs", [])
                dmg_msg_m = after_logs.pop() if len(after_logs) > before_len else ""
                logs.append(f"我方随从【{m_name}】受到真实伤害波及。{dmg_msg_m}")
            enemy.hp = min(enemy.max_hp, enemy.hp + 15)
            logs.append(f"【{enemy.name}】吸取了生命力，恢复了 15 点生命值。")

        elif intent.type == "reality_shatter":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="true")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"【{enemy.name}】引爆现实碎裂，对玩家造成真实伤害。{dmg_msg}")
        return "\n".join(logs)

register_enemy("【觉醒】虚空之门·尤格-索托斯")(BossYogSothothTemplate)
