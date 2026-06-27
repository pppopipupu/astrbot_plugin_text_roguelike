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
            if self.id == "abyss_altar" and self.upgraded:
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
        grid = engine._summon_minion(run, self.id, self.name, self.minion_hp, self.minion_atk, 0)
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
        if base_id.startswith("duel_"):
            base_id = base_id[5:]
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
                if b.id == buff_id:
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
            from ...models.state import ensure_card_state
            target_cid = ensure_card_state(run.player.hand[idx])
            val = 4 if self.upgraded else 3
            old_val = target_cid.replay
            new_val = old_val + val
            import copy
            new_cid = copy.copy(target_cid)
            new_cid.replay = new_val
            run.player.hand[idx] = new_cid
            card_name = ALL_CARDS.get(new_cid).name
            if old_val > 0:
                return f"使用了【{self.name}】。随机使手牌中的【{card_name}】获得了重放 {val} 效果（累计重放 {new_val}）。"
            else:
                return f"使用了【{self.name}】。随机使手牌中的【{card_name}】获得了重放 {val} 效果。"
        else:
            return f"使用了【{self.name}】，但手牌为空，未触发重放赋予效果。"

@register_card("neutral_omega")
class NeutralOmegaCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        import copy
        import random
        from .base import ALL_CARDS
        hand_copies = [copy.deepcopy(cid) for cid in p.hand]
        random.shuffle(hand_copies)
        
        for copy_cid in hand_copies:
            if engine.is_battle_won(run):
                break
            card_obj = ALL_CARDS.get(copy_cid)
            if not card_obj or getattr(card_obj, "unplayable", False):
                continue
            card_target = None
            if card_obj.type == "spell":
                p0_spells = {"first_aid", "get_ready", "adrenaline", "mana_potion", "mass_healing_word", "refresh_spirit", "shield", "misty_step", "arcane_intellect", "calculated_gamble", "time_warp", "time_stop", "archmage_wish"}
                if card_obj.id in p0_spells:
                    card_target = "p0"
                else:
                    card_target = engine._get_first_alive_enemy(run)
            extra_res = engine._execute_card_effect(run, card_obj, card_target)
            from ...models.events import CardPlayedEvent
            played_evt = CardPlayedEvent(run, card_obj, card_target, extra_res, is_extra=True)
            engine.event_bus.dispatch(played_evt)
            run.node_data.setdefault("extra_play_msgs", []).append(f" 🌀 [Omega 复制品打出] {played_evt.feedback}")
            if hasattr(card_obj, "execute_tags"):
                card_obj.execute_tags(run, card_target, engine)
                
        return "🌌 引导了【Omega】的终极涟漪！"

@register_card("discover")
class DiscoverCard(Card):
    def execute(self, run, target, engine) -> str:
        from .base import ALL_CARDS
        p = run.player
        if not p.exhaust_pile:
            return f"❌ 你的消耗堆中没有任何卡牌，【{self.name}】未能发掘出任何东西。"

        if target is not None:
            parts_str = str(target)
            if "," in parts_str:
                parts = parts_str.split(",")
            else:
                parts = parts_str.split()
            
            indices = []
            for p_str in parts:
                p_str = p_str.strip()
                if p_str.isdigit():
                    indices.append(int(p_str) - 1)
            
            valid_indices = [idx for idx in indices if 0 <= idx < len(p.exhaust_pile)]
            max_count = 2 if self.upgraded else 1
            valid_indices = valid_indices[:max_count]
            
            if valid_indices:
                valid_indices.sort(reverse=True)
                selected_names = []
                for idx in valid_indices:
                    cid = p.exhaust_pile.pop(idx)
                    p.hand.append(cid)
                    selected_names.append(ALL_CARDS[cid].name if cid in ALL_CARDS else "未知卡牌")
                selected_names.reverse()
                return f"✨ 你使用【{self.name}】发掘了消耗堆中的【{', '.join(selected_names)}】并加入了手牌。"
            else:
                return "❌ 提供的消耗堆序号不合法或消耗堆中没有对应的卡牌。"

        run.node_data.setdefault("state_stack", []).append({
            "type": "discover_selection",
            "count": 2 if self.upgraded else 1,
            "selected": []
        })
        exhaust_list = "\n".join(f"{i+1}. {ALL_CARDS[c].name}" for i, c in enumerate(p.exhaust_pile))
        return f"🔮 请选择一张卡牌发掘并加入手牌（使用 选择 <序号>）：\n{exhaust_list}"

