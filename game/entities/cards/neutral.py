from typing import Optional, List
from ...models.state import Card, AmuletState, MinionState
from ...data.card_data import CARD_CONFIG
from .registry import register_card

@register_card("dagger_throw")
@register_card("fire_bolt")
@register_card("quick_strike")
@register_card("agile_strike")
class SpellDamageCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, base_dmg, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, desc=desc)
        self.base_dmg = base_dmg

    def execute(self, run, target, engine) -> str:
        dmg = self.base_dmg
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
        name = engine._get_target_name(run, target)
        
        is_agile = run.node_data.get("agile_triggering", False)
        dtype = "true" if (self.id == "agile_strike+" and is_agile) else self.damage_type
        
        target_enemy = None
        if target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if 0 <= idx < len(run.enemies):
                    target_enemy = run.enemies[idx]
            except ValueError:
                pass
                
        engine._damage_target(run, target, dmg, damage_type=dtype, card=self)
        
        is_kill = False
        if target_enemy and (target_enemy not in run.enemies or target_enemy.hp <= 0):
            is_kill = True
            
        bonus_msg = ""
        if self.id == "dagger_throw+" and is_kill:
            run.player.actions += 1
            bonus_msg = " ✨ [击杀奖励] 获得了 1A 动作点！"
        elif self.id == "quick_strike+":
            for m in run.player.minions.values():
                m.atk += 1
            bonus_msg = " 🛡️ [迅捷打击+] 场上所有我方随从本回合攻击力 +1！"
        elif self.id == "agile_strike+" and is_agile:
            engine._draw_cards(run.player, 1, run)
            bonus_msg = " ⚡ [灵巧打击+] 抽了 1 张牌！"
            
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(target=name, dmg=dmg) + bonus_msg
        
        return f"使用了【{self.name}】，对【{name}】造成了 {dmg} 点伤害。" + bonus_msg

@register_card("first_aid")
class SpellHealCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, heal_amount, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, desc=desc)
        self.heal_amount = heal_amount

    def execute(self, run, target, engine) -> str:
        name = engine._get_target_name(run, target)
        engine._heal_target(run, target, self.heal_amount)
        
        shield_msg = ""
        if self.id == "first_aid+":
            run.player.shield += 2
            shield_msg = "，并获得了 2 点护盾"
            
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if self.id == "first_aid+":
            return f"为【{name}】恢复了 {self.heal_amount} 点生命值{shield_msg}。"
        if feedback_tmpl:
            return feedback_tmpl.format(target=name, heal_amount=self.heal_amount)
        return f"为【{name}】恢复了 {self.heal_amount} 点生命值。"

@register_card("get_ready")
class GetReadyCard(Card):
    def execute(self, run, target, engine) -> str:
        if self.upgraded:
            run.player.actions += 1
            run.player.bonus_actions += 1
            engine._draw_cards(run.player, 2, run)
            return "获得了 1A 1BA 并抽了 2 张牌。"
        else:
            run.player.bonus_actions += 2
            engine._draw_cards(run.player, 1, run)
            cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
            return cfg.get("feedback", "获得了 2BA 并抽了 1 张牌。")

@register_card("adrenaline")
class AdrenalineCard(Card):
    def execute(self, run, target, engine) -> str:
        if self.upgraded:
            run.player.actions += 1
            run.player.bonus_actions += 1
            engine._draw_cards(run.player, 1, run)
            run.player.hp -= 3
            return "获得了 1A 1BA 并抽了 1 张牌，失去了 3 点生命值。"
        else:
            run.player.actions += 1
            run.player.hp -= 2
            cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
            return cfg.get("feedback", "获得了 1A 并失去了 2 点生命值。")

@register_card("lucky_coin")
@register_card("thorns_necklace")
@register_card("ring_of_elements")
@register_card("arcane_crystal")
@register_card("mage_ward")
@register_card("void_beacon")
@register_card("abyss_altar")
@register_card("abyss_altar_awaken")
@register_card("abyss_altar_converge")
@register_card("abyss_altar_burst")
@register_card("abyss_altar_end")
class DeployAmuletCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, countdown, amulet_desc, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, countdown=countdown, desc=desc)
        self.amulet_desc = amulet_desc

    def execute(self, run, target, engine) -> str:
        grid = engine._get_free_grid(run.player)
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        if grid:
            cd = self.countdown
            if "ancient_keyring" in run.player.relics:
                import random
                if random.random() < 0.5:
                    cd = max(1, cd - 1)
            deploy_id = self.id
            deploy_name = self.name
            deploy_desc = self.amulet_desc
            if self.id == "abyss_altar+":
                deploy_id = "abyss_altar_awaken"
                aw_cfg = CARD_CONFIG.get("abyss_altar_awaken", {})
                deploy_name = aw_cfg.get("name", "苏醒的深渊祭坛")
                deploy_desc = aw_cfg.get("amulet_desc", "谢幕曲：在此格子部署【汇集的深渊祭坛】。")
            run.player.amulets[grid] = AmuletState(deploy_id, deploy_name, cd, deploy_desc)
            feedback_success = cfg.get("feedback_success", "将【{name}】部署到了格子 [{grid}]。")
            return feedback_success.format(name=self.name, grid=grid)
        return cfg.get("feedback_fail", "战场格子已满，部署失败。")

