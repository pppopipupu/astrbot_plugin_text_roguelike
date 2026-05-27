from typing import Optional, List

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
        engine._damage_target(run, target, 6)
        tname = engine._get_target_name(run, target)
        return f"对【{tname}】造成了 6 点伤害。"

class MercenaryBattlecry(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        m = run.player.minions[my_grid]
        m.atk += 4
        return "本回合攻击力提升了 4 点。"

class ShieldGuardDefend(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        run.player.shield += 2
        return "为玩家提供了 2 点护盾。"

class ShieldGuardBash(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        engine._damage_target(run, target, 3)
        run.player.shield += 1
        tname = engine._get_target_name(run, target)
        return f"对【{tname}】造成了 3 点伤害，并为玩家提供了 1 点护盾。"

class FamiliarAssist(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        engine._draw_cards(run.player, 1)
        return "玩家抽取了 1 张牌。"

class FamiliarCharge(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        run.player.bonus_actions += 1
        return "玩家获得了 1 个附赠动作点 (BA)。"

class WaterTouch(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        t = target or "e1"
        if t.startswith("e"):
            try:
                grid_idx = int(t[1:]) - 1
            except ValueError:
                grid_idx = 0
            if 0 <= grid_idx < len(run.enemies):
                enemy = run.enemies[grid_idx]
                enemy.bonus_actions = max(0, enemy.bonus_actions - 1)
                return f"扣除了敌人【{enemy.name}】下回合 1 个附赠动作点。"
        return "未找到敌方目标。"

class WaterLance(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        t = target or "e1"
        engine._damage_target(run, t, 4)
        tname = engine._get_target_name(run, t)
        if t.startswith("e"):
            try:
                grid_idx = int(t[1:]) - 1
            except ValueError:
                grid_idx = 0
            if 0 <= grid_idx < len(run.enemies):
                enemy = run.enemies[grid_idx]
                enemy.actions = max(0, enemy.actions - 1)
                return f"对【{tname}】造成了 4 点伤害，并扣掉了其下回合 1 个动作点。"
        return f"对【{tname}】造成了 4 点伤害。"

class GolemOverload(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        m = run.player.minions[my_grid]
        m.hp -= 4
        m.atk += 3
        if m.hp <= 0:
            del run.player.minions[my_grid]
            return "自身失去 4 点生命值并过载死亡，本回合攻击力增加 3 点。"
        return "自身失去 4 点生命值，本回合攻击力增加 3 点。"

class GolemRepair(BaseMinionSkill):
    def execute(self, run, my_grid, target, engine) -> str:
        m = run.player.minions[my_grid]
        m.hp = min(m.max_hp, m.hp + 6)
        return f"恢复了自身 6 点生命值，当前生命 {m.hp}/{m.max_hp}。"

class MinionTemplate:
    def __init__(self, id: str, name: str, skills: List[BaseMinionSkill]):
        self.id = id
        self.name = name
        self.skills = skills

ALL_MINIONS = {
    "mercenary": MinionTemplate("mercenary", "雇佣兵", [
        MercenaryHeavyStrike("重击", 1, 0, "消耗 1A，造成 6 点伤害。"),
        MercenaryBattlecry("战吼", 0, 1, "消耗 1BA，本回合随从攻击力增加 4。")
    ]),
    "shield_guard": MinionTemplate("shield_guard", "盾卫", [
        ShieldGuardDefend("重整防线", 0, 1, "消耗 1BA，为玩家提供 2 点护盾。"),
        ShieldGuardBash("持盾撞击", 1, 0, "消耗 1A，造成 3 点伤害，玩家获得 1 点护盾。")
    ]),
    "find_familiar": MinionTemplate("find_familiar", "召唤魔宠", [
        FamiliarAssist("奥术协助", 0, 1, "消耗 1BA，玩家抽 1 张牌。"),
        FamiliarCharge("法力充能", 1, 0, "消耗 1A，为玩家提供 1BA。")
    ]),
    "water_elemental": MinionTemplate("water_elemental", "寒冰元素", [
        WaterTouch("寒冰触碰", 0, 1, "消耗 1BA，扣除敌方领主下回合 1BA。"),
        WaterLance("霜冻冰枪", 1, 0, "消耗 1A，造成 4 点伤害，若目标是随从则使其本回合无法攻击，若为领主则扣除其下回合 1A。")
    ]),
    "arcane_golem": MinionTemplate("arcane_golem", "奥术傀儡", [
        GolemOverload("能量过载", 0, 1, "消耗 1BA，自身失去 4 生命，本回合攻击力 +3。"),
        GolemRepair("自我修复", 1, 0, "消耗 1A，恢复自身 6 点生命值。")
    ])
}

MINION_SKILLS = {}
for mid, temp in ALL_MINIONS.items():
    MINION_SKILLS[mid] = [
        {"name": s.name, "cost_a": s.cost_a, "cost_ba": s.cost_ba, "desc": s.desc}
        for s in temp.skills
    ]