@register_card("neutral_power_word_kill")
class NeutralPowerWordKillCard(Card):
    def execute(self, run, target, engine) -> str:
        name = engine._get_target_name(run, target)
        target_enemy = None
        if target and target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if 0 <= idx < len(run.enemies):
                    target_enemy = run.enemies[idx]
            except ValueError:
                pass
        
        threshold = 100 if self.upgraded else 60
        if target_enemy and target_enemy.hp < threshold:
            engine._damage_target(run, target, target_enemy.hp, damage_type="true", card=self)
            return f"你指着【{name}】吐露死亡真言：【律令死亡】！其身形瞬间枯萎，当场陨灭！"
        
        if self.upgraded and target_enemy:
            engine._damage_target(run, target, 40, damage_type="true", card=self)
            return f"❌ 律令未达致死判定条件，但【{name}】依然受到了 40 点时间的真实伤害！卡牌化作灰烬自毁。"
        
        return f"❌ 律令失败：目标生命值不低于 {threshold} 点，无法将其即死！卡牌化作灰烬自毁。"

@register_card("neutral_power_word_stun")
class NeutralPowerWordStunCard(Card):
    def execute(self, run, target, engine) -> str:
        name = engine._get_target_name(run, target)
        target_enemy = None
        if target and target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if 0 <= idx < len(run.enemies):
                    target_enemy = run.enemies[idx]
            except ValueError:
                pass
        
        threshold = 150 if self.upgraded else 100
        if target_enemy and target_enemy.hp < threshold:
            engine._add_buff_to(target_enemy, "stun", "单体晕眩", "下回合无法行动", 1)
            return f"你吐露震慑真言：【律令震慑】！【{name}】脑部剧震，陷入深度晕眩！"
        
        if self.upgraded and target_enemy:
            engine._damage_target(run, target, 15, damage_type="force", card=self)
            target_enemy.actions = max(0, target_enemy.actions - 1)
            return f"❌ 律令未达深度震慑条件，但【{name}】受到了 15 点力场伤害，且因受震慑其下回合动作点数减少 1A！"
            
        return f"❌ 律令失败：目标生命值不低于 {threshold} 点，不受震慑干扰！"

@register_card("neutral_power_word_pain")
class NeutralPowerWordPainCard(Card):
    def execute(self, run, target, engine) -> str:
        name = engine._get_target_name(run, target)
        target_enemy = None
        if target and target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if 0 <= idx < len(run.enemies):
                    target_enemy = run.enemies[idx]
            except ValueError:
                pass
        
        threshold = 180 if self.upgraded else 120
        bleed_layers = 4 if self.upgraded else 3
        weak_layers = 3 if self.upgraded else 2
        
        if target_enemy and target_enemy.hp < threshold:
            engine._add_buff_to(target_enemy, "bleed", "流血", "每回合开始受到4点真实伤害", bleed_layers)
            engine._add_buff_to(target_enemy, "weak", "虚弱", "造成的伤害减少50%", weak_layers)
            return f"你吐露痛苦真言：【律令痛苦】！【{name}】浑身皮肤崩裂，痛苦不堪，陷入 {bleed_layers} 层【流血】与 {weak_layers} 层【虚弱】状态！"
            
        if self.upgraded and target_enemy:
            engine._damage_target(run, target, 12, damage_type="slashing", card=self)
            return f"❌ 律令未达折磨判定条件，但你对【{name}】造成了 12 点物理挥砍伤害！"
            
        return f"❌ 律令失败：目标生命值不低于 {threshold} 点，顶住了痛苦折磨！"