@register_card("minion_icerainboww")
@register_card("mercenary")
@register_card("shield_guard")
@register_card("find_familiar")
@register_card("arcane_golem")
@register_card("water_elemental")
@register_card("gate_guard")
class SummonMinionCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, minion_hp, minion_atk, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, desc=desc)
        self.minion_hp = minion_hp
        self.minion_atk = minion_atk

    def execute(self, run, target, engine) -> str:
        if self.id.startswith("minion_icerainboww"):
            from ...models.manager import SaveManager
            boss_cfg = SaveManager().load_admin_config()
            if not boss_cfg.get("icerainboww_enabled", True):
                return "❌ 该卡牌当前已被管理员禁用，无法使用。"
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        ba = 1 if self.id.startswith("arcane_golem") else 0
        grid = engine._summon_minion(run, self.id, self.name, self.minion_hp, self.minion_atk, ba)
        if grid:
            battlecry_msg = ""
            target_name = "无"
            if self.id == "mercenary+":
                chosen_target = target if (target and target.startswith("e")) else engine._get_first_alive_enemy(run)
                if chosen_target:
                    engine._damage_target(run, chosen_target, self.minion_atk, source=f"p{grid}", damage_type="attack")
                    tname = engine._get_target_name(run, chosen_target)
                    battlecry_msg = f"\n⚔️ [入场曲] 【雇佣兵+】立即攻击了【{tname}】，造成了 {self.minion_atk} 点伤害！"
            elif self.id == "shield_guard+":
                engine._gain_shield(run, "p0", 8)
                battlecry_msg = f"\n🛡️ [入场曲] 获得了 8 点入场曲护盾！"
            elif self.id == "minion_icerainboww+":
                engine._gain_shield(run, "p0", 8)
                for enemy in list(run.enemies):
                    engine._add_buff_to(enemy, "minor_vulnerable_cold", "轻度寒冷易伤", "受到的寒冷伤害增加 50%", 1)
                battlecry_msg = f"\n❄️ [入场曲] 获得了 8 点护盾，并使所有敌人受到 1 层轻度寒冷易伤！"
            elif self.id.startswith("gate_guard"):
                chosen_target = target if (target and target.startswith("e")) else engine._get_first_alive_enemy(run)
                if chosen_target:
                    try:
                        f_idx = int(chosen_target.replace("e", "")) - 1
                        if 0 <= f_idx < len(run.enemies):
                            target_name = run.enemies[f_idx].name
                            engine._add_buff_to(run.enemies[f_idx], "stun", "眩晕", "无法行动", 1)
                            battlecry_msg = f"\n🚪 [入场曲] 使【{target_name}】眩晕了 1 回合！"
                    except ValueError:
                        pass
                
            feedback_success = cfg.get("feedback_success", "在格子 [{grid}] 召唤了【{name}】。")
            return feedback_success.format(grid=grid, name=self.name, target=target_name) + battlecry_msg
        return cfg.get("feedback_fail", "战场已满，召唤失败。")

@register_card("quicken")
@register_card("spell_surge")
@register_card("arcane_charge")
class AbilityCard(Card):
    def execute(self, run, target, engine) -> str:
        from ...data.buff_data import BUFF_CONFIG
        base_id = self.id.split(":replay:")[0].split(":fragile:")[0].rstrip("+")
        buff_info = BUFF_CONFIG.get(base_id, {})
        buff_name = buff_info.get("name", self.name.split(" (重放 ")[0].split(" (易碎 ")[0])
        buff_desc = buff_info.get("desc", "")
        engine._add_buff_to(run.player, base_id, buff_name, buff_desc)
        
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(name=self.name)
        return f"使用了【{self.name}】。"

