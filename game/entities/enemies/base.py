from typing import Tuple, List

class EnemyTemplate:
    def __init__(self, name: str):
        self.name = name

    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ...models.state import EnemyIntentState
        stage = run.player.stage
        intents_list = []
        for _ in range(enemy.max_actions):
            itype, val, desc = self._roll_single_intent(run, enemy, stage)
            intents_list.append(EnemyIntentState(
                type=itype,
                val=val,
                desc=desc,
                cost_a=1,
                cost_ba=0
            ))
        for _ in range(enemy.max_bonus_actions):
            itype, val, desc = self._roll_single_intent(run, enemy, stage)
            intents_list.append(EnemyIntentState(
                type=itype,
                val=val,
                desc=desc,
                cost_a=0,
                cost_ba=1
            ))
        return intents_list

    def _roll_single_intent(self, run, enemy, stage) -> Tuple[str, int, str]:
        import random
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
        ward_grids = []
        if p.minions:
            for grid, mstate in p.minions.items():
                if any(bf.id == "ward" for bf in mstate.buffs):
                    ward_grids.append(grid)
        if ward_grids:
            target_key = random.choice(ward_grids)
            target = p.minions[target_key]
            m_name = target.name
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, f"p{target_key}", final_dmg, source=f"enemy:{enemy.name}", damage_type="bludgeoning")
            after_logs = run.node_data.get("battle_logs", [])
            if len(after_logs) > before_len:
                dmg_msg = after_logs.pop()
                logs.append(f"敌人【{enemy.name}】受【守护】吸引，攻击了我方随从【{m_name}】。{dmg_msg}")
        else:
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
            logs.append(f"敌人【{enemy.name}】进行防守，获得 {intent.val} 点护盾。")

from .boss import BossRedDragonTemplate, BossCorruptedHeartTemplate, BossIcerainbowwTemplate, BossThunderLordTemplate, BossYogSothothTemplate
from .minions import (
    GoblinCenturionTemplate, GargoylePriestTemplate, BeastMasterTemplate,
    ObsidianDjinnTemplate, GhostArchmageTemplate, ShadowFiendTemplate,
    DoomguardTemplate, NecromancerTemplate, PortalGuardianTemplate,
    FireGuardTemplate, DemonServantTemplate, LightningOrbTemplate,
    VoidWandererTemplate, AncientWardenTemplate, AstralHoundTemplate,
    VoidLurkerTemplate
)

ALL_ENEMIES = {
    "远古红龙": BossRedDragonTemplate("远古红龙"),
    "腐化之心": BossCorruptedHeartTemplate("腐化之心"),
    "Icerainboww": BossIcerainbowwTemplate("Icerainboww"),
    "地精百夫长": GoblinCenturionTemplate("地精百夫长"),
    "石像鬼祭司": GargoylePriestTemplate("石像鬼祭司"),
    "狂暴兽王": BeastMasterTemplate("狂暴兽王"),
    "黑曜石巨灵": ObsidianDjinnTemplate("黑曜石巨灵"),
    "幽灵大魔法师": GhostArchmageTemplate("幽灵大魔法师"),
    "暗影影魔": ShadowFiendTemplate("暗影影魔"),
    "雷霆领主": BossThunderLordTemplate("雷霆领主"),
    "末日守卫": DoomguardTemplate("末日守卫"),
    "亡灵巫师": NecromancerTemplate("亡灵巫师"),
    "传送门守卫者": PortalGuardianTemplate("传送门守卫者"),
    "火元素守卫": FireGuardTemplate("火元素守卫"),
    "狂暴魔仆": DemonServantTemplate("狂暴魔仆"),
    "雷影魔仆": LightningOrbTemplate("雷影魔仆"),
    "虚空之门·尤格-索托斯": BossYogSothothTemplate("虚空之门·尤格-索托斯"),
    "【觉醒】虚空之门·尤格-索托斯": BossYogSothothTemplate("【觉醒】虚空之门·尤格-索托斯"),
    "虚空游荡者": VoidWandererTemplate("虚空游荡者"),
    "先古守卫": AncientWardenTemplate("先古守卫"),
    "星界猎犬": AstralHoundTemplate("星界猎犬"),
    "虚空潜伏者": VoidLurkerTemplate("虚空潜伏者"),
}

def get_enemy_template(name: str) -> EnemyTemplate:
    base_name = name.split(" ")[0] if name else ""
    return ALL_ENEMIES.get(base_name, EnemyTemplate(base_name))
