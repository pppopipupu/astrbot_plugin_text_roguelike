from typing import Optional
from ...data.amulet_data import AMULET_CONFIG

class AmuletTemplate:
    def on_end_turn(self, run, grid: str, engine) -> str:
        return ""

    def on_take_damage(self, run, grid: str, source: str, amount: int, engine) -> str:
        return ""

    def on_spell_played(self, run, grid: str, card, engine) -> str:
        return ""

    def on_death(self, run, grid: str, is_upgraded: bool, engine) -> str:
        return ""

class LuckyCoinAmulet(AmuletTemplate):
    def on_end_turn(self, run, grid, engine) -> str:
        av = run.player.amulets.get(grid)
        is_upgraded = av.id.endswith("+") if av else False
        if is_upgraded:
            run.player.gold += 4
            engine._draw_cards(run.player, 1, run)
        else:
            cfg = AMULET_CONFIG.get("lucky_coin", {})
            gold = cfg.get("gold_on_end", 3)
            run.player.gold += gold
        return ""

    def on_death(self, run, grid, is_upgraded, engine) -> str:
        if is_upgraded:
            run.player.gold += 15
            engine._draw_cards(run.player, 1, run)
            return "获得 15 金币并抽 1 张牌。"
        else:
            run.player.gold += 10
            return "获得 10 金币。"

class MageWardAmulet(AmuletTemplate):
    def on_end_turn(self, run, grid, engine) -> str:
        av = run.player.amulets.get(grid)
        is_upgraded = av.id.endswith("+") if av else False
        if is_upgraded:
            run.player.shield += 6
            if not run.node_data.get("player_damaged_this_turn", False):
                av.countdown += 1
        else:
            cfg = AMULET_CONFIG.get("mage_ward", {})
            shield = cfg.get("shield_on_end", 4)
            run.player.shield += shield
        return ""

    def on_death(self, run, grid, is_upgraded, engine) -> str:
        shield = 10 if is_upgraded else 5
        run.player.shield += shield
        return f"玩家获得 {shield} 点护盾。"

class ThornsNecklaceAmulet(AmuletTemplate):
    def on_take_damage(self, run, grid, source, amount, engine) -> str:
        av = run.player.amulets.get(grid)
        is_upgraded = av.id.endswith("+") if av else False
        if is_upgraded:
            dmg = 4
            run.player.shield += 1
        else:
            cfg = AMULET_CONFIG.get("thorns_necklace", {})
            dmg = cfg.get("damage_on_hit", 2)
        engine._damage_target(run, source, dmg, damage_type="true")
        src_name = engine._get_target_name(run, source)
        msg = f"【荆棘项链】反弹了 {dmg} 点伤害给【{src_name}】。"
        av.countdown -= 1
        if av.countdown <= 0:
            del run.player.amulets[grid]
            run.player.discard_pile.append(av.id)
            lw = self.on_death(run, grid, is_upgraded, engine)
            msg += f"\n🔔 [谢幕曲] 我方【{av.name}】吟唱结束进入墓地：{lw}"
        return msg

    def on_death(self, run, grid, is_upgraded, engine) -> str:
        if is_upgraded:
            for idx in range(len(run.enemies)):
                engine._damage_target(run, f"e{idx+1}", 4, damage_type="true")
            return "对全体敌人造成 4 点真实伤害。"
        else:
            t = engine._get_first_alive_enemy(run)
            if t:
                engine._damage_target(run, t, 4, damage_type="true")
                tname = engine._get_target_name(run, t)
                return f"对【{tname}】造成 4 点真实伤害。"
            return "没有存活的敌人。"

class ArcaneCrystalAmulet(AmuletTemplate):
    def on_spell_played(self, run, grid, card, engine) -> str:
        av = run.player.amulets.get(grid)
        is_upgraded = av.id.endswith("+") if av else False
        if is_upgraded:
            heal = 3
            shield = 2
            run.player.hp = min(run.player.max_hp, run.player.hp + heal)
            run.player.shield += shield
        else:
            cfg = AMULET_CONFIG.get("arcane_crystal", {})
            heal = cfg.get("heal_on_spell", 2)
            run.player.hp = min(run.player.max_hp, run.player.hp + heal)
        return ""

    def on_death(self, run, grid, is_upgraded, engine) -> str:
        heal = 8 if is_upgraded else 4
        run.player.hp = min(run.player.max_hp, run.player.hp + heal)
        return f"玩家回复 {heal} 点生命值。"

class RingOfElementsAmulet(AmuletTemplate):
    def on_death(self, run, grid, is_upgraded, engine) -> str:
        if is_upgraded:
            for idx in range(len(run.enemies)):
                engine._damage_target(run, f"e{idx+1}", 8, damage_type="fire")
            return "对全体敌人造成 8 点火焰伤害。"
        else:
            t = engine._get_first_alive_enemy(run)
            if t:
                engine._damage_target(run, t, 4, damage_type="fire")
                tname = engine._get_target_name(run, t)
                return f"对【{tname}】造成 4 点火焰伤害。"
            return "没有存活的敌人。"

ALL_AMULETS = {
    "lucky_coin": LuckyCoinAmulet(),
    "mage_ward": MageWardAmulet(),
    "thorns_necklace": ThornsNecklaceAmulet(),
    "arcane_crystal": ArcaneCrystalAmulet(),
    "ring_of_elements": RingOfElementsAmulet(),
}
