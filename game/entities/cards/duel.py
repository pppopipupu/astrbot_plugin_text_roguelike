from typing import Optional
from ...models.state import Card, BuffState, AmuletState
from .duel_registry import register_duel_card

class DuelGenericCard(Card):
    def execute(self, run, target, engine) -> str:
        try:
            from ...data.duel_card_data import DUEL_CARD_CONFIG
        except ImportError:
            from astrbot_plugin_text_roguelike.game.data.duel_card_data import DUEL_CARD_CONFIG
        cfg = DUEL_CARD_CONFIG.get(self.id, {})
        face_target = cfg.get("face_target", True)
        is_damage = ("base_dmg" in cfg or "damage" in cfg or "damage_type" in cfg)
        
        if is_damage and not face_target:
            if target == "e1":
                return "❌ 该卡牌只能以随从为目标"
                
        dmg_val = cfg.get("base_dmg", cfg.get("damage", 0))
        if dmg_val > 0:
            dtype = cfg.get("damage_type", "effect")
            engine._damage_target(run, target, dmg_val, damage_type=dtype, card=self)
            
        shield_val = cfg.get("shield", 0)
        if shield_val > 0:
            engine._gain_shield(run, "p0", shield_val)
            
        heal_val = cfg.get("heal_amount", 0)
        if heal_val > 0:
            engine._heal_target(run, "p0", heal_val)
            
        draw_val = cfg.get("draw", 0)
        if draw_val > 0:
            engine._draw_cards(run.player, draw_val, run, ignore_focus=True)
            
        minion_hp = cfg.get("minion_hp", 0)
        if minion_hp > 0:
            minion_atk = cfg.get("minion_atk", 1)
            minion_id = self.id.replace("duel_", "")
            engine._summon_minion(run, minion_id, self.name, minion_hp, minion_atk, 0)
            
        if self.type == "amulet":
            grid = engine._get_free_grid(run.player)
            if grid:
                cd = cfg.get("countdown", self.countdown)
                run.player.amulets[grid] = AmuletState(self.id, self.name, cd, cfg.get("amulet_desc", self.desc))
            
        return ""

