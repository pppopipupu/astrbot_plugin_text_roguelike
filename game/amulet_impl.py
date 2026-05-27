from typing import Optional
from .data.amulet_data import AMULET_CONFIG

class AmuletTemplate:
    def on_end_turn(self, run, grid: str, engine) -> str:
        return ""

    def on_take_damage(self, run, grid: str, source: str, amount: int, engine) -> str:
        return ""

    def on_spell_played(self, run, grid: str, card, engine) -> str:
        return ""

class LuckyCoinAmulet(AmuletTemplate):
    def on_end_turn(self, run, grid, engine) -> str:
        cfg = AMULET_CONFIG.get("lucky_coin", {})
        gold = cfg.get("gold_on_end", 3)
        run.player.gold += gold
        return ""

class MageWardAmulet(AmuletTemplate):
    def on_end_turn(self, run, grid, engine) -> str:
        cfg = AMULET_CONFIG.get("mage_ward", {})
        shield = cfg.get("shield_on_end", 4)
        run.player.shield += shield
        return ""

class ThornsNecklaceAmulet(AmuletTemplate):
    def on_take_damage(self, run, grid, source, amount, engine) -> str:
        cfg = AMULET_CONFIG.get("thorns_necklace", {})
        dmg = cfg.get("damage_on_hit", 2)
        m = run.player.amulets[grid]
        engine._damage_target(run, source, dmg)
        src_name = engine._get_target_name(run, source)
        msg = f"【荆棘项链】反弹了 {dmg} 点伤害给【{src_name}】。"
        m.countdown -= 1
        if m.countdown <= 0:
            del run.player.amulets[grid]
            msg += f"\n我方【荆棘项链】耐久耗尽销毁。"
        return msg

class ArcaneCrystalAmulet(AmuletTemplate):
    def on_spell_played(self, run, grid, card, engine) -> str:
        cfg = AMULET_CONFIG.get("arcane_crystal", {})
        heal = cfg.get("heal_on_spell", 2)
        run.player.hp = min(run.player.max_hp, run.player.hp + heal)
        return ""

ALL_AMULETS = {
    "lucky_coin": LuckyCoinAmulet(),
    "mage_ward": MageWardAmulet(),
    "thorns_necklace": ThornsNecklaceAmulet(),
    "arcane_crystal": ArcaneCrystalAmulet(),
    "ring_of_elements": AmuletTemplate(),
}
