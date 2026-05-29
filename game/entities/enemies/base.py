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
        strength = 0
        if enemy.name != "腐化之心":
            if getattr(enemy, "buffs", None):
                for b in enemy.buffs:
                    if b.id == "strength":
                        strength += b.stacks
        final_dmg = dmg + strength
        if p.minions and random.random() < 0.5:
            target_key = random.choice(list(p.minions.keys()))
            target = p.minions[target_key]
            m_name = target.name
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, f"p{target_key}", final_dmg, source=f"enemy:{enemy.name}", damage_type="bludgeoning")
            after_logs = run.node_data.get("battle_logs", [])
            if len(after_logs) > before_len:
                dmg_msg = after_logs.pop()
                logs.append(f"敌人【{enemy.name}】攻击了我方随从【{m_name}】。{dmg_msg}")
        else:
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", final_dmg, source=f"enemy:{enemy.name}", damage_type="bludgeoning")
            after_logs = run.node_data.get("battle_logs", [])
            if len(after_logs) > before_len:
                dmg_msg = after_logs.pop()
                logs.append(f"敌人【{enemy.name}】对玩家发动攻击。{dmg_msg}")

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