@register_card("tactical_focus")
class TacticalFocusCard(Card):
    def execute(self, run, target, engine) -> str:
        draw_count = 5 if self.upgraded else 3
        engine._draw_cards(run.player, draw_count, run)
        from ...data.buff_data import BUFF_CONFIG
        buff_info = BUFF_CONFIG.get("tactical_focus", {})
        buff_name = buff_info.get("name", "无法抽牌")
        buff_desc = buff_info.get("desc", "本回合无法再抽牌")
        engine._add_buff_to(run.player, "tactical_focus", buff_name, buff_desc)
        cfg = CARD_CONFIG.get("tactical_focus", {})
        feedback_tmpl = cfg.get("feedback", "使用了【{name}】，免费抽了 {draw_count} 张牌，但本回合无法再抽牌。")
        return feedback_tmpl.format(name=self.name, draw_count=draw_count)

@register_card("iron_will")
class IronWillCard(Card):
    def execute(self, run, target, engine) -> str:
        buff_id = "iron_will+" if self.upgraded else "iron_will"
        buff_name = "钢铁意志+" if self.upgraded else "钢铁意志"
        buff_desc = "最大生命上限增加 15 并回复 15 生命，治疗翻倍" if self.upgraded else "最大生命上限增加 10 并回复 10 生命"
        engine._add_buff_to(run.player, buff_id, buff_name, buff_desc, 1, None)
        heal_val = 15 if self.upgraded else 10
        engine._heal_target(run, "p0", heal_val)
        if self.upgraded:
            for b in run.player.buffs:
                if b.id == self.id:
                    b.stacks2 = 2
                    break
        shield_msg = ""
        if self.upgraded:
            engine._gain_shield(run, "p0", 8)
            shield_msg = "，并获得了 8 点护盾"
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        if self.upgraded:
            return f"使用了【钢铁意志+】，获得了【钢铁意志+】buff（最大生命上限增加 15 并回复 15 生命，治疗翻倍）{shield_msg}。"
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(name=self.name)
        return f"使用了【钢铁意志】，获得了【钢铁意志】buff（最大生命上限增加 10 并回复 10 生命，可叠加）。"

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
        if self.upgraded:
            run.player.actions += 1
            engine._draw_cards(run.player, 2, run)
            return "饮用了【魔力药水+】，获得了 1A 并抽了 2 张牌。"
        else:
            run.player.bonus_actions += 1
            engine._draw_cards(run.player, 1, run)
            cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
            return cfg.get("feedback", "饮用了【魔力药水】，获得了 1BA 并抽了 1 张牌。")

@register_card("mass_healing_word")
class MassHealingWordCard(Card):
    def execute(self, run, target, engine) -> str:
        heal_val = getattr(self, "heal_amount", 8)
        engine._heal_target(run, "p0", heal_val)
        for grid in list(run.player.minions.keys()):
            engine._heal_target(run, f"p{grid}", heal_val)
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(heal_amount=heal_val)
        return f"使用了【{self.name}】，为自己和所有随从恢复了 {heal_val} 点生命值。"

@register_card("refresh_spirit")
class RefreshSpiritCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        exhausted_count = 0
        remaining_hand = []
        from ...models.events import CardExhaustEvent
        from .base import ALL_CARDS
        for cid in p.hand:
            card_obj = ALL_CARDS.get(cid)
            if card_obj and card_obj.type != "minion":
                p.exhaust_pile.append(cid)
                engine._log_event(run, f"✨ [消耗] 【{card_obj.name}】已被移入消耗堆。")
                exhaust_evt = CardExhaustEvent(run, cid, "effect")
                engine.event_bus.dispatch(exhaust_evt)
                exhausted_count += 1
            else:
                remaining_hand.append(cid)
        p.hand = remaining_hand
        
        shield_mult = 8 if self.upgraded else 6
        shield_to_gain = exhausted_count * shield_mult
        if shield_to_gain > 0:
            engine._gain_shield(run, "p0", shield_to_gain)
            
        bonus_msg = ""
        if self.upgraded and exhausted_count >= 3:
            run.player.actions += 1
            bonus_msg = " ⚡ [重振精神+] 获得了 1A 动作点！"
            
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if self.upgraded:
            return f"使用了【{self.name}】，消耗了 {exhausted_count} 张非随从牌，获得了 {shield_to_gain} 点护盾。{bonus_msg}"
        if feedback_tmpl:
            return feedback_tmpl.format(exhaust_count=exhausted_count, shield_amount=shield_to_gain)
        return f"使用了【{self.name}】，消耗了 {exhausted_count} 张非随从牌，获得了 {shield_to_gain} 点护盾。"

