from typing import Optional, List
from ...models.state import Card
from ...data.card_data import CARD_CONFIG
from .registry import register_card

@register_card("magic_missile")
class MagicMissileCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 4 if self.upgraded else 3
        count = 4 if self.upgraded else 3
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
                for _ in range(count):
                    if original_enemy in run.enemies:
                        curr_idx = run.enemies.index(original_enemy)
                        engine._damage_target(run, f"e{curr_idx+1}", dmg, damage_type="true", card=self)
                        total += dmg
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(target=name, count=count, total=total)
        return f"释放魔法飞弹，无视护盾对【{name}】造成了 {count} 次共 {total} 点伤害。"

@register_card("fireball")
class FireballCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = getattr(self, "base_dmg", 24 if self.upgraded else 18)
        if self.damage_type == "fire":
            has_ring = any(av.id.startswith("ring_of_elements") for av in run.player.amulets.values())
            if has_ring:
                ring_val = 0
                for av in run.player.amulets.values():
                    if av.id.startswith("ring_of_elements"):
                        ring_val = max(ring_val, 3 if av.id.endswith("+") else 2)
                dmg += ring_val
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        for idx in range(len(run.enemies) - 1, -1, -1):
            engine._damage_target(run, f"e{idx+1}", dmg, damage_type="fire", card=self)
            
        burn_dmg = 8 if self.upgraded else 6
        burn_turns = 3 if self.upgraded else 2
        for enemy in list(run.enemies):
            engine._add_buff_to(enemy, "burning", "燃烧", "每回合开始时受到火焰伤害", burn_dmg, burn_turns)

        bonus_msg = ""
        if self.id == "fireball+":
            engine._add_buff_to(run.player, "fire_grow", "烈焰成长", "造成的火焰伤害增加", 1)
            bonus_msg = " 🔥 [火球术+] 获得了 1 层【烈焰成长】（火焰伤害永久 +1）！"
            
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(dmg=dmg) + bonus_msg
        return f"释放火球术！对所有敌人造成了 {dmg} 点火焰伤害。" + bonus_msg

@register_card("thunderwave")
class ThunderwaveCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = getattr(self, "base_dmg", 9 if self.upgraded else 6)
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
            
        bonus_msg = ""
        if self.upgraded:
            first_enemy = engine._get_first_alive_enemy(run)
            if first_enemy:
                try:
                    f_idx = int(first_enemy.replace("e", "")) - 1
                    if 0 <= f_idx < len(run.enemies):
                        engine._add_buff_to(run.enemies[f_idx], "stun", "眩晕", "无法行动", 1)
                        bonus_msg = f" ⚡ [雷鸣波+] 眩晕了【{run.enemies[f_idx].name}】1 回合！"
                except ValueError:
                    pass
                    
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(dmg=dmg) + bonus_msg
        return f"释放雷鸣波，对所有敌人造成了 {dmg} 点伤害，并扣除他们各 1 个动作。" + bonus_msg

@register_card("shield")
class ShieldSpellCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        shield_val = getattr(self, "shield_amount", 12 if self.upgraded else 8)
        if self.upgraded and p.hp < p.max_hp / 2:
            heal_val = shield_val // 2
            shield_val = shield_val - heal_val
            engine._heal_target(run, "p0", heal_val)
            engine._gain_shield(run, "p0", shield_val)
            return f"获得了 {shield_val} 点护盾，并为自己恢复了 {heal_val} 点生命值。"
        else:
            engine._gain_shield(run, "p0", shield_val)
            cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
            feedback_tmpl = cfg.get("feedback")
            if feedback_tmpl:
                return feedback_tmpl.format(shield_amount=shield_val)
            return f"获得了 {shield_val} 点护盾。"

