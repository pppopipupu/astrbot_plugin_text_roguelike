from typing import Optional, List
from .models import Card

class SpellDamageCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, base_dmg, is_fire=False, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, desc=desc)
        self.base_dmg = base_dmg
        self.is_fire = is_fire

    def execute(self, run, target, engine) -> str:
        dmg = self.base_dmg
        charge_buff = next((b for b in run.player.buffs if b.id == "arcane_charge"), None)
        charge_stacks = charge_buff.stacks if charge_buff else 0
        dmg += charge_stacks * 3
        if self.is_fire:
            has_ring = any(av.id == "ring_of_elements" for av in run.player.amulets.values())
            if has_ring:
                dmg += 2
        engine._damage_target(run, target, dmg)
        name = engine._get_target_name(run, target)
        return f"对【{name}】造成了 {dmg} 点伤害。" if self.id == "dagger_throw" else f"释放火焰弹，对【{name}】造成了 {dmg} 点伤害。"

class SpellHealCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, heal_amount, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, desc=desc)
        self.heal_amount = heal_amount

    def execute(self, run, target, engine) -> str:
        engine._heal_target(run, target, self.heal_amount)
        name = engine._get_target_name(run, target)
        return f"为【{name}】恢复了 {self.heal_amount} 点生命值。"

class GetReadyCard(Card):
    def execute(self, run, target, engine) -> str:
        run.player.bonus_actions += 2
        engine._draw_cards(run.player, 1)
        return "获得了 2BA 并抽了 1 张牌。"

class AdrenalineCard(Card):
    def execute(self, run, target, engine) -> str:
        run.player.actions += 1
        run.player.hp -= 2
        return "获得了 1A，失去了 2 点生命值。"

class DeployAmuletCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, countdown, amulet_desc, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, countdown=countdown, desc=desc)
        self.amulet_desc = amulet_desc

    def execute(self, run, target, engine) -> str:
        grid = engine._get_free_grid(run.player)
        if grid:
            from .models import AmuletState
            run.player.amulets[grid] = AmuletState(self.id, self.name, self.countdown, self.amulet_desc)
            return f"将【{self.name}】部署到了格子 [{grid}]。"
        return "战场格子已满，部署失败。"

class SummonMinionCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, minion_hp, minion_atk, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, desc=desc)
        self.minion_hp = minion_hp
        self.minion_atk = minion_atk

    def execute(self, run, target, engine) -> str:
        grid = engine._get_free_grid(run.player)
        if grid:
            from .models import MinionState
            run.player.minions[grid] = MinionState(self.id, self.name, self.minion_hp, self.minion_hp, self.minion_atk, 1, 1)
            return f"在格子 [{grid}] 召唤了【{self.name}】。"
        return "战场已满，召唤失败。"

class AbilityCard(Card):
    def execute(self, run, target, engine) -> str:
        if self.id == "tactical_focus":
            engine._add_buff_to(run.player, self.id, self.name, "每回合开始额外获得 1BA")
            return f"使用了【{self.name}】，获得了【战术专注】buff（每回合开始额外获得 1BA，可叠加）。"
        elif self.id == "quicken":
            engine._add_buff_to(run.player, self.id, self.name, "所有法术牌动作消耗减少 1BA（最低为 0）")
            return f"使用了【{self.name}】，获得了【超魔-瞬发】buff（所有法术牌动作消耗减少 1BA，可叠加）。"
        elif self.id == "spell_surge":
            engine._add_buff_to(run.player, self.id, self.name, "每使用一张蓝色牌，抽 1 张牌")
            return f"使用了【{self.name}】，获得了【法术涌动】buff（每使用一张蓝色牌，抽 1 张牌，可叠加）。"
        elif self.id == "arcane_charge":
            engine._add_buff_to(run.player, self.id, self.name, "法术伤害 +3")
            return f"使用了【{self.name}】，获得了【奥术充能】buff（法术伤害 +3，可叠加）。"
        return f"使用了【{self.name}】。"

class IronWillCard(Card):
    def execute(self, run, target, engine) -> str:
        engine._add_buff_to(run.player, self.id, self.name, "最大生命上限增加 10 并回复 10 生命")
        engine._heal_target(run, "p0", 10)
        return "使用了【钢铁意志】，获得了【钢铁意志】buff（最大生命上限增加 10 并回复 10 生命，可叠加）。"

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
        return f"释放魔法飞弹，无视护盾对【{name}】造成了 3 次共 {total} 点伤害。"

class FireballCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 12
        charge_buff = next((b for b in run.player.buffs if b.id == "arcane_charge"), None)
        charge_stacks = charge_buff.stacks if charge_buff else 0
        dmg += charge_stacks * 3
        has_ring = any(av.id == "ring_of_elements" for av in run.player.amulets.values())
        if has_ring:
            dmg += 2
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
        return f"释放火球术！对所有敌人造成了 {dmg} 点火焰伤害。"

class ThunderwaveCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 6
        charge_buff = next((b for b in run.player.buffs if b.id == "arcane_charge"), None)
        charge_stacks = charge_buff.stacks if charge_buff else 0
        dmg += charge_stacks * 3
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
        return f"释放雷鸣波，对所有敌人造成了 {dmg} 点伤害，并扣除他们各 1 个动作。"

class ShieldSpellCard(Card):
    def execute(self, run, target, engine) -> str:
        run.player.shield += 8
        return "获得了 8 点护盾。"

class MistyStepCard(Card):
    def execute(self, run, target, engine) -> str:
        engine._draw_cards(run.player, 2)
        return "使用了迷踪步，抽了 2 张牌。"

class ArcaneIntellectCard(Card):
    def execute(self, run, target, engine) -> str:
        engine._draw_cards(run.player, 3)
        return "使用了奥术智慧，抽了 3 张牌。"

class EchoFormCard(Card):
    def execute(self, run, target, engine) -> str:
        engine._add_buff_to(run.player, self.id, self.name, "每回合打出的第一张牌将会额外打出一次")
        return f"使用了【{self.name}】，获得了【回响形态】buff（每回合打出的第一张牌额外打出一次，可叠加）。"

class CalculatedGambleCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        discard_count = len(p.hand)
        if discard_count > 0:
            for cid in p.hand:
                p.discard_pile.append(cid)
            p.hand.clear()
            engine._draw_cards(p, discard_count)
            return f"丢弃了所有的手牌（共 {discard_count} 张），并重新抽取了 {discard_count} 张牌。"
        return "手牌已空，没有丢弃任何卡牌。"

