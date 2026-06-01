from typing import Optional, List
from ...models.state import Card
from ...data.card_data import CARD_CONFIG
from .registry import register_card

@register_card("time_warp")
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
        engine._draw_cards(p, max_hand, run)
        after = len(p.hand)
        draw_count = after - before
        if self.upgraded:
            p.actions += 1
            p.bonus_actions += 1
            engine._add_buff_to(p, "time_warp_spell_boost", "时空强化", "本回合所有法术伤害 +2", 1)
            return f"时光倒流！已将所有卡牌重新洗回抽牌堆，重新抽取了 {draw_count} 张牌。玩家额外获得 1A 1BA，且本回合所有法术伤害 +2。"
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(draw_count=draw_count)
        return f"时光倒流！已将所有卡牌重新洗回抽牌堆，并重新抽取了 {draw_count} 张牌。"

@register_card("meteor_swarm")
class MeteorSwarmCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, base_dmg, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, desc=desc)
        self.base_dmg = base_dmg

    def execute(self, run, target, engine) -> str:
        import random
        num_dice = 12 if self.upgraded else 8
        dice_results = [random.randint(1, 12) for _ in range(num_dice)]
        dmg = sum(dice_results)
        extra_true_dmg = 0
        if self.upgraded:
            extra_true_dmg = sum(2 for d in dice_results if d > 8)
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
            if extra_true_dmg > 0:
                engine._damage_target(run, f"e{idx+1}", extra_true_dmg, damage_type="true", card=self)
        if self.upgraded:
            if extra_true_dmg > 0:
                return f"释放流星爆！对所有敌人造成了 {dmg} 点火焰伤害，并因大骰子额外造成 {extra_true_dmg} 点真实伤害。"
            return f"释放流星爆！对所有敌人造成了 {dmg} 点火焰伤害。"
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(dmg=dmg)
        return f"释放流星爆！对所有敌人造成了 {dmg} 点火焰伤害。"

@register_card("archmage_wish")
class ArchmageWishCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        if self.upgraded:
            p.shield += 15
            engine._add_buff_to(p, "wish_power+", "祈愿奥术", "本场战斗法术伤害 +6")
            before_hand = list(p.hand)
            engine._draw_cards(p, 3, run)
            drawn = p.hand[len(before_hand):]
            run.node_data.setdefault("temp_retain_cards", []).extend(drawn)
            return "完成了大法师的祈愿！获得了 15 点护盾，【祈愿奥术】法术伤害 +6，并抽了 3 张牌且它们本回合获得保留。"
        else:
            p.shield += 10
            engine._add_buff_to(p, "wish_power", "祈愿奥术", "本场战斗法术伤害 +4")
            engine._draw_cards(p, 2, run)
            cfg = CARD_CONFIG.get(self.id, {})
            return cfg.get("feedback", "完成了大法师的祈愿！获得了 10 点护盾，【祈愿奥术】法术伤害 +4，并抽了 2 张牌。")

@register_card("time_stop")
class TimeStopCard(Card):
    def execute(self, run, target, engine) -> str:
        if self.upgraded:
            run.node_data["extra_turns_left"] = 4
            run.node_data["time_stop_upgraded"] = True
            return "施展了时间停止！你获得了 4 个额外回合，且在额外回合中受到的负面效果暂停生效。"
        else:
            run.node_data["extra_turns_left"] = 3
            run.node_data["time_stop_upgraded"] = False
            cfg = CARD_CONFIG.get(self.id, {})
            return cfg.get("feedback", "施展了时间停止！你获得了 3 个额外回合。")

@register_card("break_limits")
class BreakLimitsCard(Card):
    def execute(self, run, target, engine) -> str:
        from ..buffs.buffs import is_debuff
        p = run.player
        doubled_count = 0
        for b in p.buffs:
            if not is_debuff(b.id):
                b.stacks *= 2
                if getattr(b, "stacks2", None) is not None:
                    b.stacks2 *= 2
                doubled_count += 1
        p.actions += 1
        if self.upgraded:
            p.bonus_actions += 1
            return f"突破了极限！使 {doubled_count} 个正面 Buff 的层数翻倍，获得了 1A 1BA。"
        return f"突破了极限！使 {doubled_count} 个正面 Buff 的层数翻倍，获得了 1A。"

@register_card("abyss_collapse")
class AbyssCollapseCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = getattr(self, "base_dmg", 32 if self.upgraded else 24)
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        if "abyss_gaze" in run.player.relics:
            dmg += 4
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        
        feedback_parts = []
        for idx in range(len(run.enemies) - 1, -1, -1):
            enemy = run.enemies[idx]
            is_stunned = any(b.id == "stun" for b in enemy.buffs)
            final_dmg = dmg * 2 if is_stunned else dmg
            engine._damage_target(run, f"e{idx+1}", final_dmg, damage_type="necrotic", card=self)
            feedback_parts.append(f"【{enemy.name}】受到 {final_dmg} 点黯蚀伤害")
        return f"释放深渊崩塌！" + "，".join(feedback_parts) + "。"

