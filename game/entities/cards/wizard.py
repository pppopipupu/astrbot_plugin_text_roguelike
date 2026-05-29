from typing import Optional, List
from ...models.state import Card
from ...data.card_data import CARD_CONFIG
from .registry import register_card

@register_card("magic_missile")
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
                original_enemy = run.enemies[idx]
                dmg = engine.get_modified_spell_damage(run, self, dmg)
                for _ in range(3):
                    if original_enemy in run.enemies:
                        curr_idx = run.enemies.index(original_enemy)
                        engine._damage_target(run, f"e{curr_idx+1}", dmg, damage_type="true", card=self)
                        total += dmg
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(target=name, count=3, total=total)
        return f"释放魔法飞弹，无视护盾对【{name}】造成了 3 次共 {total} 点伤害。"

@register_card("fireball")
class FireballCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 16
        if self.damage_type == "fire":
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
        for idx in range(len(run.enemies) - 1, -1, -1):
            engine._damage_target(run, f"e{idx+1}", dmg, damage_type="fire", card=self)
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(dmg=dmg)
        return f"释放火球术！对所有敌人造成了 {dmg} 点火焰伤害。"

@register_card("thunderwave")
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
        for idx in range(len(run.enemies) - 1, -1, -1):
            run.enemies[idx].actions = max(0, run.enemies[idx].actions - 1)
            engine._damage_target(run, f"e{idx+1}", dmg, damage_type="thunder", card=self)
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(dmg=dmg)
        return f"释放雷鸣波，对所有敌人造成了 {dmg} 点伤害，并扣除他们各 1 个动作。"

@register_card("shield")
class ShieldSpellCard(Card):
    def execute(self, run, target, engine) -> str:
        run.player.shield += 8
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(shield_amount=8)
        return "获得了 8 点护盾。"

@register_card("arcane_spark")
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
        engine._damage_target(run, target, dmg, damage_type=self.damage_type, card=self)
        engine._draw_cards(run.player, 1, run)
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(target=name, dmg=dmg)
        return f"释放奥术星火，对【{name}】造成了 {dmg} 点伤害，并抽了 1 张牌。"

@register_card("echo_form")
class EchoFormCard(Card):
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
        return f"使用了【{self.name}】，获得了【回响形态】buff（每回合打出的卡牌额外打出，每张牌最多回响 8 次，多余层数顺延至后续卡牌，可叠加）。"

@register_card("doomsday_judgment")
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
        for idx in range(len(run.enemies) - 1, -1, -1):
            engine._add_buff_to(run.enemies[idx], "stun", "眩晕", "无法行动", 1)
            engine._damage_target(run, f"e{idx+1}", dmg, damage_type="necrotic", card=self)
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(dmg=dmg)
        return f"释放末日审判！对所有敌人造成了 {dmg} 点伤害并眩晕他们一回合。"

@register_card("overcharge")
class OverchargeCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, exhaust=False, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, exhaust=exhaust, desc=desc)

    def execute(self, run, target, engine) -> str:
        engine._add_buff_to(run.player, "arcane_charge", "奥术充能", "法术伤害 +3")
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "使用了【过载充能】，获得了【奥术充能】buff（法术伤害 +3，可叠加）。")

@register_card("magic_network")
class MagicNetworkCard(Card):
    def execute(self, run, target, engine) -> str:
        engine._add_buff_to(run.player, "magic_network", "魔网天成", "本回合内每使用一张法术牌，对所有敌人造成 3 点伤害，获得 3 点护盾。")
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "使用了【魔网天成】，本回合内你的法术将与魔网产生共鸣。")

@register_card("fleeting_spark")
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
        engine._damage_target(run, target, dmg, damage_type=self.damage_type, card=self)
        engine._draw_cards(run.player, 2, run)
        p = run.player
        if p.hand:
            run.node_data["pending_discard"] = True
            run.node_data["pending_discard_source"] = self.id
            return f"使用了【{self.name}】，对【{name}】造成了 {dmg} 点伤害，并抽了 2 张牌。请选择一张手牌丢弃。输入 选择 <手牌序号> 进行丢弃。"
        else:
            return f"使用了【{self.name}】，对【{name}】造成了 {dmg} 点伤害，并抽了 2 张牌，但手牌已空，无需丢弃。"

@register_card("chain_lightning")
class ChainLightningCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 12
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        name = engine._get_target_name(run, target)
        def get_base_name(n: str) -> str:
            parts = n.split()
            if len(parts) > 1 and len(parts[-1]) == 1 and parts[-1].isupper():
                return " ".join(parts[:-1])
            return n
        base_target_name = ""
        if target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if idx < 0:
                    idx = 0
            except ValueError:
                idx = 0
            if 0 <= idx < len(run.enemies):
                base_target_name = get_base_name(run.enemies[idx].name)
        affected_count = 0
        if base_target_name:
            for idx in range(len(run.enemies) - 1, -1, -1):
                enemy = run.enemies[idx]
                if get_base_name(enemy.name) == base_target_name:
                    engine._damage_target(run, f"e{idx+1}", dmg, damage_type="lightning", card=self)
                    affected_count += 1
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(dmg=dmg)
        return f"释放链式闪电！对所有同名敌人造成了 {dmg} 点闪电伤害。"