ALL_CARDS = {
    "dagger_throw": SpellDamageCard("dagger_throw", "匕首投掷", "neutral", "spell", 1, 0, 4, desc="造成 4 点伤害。"),
    "first_aid": SpellHealCard("first_aid", "绷带包扎", "neutral", "spell", 0, 1, 4, desc="恢复 4 点生命值。"),
    "get_ready": GetReadyCard("get_ready", "准备就绪", "neutral", "spell", 1, 0, desc="获得 2BA，抽 1 张牌。"),
    "adrenaline": AdrenalineCard("adrenaline", "肾上腺素", "neutral", "spell", 0, 1, desc="获得 1A，失去 2 点生命。"),
    "lucky_coin": DeployAmuletCard("lucky_coin", "幸运金币", "neutral", "amulet", 1, 0, 3, "每回合结束时，玩家获得 3 金币。", desc="每回合结束时，玩家获得 3 金币。"),
    "thorns_necklace": DeployAmuletCard("thorns_necklace", "荆棘项链", "neutral", "amulet", 1, 0, 2, "受到伤害时，向伤害源反弹 2 点伤害。", desc="当玩家受到伤害时，对伤害来源造成 2 点伤害。"),
    "tactical_focus": AbilityCard("tactical_focus", "战术专注", "neutral", "ability", 1, 0, desc="本场战斗中，玩家每回合开始时额外获得 1BA。"),
    "iron_will": IronWillCard("iron_will", "钢铁意志", "neutral", "ability", 1, 0, desc="玩家最大生命值在本次战斗中 +10 并回复 10 生命。"),
    "mercenary": SummonMinionCard("mercenary", "雇佣兵", "neutral", "minion", 1, 0, 10, 4, desc="生命 10，攻击 4。拥有普通攻击（消耗 1A）。"),
    "shield_guard": SummonMinionCard("shield_guard", "盾卫", "neutral", "minion", 1, 0, 15, 1, desc="生命 15，攻击 1。技能：重整防线（消耗 1BA，为玩家提供 2 点护盾）。"),

    "fire_bolt": SpellDamageCard("fire_bolt", "火焰弹", "wizard", "spell", 0, 1, 3, is_fire=True, desc="造成 3 点火焰伤害。"),
    "magic_missile": MagicMissileCard("magic_missile", "魔法飞弹", "wizard", "spell", 1, 0, desc="造成 3 次 3 点伤害，无视护盾。"),
    "fireball": FireballCard("fireball", "火球术", "wizard", "spell", 1, 1, desc="造成 20 点火焰伤害。"),
    "thunderwave": ThunderwaveCard("thunderwave", "雷鸣波", "wizard", "spell", 1, 0, desc="造成 6 点伤害，使敌人下回合减少 1A。"),
    "shield": ShieldSpellCard("shield", "护盾术", "wizard", "spell", 0, 1, desc="获得 8 点护盾。"),
    "misty_step": MistyStepCard("misty_step", "迷踪步", "wizard", "spell", 0, 1, desc="抽 2 张牌。"),
    "arcane_intellect": ArcaneIntellectCard("arcane_intellect", "奥术智慧", "wizard", "spell", 1, 0, desc="抽 3 张牌。"),
    "ring_of_elements": DeployAmuletCard("ring_of_elements", "元素指环", "wizard", "amulet", 1, 0, 4, "火焰伤害 +2", desc="玩家造成的火焰伤害 +2。"),
    "arcane_crystal": DeployAmuletCard("arcane_crystal", "奥术水晶", "wizard", "amulet", 1, 0, 3, "每使用一张法术牌回复 2 点生命值", desc="每当玩家使用法术牌，回复 2 点生命值。"),
    "mage_ward": DeployAmuletCard("mage_ward", "法师护盾", "wizard", "amulet", 1, 0, 3, "玩家回合结束时获得 4 点护盾", desc="玩家回合结束时，获得 4 点护盾。"),
    "quicken": AbilityCard("quicken", "超魔-瞬发", "wizard", "ability", 0, 1, desc="本场战斗所有法术牌动作消耗减少 1BA（最低为 0）。"),
    "spell_surge": AbilityCard("spell_surge", "法术涌动", "wizard", "ability", 1, 0, desc="本场战斗每使用一张蓝色牌，抽 1 张牌。"),
    "arcane_charge": AbilityCard("arcane_charge", "奥术充能", "wizard", "ability", 1, 0, desc="本场战斗法术伤害 +3。"),
    "find_familiar": SummonMinionCard("find_familiar", "召唤魔宠", "wizard", "minion", 0, 1, 5, 2, desc="生命 5，攻击 2。技能：奥术协助（消耗 1BA，玩家抽 1 张牌）。"),
    "arcane_golem": SummonMinionCard("arcane_golem", "奥术傀儡", "wizard", "minion", 1, 1, 20, 6, desc="生命 20，攻击 6。仅有普通攻击。"),
    "water_elemental": SummonMinionCard("water_elemental", "寒冰元素", "wizard", "minion", 1, 0, 12, 3, desc="生命 12，攻击 3。技能：寒冰触碰（消耗 1BA，使一个敌方单位在下一回合减少 1BA）。"),
    "echo_form": EchoFormCard("echo_form", "回响形态", "neutral", "ability", 1, 1, desc="本场战斗中，你每回合打出的第一张牌将会额外打出一次。"),
    "calculated_gamble": CalculatedGambleCard("calculated_gamble", "计算下注", "neutral", "spell", 0, 1, desc="丢弃所有手牌，重新抽等量牌。"),
}

card_rarities = {
    "dagger_throw": "common",
    "first_aid": "common",
    "get_ready": "common",
    "adrenaline": "rare",
    "lucky_coin": "rare",
    "thorns_necklace": "rare",
    "tactical_focus": "epic",
    "iron_will": "epic",
    "mercenary": "rare",
    "shield_guard": "rare",
    "echo_form": "epic",
    "calculated_gamble": "rare",
    "fire_bolt": "common",
    "magic_missile": "rare",
    "fireball": "epic",
    "thunderwave": "rare",
    "shield": "common",
    "misty_step": "rare",
    "arcane_intellect": "rare",
    "ring_of_elements": "rare",
    "arcane_crystal": "rare",
    "mage_ward": "rare",
    "quicken": "epic",
    "spell_surge": "epic",
    "arcane_charge": "epic",
    "find_familiar": "common",
    "arcane_golem": "epic",
    "water_elemental": "rare"
}
for cid, rarity in card_rarities.items():
    if cid in ALL_CARDS:
        ALL_CARDS[cid].rarity = rarity
