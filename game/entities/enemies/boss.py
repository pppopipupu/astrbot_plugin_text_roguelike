from typing import Tuple, List
from .base import EnemyTemplate
from ...data.enemy_data import ENEMY_CONFIG

class BossRedDragonTemplate(EnemyTemplate):
    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        import random
        cfg = ENEMY_CONFIG.get("远古红龙", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return chosen["id"], chosen["val"], chosen["desc"]

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        p = run.player
        import random
        if enemy.intent_type == "attack":
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            dmg = enemy.intent_val + strength
            self._perform_attack(run, engine, enemy, dmg, logs)
        elif enemy.intent_type == "defend":
            enemy.shield += enemy.intent_val
            logs.append(f"敌方领主【{enemy.name}】进行防守，获得 {enemy.intent_val} 点护盾。")
        elif enemy.intent_type == "summon":
            from ...models.state import EnemyState
            cfg = ENEMY_CONFIG.get("远古红龙", {})
            sg = cfg.get("summon_goblin", {})
            new_goblin = EnemyState(
                name=sg.get("name", "魔仆"),
                hp=sg.get("hp", 5),
                max_hp=sg.get("max_hp", 5),
                shield=0,
                intent_type="attack",
                intent_val=sg.get("intent_val", 1),
                intent_desc=sg.get("intent_desc", "准备攻击 (造成 1 伤害)"),
                actions=1,
                bonus_actions=0,
                is_summon=True,
                max_actions=1,
                max_bonus_actions=0
            )
            run.enemies.append(new_goblin)
            logs.append(f"敌方领主【{enemy.name}】召唤了一个【魔仆】。")
        elif enemy.intent_type == "attack_all":
            strength = 0
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
            dmg = enemy.intent_val + strength
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
    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        turn = run.node_data.get("heart_turn", 1)
        cycle = (turn - 1) % 4 + 1
        if cycle == 1:
            return "debuff", 0, "邪恶之语 (将晕眩与苦恼放入玩家牌组)"
        elif cycle == 2:
            return "multi_attack", 2, "血弹喷射 (造成 2 点伤害，重复 8 次)"
        elif cycle == 3:
            return "big_attack", 20, "毁灭之痛 (造成 20 点伤害)"
        else:
            return "strength_buff", 2, "充能 (获得 2 层力量，使后续伤害增加 2)"

    def roll_intent_ba(self, run, engine, enemy) -> Tuple[str, int, str]:
        turn = run.node_data.get("heart_turn", 1)
        cycle = (turn - 1) % 4 + 1
        if cycle == 1:
            return "defend_large", 15, "暗影护盾 (获得 15 护盾)"
        elif cycle == 2:
            return "defend_normal", 10, "护盾 (获得 10 护盾)"
        elif cycle == 3:
            return "defend_normal", 10, "护盾 (获得 10 护盾)"
        else:
            return "defend_large", 20, "暗影护盾 (获得 20 护盾)"

    def roll_intent_ba2(self, run, engine, enemy) -> Tuple[str, int, str]:
        turn = run.node_data.get("heart_turn", 1)
        cycle = (turn - 1) % 4 + 1
        if cycle == 1:
            return "drain_ba", 1, "虚空之歌 (使玩家下回合失去 1BA)"
        elif cycle == 2:
            return "heart_strike", 4, "心跳重击 (造成 4 伤害)"
        elif cycle == 3:
            return "gaze_discard", 1, "虚无凝视 (迫使玩家随机丢弃 1 张手牌)"
        else:
            return "heart_heal", 10, "回潮 (恢复 10 生命)"

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        p = run.player
        import random
        
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks

        if enemy.intent_type == "debuff":
            p.draw_pile.append("curse_dazed")
            p.draw_pile.append("curse_agony")
            random.shuffle(p.draw_pile)
            logs.append(f"【{enemy.name}】施放了【邪恶之语】，将【晕眩】与【苦恼】放入了玩家的抽牌堆并进行了洗牌。")
            
        elif enemy.intent_type == "multi_attack":
            dmg = enemy.intent_val + strength
            logs.append(f"【{enemy.name}】释放【血弹喷射】，发动 8 次攻击（每次 {dmg} 伤害）：")
            for _ in range(8):
                if enemy.hp <= 0:
                    break
                self._perform_attack(run, engine, enemy, dmg, logs)
                
        elif enemy.intent_type == "big_attack":
            dmg = enemy.intent_val + strength
            self._perform_attack(run, engine, enemy, dmg, logs)
            
        elif enemy.intent_type == "strength_buff":
            engine._add_buff_to(enemy, "strength", "力量", f"造成的伤害增加 {enemy.intent_val} 点", enemy.intent_val)
            logs.append(f"【{enemy.name}】进行【充能】，力量提升了 {enemy.intent_val} 点。")
            
        elif enemy.intent_type in ("defend_large", "defend_normal"):
            enemy.shield += enemy.intent_val
            logs.append(f"【{enemy.name}】获得 {enemy.intent_val} 点护盾。")
            
        elif enemy.intent_type == "drain_ba":
            run.node_data["drain_ba"] = True
            logs.append(f"【{enemy.name}】吟唱【虚空之歌】，玩家将在下一回合失去 1 个附赠动作点 (BA)。")
            
        elif enemy.intent_type == "heart_strike":
            dmg = enemy.intent_val + strength
            self._perform_attack(run, engine, enemy, dmg, logs)
            
        elif enemy.intent_type == "gaze_discard":
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
                
        elif enemy.intent_type == "heart_heal":
            enemy.hp = min(enemy.max_hp, enemy.hp + enemy.intent_val)
            logs.append(f"【{enemy.name}】自我回潮，恢复了 {enemy.intent_val} 点生命值。")

class BossIcerainbowwTemplate(EnemyTemplate):
    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        turn = run.node_data.get("icerainboww_turn", 1)
        cycle = (turn - 1) % 4 + 1
        if cycle == 1:
            return "icerain_shoot", 2, "冰雨弓射击 (造成 2 寒冷伤害，使玩家下回合失去 1A)"
        elif cycle == 2:
            return "winter_gaze", 4, "寒冬凝视 (造成 4 心灵伤害，并使玩家受到轻度寒冷易伤)"
        elif cycle == 3:
            return "smash_attack", 10, "粉碎攻击 (造成 10 寒冷伤害，并使玩家受到轻度寒冷易伤)"
        else:
            return "frost_blast", 6, "冰霜爆震 (对玩家与所有我方随从造成 6 寒冷伤害)"

    def roll_intent_a2(self, run, engine, enemy) -> Tuple[str, int, str]:
        turn = run.node_data.get("icerainboww_turn", 1)
        cycle = (turn - 1) % 4 + 1
        if cycle == 1:
            return "fury", 1, "愤怒 (获得 1 层愤怒buff，被打出珍奇或传奇卡牌激怒时自身增伤)"
        elif cycle == 2:
            return "aurora_shield", 12, "极光屏障 (获得 12 护盾并净化 1 负面 Buff，无负面时额外获得 4 护盾)"
        elif cycle == 3:
            return "icerain_shoot", 2, "冰雨弓射击 (造成 2 寒冷伤害，使玩家下回合失去 1A)"
        else:
            return "fury", 1, "愤怒 (获得 1 层愤怒buff，被打出珍奇或传奇卡牌激怒时自身增伤)"

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        p = run.player
        import random
        
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks

        val = enemy.intent_val + strength

        if enemy.intent_type == "icerain_shoot":
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

        elif enemy.intent_type == "fury":
            engine._add_buff_to(enemy, "fury", "愤怒", "玩家使用珍奇或传奇卡牌时，该怪物获得等同于愤怒层数的力量", 1)
            logs.append(f"【{enemy.name}】获得了 1 层【愤怒】Buff！")

        elif enemy.intent_type == "smash_attack":
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

        elif enemy.intent_type == "aurora_shield":
            neg_buff = next((b for b in enemy.buffs if b.id == "stun"), None)
            shield_gain = enemy.intent_val
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

        elif enemy.intent_type == "winter_gaze":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="psychic")
            after_logs = run.node_data.get("battle_logs", [])
            if len(after_logs) > before_len:
                dmg_msg = after_logs.pop()
                logs.append(f"【{enemy.name}】投射【寒冬凝视】。{dmg_msg}")
            engine._add_buff_to(p, "minor_vulnerable_cold", "轻度寒冷易伤", "受到的寒冷伤害增加 50%", 1)
            logs.append(f"【{enemy.name}】的寒冬凝视使玩家获得了 1 层【轻度寒冷易伤】状态。")

        elif enemy.intent_type == "frost_blast":
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