@register_card("arcane_spark")
class ArcaneSparkCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = getattr(self, "base_dmg", 4 if self.upgraded else 2)
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        name = engine._get_target_name(run, target)
        engine._damage_target(run, target, dmg, damage_type=self.damage_type, card=self)
        
        p = run.player
        before_hand_len = len(p.hand)
        engine._draw_cards(p, 1, run)
        
        bonus_msg = ""
        if self.upgraded and len(p.hand) > before_hand_len:
            drawn_cid = p.hand[-1]
            from .base import ALL_CARDS
            drawn_card = ALL_CARDS.get(drawn_cid)
            if drawn_card and drawn_card.type == "spell":
                run.node_data.setdefault("free_spells_this_turn", []).append(drawn_cid)
                bonus_msg = f" ⚡ [奥术星火+] 抽到了法术牌【{drawn_card.name}】，该卡牌本回合动作消耗降为 0！"
                
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(target=name, dmg=dmg) + bonus_msg
        return f"释放奥术星火，对【{name}】造成了 {dmg} 点伤害，并抽了 1 张牌。" + bonus_msg

@register_card("echo_form")
class EchoFormCard(Card):
    def execute(self, run, target, engine) -> str:
        from ...data.buff_data import BUFF_CONFIG
        buff_info = BUFF_CONFIG.get(self.id.replace("+", ""), {})
        buff_name = buff_info.get("name", self.name)
        buff_desc = buff_info.get("desc", "")
        engine._add_buff_to(run.player, self.id, buff_name, buff_desc)
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(name=self.name)
        return f"使用了【{self.name}】，获得了【回响形态】buff（每回合打出的卡牌额外打出，每张牌最多回响 8 次，多余层数顺延至后续卡牌，可叠加）。"

@register_card("doomsday_judgment")
class DoomsdayJudgmentCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = getattr(self, "base_dmg", 24 if self.upgraded else 18)
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
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(dmg=dmg)
        return f"释放末日审判！对所有敌人造成了 {dmg} 点伤害并眩晕他们一回合。"

@register_card("overcharge")
class OverchargeCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, exhaust=False, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, exhaust=exhaust, desc=desc)

    def execute(self, run, target, engine) -> str:
        stacks = 2 if self.upgraded else 1
        engine._add_buff_to(run.player, "arcane_charge", "奥术充能", "法术伤害 +3", stacks)
        bonus_msg = ""
        if self.upgraded:
            engine._draw_cards(run.player, 1, run)
            bonus_msg = " ⚡ 并抽了 1 张法术牌。"
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        return cfg.get("feedback", "使用了【过载充能】，获得了【奥术充能】buff（法术伤害 +3，可叠加）。").replace("（法术伤害 +3，可叠加）", "") + f"（获得了 {stacks} 层奥术充能）" + bonus_msg

@register_card("magic_network")
class MagicNetworkCard(Card):
    def execute(self, run, target, engine) -> str:
        buff_id = self.id
        buff_name = "魔网天成+" if self.upgraded else "魔网天成"
        buff_desc = "本回合内每使用一张法术牌，对所有敌人造成 5 点伤害，获得 5 点护盾。支持回响触发。" if self.upgraded else "本回合内每使用一张法术牌，对所有敌人造成 3 点伤害，获得 3 点护盾。"
        engine._add_buff_to(run.player, buff_id, buff_name, buff_desc)
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        return cfg.get("feedback", "使用了【魔网天成】，本回合内你的法术将与魔网产生共鸣。")

@register_card("fleeting_spark")
class FleetingSparkCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = getattr(self, "base_dmg", 9 if self.upgraded else 6)
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        name = engine._get_target_name(run, target)
        engine._damage_target(run, target, dmg, damage_type=self.damage_type, card=self)
        
        draw_count = 3 if self.upgraded else 2
        engine._draw_cards(run.player, draw_count, run)
        p = run.player
        if p.hand:
            run.node_data["pending_discard"] = True
            run.node_data["pending_discard_source"] = self.id
            return f"使用了【{self.name}】，对【{name}】造成了 {dmg} 点伤害，并抽了 {draw_count} 张牌。请选择一张手牌丢弃。输入 选择 <手牌序号> 进行丢弃。"
        else:
            return f"使用了【{self.name}】，对【{name}】造成了 {dmg} 点伤害，并抽了 {draw_count} 张牌，但手牌已空，无需丢弃。"

