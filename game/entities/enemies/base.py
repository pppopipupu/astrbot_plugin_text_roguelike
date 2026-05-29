from typing import Tuple, List

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

from .boss import BossRedDragonTemplate, BossCorruptedHeartTemplate
from .minions import GoblinCenturionTemplate, GargoylePriestTemplate, BeastMasterTemplate, ObsidianDjinnTemplate, GhostArchmageTemplate, ShadowFiendTemplate

ALL_ENEMIES = {
    "远古红龙": BossRedDragonTemplate("远古红龙"),
    "腐化之心": BossCorruptedHeartTemplate("腐化之心"),
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
