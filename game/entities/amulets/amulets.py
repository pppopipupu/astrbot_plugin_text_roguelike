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
            run.player.minion_graveyard.append(av.id)
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

class VoidBeaconAmulet(AmuletTemplate):
    def on_end_turn(self, run, grid, engine) -> str:
        av = run.player.amulets.get(grid)
        is_upgraded = av.id.endswith("+") if av else False
        damage = 8 if is_upgraded else 5
        for enemy in list(run.enemies):
            engine._add_buff_to(enemy, "vulnerable_force", "力场易伤", "受到的力场伤害增加 100%", 1)
        import random
        alive_enemies = [e for e in run.enemies if e.hp > 0]
        if alive_enemies:
            target = random.choice(alive_enemies)
            curr_idx = run.enemies.index(target)
            engine._damage_target(run, f"e{curr_idx+1}", damage, damage_type="force")
            engine._log_event(run, f"🌌 【虚空信标】使所有敌人获得 1 层力场易伤，并对【{target.name}】造成了 {damage} 点力场伤害！")
        return ""

class AbyssAltarAmulet(AmuletTemplate):
    def on_death(self, run, grid, is_upgraded, engine) -> str:
        from ...models.state import AmuletState
        next_id = "abyss_altar_awaken+" if is_upgraded else "abyss_altar_awaken"
        next_name = "【觉醒】苏醒的深渊祭坛" if is_upgraded else "苏醒的深渊祭坛"
        next_desc = "谢幕曲：在此格子部署【汇集的深渊祭坛】。"
        run.player.amulets[grid] = AmuletState(next_id, next_name, 1, next_desc)
        return f"部署了【{next_name}】。"

class AbyssAltarAwakenAmulet(AmuletTemplate):
    def on_death(self, run, grid, is_upgraded, engine) -> str:
        from ...models.state import AmuletState
        next_id = "abyss_altar_converge+" if is_upgraded else "abyss_altar_converge"
        next_name = "【觉醒】汇集的深渊祭坛" if is_upgraded else "汇集的深渊祭坛"
        next_desc = "谢幕曲：在此格子部署【爆发的深渊祭坛】。"
        run.player.amulets[grid] = AmuletState(next_id, next_name, 1, next_desc)
        return f"部署了【{next_name}】。"

class AbyssAltarConvergeAmulet(AmuletTemplate):
    def on_death(self, run, grid, is_upgraded, engine) -> str:
        from ...models.state import AmuletState
        next_id = "abyss_altar_burst+" if is_upgraded else "abyss_altar_burst"
        next_name = "【觉醒】爆发的深渊祭坛" if is_upgraded else "爆发的深渊祭坛"
        next_desc = "谢幕曲：在此格子部署【终结的深渊祭坛】。"
        run.player.amulets[grid] = AmuletState(next_id, next_name, 1, next_desc)
        return f"部署了【{next_name}】。"

class AbyssAltarBurstAmulet(AmuletTemplate):
    def on_death(self, run, grid, is_upgraded, engine) -> str:
        from ...models.state import AmuletState
        next_id = "abyss_altar_end+" if is_upgraded else "abyss_altar_end"
        next_name = "【觉醒】终结的深渊祭坛" if is_upgraded else "终结的深渊祭坛"
        next_desc = "谢幕曲对场上所有敌人造成 500 点真实伤害，玩家受到 10 点真实伤害。"
        run.player.amulets[grid] = AmuletState(next_id, next_name, 1, next_desc)
        return f"部署了【{next_name}】。"

class AbyssAltarEndAmulet(AmuletTemplate):
    def on_death(self, run, grid, is_upgraded, engine) -> str:
        dmg_enemies = 600 if is_upgraded else 500
        dmg_player = 5 if is_upgraded else 10
        feedback_parts = []
        for idx in range(len(run.enemies) - 1, -1, -1):
            enemy = run.enemies[idx]
            engine._damage_target(run, f"e{idx+1}", dmg_enemies, damage_type="true", source="abyss_altar_end")
            feedback_parts.append(f"【{enemy.name}】受到 {dmg_enemies} 点真实伤害")
        engine._damage_target(run, "p0", dmg_player, damage_type="true", source="abyss_altar_end")
        return "深渊仪式终结！" + "，".join(feedback_parts) + f"，玩家受到 {dmg_player} 点真实伤害。"

ALL_AMULETS = {
    "lucky_coin": LuckyCoinAmulet(),
    "mage_ward": MageWardAmulet(),
    "thorns_necklace": ThornsNecklaceAmulet(),
    "arcane_crystal": ArcaneCrystalAmulet(),
    "ring_of_elements": RingOfElementsAmulet(),
    "void_beacon": VoidBeaconAmulet(),
    "abyss_altar": AbyssAltarAmulet(),
    "abyss_altar_awaken": AbyssAltarAwakenAmulet(),
    "abyss_altar_converge": AbyssAltarConvergeAmulet(),
    "abyss_altar_burst": AbyssAltarBurstAmulet(),
    "abyss_altar_end": AbyssAltarEndAmulet(),
}