@register_card("chain_lightning")
class ChainLightningCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = getattr(self, "base_dmg", 18 if self.upgraded else 12)
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
                
        bonus_msg = ""
        if self.upgraded and base_target_name:
            same_name_count = sum(1 for e in run.enemies if get_base_name(e.name) == base_target_name)
            if same_name_count == 1:
                dmg = int(dmg * 1.5)
                bonus_msg = " ⚡ [链式闪电+] 触发单体暴击，造成 1.5 倍伤害！"
                
        affected_count = 0
        if base_target_name:
            for idx in range(len(run.enemies) - 1, -1, -1):
                enemy = run.enemies[idx]
                if get_base_name(enemy.name) == base_target_name:
                    engine._damage_target(run, f"e{idx+1}", dmg, damage_type="lightning", card=self)
                    affected_count += 1
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(dmg=dmg) + bonus_msg
        return f"释放链式闪电！对所有同名敌人造成了 {dmg} 点闪电伤害。" + bonus_msg

@register_card("sunburst")
class SunburstCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = getattr(self, "base_dmg", 22 if self.upgraded else 16)
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        for idx in range(len(run.enemies) - 1, -1, -1):
            engine._damage_target(run, f"e{idx+1}", dmg, damage_type="radiant", card=self)
            
        for grid in list(run.player.minions.keys()):
            engine._damage_target(run, f"p{grid}", dmg, damage_type="radiant", card=self)
            
        bonus_msg = ""
        if self.upgraded:
            for grid, m_state in list(run.player.minions.items()):
                m_state.buffs.clear()
                m_state.atk += 3
                engine._log_event(run, f"☀️ [阳炎爆+ 效果] 净化了我方随从【{m_state.name}】的所有状态，且使其攻击力增加 3 点！")
            bonus_msg = " ☀️ [阳炎爆+] 净化了我方随从并使其攻击力增加 3 点！"
            
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(dmg=dmg) + bonus_msg
        return f"释放【阳炎爆】，对所有除玩家外的生物造成了 {dmg} 点光耀伤害。" + bonus_msg

@register_card("arcane_torrent")
class ArcaneTorrentCard(Card):
    def execute(self, run, target, engine) -> str:
        X = run.node_data.get("last_x_cost_a", 0)
        single_dmg = 4 if self.upgraded else 3
        if X <= 2:
            count = X * 2
        else:
            count = X * 4
        single_dmg = engine.get_modified_spell_damage(run, self, single_dmg)
        for enemy in list(run.enemies):
            for _ in range(count):
                if enemy in run.enemies:
                    curr_idx = run.enemies.index(enemy)
                    engine._damage_target(run, f"e{curr_idx+1}", single_dmg, damage_type="true", card=self)
        from ...data.card_data import CARD_CONFIG
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(count=count)
        return f"释放了奥术洪流，对所有敌人造成了 {count} 次真实伤害。"

@register_card("arcane_barrier")
class ArcaneBarrierCard(Card):
    def execute(self, run, target, engine) -> str:
        X = run.node_data.get("last_x_cost_ba", 0)
        coef = 9 if self.upgraded else 6
        shield_val = X * coef
        engine._gain_shield(run, "p0", shield_val)
        bonus_msg = ""
        if X > 1:
            from ...data.buff_data import BUFF_CONFIG
            buff_info = BUFF_CONFIG.get("buffer", {})
            buff_name = buff_info.get("name", "缓冲")
            buff_desc = buff_info.get("desc", "")
            engine._add_buff_to(run.player, "buffer", buff_name, buff_desc, 1)
            bonus_msg = f" 🛡️ 并获得 1 层【{buff_name}】！"
        from ...data.card_data import CARD_CONFIG
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(shield=shield_val) + bonus_msg
        return f"凝聚了奥法屏障，获得了 {shield_val} 点护盾。" + bonus_msg

