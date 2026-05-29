from typing import Optional

class Effect:
    def apply(self, run, source: str, target: str, engine) -> str:
        return ""

class DamageEffect(Effect):
    def __init__(self, amount: int):
        self.amount = amount

    def apply(self, run, source: str, target: str, engine) -> str:
        name = engine._get_target_name(run, target)
        engine._damage_target(run, target, self.amount)
        return f"对【{name}】造成了 {self.amount} 点伤害。"

class HealEffect(Effect):
    def __init__(self, amount: int):
        self.amount = amount

    def apply(self, run, source: str, target: str, engine) -> str:
        name = engine._get_target_name(run, target)
        engine._heal_target(run, target, self.amount)
        return f"为【{name}】恢复了 {self.amount} 点生命值。"

class ShieldEffect(Effect):
    def __init__(self, amount: int):
        self.amount = amount

    def apply(self, run, source: str, target: str, engine) -> str:
        name = engine._get_target_name(run, target)
        if target == "p0":
            run.player.shield += self.amount
        elif target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if idx < 0:
                    idx = 0
            except ValueError:
                idx = 0
            if 0 <= idx < len(run.enemies):
                run.enemies[idx].shield += self.amount
        return f"使【{name}】获得了 {self.amount} 点护盾。"

class DrawCardEffect(Effect):
    def __init__(self, count: int):
        self.count = count

    def apply(self, run, source: str, target: str, engine) -> str:
        engine._draw_cards(run.player, self.count)
        return f"抽了 {self.count} 张牌。"

class ModifyActionEffect(Effect):
    def __init__(self, count: int, action_type: str = "A"):
        self.count = count
        self.action_type = action_type

    def apply(self, run, source: str, target: str, engine) -> str:
        p = run.player
        if self.action_type == "A":
            p.actions += self.count
            return f"获得了 {self.count}A。"
        else:
            p.bonus_actions += self.count
            return f"获得了 {self.count}BA。"
