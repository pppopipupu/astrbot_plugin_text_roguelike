from typing import Optional

class AmuletTemplate:
    def on_end_turn(self, run, grid: str, engine) -> str:
        return ""

    def on_take_damage(self, run, grid: str, source: str, amount: int, engine) -> str:
        return ""

    def on_spell_played(self, run, grid: str, card, engine) -> str:
        return ""

class LuckyCoinAmulet(AmuletTemplate):
    def on_end_turn(self, run, grid, engine) -> str:
        run.player.gold += 3
        return ""

class MageWardAmulet(AmuletTemplate):
    def on_end_turn(self, run, grid, engine) -> str:
        run.player.shield += 4
        return ""

class ThornsNecklaceAmulet(AmuletTemplate):
    def on_take_damage(self, run, grid, source, amount, engine) -> str:
        m = run.player.amulets[grid]
        engine._damage_target(run, source, 2)
        src_name = engine._get_target_name(run, source)
        msg = f"【荆棘项链】反弹了 2 点伤害给【{src_name}】。"
        m.countdown -= 1
        if m.countdown <= 0:
            del run.player.amulets[grid]
            msg += "\n我方【荆棘项链】耐久耗尽销毁。"
        return msg

class ArcaneCrystalAmulet(AmuletTemplate):
    def on_spell_played(self, run, grid, card, engine) -> str:
        run.player.hp = min(run.player.max_hp, run.player.hp + 2)
        return ""

ALL_AMULETS = {
    "lucky_coin": LuckyCoinAmulet(),
    "mage_ward": MageWardAmulet(),
    "thorns_necklace": ThornsNecklaceAmulet(),
    "arcane_crystal": ArcaneCrystalAmulet(),
    "ring_of_elements": AmuletTemplate(),
}