@register_duel_card("duel_time_warp")
class DuelTimeWarp(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        p.draw_pile.extend(p.discard_pile)
        p.draw_pile.extend(p.hand)
        p.discard_pile.clear()
        p.hand.clear()
        import random
        random.shuffle(p.draw_pile)
        before = len(p.hand)
        engine._draw_cards(p, 12, run, ignore_focus=True)
        after = len(p.hand)
        draw_count = after - before
        msg = f"时光倒流！已将所有卡牌重新洗回抽牌堆，重新抽取了 {draw_count} 张牌。"
        if self.upgraded:
            p.actions += 1
            p.bonus_actions += 1
            engine._add_buff_to(p, "time_warp_spell_boost", "时空强化", "本回合所有法术伤害 +2", 1)
            msg = f"时光倒流！已将所有卡牌重新洗回抽牌堆，重新抽取了 {draw_count} 张牌。玩家额外获得 1A 1BA，且本回合所有法术伤害 +2。"
        run.node_data.setdefault("battle_logs", []).append(msg)
        return ""

@register_duel_card("duel_unmined_gem")
class DuelUnminedGem(Card):
    def execute(self, run, target, engine) -> str:
        import random
        p = run.player
        if p.hand:
            idx = random.randint(0, len(p.hand) - 1)
            target_cid = p.hand[idx]
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
            p.hand[idx] = new_cid
            
            from .duel import ALL_DUEL_CARDS
            card_name = ALL_DUEL_CARDS[new_cid].name
            if ":replay:" in target_cid:
                msg = f"使用了【未掘宝石】。随机使手牌中的【{card_name}】获得了重放 {val} 效果（累计重放 {new_val}）。"
            else:
                msg = f"使用了【未掘宝石】。随机使手牌中的【{card_name}】获得了重放 {val} 效果。"
            run.node_data.setdefault("battle_logs", []).append(msg)
        return ""

@register_duel_card("duel_body_slam")
class DuelBodySlam(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        shield_val = p.shield
        damage = shield_val
        if self.upgraded:
            damage = int(shield_val * 1.5)
        engine._damage_target(run, target, damage, damage_type="slashing", card=self)
        return ""

@register_duel_card("duel_warrior_bash")
class DuelWarriorBash(Card):
    def execute(self, run, target, engine) -> str:
        try:
            from ...data.duel_card_data import DUEL_CARD_CONFIG
        except ImportError:
            from astrbot_plugin_text_roguelike.game.data.duel_card_data import DUEL_CARD_CONFIG
        cfg = DUEL_CARD_CONFIG.get(self.id, {})
        damage = cfg.get("base_dmg", cfg.get("damage", 8))
        engine._damage_target(run, target, damage, damage_type="bludgeoning", card=self)
        
        from ...core.duel.observers import get_entity_by_ref
        tgt_entity = get_entity_by_ref(run, target)
        if tgt_entity:
            layers = 3 if self.upgraded else 2
            engine._add_buff_to(tgt_entity, "vulnerable", "易伤", "受到的伤害增加 50%", layers)
        return ""

@register_duel_card("duel_warrior_anger")
class DuelWarriorAnger(Card):
    def execute(self, run, target, engine) -> str:
        try:
            from ...data.duel_card_data import DUEL_CARD_CONFIG
        except ImportError:
            from astrbot_plugin_text_roguelike.game.data.duel_card_data import DUEL_CARD_CONFIG
        cfg = DUEL_CARD_CONFIG.get(self.id, {})
        damage = cfg.get("base_dmg", cfg.get("damage", 4))
        engine._damage_target(run, target, damage, damage_type="slashing", card=self)
        run.player.discard_pile.append("duel_warrior_anger" + ("+" if self.upgraded else ""))
        return ""

@register_duel_card("duel_calculated_gamble")
class DuelCalculatedGamble(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        hand_len = len(p.hand)
        p.discard_pile.extend(p.hand)
        p.hand.clear()
        draw_count = hand_len + (1 if self.upgraded else 0)
        engine._draw_cards(p, draw_count, run, ignore_focus=True)
        msg = f"使用了【计算下注】。丢弃了所有手牌，并重新抽取了 {draw_count} 张牌。"
        run.node_data.setdefault("battle_logs", []).append(msg)
        return ""

@register_duel_card("duel_double_tap")
class DuelDoubleTap(Card):
    def execute(self, run, target, engine) -> str:
        stacks = 2 if self.upgraded else 1
        engine._add_buff_to(run.player, "double_tap_buff", "双发", "下一次物理伤害卡将触发额外打出", stacks)
        return ""

@register_duel_card("duel_arcane_torrent")
class DuelArcaneTorrent(Card):
    def execute(self, run, target, engine) -> str:
        X = run.node_data.get("last_x_cost_a", 0)
        single_dmg = 4 if self.upgraded else 3
        if X <= 2:
            count = X * 2
        else:
            count = X * 4
        for idx in range(len(run.enemies)):
            enemy = run.enemies[idx]
            if enemy.hp > 0:
                for _ in range(count):
                    engine._damage_target(run, f"e{idx+1}", single_dmg, damage_type="true", card=self)
        return ""

@register_duel_card("duel_quest_temporal_mystery")
class DuelQuestTemporalMystery(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["temporal_quest_progress"] = 0
        engine._add_buff_to(run.player, "temporal_quest", "时序之谜", "单回合使用4张法术牌(0/4)")
        return "🔮 [任务] 时序之谜已打出！"

@register_duel_card("duel_quest_fire_trial")
class DuelQuestFireTrial(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["fire_quest_progress"] = 0
        engine._add_buff_to(run.player, "fire_quest", "火焰审判", "对敌方领主造成法伤(0/30)")
        return "🔥 [任务] 火焰审判已打出！"

@register_duel_card("duel_quest_ancient_resonance")
class DuelQuestAncientResonance(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["ancient_quest_progress"] = 0
        engine._add_buff_to(run.player, "ancient_quest", "远古共鸣", "部署3个护符(0/3)")
        return "🔔 [任务] 远古共鸣已打出！"

@register_duel_card("duel_quest_master_of_arms")
class DuelQuestMasterOfArms(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["arms_quest_progress"] = 0
        engine._add_buff_to(run.player, "arms_quest", "兵器大师", "使用5张物理伤害牌(0/5)")
        return "🗡️ [任务] 兵器大师已打出！"

@register_duel_card("duel_quest_unbreakable_wall")
class DuelQuestUnbreakableWall(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["wall_quest_progress"] = 0
        engine._add_buff_to(run.player, "wall_quest", "不落坚壁", "护盾值达到20点(0/20)")
        return "🛡️ [任务] 不落坚壁已打出！"

@register_duel_card("duel_quest_bloody_fury")
class DuelQuestBloodyFury(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["fury_quest_progress"] = 0
        engine._add_buff_to(run.player, "fury_quest", "浴血狂暴", "生命值低于25点(0/1)")
        return "🩸 [任务] 浴血狂暴已打出！"

@register_duel_card("duel_reward_temporal_distortion")
class DuelRewardTemporalDistortion(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["extra_turns_left"] = run.node_data.get("extra_turns_left", 0) + 1
        return "⏳ [时序扭曲] 获得了 1 个额外回合！"

@register_duel_card("duel_reward_super_fireball")
class DuelRewardSuperFireball(Card):
    def execute(self, run, target, engine) -> str:
        engine._damage_target(run, target, 25, damage_type="fire", card=self)
        return ""

@register_duel_card("duel_reward_ancient_resonance")
class DuelRewardAncientResonance(Card):
    def execute(self, run, target, engine) -> str:
        try:
            from ...data.amulet_data import AMULET_CONFIG
        except ImportError:
            from astrbot_plugin_text_roguelike.game.data.amulet_data import AMULET_CONFIG
        p = run.player
        triggered = []
        for ak, av in list(p.amulets.items()):
            del p.amulets[ak]
            p.minion_graveyard.append(av.id)
            base_id = av.id[:-1] if av.id.endswith("+") else av.id
            if base_id.startswith("duel_"):
                base_id = base_id[5:]
            cfg = AMULET_CONFIG.get(base_id)
            if cfg:
                lw_msg = ""
                is_upgraded = av.id.endswith("+")
                dmg_val = cfg.get("damage", 0)
                if dmg_val > 0:
                    if is_upgraded:
                        dmg_val += 3
                    opp_target = engine._get_first_alive_enemy(run)
                    engine._damage_target(run, opp_target, dmg_val, damage_type="thunder")
                    lw_msg = f"对敌方造成了 {dmg_val} 点雷鸣伤害"
                heal_val = cfg.get("heal", 0)
                if heal_val > 0:
                    if is_upgraded:
                        heal_val += 2
                    engine._heal_target(run, "p0", heal_val)
                    lw_msg = f"玩家恢复了 {heal_val} 点生命值"
                shield_val = cfg.get("shield", 0)
                if shield_val > 0:
                    if is_upgraded:
                        shield_val += 2
                    engine._gain_shield(run, "p0", shield_val)
                    lw_msg = f"玩家获得了 {shield_val} 点护盾"
                if lw_msg:
                    triggered.append(f"【{av.name}】:{lw_msg}")
        return "🔔 [秘钥绽放] " + "，".join(triggered)

@register_duel_card("duel_reward_master_blade")
class DuelRewardMasterBlade(Card):
    def execute(self, run, target, engine) -> str:
        engine._damage_target(run, target, 22, damage_type="slashing", card=self)
        return ""

@register_duel_card("duel_reward_wall_of_sighs")
class DuelRewardWallOfSighs(Card):
    def execute(self, run, target, engine) -> str:
        engine._gain_shield(run, "p0", 15)
        run.player.max_hp += 15
        run.player.hp += 15
        return "🛡️ [叹息之墙] 获得了 15 点护盾，最大生命值上限提升了 15 点！"

@register_duel_card("duel_reward_fury")
class DuelRewardFury(Card):
    def execute(self, run, target, engine) -> str:
        engine._add_buff_to(run.player, "duel_fury_buff", "狂怒", "物理伤害额外加 6", 6)
        return "🩸 [狂暴] 获得了狂怒 Buff，物理伤害永久 +6！"

@register_duel_card("duel_meteor_swarm")
class DuelMeteorSwarm(Card):
    def execute(self, run, target, engine) -> str:
        import random
        num_dice = 8 if self.upgraded else 6
        dice_results = [random.randint(1, 6) for _ in range(num_dice)]
        dmg = sum(dice_results)
        extra_true_dmg = sum(2 for d in dice_results if d == 6) if self.upgraded else 0
        engine._damage_target(run, "e1", dmg, damage_type="fire", card=self)
        if extra_true_dmg > 0:
            engine._damage_target(run, "e1", extra_true_dmg, damage_type="true", card=self)
        p2 = run.player2
        for gid, m in list(p2.minions.items()):
            t_ref = f"e{int(gid)+1}"
            engine._damage_target(run, t_ref, dmg, damage_type="fire", card=self)
            if extra_true_dmg > 0:
                engine._damage_target(run, t_ref, extra_true_dmg, damage_type="true", card=self)
        if self.upgraded:
            return f"释放流星爆！对所有敌方角色造成了 {dmg} 点火焰伤害，并因大骰子额外造成 {extra_true_dmg} 点真实伤害。"
        return f"释放流星爆！对所有敌方角色造成了 {dmg} 点火焰伤害。"

@register_duel_card("duel_doomsday_judgment")
class DuelDoomsdayJudgment(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 18 if self.upgraded else 12
        engine._add_buff_to(run.player2, "stun", "眩晕", "无法行动", 1)
        engine._damage_target(run, "e1", dmg, damage_type="necrotic", card=self)
        p2 = run.player2
        for gid, m in list(p2.minions.items()):
            t_ref = f"e{int(gid)+1}"
            engine._add_buff_to(m, "stun", "眩晕", "无法行动", 1)
            engine._damage_target(run, t_ref, dmg, damage_type="necrotic", card=self)
        return f"释放末日审判！对所有敌方角色造成了 {dmg} 点黯蚀伤害并眩晕他们一回合。"

@register_duel_card("duel_glacier_tempest")
class DuelGlacierTempest(Card):
    def execute(self, run, target, engine) -> str:
        base_dmg = 12 if self.upgraded else 8
        total_dmg = 0
        engine._damage_target(run, "e1", base_dmg, damage_type="cold", card=self)
        total_dmg += base_dmg
        p2 = run.player2
        for gid, m in list(p2.minions.items()):
            t_ref = f"e{int(gid)+1}"
            engine._damage_target(run, t_ref, base_dmg, damage_type="cold", card=self)
            total_dmg += base_dmg
        shield_msg = ""
        if run.player.minions and total_dmg > 0:
            shield_gain = total_dmg // 2
            engine._gain_shield(run, "p0", shield_gain)
            shield_msg = f"，并获得了 {shield_gain} 点护盾"
        return f"释放了极寒风暴！对所有敌方角色造成了 {base_dmg} 点冰霜伤害{shield_msg}。"

@register_duel_card("duel_frost_nova")
class DuelFrostNova(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 14 if self.upgraded else 10
        vuln_stacks = 3 if self.upgraded else 2
        engine._damage_target(run, "e1", dmg, damage_type="cold", card=self)
        engine._add_buff_to(run.player2, "minor_vulnerable_cold", "轻度寒冷易伤", "受到的寒冷伤害增加 50%", vuln_stacks)
        engine._add_buff_to(run.player2, "stun", "眩晕", "无法行动", 1)
        p2 = run.player2
        for gid, m in list(p2.minions.items()):
            t_ref = f"e{int(gid)+1}"
            engine._damage_target(run, t_ref, dmg, damage_type="cold", card=self)
            engine._add_buff_to(m, "minor_vulnerable_cold", "轻度寒冷易伤", "受到的寒冷伤害增加 50%", vuln_stacks)
            engine._add_buff_to(m, "stun", "眩晕", "无法行动", 1)
        return f"释放霜冻新星！对所有敌方角色造成了 {dmg} 点冰霜伤害且被施加 {vuln_stacks} 层寒冷易伤与眩晕。"

@register_duel_card("duel_abyss_collapse")
class DuelAbyssCollapse(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 24 if self.upgraded else 18
        is_p2_stunned = any(b.id == "stun" for b in run.player2.buffs)
        p2_dmg = dmg * 2 if is_p2_stunned else dmg
        engine._damage_target(run, "e1", p2_dmg, damage_type="necrotic", card=self)
        p2 = run.player2
        for gid, m in list(p2.minions.items()):
            t_ref = f"e{int(gid)+1}"
            is_stunned = any(b.id == "stun" for b in m.buffs)
            m_dmg = dmg * 2 if is_stunned else dmg
            engine._damage_target(run, t_ref, m_dmg, damage_type="necrotic", card=self)
        return f"释放深渊崩塌！对所有敌方角色造成了黯蚀伤害（被眩晕目标受到双倍伤害）。"

@register_duel_card("duel_shockwave")
class DuelShockwave(Card):
    def execute(self, run, target, engine) -> str:
        stacks = 3 if self.upgraded else 2
        engine._add_buff_to(run.player2, "minor_vulnerable", "轻度易伤", "受到的所有类型伤害增加 50%", stacks)
        engine._add_buff_to(run.player2, "weak", "虚弱", "造成的物理伤害减少 3 点", stacks)
        p2 = run.player2
        for gid, m in list(p2.minions.items()):
            engine._add_buff_to(m, "minor_vulnerable", "轻度易伤", "受到的所有类型伤害增加 50%", stacks)
            engine._add_buff_to(m, "weak", "虚弱", "造成的物理伤害减少 3 点", stacks)
        return f"释放了【震荡波】，对所有敌方角色施加了 {stacks} 层【轻度易伤】和【虚弱】。"

@register_duel_card("duel_mana_overload")
class DuelManaOverload(Card):
    def execute(self, run, target, engine) -> str:
        if target == "e1" or not target or not target.startswith("e"):
            return "❌ 该卡牌只能以随从为目标"
        p2 = run.player2
        try:
            gid = str(int(target[1:]) - 1)
        except ValueError:
            return "❌ 无效的目标格子"
        if gid not in p2.minions:
            return "❌ 目标格子没有随从"
        m = p2.minions[gid]
        p = run.player
        base_dmg = 10
        is_double = (p.bonus_actions == 0)
        dmg = base_dmg * 2 if is_double else base_dmg
        engine._damage_target(run, target, dmg, damage_type="effect", card=self)
        is_killed = (m.hp <= 0 or gid not in p2.minions)
        ba_msg = ""
        if is_killed:
            p.bonus_actions += 2
            ba_msg = "，并成功击杀目标，获得 2BA"
        double_msg = "（触发翻倍）" if is_double else ""
        return f"使用了【能量逆载】{double_msg}对随从造成了 {dmg} 点伤害{ba_msg}。"

@register_duel_card("duel_destiny_scales")
class DuelDestinyScales(Card):
    def execute(self, run, target, engine) -> str:
        if target == "e1" or not target or not target.startswith("e"):
            return "❌ 该卡牌只能以随从为目标"
        p2 = run.player2
        try:
            gid = str(int(target[1:]) - 1)
        except ValueError:
            return "❌ 无效的目标格子"
        if gid not in p2.minions:
            return "❌ 目标格子没有随从"
        m = p2.minions[gid]
        old_atk = m.atk
        old_hp = m.hp
        m.atk = old_hp
        m.hp = old_atk
        if m.hp > m.max_hp:
            m.hp = m.max_hp
        has_stun = any(b.id == "stun" for b in m.buffs)
        has_vuln = any(b.id == "vulnerable" or b.id == "minor_vulnerable" for b in m.buffs)
        bonus_msg = ""
        if has_stun or has_vuln:
            engine._damage_target(run, target, 8, damage_type="true", card=self)
            engine._draw_cards(run.player, 1, run, ignore_focus=True)
            bonus_msg = "，且由于目标处于负面状态，额外对其造成 8 点真伤并抽了 1 张牌"
        return f"使用了【命运天平】，将随从的攻防对调为 {m.atk}/{m.hp}{bonus_msg}。"

@register_duel_card("duel_ancient_blessing")
class DuelAncientBlessing(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        minions_count = len(p.minions)
        if minions_count == 0:
            engine._draw_cards(p, 2, run, ignore_focus=True)
            return "使用了【古老祈福】，我方场上无随从，触发兜底效果：抽取了 2 张牌。"
        if minions_count > 2:
            for gid, m in list(p.minions.items()):
                m.atk += 2
                m.hp += 2
                m.max_hp += 2
            engine._gain_shield(run, "p0", 8)
            return "使用了【古老祈福】，我方拥有多于 2 个随从，触发群体强化：所有随从获得+2/+2，且玩家获得 8 点护盾。"
        import random
        gid = random.choice(list(p.minions.keys()))
        m = p.minions[gid]
        m.atk += 2
        m.hp += 2
        m.max_hp += 2
        return f"使用了【古老祈福】，随机强化了随从【{m.name}】（+2/+2）。"

@register_duel_card("duel_storm_barrier")
class DuelStormBarrier(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        p2 = run.player2
        shield_val = 12
        is_low_hp = (p.hp < 80)
        if is_low_hp:
            shield_val += 8
        engine._gain_shield(run, "p0", shield_val)
        storm_msg = ""
        if p2.minions:
            import random
            gid = random.choice(list(p2.minions.keys()))
            m = p2.minions[gid]
            engine._damage_target(run, f"e{int(gid)+1}", 6, damage_type="thunder", card=self)
            engine._add_buff_to(m, "weak", "虚弱", "造成的物理伤害减少 3 点", 2)
            storm_msg = f"，且对敌方随从【{m.name}】造成 6 点雷鸣伤害并施加 2 层虚弱"
        hp_msg = "（触发低血量强化）" if is_low_hp else ""
        return f"使用了【雷雨屏障】{hp_msg}，获得了 {shield_val} 点护盾{storm_msg}。"

class DuelCardRegistryDict(dict):
    def _lazy_load_card(self, key):
        from ...data.duel_card_data import DUEL_CARD_CONFIG
        if key in DUEL_CARD_CONFIG:
            cfg = DUEL_CARD_CONFIG[key]
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
            
            from ...models.state import Card
            from .duel_registry import DUEL_CARD_CLASS_REGISTRY
            import inspect
            
            if key in DUEL_CARD_CLASS_REGISTRY:
                cls, decorator_kwargs = DUEL_CARD_CLASS_REGISTRY[key]
            else:
                orig_key = key.replace("duel_", "")
                try:
                    from .registry import CARD_CLASS_REGISTRY
                except ImportError:
                    from astrbot_plugin_text_roguelike.game.entities.cards.registry import CARD_CLASS_REGISTRY
                if orig_key in CARD_CLASS_REGISTRY:
                    cls, decorator_kwargs = CARD_CLASS_REGISTRY[orig_key]
                else:
                    cls = DuelGenericCard
                    decorator_kwargs = {}
                
            inst_kwargs = {
                "id": key,
                "name": name,
                "color": color,
                "type": ctype,
                "cost_a": cost_a,
                "cost_ba": cost_ba,
                "desc": desc,
            }
            for prop in ("base_dmg", "heal_amount", "countdown", "amulet_desc", "minion_hp", "minion_atk", "exhaust", "damage_type"):
                if prop in cfg:
                    inst_kwargs[prop] = cfg[prop]
            if "amulet_desc" not in inst_kwargs:
                inst_kwargs["amulet_desc"] = desc
            inst_kwargs.update(decorator_kwargs)
            
            sig = inspect.signature(cls.__init__)
            has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            if has_kwargs:
                filtered = inst_kwargs
            else:
                filtered = {k: v for k, v in inst_kwargs.items() if k in sig.parameters}
                
            inst = cls(**filtered)
            for prop in ("base_dmg", "heal_amount", "countdown", "amulet_desc", "minion_hp", "minion_atk", "exhaust", "damage_type"):
                if prop in cfg:
                    setattr(inst, prop, cfg[prop])
            inst.is_duel_custom = (key in DUEL_CARD_CLASS_REGISTRY) or (cls == DuelGenericCard)
            inst.rarity = rarity
            inst.exhaust = exhaust
            inst.fleeting = fleeting
            inst.agile = agile
            inst.retain = retain
            inst.innate = cfg.get("innate", False)
            inst.ethereal = cfg.get("ethereal", False)
            inst.unplayable = cfg.get("unplayable", False)
            inst.damage_type = cfg.get("damage_type", "effect")
            fragile_val = cfg.get("fragile", 0)
            if fragile_val > 0:
                from ...entities.tags import FragileTag
                inst.add_tag(FragileTag("fragile", fragile_val))
                if " (易碎 " not in inst.name:
                    inst.name = f"{inst.name} (易碎 {fragile_val})"
            self[key] = inst
            return inst
        return None

    def __getitem__(self, key):
        if isinstance(key, str) and ":replay:" in key:
            parts = key.rsplit(":replay:", 1)
            base_key = parts[0]
            replay_val = int(parts[1])
            base_card = self[base_key]
            import copy
            replay_card = copy.copy(base_card)
            replay_card.id = base_key
            from ...entities.tags import ReplayTag
            replay_card.add_tag(ReplayTag("replay", replay_val))
            replay_card.name = base_card.name
            import re
            clean_desc = re.sub(r"重放 \d+。", "", base_card.desc)
            if clean_desc.endswith("。") or clean_desc.endswith("！"):
                replay_card.desc = clean_desc + f"重放 {replay_val}。"
            else:
                replay_card.desc = clean_desc + f"。重放 {replay_val}。"
            return replay_card

        if isinstance(key, str) and ":fragile:" in key:
            parts = key.split(":fragile:")
            base_key = parts[0]
            fragile_val = int(parts[1])
            base_card = self[base_key]
            import copy
            fragile_card = copy.copy(base_card)
            fragile_card.id = base_key
            from ...entities.tags import FragileTag
            fragile_card.add_tag(FragileTag("fragile", fragile_val))
            clean_name = base_card.name
            if " (易碎 " in clean_name:
                clean_name = clean_name.split(" (易碎 ")[0]
            fragile_card.name = f"{clean_name} (易碎 {fragile_val})"
            import re
            fragile_card.desc = re.sub(r"易碎 \d+。", f"易碎 {fragile_val}。", base_card.desc)
            return fragile_card

        if isinstance(key, str) and key.endswith("+"):
            base_key = key[:-1]
            if not super().__contains__(base_key):
                self._lazy_load_card(base_key)
            if not super().__contains__(base_key):
                raise KeyError(key)
            import copy
            base_card = super().__getitem__(base_key)
            upgraded_card = copy.copy(base_card)
            upgraded_card.id = key
            if " (易碎 " in upgraded_card.name:
                parts = upgraded_card.name.split(" (易碎 ")
                name_part = parts[0]
                fragile_part = " (易碎 " + parts[1]
                upgraded_card.name = name_part + "+" + fragile_part
            else:
                if not upgraded_card.name.endswith("+"):
                    upgraded_card.name += "+"
            upgraded_card.upgraded = True
            
            from ...data.card_upgrade_data import CARD_UPGRADE_CONFIG
            up_cfg = CARD_UPGRADE_CONFIG.get(base_key, {})
            if "cost_a" in up_cfg:
                upgraded_card.cost_a = up_cfg["cost_a"]
            if "cost_ba" in up_cfg:
                upgraded_card.cost_ba = up_cfg["cost_ba"]
            if "desc" in up_cfg:
                upgraded_card.desc = up_cfg["desc"]
            if "innate" in up_cfg:
                upgraded_card.innate = up_cfg["innate"]
            if "exhaust" in up_cfg:
                upgraded_card.exhaust = up_cfg["exhaust"]
            for prop in ("base_dmg", "heal_amount", "shield_amount", "minion_hp", "minion_atk", "countdown", "amulet_desc"):
                if prop in up_cfg:
                    setattr(upgraded_card, prop, up_cfg[prop])
            return upgraded_card
            
        if not super().__contains__(key):
            self._lazy_load_card(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        if isinstance(key, str):
            clean_key = key.split(":replay:")[0].split(":fragile:")[0]
            if clean_key.endswith("+"):
                base_key = clean_key[:-1]
                if super().__contains__(base_key):
                    return True
                from ...data.duel_card_data import DUEL_CARD_CONFIG
                return base_key in DUEL_CARD_CONFIG
            if super().__contains__(clean_key):
                return True
            from ...data.duel_card_data import DUEL_CARD_CONFIG
            return clean_key in DUEL_CARD_CONFIG
        return super().__contains__(key)

from ...data.duel_card_data import DUEL_CARD_CONFIG
ALL_DUEL_CARDS = DuelCardRegistryDict()
