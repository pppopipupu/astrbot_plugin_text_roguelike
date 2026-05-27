from typing import Optional, Tuple, List
from .data.enemy_data import ENEMY_CONFIG

class EnemyTemplate:
    def __init__(self, name: str):
        self.name = name

    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        import random
        stage = run.player.stage
        intents = [
            ("attack", 3 + (stage // 2) + random.randint(0, 2)),
            ("defend", 3 + stage + random.randint(0, 2))
        ]
        itype, val = random.choice(intents)
        if itype == "attack":
            desc = f"攻击 (造成 {val} 伤害)"
        else:
            desc = f"防御 (获得 {val} 护盾)"
        return itype, val, desc

    def roll_intent_ba(self, run, engine, enemy) -> Tuple[str, int, str]:
        return self.roll_intent(run, engine, enemy)

    def roll_intent_ba2(self, run, engine, enemy) -> Tuple[str, int, str]:
        return self.roll_intent(run, engine, enemy)

    def _perform_attack(self, run, engine, enemy, dmg: int, logs: List[str]):
        p = run.player
        import random
        has_thorns = False
        thorns_key = None
        for ak, av in p.amulets.items():
            if av.id == "thorns_necklace":
                has_thorns = True
                thorns_key = ak
                break
        if p.minions and random.random() < 0.5:
            target_key = random.choice(list(p.minions.keys()))
            target = p.minions[target_key]
            target.hp -= dmg
            logs.append(f"敌人【{enemy.name}】攻击了我方随从【{target.name}】，造成 {dmg} 点伤害。")
            if target.hp <= 0:
                logs.append(f"我方随从【{target.name}】已被击败！")
                p.graveyard.append("minion:" + target.id)
                del p.minions[target_key]
        else:
            if p.shield >= dmg:
                p.shield -= dmg
                logs.append(f"敌人【{enemy.name}】发动攻击，造成 {dmg} 点护盾伤害。")
            else:
                take = dmg - p.shield
                p.hp -= take
                p.shield = 0
                logs.append(f"敌人【{enemy.name}】发动攻击，造成 {take} 点生命伤害。")
            if has_thorns:
                enemy.hp -= 2
                logs.append(f"【荆棘项链】反弹了 2 点伤害给【{enemy.name}】。")
                p.amulets[thorns_key].countdown -= 1
                if p.amulets[thorns_key].countdown <= 0:
                    del p.amulets[thorns_key]
                    logs.append("我方【荆棘项链】耐久耗尽销毁。")

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        if enemy.intent_type == "attack":
            self._perform_attack(run, engine, enemy, enemy.intent_val, logs)
        elif enemy.intent_type == "defend":
            enemy.shield += enemy.intent_val
            logs.append(f"敌人【{enemy.name}】进行防守，获得 {enemy.intent_val} 点护盾。")

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
            from .models import EnemyState
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

class GoblinCenturionTemplate(EnemyTemplate):
    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        import random
        cfg = ENEMY_CONFIG.get("地精百夫长", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return chosen["id"], chosen["val"], chosen["desc"]

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        if enemy.intent_type == "heavy_strike":
            self._perform_attack(run, engine, enemy, enemy.intent_val, logs)
        elif enemy.intent_type == "defend":
            enemy.shield += enemy.intent_val
            logs.append(f"【{enemy.name}】举起盾牌，获得 {enemy.intent_val} 点护盾。")
        elif enemy.intent_type == "command":
            enemy.actions += 1
            logs.append(f"【{enemy.name}】发出咆哮，获得 1 个额外动作点。")

class GargoylePriestTemplate(EnemyTemplate):
    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        import random
        cfg = ENEMY_CONFIG.get("石像鬼祭司", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return chosen["id"], chosen["val"], chosen["desc"]

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        if enemy.intent_type == "attack":
            self._perform_attack(run, engine, enemy, enemy.intent_val, logs)
        elif enemy.intent_type == "defend":
            enemy.shield += enemy.intent_val
            logs.append(f"【{enemy.name}】施展暗影护盾，获得 {enemy.intent_val} 点护盾。")
        elif enemy.intent_type == "drain":
            self._perform_attack(run, engine, enemy, enemy.intent_val, logs)
            if run.enemies:
                min_hp_enemy = min(run.enemies, key=lambda e: e.hp)
                min_hp_enemy.hp = min(min_hp_enemy.max_hp, min_hp_enemy.hp + 4)
                logs.append(f"【{enemy.name}】汲取生命，为【{min_hp_enemy.name}】恢复了 4 点生命值。")

class BeastMasterTemplate(EnemyTemplate):
    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        import random
        cfg = ENEMY_CONFIG.get("狂暴兽王", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return chosen["id"], chosen["val"], chosen["desc"]

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        if enemy.intent_type == "attack":
            self._perform_attack(run, engine, enemy, enemy.intent_val, logs)
        elif enemy.intent_type == "defend":
            enemy.shield += enemy.intent_val
            logs.append(f"【{enemy.name}】收缩防线，获得 {enemy.intent_val} 点护盾。")
        elif enemy.intent_type == "summon_beast":
            from .models import EnemyState
            cfg = ENEMY_CONFIG.get("狂暴兽王", {})
            sh = cfg.get("summon_hound", {})
            new_hound = EnemyState(
                name=sh.get("name", "狂暴猎犬"),
                hp=sh.get("hp", 8),
                max_hp=sh.get("max_hp", 8),
                shield=0,
                intent_type="attack",
                intent_val=sh.get("intent_val", 2),
                intent_desc=sh.get("intent_desc", "扑咬 (造成 2 伤害)"),
                actions=1,
                bonus_actions=0,
                is_summon=True,
                max_actions=1,
                max_bonus_actions=0
            )
            run.enemies.append(new_hound)
            logs.append(f"【{enemy.name}】召唤了一只【狂暴猎犬】加入战场。")

class ObsidianDjinnTemplate(EnemyTemplate):
    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        import random
        cfg = ENEMY_CONFIG.get("黑曜石巨灵", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return chosen["id"], chosen["val"], chosen["desc"]

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        p = run.player
        if enemy.intent_type == "quake":
            self._perform_attack(run, engine, enemy, enemy.intent_val, logs)
            p.bonus_actions = max(0, p.bonus_actions - 1)
            logs.append(f"【{enemy.name}】引发地震，剥夺了玩家 1 个附赠动作点 (BA)。")
        elif enemy.intent_type == "defend":
            enemy.shield += enemy.intent_val
            logs.append(f"【{enemy.name}】加固外壳，获得 {enemy.intent_val} 点护盾。")

class GhostArchmageTemplate(EnemyTemplate):
    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        import random
        cfg = ENEMY_CONFIG.get("幽灵大魔法师", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return chosen["id"], chosen["val"], chosen["desc"]

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        p = run.player
        import random
        if enemy.intent_type == "spell_burst":
            self._perform_attack(run, engine, enemy, enemy.intent_val, logs)
        elif enemy.intent_type == "mana_drain":
            self._perform_attack(run, engine, enemy, enemy.intent_val, logs)
            if p.hand:
                discarded = p.hand.pop(random.randint(0, len(p.hand) - 1))
                from .card_impl import ALL_CARDS
                card_name = ALL_CARDS[discarded].name if discarded in ALL_CARDS else "未知卡牌"
                p.discard_pile.append(discarded)
                logs.append(f"【{enemy.name}】施展虹吸，迫使玩家随机丢弃了卡牌【{card_name}】。")

class ShadowFiendTemplate(EnemyTemplate):
    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        import random
        cfg = ENEMY_CONFIG.get("暗影影魔", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return chosen["id"], chosen["val"], chosen["desc"]

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        p = run.player
        if enemy.intent_type == "shadow_strike":
            dmg = enemy.intent_val
            p.hp -= dmg
            logs.append(f"【{enemy.name}】施展影袭，直接对玩家造成 {dmg} 点生命伤害。")
        elif enemy.intent_type == "defend":
            enemy.shield += enemy.intent_val
            logs.append(f"【{enemy.name}】进入虚化，获得 {enemy.intent_val} 点护盾。")

ALL_ENEMIES = {
    "远古红龙": BossRedDragonTemplate("远古红龙"),
    "地精百夫长": GoblinCenturionTemplate("地精百夫长"),
    "石像鬼祭司": GargoylePriestTemplate("石像鬼祭司"),
    "狂暴兽王": BeastMasterTemplate("狂暴兽王"),
    "黑曜石巨灵": ObsidianDjinnTemplate("黑曜石巨灵"),
    "幽灵大魔法师": GhostArchmageTemplate("幽灵大魔法师"),
    "暗影影魔": ShadowFiendTemplate("暗影影魔"),
}

def get_enemy_template(name: str) -> EnemyTemplate:
    base_name = name.split(" ")[0] if name else ""
    return ALL_ENEMIES.get(base_name, EnemyTemplate(base_name))