@register_card("demon_contract")
class DemonContractCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        ba_gain = 3 if self.upgraded else 2
        draw_cnt = 4 if self.upgraded else 3
        p.bonus_actions += ba_gain
        engine._draw_cards(p, draw_cnt, run)
        
        buff_id = "demon_contract_buff"
        buff_stacks = 2 if self.upgraded else 1
        engine._add_buff_to(p, buff_id, "恶魔契约", "打出的下一张法术牌额外打出多次", buff_stacks)
        return f"签结了恶魔契约！获得了 {ba_gain}BA 并抽了 {draw_cnt} 张牌，获得了【恶魔契约】Buff（下一次法术回响 {buff_stacks} 次）。"

@register_card("frost_nova")
class FrostNovaCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = getattr(self, "base_dmg", 20 if self.upgraded else 14)
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        if "frost_blade" in run.player.relics:
            dmg += 4
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        
        vuln_stacks = 3 if self.upgraded else 2
        feedback_parts = []
        for idx in range(len(run.enemies) - 1, -1, -1):
            enemy = run.enemies[idx]
            engine._damage_target(run, f"e{idx+1}", dmg, damage_type="cold", card=self)
            engine._add_buff_to(enemy, "minor_vulnerable_cold", "轻度寒冷易伤", "受到的寒冷伤害增加 50%", vuln_stacks)
            engine._add_buff_to(enemy, "stun", "眩晕", "无法行动", 1)
            feedback_parts.append(f"【{enemy.name}】受到 {dmg} 点冰霜伤害且被施加 {vuln_stacks} 层寒冷易伤与眩晕")
        return f"释放霜冻新星！" + "，".join(feedback_parts) + "。"

@register_card("glacier_fortress")
class GlacierFortressCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        shield_val = 28 if self.upgraded else 20
        engine._gain_shield(run, "p0", shield_val)
        
        buff_id = "glacier_fortress_buff+" if self.upgraded else "glacier_fortress_buff"
        engine._add_buff_to(p, buff_id, "冰川壁垒", "回合结束时获得额外护盾", 1)
        return f"筑起了冰川壁垒！获得了 {shield_val} 点护盾，且获得了【冰川壁垒】形态。"

@register_card("abyss_erosion")
class AbyssErosionCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 15 if self.upgraded else 10
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        if "abyss_gaze" in run.player.relics:
            dmg += 4
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        weakness_stacks = 5 if self.upgraded else 3
        engine._damage_target(run, target, dmg, damage_type="necrotic", card=self)
        enemy_state = None
        if target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if 0 <= idx < len(run.enemies):
                    enemy_state = run.enemies[idx]
            except ValueError:
                pass
        if not enemy_state and run.enemies:
            enemy_state = run.enemies[0]
        if enemy_state:
            engine._add_buff_to(enemy_state, "void_weakness", "虚空弱化", "受到的所有伤害增加", weakness_stacks)
        tname = engine._get_target_name(run, target)
        return f"释放了深渊侵蚀！对【{tname}】施加了 {weakness_stacks} 层虚空弱化。"

@register_card("glacier_tempest")
class GlacierTempestCard(Card):
    def execute(self, run, target, engine) -> str:
        base_dmg = 18 if self.upgraded else 12
        if "arcane_rune" in run.player.relics:
            base_dmg += 1
        if "mark_of_fury" in run.player.relics:
            base_dmg += 2
        if "unstable_crystal" in run.player.relics:
            base_dmg += 1
        if "frost_blade" in run.player.relics:
            base_dmg += 4
        total_dmg = 0
        feedback_parts = []
        for idx in range(len(run.enemies) - 1, -1, -1):
            enemy = run.enemies[idx]
            dmg = engine.get_modified_spell_damage(run, self, base_dmg)
            engine._damage_target(run, f"e{idx+1}", dmg, damage_type="cold", card=self)
            total_dmg += dmg
            feedback_parts.append(f"【{enemy.name}】受到 {dmg} 点冰霜伤害")
        shield_msg = ""
        if run.player.minions and total_dmg > 0:
            shield_gain = total_dmg // 2
            engine._gain_shield(run, "p0", shield_gain)
            shield_msg = f"，并获得了 {shield_gain} 点护盾"
        return f"释放了极寒风暴！" + "，".join(feedback_parts) + shield_msg + "。"
