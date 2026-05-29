from typing import Optional, List
from ...data.minion_data import MINION_CONFIG

class BaseMinionSkill:
    def __init__(self, name: str, cost_a: int, cost_ba: int, desc: str):
        self.name = name
        self.cost_a = cost_a
        self.cost_ba = cost_ba
        self.desc = desc

    def execute(self, run, my_grid: str, target: Optional[str], engine) -> str:
        return ""

class MercenaryHeavyStrike(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        cfg = MINION_CONFIG["mercenary"]["skills"][0]
        damage = cfg["damage"]
        tname = engine._get_target_name(run, target)
        engine._damage_target(run, target, damage)
        return cfg["feedback"].format(target=tname, damage=damage)

class MercenaryBattlecry(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        cfg = MINION_CONFIG["mercenary"]["skills"][1]
        atk_buff = cfg["atk_buff"]
        m = run.player.minions[my_grid]
        m.atk += atk_buff
        return cfg["feedback"].format(atk_buff=atk_buff)

class ShieldGuardDefend(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        cfg = MINION_CONFIG["shield_guard"]["skills"][0]
        shield = cfg["shield"]
        run.player.shield += shield
        return cfg["feedback"].format(shield=shield)

class ShieldGuardBash(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        cfg = MINION_CONFIG["shield_guard"]["skills"][1]
        damage = cfg["damage"]
        shield = cfg["shield"]
        tname = engine._get_target_name(run, target)
        engine._damage_target(run, target, damage)
        run.player.shield += shield
        return cfg["feedback"].format(target=tname, damage=damage, shield=shield)

class FamiliarAssist(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        cfg = MINION_CONFIG["find_familiar"]["skills"][0]
        draw = cfg["draw"]
        engine._draw_cards(run.player, draw, run)
        return cfg["feedback"].format(draw=draw)

class FamiliarCharge(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        cfg = MINION_CONFIG["find_familiar"]["skills"][1]
        ba_gain = cfg["ba_gain"]
        run.player.bonus_actions += ba_gain
        return cfg["feedback"].format(ba_gain=ba_gain)

class WaterTouch(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        cfg = MINION_CONFIG["water_elemental"]["skills"][0]
        t = target or "e1"
        if t.startswith("e"):
            try:
                grid_idx = int(t[1:]) - 1
            except ValueError:
                grid_idx = 0
            if 0 <= grid_idx < len(run.enemies):
                enemy = run.enemies[grid_idx]
                enemy.bonus_actions = max(0, enemy.bonus_actions - 1)
                return cfg["feedback"].format(target=enemy.name)
        return "未找到敌方目标。"

class WaterLance(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        cfg = MINION_CONFIG["water_elemental"]["skills"][1]
        damage = cfg["damage"]
        t = target or "e1"
        tname = engine._get_target_name(run, t)
        engine._damage_target(run, t, damage)
        if t.startswith("e"):
            try:
                grid_idx = int(t[1:]) - 1
            except ValueError:
                grid_idx = 0
            if 0 <= grid_idx < len(run.enemies):
                enemy = run.enemies[grid_idx]
                enemy.actions = max(0, enemy.actions - 1)
                feedback_boss = cfg.get("feedback_boss")
                if feedback_boss:
                    return feedback_boss.format(target=tname, damage=damage)
        return cfg["feedback"].format(target=tname, damage=damage)

class GolemOverload(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        cfg = MINION_CONFIG["arcane_golem"]["skills"][0]
        self_damage = cfg["self_damage"]
        atk_buff = cfg["atk_buff"]
        m = run.player.minions[my_grid]
        m.hp -= self_damage
        m.atk += atk_buff
        if m.hp <= 0:
            del run.player.minions[my_grid]
            return cfg["feedback_dead"].format(self_damage=self_damage, atk_buff=atk_buff)
        return cfg["feedback"].format(self_damage=self_damage, atk_buff=atk_buff)

class GolemRepair(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        cfg = MINION_CONFIG["arcane_golem"]["skills"][1]
        heal = cfg["heal"]
        m = run.player.minions[my_grid]
        m.hp = min(m.max_hp, m.hp + heal)
        return cfg["feedback"].format(heal=heal, hp=m.hp, max_hp=m.max_hp)

class IcerainbowwSpray(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        cfg = MINION_CONFIG["minion_icerainboww"]["skills"][0]
        damage = cfg["damage"]
        for idx, enemy in enumerate(list(run.enemies)):
            engine._damage_target(run, f"e{idx+1}", damage, source="minion:Icerainboww", damage_type="cold")
            engine._add_buff_to(enemy, "minor_vulnerable_cold", "轻度寒冷易伤", "受到的寒冷伤害增加 50%", 1)
        return cfg["feedback"] + "（对所有敌人造成 4 点寒冷伤害并附加 1 层轻度寒冷易伤）"

class IcerainbowwShield(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        cfg = MINION_CONFIG["minion_icerainboww"]["skills"][1]
        run.player.shield += 12
        for mk, mv in list(run.player.minions.items()):
            mv.hp = min(mv.max_hp, mv.hp + 4)
        return cfg["feedback"] + "（为玩家提供 12 点护盾，并为我方所有随从恢复 4 点生命）"

class MinionTemplate:
    def __init__(self, id: str, name: str, skills: List[BaseMinionSkill]):
        self.id = id
        self.name = name
        self.skills = skills

ALL_MINIONS = {
    "mercenary": MinionTemplate(
        "mercenary",
        MINION_CONFIG["mercenary"]["name"],
        [
            MercenaryHeavyStrike(
                MINION_CONFIG["mercenary"]["skills"][0]["name"],
                MINION_CONFIG["mercenary"]["skills"][0]["cost_a"],
                MINION_CONFIG["mercenary"]["skills"][0]["cost_ba"],
                MINION_CONFIG["mercenary"]["skills"][0]["desc"]
            ),
            MercenaryBattlecry(
                MINION_CONFIG["mercenary"]["skills"][1]["name"],
                MINION_CONFIG["mercenary"]["skills"][1]["cost_a"],
                MINION_CONFIG["mercenary"]["skills"][1]["cost_ba"],
                MINION_CONFIG["mercenary"]["skills"][1]["desc"]
            )
        ]
    ),
    "shield_guard": MinionTemplate(
        "shield_guard",
        MINION_CONFIG["shield_guard"]["name"],
        [
            ShieldGuardDefend(
                MINION_CONFIG["shield_guard"]["skills"][0]["name"],
                MINION_CONFIG["shield_guard"]["skills"][0]["cost_a"],
                MINION_CONFIG["shield_guard"]["skills"][0]["cost_ba"],
                MINION_CONFIG["shield_guard"]["skills"][0]["desc"]
            ),
            ShieldGuardBash(
                MINION_CONFIG["shield_guard"]["skills"][1]["name"],
                MINION_CONFIG["shield_guard"]["skills"][1]["cost_a"],
                MINION_CONFIG["shield_guard"]["skills"][1]["cost_ba"],
                MINION_CONFIG["shield_guard"]["skills"][1]["desc"]
            )
        ]
    ),
    "find_familiar": MinionTemplate(
        "find_familiar",
        MINION_CONFIG["find_familiar"]["name"],
        [
            FamiliarAssist(
                MINION_CONFIG["find_familiar"]["skills"][0]["name"],
                MINION_CONFIG["find_familiar"]["skills"][0]["cost_a"],
                MINION_CONFIG["find_familiar"]["skills"][0]["cost_ba"],
                MINION_CONFIG["find_familiar"]["skills"][0]["desc"]
            ),
            FamiliarCharge(
                MINION_CONFIG["find_familiar"]["skills"][1]["name"],
                MINION_CONFIG["find_familiar"]["skills"][1]["cost_a"],
                MINION_CONFIG["find_familiar"]["skills"][1]["cost_ba"],
                MINION_CONFIG["find_familiar"]["skills"][1]["desc"]
            )
        ]
    ),
    "water_elemental": MinionTemplate(
        "water_elemental",
        MINION_CONFIG["water_elemental"]["name"],
        [
            WaterTouch(
                MINION_CONFIG["water_elemental"]["skills"][0]["name"],
                MINION_CONFIG["water_elemental"]["skills"][0]["cost_a"],
                MINION_CONFIG["water_elemental"]["skills"][0]["cost_ba"],
                MINION_CONFIG["water_elemental"]["skills"][0]["desc"]
            ),
            WaterLance(
                MINION_CONFIG["water_elemental"]["skills"][1]["name"],
                MINION_CONFIG["water_elemental"]["skills"][1]["cost_a"],
                MINION_CONFIG["water_elemental"]["skills"][1]["cost_ba"],
                MINION_CONFIG["water_elemental"]["skills"][1]["desc"]
            )
        ]
    ),
    "arcane_golem": MinionTemplate(
        "arcane_golem",
        MINION_CONFIG["arcane_golem"]["name"],
        [
            GolemOverload(
                MINION_CONFIG["arcane_golem"]["skills"][0]["name"],
                MINION_CONFIG["arcane_golem"]["skills"][0]["cost_a"],
                MINION_CONFIG["arcane_golem"]["skills"][0]["cost_ba"],
                MINION_CONFIG["arcane_golem"]["skills"][0]["desc"]
            ),
            GolemRepair(
                MINION_CONFIG["arcane_golem"]["skills"][1]["name"],
                MINION_CONFIG["arcane_golem"]["skills"][1]["cost_a"],
                MINION_CONFIG["arcane_golem"]["skills"][1]["cost_ba"],
                MINION_CONFIG["arcane_golem"]["skills"][1]["desc"]
            )
        ]
    ),
    "minion_icerainboww": MinionTemplate(
        "minion_icerainboww",
        MINION_CONFIG["minion_icerainboww"]["name"],
        [
            IcerainbowwSpray(
                MINION_CONFIG["minion_icerainboww"]["skills"][0]["name"],
                MINION_CONFIG["minion_icerainboww"]["skills"][0]["cost_a"],
                MINION_CONFIG["minion_icerainboww"]["skills"][0]["cost_ba"],
                MINION_CONFIG["minion_icerainboww"]["skills"][0]["desc"]
            ),
            IcerainbowwShield(
                MINION_CONFIG["minion_icerainboww"]["skills"][1]["name"],
                MINION_CONFIG["minion_icerainboww"]["skills"][1]["cost_a"],
                MINION_CONFIG["minion_icerainboww"]["skills"][1]["cost_ba"],
                MINION_CONFIG["minion_icerainboww"]["skills"][1]["desc"]
            )
        ]
    )
}

MINION_SKILLS = {}
for mid, temp in ALL_MINIONS.items():
    MINION_SKILLS[mid] = [
        {"name": s.name, "cost_a": s.cost_a, "cost_ba": s.cost_ba, "desc": s.desc}
        for s in temp.skills
    ]
