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
        has_thorns = False
        thorns_key = None
        for ak, av in p.amulets.items():
            if av.id == "thorns_necklace":
                has_thorns = True
                thorns_key = ak
                break
        if enemy.intent_type == "attack":
            dmg = enemy.intent_val
            if p.shield >= dmg:
                p.shield -= dmg
                logs.append(f"敌方领主【{enemy.name}】发动攻击，造成 {dmg} 点护盾伤害。")
            else:
                take = dmg - p.shield
                p.hp -= take
                p.shield = 0
                logs.append(f"敌方领主【{enemy.name}】发动攻击，造成 {take} 点生命伤害。")
            if has_thorns:
                enemy.hp -= 2
                logs.append(f"【荆棘项链】反弹了 2 点伤害给【{enemy.name}】。")
                p.amulets[thorns_key].countdown -= 1
                if p.amulets[thorns_key].countdown <= 0:
                    del p.amulets[thorns_key]
                    logs.append("我方【荆棘项链】耐久耗尽销毁。")
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
            dmg = enemy.intent_val
            if p.shield >= dmg:
                p.shield -= dmg
                logs.append(f"敌方领主【{enemy.name}】扫尾攻击，造成 {dmg} 点护盾伤害。")
            else:
                take = dmg - p.shield
                p.hp -= take
                p.shield = 0
                logs.append(f"敌方领主【{enemy.name}】扫尾攻击，造成 {take} 点生命伤害。")
            for mk in list(p.minions.keys()):
                p.minions[mk].hp -= dmg
                logs.append(f"我方随从【{p.minions[mk].name}】受到扫尾波及，失去 {dmg} 生命。")
                if p.minions[mk].hp <= 0:
                    logs.append(f"我方随从【{p.minions[mk].name}】已被击败！")
                    p.graveyard.append("minion:" + p.minions[mk].id)
                    del p.minions[mk]

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