@register_card("neutral_plane_shift")
class NeutralPlaneShiftCard(Card):
    def execute(self, run, target, engine) -> str:
        forbidden_stages = (32,) if self.upgraded else (25, 32)
        if run.player.stage in forbidden_stages:
            return "❌ 异界传送在此强力领主战中被神秘结界屏蔽了，你无法在这里传送脱逃！"
        
        run.enemies.clear()
        if self.upgraded:
            run.player.gp += 40
            return "🔮 你咏唱了【异界传送+】，张开空间裂缝使自己瞬间传送逃离战场！你凭借精妙的空间法术顺手带走了部分战场遗珍，获得了 40 点金币奖励！"
        else:
            run.node_data["no_reward"] = True
            return "🔮 你咏唱了【异界传送】，张开空间裂缝使自己瞬间传送逃离战场！由于你半途脱逃，你将无法获得这场战斗的任何金币和卡牌奖励！"

@register_card("neutral_emperor_eye")
class NeutralEmperorEyeCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        if target is not None:
            try:
                keep_idx = int(target)
                hand_idx = run.node_data.get("current_playing_card_hand_idx", 0) + 1
                if keep_idx == hand_idx:
                    return "❌ 不能选择正在被打出的霸瞳天星作为保留卡牌。"
                if keep_idx < hand_idx:
                    remaining_idx = keep_idx - 1
                else:
                    remaining_idx = keep_idx - 2
                if 0 <= remaining_idx < len(p.hand):
                    return engine.execute_emperor_eye_resolve(run, remaining_idx, self.upgraded)
                else:
                    return f"❌ 提供的手牌序号 {keep_idx} 超出范围。打出霸瞳天星前你共有 {len(p.hand) + 1} 张手牌。"
            except ValueError:
                return "❌ 参数必须为数字代表的手牌序号。"
        if not p.hand:
            return engine.execute_emperor_eye_resolve(run, -1, self.upgraded)
        run.node_data.setdefault("state_stack", []).append({
            "type": "overload_star_select",
            "upgraded": self.upgraded
        })
        from .base import ALL_CARDS
        hand_list = "\n".join(f"{i+1}. {ALL_CARDS[c].name}" for i, c in enumerate(p.hand))
        return f"👁️ 【霸瞳天星】已发动。请选择你要保留的手牌（输入 c <序号>，除此牌外的所有手牌都将被消耗）：\n{hand_list}"

@register_card("neutral_astral_strike")
class AstralStrikeCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        dmg = 36 if self.upgraded else 30
        if not target or not target.startswith("e"):
            return "❌ 请指定敌方目标（例如：p 卡牌序号 e1）。"
        res = engine.combat_resolver.damage_target(run, target, dmg, source="p0", damage_type="force")
        gem_msg = ""
        if self.upgraded:
            from ...data.gem_data import GEM_CONFIG
            import random
            gem_id = random.choice(list(GEM_CONFIG.keys()))
            gem_name = GEM_CONFIG[gem_id]["name"]
            run.node_data.setdefault("pending_gems", []).append(gem_id)
            gem_msg = f"\n💎 【星界坠击+】额外共鸣！你额外收获了一颗被虚空能量包裹的宝石【{gem_name}】，它将在战斗结束后供你进行镶嵌！"
        return f"你引导星辰砸落！{res}{gem_msg}"

@register_card("neutral_hero_anthem")
class HeroAnthemCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        shield = 10 if self.upgraded else 6
        p.shield += shield
        engine._draw_cards(p, 1, run)
        return f"你唱响了【英雄赞歌】，身体洋溢着金色的气场（获得了 {shield} 点护盾，并抽了 1 张牌）！"

