from typing import Optional, List
from .models import Card
from .data.card_data import CARD_CONFIG

class SpellDamageCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, base_dmg, is_fire=False, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, desc=desc)
        self.base_dmg = base_dmg
        self.is_fire = is_fire

    def execute(self, run, target, engine) -> str:
        dmg = self.base_dmg
        if self.is_fire:
            has_ring = any(av.id == "ring_of_elements" for av in run.player.amulets.values())
            if has_ring:
                dmg += 2
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        name = engine._get_target_name(run, target)
        engine._damage_target(run, target, dmg)
        
        # 从配置模块动态读取反馈模板
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(target=name, dmg=dmg)
        
        return f"使用了【{self.name}】，对【{name}】造成了 {dmg} 点伤害。"

class SpellHealCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, heal_amount, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, desc=desc)
        self.heal_amount = heal_amount

    def execute(self, run, target, engine) -> str:
        name = engine._get_target_name(run, target)
        engine._heal_target(run, target, self.heal_amount)
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(target=name, heal_amount=self.heal_amount)
        return f"为【{name}】恢复了 {self.heal_amount} 点生命值。"

class GetReadyCard(Card):
    def execute(self, run, target, engine) -> str:
        run.player.bonus_actions += 2
        engine._draw_cards(run.player, 1)
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "获得了 2BA 并抽了 1 张牌。")

class AdrenalineCard(Card):
    def execute(self, run, target, engine) -> str:
        run.player.actions += 1
        run.player.hp -= 2
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "获得了 1A，失去了 2 点生命值。")

class DeployAmuletCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, countdown, amulet_desc, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, countdown=countdown, desc=desc)
        self.amulet_desc = amulet_desc

    def execute(self, run, target, engine) -> str:
        grid = engine._get_free_grid(run.player)
        cfg = CARD_CONFIG.get(self.id, {})
        if grid:
            from .models import AmuletState
            run.player.amulets[grid] = AmuletState(self.id, self.name, self.countdown, self.amulet_desc)
            feedback_success = cfg.get("feedback_success", "将【{name}】部署到了格子 [{grid}]。")
            return feedback_success.format(name=self.name, grid=grid)
        return cfg.get("feedback_fail", "战场格子已满，部署失败。")

class SummonMinionCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, minion_hp, minion_atk, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, desc=desc)
        self.minion_hp = minion_hp
        self.minion_atk = minion_atk

    def execute(self, run, target, engine) -> str:
        grid = engine._get_free_grid(run.player)
        cfg = CARD_CONFIG.get(self.id, {})
        if grid:
            from .models import MinionState
            ba = 1 if self.id == "arcane_golem" else 0
            hp = self.minion_hp
            if "fool_oath" in run.player.relics:
                hp = max(1, hp - 3)
            run.player.minions[grid] = MinionState(self.id, self.name, hp, hp, self.minion_atk, 1, ba)
            feedback_success = cfg.get("feedback_success", "在格子 [{grid}] 召唤了【{name}】。")
            return feedback_success.format(grid=grid, name=self.name)
        return cfg.get("feedback_fail", "战场已满，召唤失败。")

class AbilityCard(Card):
    def execute(self, run, target, engine) -> str:
        from .data.buff_data import BUFF_CONFIG
        buff_info = BUFF_CONFIG.get(self.id, {})
        buff_name = buff_info.get("name", self.name)
        buff_desc = buff_info.get("desc", "")
        engine._add_buff_to(run.player, self.id, buff_name, buff_desc)
        
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(name=self.name)
        return f"使用了【{self.name}】。"

class IronWillCard(Card):
    def execute(self, run, target, engine) -> str:
        from .data.buff_data import BUFF_CONFIG
        buff_info = BUFF_CONFIG.get(self.id, {})
        buff_name = buff_info.get("name", "钢铁意志")
        buff_desc = buff_info.get("desc", "最大生命上限增加 10 并回复 10 生命")
        engine._add_buff_to(run.player, self.id, buff_name, buff_desc)
        engine._heal_target(run, "p0", 10)
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "使用了【钢铁意志】，获得了【钢铁意志】buff（最大生命上限增加 10 并回复 10 生命，可叠加）。")

class MagicMissileCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 3
        total = 0
        name = engine._get_target_name(run, target)
        if target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if idx < 0:
                    idx = 0
            except ValueError:
                idx = 0
            if 0 <= idx < len(run.enemies):
                enemy = run.enemies[idx]
                for _ in range(3):
                    enemy.hp -= dmg
                    total += dmg
                if enemy.hp <= 0:
                    run.player.graveyard.append("enemy:" + enemy.name)
                    run.enemies.pop(idx)
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(target=name, count=3, total=total)
        return f"释放魔法飞弹，无视护盾对【{name}】造成了 3 次共 {total} 点伤害。"

class FireballCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 16
        has_ring = any(av.id == "ring_of_elements" for av in run.player.amulets.values())
        if has_ring:
            dmg += 2
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        for enemy in run.enemies:
            if enemy.shield >= dmg:
                enemy.shield -= dmg
            else:
                enemy.hp -= (dmg - enemy.shield)
                enemy.shield = 0
        dead_enemies = [e for e in run.enemies if e.hp <= 0]
        for de in dead_enemies:
            run.player.graveyard.append("enemy:" + de.name)
        run.enemies = [e for e in run.enemies if e.hp > 0]
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(dmg=dmg)
        return f"释放火球术！对所有敌人造成了 {dmg} 点火焰伤害。"

class ThunderwaveCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 6
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        for enemy in run.enemies:
            if enemy.shield >= dmg:
                enemy.shield -= dmg
            else:
                enemy.hp -= (dmg - enemy.shield)
                enemy.shield = 0
            enemy.actions = max(0, enemy.actions - 1)
        dead_enemies = [e for e in run.enemies if e.hp <= 0]
        for de in dead_enemies:
            run.player.graveyard.append("enemy:" + de.name)
        run.enemies = [e for e in run.enemies if e.hp > 0]
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(dmg=dmg)
        return f"释放雷鸣波，对所有敌人造成了 {dmg} 点伤害，并扣除他们各 1 个动作。"

class ShieldSpellCard(Card):
    def execute(self, run, target, engine) -> str:
        run.player.shield += 8
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(shield_amount=8)
        return "获得了 8 点护盾。"

class MistyStepCard(Card):
    def execute(self, run, target, engine) -> str:
        engine._draw_cards(run.player, 2)
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(draw_count=2)
        return "使用了迷踪步，抽了 2 张牌。"

class ArcaneIntellectCard(Card):
    def execute(self, run, target, engine) -> str:
        engine._draw_cards(run.player, 3)
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(draw_count=3)
        return "使用了奥术智慧，抽了 3 张牌。"

class EchoFormCard(Card):
    def execute(self, run, target, engine) -> str:
        from .data.buff_data import BUFF_CONFIG
        buff_info = BUFF_CONFIG.get(self.id, {})
        buff_name = buff_info.get("name", self.name)
        buff_desc = buff_info.get("desc", "")
        engine._add_buff_to(run.player, self.id, buff_name, buff_desc)
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(name=self.name)
        return f"使用了【{self.name}】，获得了【回响形态】buff（每回合打出的卡牌额外打出，每张牌最多回响 8 次，多余层数顺延至后续卡牌，可叠加）。"

class CalculatedGambleCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        discard_count = len(p.hand)
        cfg = CARD_CONFIG.get(self.id, {})
        if discard_count > 0:
            agile_effects = []
            hand_cards = list(p.hand)
            p.hand.clear()
            for cid in hand_cards:
                effect_msg = engine._discard_card(run, cid)
                if effect_msg:
                    agile_effects.append(effect_msg)
            engine._draw_cards(p, discard_count)
            agile_str = "\n" + "\n".join(agile_effects) if agile_effects else ""
            feedback_tmpl = cfg.get("feedback")
            if feedback_tmpl:
                return feedback_tmpl.format(discard_count=discard_count) + agile_str
            return f"丢弃了所有的手牌（共 {discard_count} 张），并重新抽取了 {discard_count} 张牌。" + agile_str
        return cfg.get("feedback_empty", "手牌已空，没有丢弃任何卡牌。")

class ManaPotionCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, exhaust=False, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, exhaust=exhaust, desc=desc)

    def execute(self, run, target, engine) -> str:
        run.player.bonus_actions += 1
        engine._draw_cards(run.player, 1)
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "饮用了【魔力药水】，获得了 1BA 并抽了 1 张牌。")

class ArcaneSparkCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 2
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        name = engine._get_target_name(run, target)
        engine._damage_target(run, target, dmg)
        engine._draw_cards(run.player, 1)
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(target=name, dmg=dmg)
        return f"释放奥术星火，对【{name}】造成了 {dmg} 点伤害，并抽了 1 张牌。"

class OverchargeCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, exhaust=False, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, exhaust=exhaust, desc=desc)

    def execute(self, run, target, engine) -> str:
        from .data.buff_data import BUFF_CONFIG
        buff_info = BUFF_CONFIG.get("arcane_charge", {})
        buff_name = buff_info.get("name", "奥术充能")
        buff_desc = buff_info.get("desc", "法术伤害 +3")
        engine._add_buff_to(run.player, "arcane_charge", "奥术充能", "法术伤害 +3")
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "使用了【过载充能】，获得了【奥术充能】buff（法术伤害 +3，可叠加）。")

class DoomsdayJudgmentCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 18
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        for enemy in list(run.enemies):
            if enemy.shield >= dmg:
                enemy.shield -= dmg
            else:
                enemy.hp -= (dmg - enemy.shield)
                enemy.shield = 0
            engine._add_buff_to(enemy, "stun", "眩晕", "无法行动", 1)
        dead_enemies = [e for e in run.enemies if e.hp <= 0]
        for de in dead_enemies:
            run.player.graveyard.append("enemy:" + de.name)
        run.enemies = [e for e in run.enemies if e.hp > 0]
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(dmg=dmg)
        return f"释放末日审判！对所有敌人造成了 {dmg} 点伤害并眩晕他们一回合。"

class TimeWarpCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        max_hand = 9 if "mask_of_void" in p.relics else 12
        p.draw_pile.extend(p.discard_pile)
        p.draw_pile.extend(p.hand)
        p.discard_pile.clear()
        p.hand.clear()
        import random
        random.shuffle(p.draw_pile)
        before = len(p.hand)
        engine._draw_cards(p, max_hand)
        after = len(p.hand)
        draw_count = after - before
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(draw_count=draw_count)
        return f"时光倒流！已将所有卡牌重新洗回抽牌堆，并重新抽取了 {draw_count} 张牌。"

class MagicNetworkCard(Card):
    def execute(self, run, target, engine) -> str:
        engine._add_buff_to(run.player, "magic_network", "魔网天成", "本回合内每使用一张法术牌，对所有敌人造成 3 点伤害，获得 3 点护盾。")
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "使用了【魔网天成】，本回合内你的法术将与魔网产生共鸣。")

class MeteorSwarmCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, base_dmg, is_fire=True, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, desc=desc)
        self.base_dmg = base_dmg
        self.is_fire = is_fire

    def execute(self, run, target, engine) -> str:
        import random
        dmg = sum(random.randint(1, 12) for _ in range(8))
        if self.is_fire:
            has_ring = any(av.id == "ring_of_elements" for av in run.player.amulets.values())
            if has_ring:
                dmg += 2
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        for enemy in list(run.enemies):
            if enemy.shield >= dmg:
                enemy.shield -= dmg
            else:
                enemy.hp -= (dmg - enemy.shield)
                enemy.shield = 0
        dead_enemies = [e for e in run.enemies if e.hp <= 0]
        for de in dead_enemies:
            run.player.graveyard.append("enemy:" + de.name)
        run.enemies = [e for e in run.enemies if e.hp > 0]
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(dmg=dmg)
        return f"释放流星爆！对所有敌人造成了 {dmg} 点火焰伤害。"

class ArchmageWishCard(Card):
    def execute(self, run, target, engine) -> str:
        run.player.shield += 10
        engine._add_buff_to(run.player, "wish_power", "祈愿奥术", "本场战斗法术伤害 +4")
        engine._draw_cards(run.player, 2)
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "完成了大法师的祈愿！获得了 10 点护盾，【祈愿奥术】法术伤害 +4，并抽了 2 张牌。")

class FleetingSparkCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 6
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        name = engine._get_target_name(run, target)
        engine._damage_target(run, target, dmg)
        engine._draw_cards(run.player, 2)
        p = run.player
        if p.hand:
            run.node_data["pending_discard"] = True
            run.node_data["pending_discard_source"] = self.id
            return f"使用了【{self.name}】，对【{name}】造成了 {dmg} 点伤害，并抽了 2 张牌。请选择一张手牌丢弃。输入 选择 <手牌序号> 进行丢弃。"
        else:
            return f"使用了【{self.name}】，对【{name}】造成了 {dmg} 点伤害，并抽了 2 张牌，但手牌已空，无需丢弃。"

