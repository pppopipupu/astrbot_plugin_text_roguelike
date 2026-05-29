from typing import Optional, List
from ...models.state import Card, AmuletState, MinionState
from ...data.card_data import CARD_CONFIG
from .registry import register_card

@register_card("dagger_throw", is_fire=False)
@register_card("fire_bolt", is_fire=True)
@register_card("quick_strike", is_fire=False)
@register_card("agile_strike", is_fire=False)
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
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(target=name, dmg=dmg)
        
        return f"使用了【{self.name}】，对【{name}】造成了 {dmg} 点伤害。"

@register_card("first_aid")
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

@register_card("get_ready")
class GetReadyCard(Card):
    def execute(self, run, target, engine) -> str:
        run.player.bonus_actions += 2
        engine._draw_cards(run.player, 1, run)
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "获得了 2BA 并抽了 1 张牌。")

@register_card("adrenaline")
class AdrenalineCard(Card):
    def execute(self, run, target, engine) -> str:
        run.player.actions += 1
        run.player.hp -= 2
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "获得了 1A，失去了 2 点生命值。")

@register_card("lucky_coin")
@register_card("thorns_necklace")
@register_card("ring_of_elements")
@register_card("arcane_crystal")
@register_card("mage_ward")
class DeployAmuletCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, countdown, amulet_desc, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, countdown=countdown, desc=desc)
        self.amulet_desc = amulet_desc

    def execute(self, run, target, engine) -> str:
        grid = engine._get_free_grid(run.player)
        cfg = CARD_CONFIG.get(self.id, {})
        if grid:
            run.player.amulets[grid] = AmuletState(self.id, self.name, self.countdown, self.amulet_desc)
            feedback_success = cfg.get("feedback_success", "将【{name}】部署到了格子 [{grid}]。")
            return feedback_success.format(name=self.name, grid=grid)
        return cfg.get("feedback_fail", "战场格子已满，部署失败。")

@register_card("mercenary")
@register_card("shield_guard")
@register_card("find_familiar")
@register_card("arcane_golem")
@register_card("water_elemental")
class SummonMinionCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, minion_hp, minion_atk, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, desc=desc)
        self.minion_hp = minion_hp
        self.minion_atk = minion_atk

    def execute(self, run, target, engine) -> str:
        cfg = CARD_CONFIG.get(self.id, {})
        ba = 1 if self.id == "arcane_golem" else 0
        grid = engine._summon_minion(run, self.id, self.name, self.minion_hp, self.minion_atk, ba)
        if grid:
            feedback_success = cfg.get("feedback_success", "在格子 [{grid}] 召唤了【{name}】。")
            return feedback_success.format(grid=grid, name=self.name)
        return cfg.get("feedback_fail", "战场已满，召唤失败。")

@register_card("tactical_focus")
@register_card("quicken")
@register_card("spell_surge")
@register_card("arcane_charge")
class AbilityCard(Card):
    def execute(self, run, target, engine) -> str:
        from ...data.buff_data import BUFF_CONFIG
        buff_info = BUFF_CONFIG.get(self.id, {})
        buff_name = buff_info.get("name", self.name)
        buff_desc = buff_info.get("desc", "")
        engine._add_buff_to(run.player, self.id, buff_name, buff_desc)
        
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(name=self.name)
        return f"使用了【{self.name}】。"

@register_card("iron_will")
class IronWillCard(Card):
    def execute(self, run, target, engine) -> str:
        from ...data.buff_data import BUFF_CONFIG
        buff_info = BUFF_CONFIG.get(self.id, {})
        buff_name = buff_info.get("name", "钢铁意志")
        buff_desc = buff_info.get("desc", "最大生命上限增加 10 并回复 10 生命")
        engine._add_buff_to(run.player, self.id, buff_name, buff_desc)
        engine._heal_target(run, "p0", 10)
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "使用了【钢铁意志】，获得了【钢铁意志】buff（最大生命上限增加 10 并回复 10 生命，可叠加）。")

@register_card("misty_step")
class MistyStepCard(Card):
    def execute(self, run, target, engine) -> str:
        engine._draw_cards(run.player, 2, run)
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(draw_count=2)
        return "使用了迷踪步，抽了 2 张牌。"

@register_card("arcane_intellect")
class ArcaneIntellectCard(Card):
    def execute(self, run, target, engine) -> str:
        engine._draw_cards(run.player, 3, run)
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(draw_count=3)
        return "使用了奥术智慧，抽了 3 张牌。"

@register_card("calculated_gamble")
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
            engine._draw_cards(p, discard_count, run)
            agile_str = "\n" + "\n".join(agile_effects) if agile_effects else ""
            feedback_tmpl = cfg.get("feedback")
            if feedback_tmpl:
                return feedback_tmpl.format(discard_count=discard_count) + agile_str
            return f"丢弃了所有的手牌（共 {discard_count} 张），并重新抽取了 {discard_count} 张牌。" + agile_str
        return cfg.get("feedback_empty", "手牌已空，没有丢弃任何卡牌。")

@register_card("mana_potion")
class ManaPotionCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, exhaust=False, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, exhaust=exhaust, desc=desc)

    def execute(self, run, target, engine) -> str:
        run.player.bonus_actions += 1
        engine._draw_cards(run.player, 1, run)
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "饮用了【魔力药水】，获得了 1BA 并抽了 1 张牌。")