@register_card("elder_guidance")
class ElderGuidanceCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        engine._add_buff_to(p, "all_resonance", "万物共振", "你的最终伤害呈指数翻倍增长", 1)
        removed = []
        for b in list(p.buffs):
            from ..buffs import is_debuff
            if is_debuff(b.id):
                p.buffs.remove(b)
                removed.append(b.name)
        engine._draw_cards(p, 3, run)
        clean_msg = f"，解除了你的【{'、'.join(removed)}】负面状态" if removed else ""
        return f"👴 向导长老指点迷津！你清空了所有杂念{clean_msg}，并连续抽取了 3 张卡牌！"

@register_card("ironclad_rampart")
class IroncladRampartCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        engine._add_buff_to(p, "all_resonance", "万物共振", "你的最终伤害呈指数翻倍增长", 1)
        p.shield += 30
        dmg = 15
        if not target or not target.startswith("e"):
            if run.enemies:
                target = "e1"
            else:
                return "❌ 没有可攻击的目标。"
        before_len = len(run.node_data.get("battle_logs", []))
        engine._damage_target(run, target, dmg, damage_type="bludgeoning", card=self)
        after_logs = run.node_data.get("battle_logs", [])
        dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
        return f"🔨 铁匠艾恩克拉德在战场上升起精钢壁垒！你获得了 30 点护盾，重锤砸落：{dmg_msg}"

@register_card("jack_brew")
class JackBrewCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        engine._add_buff_to(p, "all_resonance", "万物共振", "你的最终伤害呈指数翻倍增长", 1)
        engine._heal_target(run, "p0", 15)
        p.actions += 1
        p.bonus_actions += 1
        return f"🍺 酒保杰克递上一杯冰镇烈性黑麦酒！你一饮而尽，生命值恢复了 15 点，且感到浑身充满了力量（获得 1A 1BA 动作点）！"

@register_card("merchant_collection")
class MerchantCollectionCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        engine._add_buff_to(p, "all_resonance", "万物共振", "你的最终伤害呈指数翻倍增长", 1)
        from .base import ALL_CARDS
        card_pool = list(ALL_CARDS.keys())
        p_class = getattr(engine.save_manager.load_stats(run.user_id), "selected_class", "法师")
        target_color = "warrior" if p_class == "战士" else "wizard"
        from ...entities.cards.market import is_card_available
        stats = engine.save_manager.load_stats(run.user_id)
        class_cards = [
            cid for cid in card_pool
            if ALL_CARDS[cid].rarity in ("legendary", "mythic")
            and not cid.startswith("curse_")
            and not cid.startswith("duel_")
            and ALL_CARDS[cid].color == target_color
            and is_card_available(cid, stats)
        ]
        if not class_cards:
            class_cards = [
                cid for cid in card_pool
                if ALL_CARDS[cid].rarity in ("legendary", "mythic")
                and not cid.startswith("curse_")
                and not cid.startswith("duel_")
            ]
        import random
        chosen = random.sample(class_cards, min(2, len(class_cards)))
        added_names = []
        from ...models.state import CardState
        for cid in chosen:
            cstate = CardState(id=cid, upgraded=True)
            p.hand.append(cstate)
            added_names.append(ALL_CARDS[cid].name)
            run.node_data.setdefault("merchant_collection_free_cards", []).append(cid)
        return f"🃏 卡牌商人掏出他的神话珍藏！你将升级版的【{'】和【'.join(added_names)}】加入了手牌，且它们在本回合的消耗全部降为 0！"

@register_card("bard_epic")
class BardEpicCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        engine._add_buff_to(p, "all_resonance", "万物共振", "你的最终伤害呈指数翻倍增长", 1)
        engine._add_buff_to(p, "strength", "力量", "造成的伤害增加", 2)
        engine._add_buff_to(p, "double_tap_buff", "双发", "打出的物理伤害牌会额外打出 1 次", 1)
        return f"🎵 迷路的诗人为你高歌一曲英雄绝响之歌！歌声穿透灵魂，使你获得了 2 层【力量】与 1 层【双发】状态！"




