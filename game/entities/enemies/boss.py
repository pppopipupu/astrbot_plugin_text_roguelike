from typing import Tuple, List
from .base import EnemyTemplate
from ...data.enemy_data import ENEMY_CONFIG

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
                m_name = p.minions[mk].name
                before_len = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, f"p{mk}", dmg, source=f"enemy:{enemy.name}", damage_type="bludgeoning")
                after_logs = run.node_data.get("battle_logs", [])
                if len(after_logs) > before_len:
                    dmg_msg = after_logs.pop()
                    logs.append(f"我方随从【{m_name}】受到扫尾波及。{dmg_msg}")

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
            if p.hand:
                discarded = p.hand.pop(random.randint(0, len(p.hand) - 1))
                from ..cards import ALL_CARDS
                card_name = ALL_CARDS[discarded].name if discarded in ALL_CARDS else "未知卡牌"
                agile_msg = engine._discard_card(run, discarded)
                logs.append(f"【{enemy.name}】虚无凝视，迫使玩家随机丢弃了卡牌【{card_name}】。")
                if agile_msg:
                    logs.append(agile_msg)
            else:
                logs.append(f"【{enemy.name}】虚无凝视，但玩家没有手牌可以丢弃。")
                
        elif intent.type == "heart_heal":
            enemy.hp = min(enemy.max_hp, enemy.hp + intent.val)
            logs.append(f"【{enemy.name}】自我回潮，恢复了 {intent.val} 点生命值。")

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
                m_name = p.minions[mk].name
                before_len = len(run.node_data.get("battle_logs", []))
                engine._damage_target(run, f"p{mk}", val, source=f"enemy:{enemy.name}", damage_type="cold")
                after_logs = run.node_data.get("battle_logs", [])
                if len(after_logs) > before_len:
                    dmg_msg = after_logs.pop()
                    logs.append(f"我方随从【{m_name}】受到冰霜爆震波及。{dmg_msg}")

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
            logs = []
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
            engine._add_buff_to(run.player, "shock", "电击", "受到的闪电和雷鸣伤害每层增加 3 点", 2)
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