@register_card("key_resonance")
class KeyResonanceCard(Card):
    def execute(self, run, target, engine) -> str:
        X = run.node_data.get("last_x_cost_a", 0)
        logs = []
        for _ in range(X):
            msg = engine.combat_resolver.recall_dead_minion(run, 10)
            logs.append(msg)
        stats = engine.save_manager.load_stats(run.user_id)
        has_key = getattr(stats, "unlocked_gatekey", False)
        damage_amount = 0
        if has_key and X > 0:
            base_dmg = 9 if self.upgraded else 6
            total_dmg = X * base_dmg
            for idx in range(len(run.enemies) - 1, -1, -1):
                engine._damage_target(run, f"e{idx+1}", total_dmg, damage_type="force", card=self)
            damage_amount = total_dmg
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        res_str = ""
        if feedback_tmpl:
            res_str = feedback_tmpl.format(recall_count=X, damage_amount=damage_amount)
        else:
            res_str = f"产生了秘钥共鸣，进行了 {X} 次死者召回，并造成了 {damage_amount} 点力场伤害。"
        if logs:
            res_str += "\n召回详情：\n" + "\n".join(logs)
        return res_str

@register_card("master_key")
class MasterKeyCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        reduction = 3 if self.upgraded else 2
        from ..amulets import ALL_AMULETS
        lw_logs = []
        for ak, av in list(p.amulets.items()):
            av.countdown -= reduction
            if av.countdown <= 0:
                del p.amulets[ak]
                p.minion_graveyard.append(av.id)
                base_id = av.id[:-1] if av.id.endswith("+") else av.id
                template = ALL_AMULETS.get(base_id)
                lw_msg = ""
                if template:
                    is_upgraded = av.id.endswith("+")
                    lw_msg = template.on_death(run, ak, is_upgraded, engine)
                if lw_msg:
                    lw_logs.append(f"🔔 [谢幕曲] 我方【{av.name}】吟唱结束进入墓地：{lw_msg}")
        if self.upgraded:
            engine._draw_cards(p, 1, run)
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        res_str = cfg.get("feedback", "使用了万能钥匙，所有护符的吟唱时间减少了。")
        if lw_logs:
            res_str += "\n" + "\n".join(lw_logs)
        return res_str

@register_card("ancient_wisdom")
class AncientWisdomCard(Card):
    def execute(self, run, target, engine) -> str:
        X = run.node_data.get("last_x_cost_a", 0)
        Y = run.node_data.get("last_x_cost_ba", 0)
        coef = 4 if self.upgraded else 3
        shield_val = Y * coef
        engine._gain_shield(run, "p0", shield_val)
        if X > 0:
            buff_name = "古老智慧+" if self.upgraded else "古老智慧"
            buff_desc = "打中立卡时，获得 3 点护盾（每层）" if self.upgraded else "打中立卡时，获得 2 点护盾（每层）"
            engine._add_buff_to(run.player, "ancient_wisdom_buff", buff_name, buff_desc, X)
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(shield=shield_val, stacks=X)
        return f"获得了 {shield_val} 点护盾与 {X} 层古老智慧形态。"

@register_card("unmined_gem")
class UnminedGemCard(Card):
    def execute(self, run, target, engine) -> str:
        import random
        from .base import ALL_CARDS
        if run.player.hand:
            idx = random.randint(0, len(run.player.hand) - 1)
            target_cid = run.player.hand[idx]
            val = 4 if self.upgraded else 3
            import re
            if ":replay:" in target_cid:
                match = re.search(r":replay:(\d+)", target_cid)
                if match:
                    old_val = int(match.group(1))
                    new_val = old_val + val
                    new_cid = re.sub(r":replay:\d+", f":replay:{new_val}", target_cid)
                else:
                    new_cid = f"{target_cid}:replay:{val}"
                    new_val = val
            else:
                new_cid = f"{target_cid}:replay:{val}"
                new_val = val
            run.player.hand[idx] = new_cid
            card_name = ALL_CARDS.get(new_cid).name
            if ":replay:" in target_cid:
                return f"使用了【{self.name}】。随机使手牌中的【{card_name}】获得了重放 {val} 效果（累计重放 {new_val}）。"
            else:
                return f"使用了【{self.name}】。随机使手牌中的【{card_name}】获得了重放 {val} 效果。"
        else:
            return f"使用了【{self.name}】，但手牌为空，未触发重放赋予效果。"

