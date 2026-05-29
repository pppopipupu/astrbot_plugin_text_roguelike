from typing import Optional, List
from ...models.state import Card
from ...data.card_data import CARD_CONFIG

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
        engine._draw_cards(run.player, 1, run)
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(target=name, dmg=dmg)
        return f"释放奥术星火，对【{name}】造成了 {dmg} 点伤害，并抽了 1 张牌。"

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

class OverchargeCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, exhaust=False, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, exhaust=exhaust, desc=desc)

    def execute(self, run, target, engine) -> str:
        engine._add_buff_to(run.player, "arcane_charge", "奥术充能", "法术伤害 +3")
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "使用了【过载充能】，获得了【奥术充能】buff（法术伤害 +3，可叠加）。")

class MagicNetworkCard(Card):
    def execute(self, run, target, engine) -> str:
        engine._add_buff_to(run.player, "magic_network", "魔网天成", "本回合内每使用一张法术牌，对所有敌人造成 3 点伤害，获得 3 点护盾。")
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "使用了【魔网天成】，本回合内你的法术将与魔网产生共鸣。")

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
        engine._draw_cards(run.player, 2, run)
        p = run.player
        if p.hand:
            run.node_data["pending_discard"] = True
            run.node_data["pending_discard_source"] = self.id
            return f"使用了【{self.name}】，对【{name}】造成了 {dmg} 点伤害，并抽了 2 张牌。请选择一张手牌丢弃。输入 选择 <手牌序号> 进行丢弃。"
        else:
            return f"使用了【{self.name}】，对【{name}】造成了 {dmg} 点伤害，并抽了 2 张牌，但手牌已空，无需丢弃。"