ALL_CARDS = {}

for cid, cfg in CARD_CONFIG.items():
    name = cfg["name"]
    color = cfg["color"]
    ctype = cfg["type"]
    cost_a = cfg["cost_a"]
    cost_ba = cfg["cost_ba"]
    desc = cfg["desc"]
    rarity = cfg.get("rarity", "common")
    exhaust = cfg.get("exhaust", False)
    fleeting = cfg.get("fleeting", False)
    agile = cfg.get("agile", False)
    retain = cfg.get("retain", False)

    if cid == "dagger_throw":
        ALL_CARDS[cid] = SpellDamageCard(cid, name, color, ctype, cost_a, cost_ba, cfg["base_dmg"], is_fire=False, desc=desc)
    elif cid == "first_aid":
        ALL_CARDS[cid] = SpellHealCard(cid, name, color, ctype, cost_a, cost_ba, cfg["heal_amount"], desc=desc)
    elif cid == "get_ready":
        ALL_CARDS[cid] = GetReadyCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "adrenaline":
        ALL_CARDS[cid] = AdrenalineCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid in ("lucky_coin", "thorns_necklace", "ring_of_elements", "arcane_crystal", "mage_ward"):
        ALL_CARDS[cid] = DeployAmuletCard(cid, name, color, ctype, cost_a, cost_ba, cfg["countdown"], cfg["amulet_desc"], desc=desc)
    elif cid in ("mercenary", "shield_guard", "find_familiar", "arcane_golem", "water_elemental"):
        ALL_CARDS[cid] = SummonMinionCard(cid, name, color, ctype, cost_a, cost_ba, cfg["minion_hp"], cfg["minion_atk"], desc=desc)
    elif cid in ("tactical_focus", "quicken", "spell_surge", "arcane_charge"):
        ALL_CARDS[cid] = AbilityCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "iron_will":
        ALL_CARDS[cid] = IronWillCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "fire_bolt":
        ALL_CARDS[cid] = SpellDamageCard(cid, name, color, ctype, cost_a, cost_ba, cfg["base_dmg"], is_fire=True, desc=desc)
    elif cid == "magic_missile":
        ALL_CARDS[cid] = MagicMissileCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "fireball":
        ALL_CARDS[cid] = FireballCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "thunderwave":
        ALL_CARDS[cid] = ThunderwaveCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "shield":
        ALL_CARDS[cid] = ShieldSpellCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "misty_step":
        ALL_CARDS[cid] = MistyStepCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "arcane_intellect":
        ALL_CARDS[cid] = ArcaneIntellectCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "echo_form":
        ALL_CARDS[cid] = EchoFormCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "calculated_gamble":
        ALL_CARDS[cid] = CalculatedGambleCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid in ("quick_strike", "agile_strike"):
        ALL_CARDS[cid] = SpellDamageCard(cid, name, color, ctype, cost_a, cost_ba, cfg["base_dmg"], is_fire=False, desc=desc)
    elif cid == "fleeting_spark":
        ALL_CARDS[cid] = FleetingSparkCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "mana_potion":
        ALL_CARDS[cid] = ManaPotionCard(cid, name, color, ctype, cost_a, cost_ba, exhaust=exhaust, desc=desc)
    elif cid == "arcane_spark":
        ALL_CARDS[cid] = ArcaneSparkCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "overcharge":
        ALL_CARDS[cid] = OverchargeCard(cid, name, color, ctype, cost_a, cost_ba, exhaust=exhaust, desc=desc)
    elif cid == "doomsday_judgment":
        ALL_CARDS[cid] = DoomsdayJudgmentCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "time_warp":
        ALL_CARDS[cid] = TimeWarpCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "magic_network":
        ALL_CARDS[cid] = MagicNetworkCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)
    elif cid == "meteor_swarm":
        ALL_CARDS[cid] = MeteorSwarmCard(cid, name, color, ctype, cost_a, cost_ba, cfg.get("base_dmg", 0), is_fire=True, desc=desc)
    elif cid == "archmage_wish":
        ALL_CARDS[cid] = ArchmageWishCard(cid, name, color, ctype, cost_a, cost_ba, desc=desc)

    ALL_CARDS[cid].rarity = rarity
    ALL_CARDS[cid].exhaust = exhaust
    ALL_CARDS[cid].fleeting = fleeting
    ALL_CARDS[cid].agile = agile
    ALL_CARDS[cid].retain = retain
