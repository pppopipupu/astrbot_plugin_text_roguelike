from typing import Optional
from ...models.state import Card
from ...data.card_data import CARD_CONFIG
from .registry import register_card

@register_card("warrior_strike")
class WarriorStrikeCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 9 if self.upgraded else 6
        name = engine._get_target_name(run, target)
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        engine._damage_target(run, target, dmg, damage_type="slashing", card=self)
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(target=name)
        return f"对【{name}】使用【打击】，造成了 {dmg} 点挥砍伤害。"

@register_card("warrior_defend")
class WarriorDefendCard(Card):
    def execute(self, run, target, engine) -> str:
        shield = 8 if self.upgraded else 5
        engine._gain_shield(run, "p0", shield)
        return f"使用了【防御】，获得了 {shield} 点护盾。"

@register_card("warrior_bash")
class WarriorBashCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 11 if self.upgraded else 8
        stacks = 3 if self.upgraded else 2
        name = engine._get_target_name(run, target)
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        engine._damage_target(run, target, dmg, damage_type="bludgeoning", card=self)
        if target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if 0 <= idx < len(run.enemies):
                    enemy = run.enemies[idx]
                    engine._add_buff_to(enemy, "minor_vulnerable", "轻度易伤", "受到的所有类型伤害增加 50%", stacks)
            except ValueError:
                pass
        return f"对【{name}】使用【痛击】，造成了 {dmg} 点钝击伤害，并施加了 {stacks} 层【轻度易伤】。"

@register_card("iron_wave")
class IronWaveCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 7 if self.upgraded else 5
        shield = 7 if self.upgraded else 5
        name = engine._get_target_name(run, target)
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        engine._damage_target(run, target, dmg, damage_type="slashing", card=self)
        engine._gain_shield(run, "p0", shield)
        return f"对【{name}】使用【铁斩波】，造成了 {dmg} 点挥砍伤害，并获得了 {shield} 点护盾。"

@register_card("warrior_anger")
class WarriorAngerCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 6 if self.upgraded else 4
        name = engine._get_target_name(run, target)
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        engine._damage_target(run, target, dmg, damage_type="slashing", card=self)
        run.player.discard_pile.append(self.id)
        return f"对【{name}】使用【愤怒】，造成了 {dmg} 点挥砍伤害。将一张复制品加入弃牌堆。"

@register_card("body_slam")
class BodySlamCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = run.player.shield
        name = engine._get_target_name(run, target)
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        engine._damage_target(run, target, dmg, damage_type="bludgeoning", card=self)
        return f"对【{name}】使用【全身撞击】，造成了等同于当前护盾值（{dmg}点）的钝击伤害。"

@register_card("pommel_strike")
class PommelStrikeCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 12 if self.upgraded else 9
        cards_to_draw = 2 if self.upgraded else 1
        name = engine._get_target_name(run, target)
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        engine._damage_target(run, target, dmg, damage_type="slashing", card=self)
        engine._draw_cards(run.player, cards_to_draw, run)
        return f"对【{name}】使用【剑柄打击】，造成了 {dmg} 点挥砍伤害并抽了 {cards_to_draw} 张牌。"

@register_card("shrug_it_off")
class ShrugItOffCard(Card):
    def execute(self, run, target, engine) -> str:
        shield = 11 if self.upgraded else 8
        engine._gain_shield(run, "p0", shield)
        engine._draw_cards(run.player, 1, run)
        return f"使用了【耸肩无视】，获得了 {shield} 点护盾并抽了 1 张牌。"

@register_card("heavy_blade")
class HeavyBladeCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 18 if self.upgraded else 14
        name = engine._get_target_name(run, target)
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        engine._damage_target(run, target, dmg, damage_type="slashing", card=self)
        return f"对【{name}】使用【重刃】，造成了 {dmg} 点挥砍伤害。"

@register_card("shockwave")
class ShockwaveCard(Card):
    def execute(self, run, target, engine) -> str:
        stacks = 3 if self.upgraded else 2
        for enemy in list(run.enemies):
            engine._add_buff_to(enemy, "minor_vulnerable", "轻度易伤", "受到的所有类型伤害增加 50%", stacks)
            engine._add_buff_to(enemy, "weak", "虚弱", "造成的物理伤害减少 3 点", stacks)
        return f"释放了【震荡波】，对所有敌人施加了 {stacks} 层【轻度易伤】和【虚弱】。"

@register_card("flame_barrier")
class FlameBarrierCard(Card):
    def execute(self, run, target, engine) -> str:
        shield = 16 if self.upgraded else 12
        barrier_dmg = 6 if self.upgraded else 4
        engine._gain_shield(run, "p0", shield)
        engine._add_buff_to(run.player, "flame_barrier_buff", "火焰屏障", "受到伤害时对攻击源反弹真实伤害", barrier_dmg)
        return f"使用了【火焰屏障】，获得了 {shield} 点护盾并挂载了反弹 {barrier_dmg} 点伤害的火焰反震形态。"

@register_card("uppercut")
class UppercutCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 17 if self.upgraded else 13
        stacks = 3 if self.upgraded else 2
        name = engine._get_target_name(run, target)
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        engine._damage_target(run, target, dmg, damage_type="bludgeoning", card=self)
        if target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if 0 <= idx < len(run.enemies):
                    enemy = run.enemies[idx]
                    engine._add_buff_to(enemy, "minor_vulnerable", "轻度易伤", "受到的所有类型伤害增加 50%", stacks)
                    engine._add_buff_to(enemy, "weak", "虚弱", "造成的物理伤害减少 3 点", stacks)
            except ValueError:
                pass
        return f"对【{name}】打出【上钩拳】，造成了 {dmg} 点钝击伤害，并施加了 {stacks} 层【轻度易伤】与【虚弱】。"

@register_card("spot_weakness")
class SpotWeaknessCard(Card):
    def execute(self, run, target, engine) -> str:
        strength_gain = 4 if self.upgraded else 3
        name = engine._get_target_name(run, target)
        is_attack = False
        if target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if 0 <= idx < len(run.enemies):
                    enemy = run.enemies[idx]
                    for it in enemy.intents:
                        if it.type in ("attack", "damage", "strike") or "伤害" in it.desc or "攻击" in it.desc:
                            is_attack = True
            except ValueError:
                pass
        if is_attack:
            engine._add_buff_to(run.player, "strength", "力量", "造成的伤害增加", strength_gain)
            return f"观察【{name}】的弱点成功！玩家获得了 {strength_gain} 层【力量】。"
        return f"观察【{name}】的弱点，但敌人的意图并不包含攻击，未获得力量。"

@register_card("ghostly_armor")
class GhostlyArmorCard(Card):
    def execute(self, run, target, engine) -> str:
        shield = 14 if self.upgraded else 10
        engine._gain_shield(run, "p0", shield)
        return f"使用了【幽魂铠甲】，获得了 {shield} 点护盾。"

@register_card("power_through")
class PowerThroughCard(Card):
    def execute(self, run, target, engine) -> str:
        shield = 22 if self.upgraded else 15
        engine._gain_shield(run, "p0", shield)
        added_wounds = 0
        for _ in range(2):
            if len(run.player.hand) < 12:
                run.player.hand.append("curse_wound")
                added_wounds += 1
        return f"使用了【硬撑】，获得了 {shield} 点护盾，并在手牌里添加了 {added_wounds} 张【伤口】诅咒卡。"

@register_card("double_tap")
class DoubleTapCard(Card):
    def execute(self, run, target, engine) -> str:
        stacks = 2 if self.upgraded else 1
        engine._add_buff_to(run.player, "double_tap_buff", "双发", "下一次物理伤害卡将触发额外打出", stacks)
        return f"使用了【双发】，本回合你打出的下一张物理伤害牌额外打出 {stacks} 次。"

@register_card("feed")
class FeedCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 14 if self.upgraded else 10
        hp_gain = 4 if self.upgraded else 3
        name = engine._get_target_name(run, target)
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        enemy_to_attack = None
        if target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if 0 <= idx < len(run.enemies):
                    enemy_to_attack = run.enemies[idx]
            except ValueError:
                pass
        engine._damage_target(run, target, dmg, damage_type="slashing", card=self)
        if enemy_to_attack and enemy_to_attack.hp <= 0:
            run.player.max_hp += hp_gain
            run.player.hp = min(run.player.max_hp, run.player.hp + hp_gain)
            return f"对【{name}】使用了【狂宴】造成 {dmg} 点挥砍伤害并将其吞噬！玩家最大生命值永久增加了 {hp_gain} 点并回复了等量生命。"
        return f"对【{name}】使用了【狂宴】，造成了 {dmg} 点挥砍伤害，但未成功击杀。"

@register_card("inflame")
class InflameCard(Card):
    def execute(self, run, target, engine) -> str:
        strength_gain = 3 if self.upgraded else 2
        engine._add_buff_to(run.player, "strength", "力量", "造成的伤害增加", strength_gain)
        return f"使用了【燃烧】，玩家获得了 {strength_gain} 层【力量】。"

@register_card("barricade")
class BarricadeCard(Card):
    def execute(self, run, target, engine) -> str:
        engine._add_buff_to(run.player, "buffer", "缓冲", "免疫接下来的伤害", 1)
        engine._add_buff_to(run.player, "barricade", "壁垒", "护盾回合开始时不衰减一半", 1)
        return f"使用了【壁垒】，获得了 1 层【缓冲】并挂载了【壁垒】形态（护盾回合开始时不流失一半）。"

@register_card("metallicize")
class MetallicizeCard(Card):
    def execute(self, run, target, engine) -> str:
        stacks = 6 if self.upgraded else 4
        engine._add_buff_to(run.player, "metallicize", "金属化", "回合结束时获得护盾", stacks)
        return f"使用了【金属化】，挂载了【金属化】形态（回合结束时获得 {stacks} 点护盾）。"

@register_card("bludgeon")
class BludgeonCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = 42 if self.upgraded else 32
        name = engine._get_target_name(run, target)
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        engine._damage_target(run, target, dmg, damage_type="bludgeoning", card=self)
        return f"对【{name}】使用了重击【重击】，造成了 {dmg} 点钝击伤害。"

@register_card("demon_form")
class DemonFormCard(Card):
    def execute(self, run, target, engine) -> str:
        stacks = 4 if self.upgraded else 3
        engine._add_buff_to(run.player, "demon_form", "恶魔形态", "回合开始时获得力量", stacks)
        bonus = ""
        if self.upgraded:
            run.player.actions += 1
            bonus = "，并额外获得了 1A 动作点"
        return f"使用了【恶魔形态】{bonus}。挂载了【恶魔形态】（每回合开始时获得 {stacks} 层力量）。"

@register_card("impervious")
class ImperviousCard(Card):
    def execute(self, run, target, engine) -> str:
        shield = 50 if self.upgraded else 30
        engine._gain_shield(run, "p0", shield)
        return f"使用了【岿然不动】，获得了 {shield} 点护盾。"


@register_card("entrench")
class EntrenchCard(Card):
    def execute(self, run, target, engine) -> str:
        multiplier = 3 if self.upgraded else 2
        old_shield = run.player.shield
        new_shield = old_shield * multiplier
        gain = new_shield - old_shield
        if gain > 0:
            engine._gain_shield(run, "p0", gain)
        return f"使用了【巩固】，获得了 {gain} 点护盾（当前护盾由 {old_shield} 点变为 {new_shield} 点）。"


@register_card("officer_recruit_vanguard")
class OfficerRecruitVanguardCard(Card):
    def execute(self, run, target, engine) -> str:
        hp = 6 if self.upgraded else 4
        atk = 3 if self.upgraded else 2
        grid = engine._summon_minion(run, self.id, self.name, hp, atk, 0)
        if grid:
            msg = f"在格子 [{grid}] 召唤了【{self.name}】。"
            rally = run.node_data.get("rally_count", 0)
            if rally >= 4:
                dmg = 5 if self.upgraded else 3
                chosen_target = target if (target and target.startswith("e")) else engine._get_first_alive_enemy(run)
                if chosen_target:
                    engine._damage_target(run, chosen_target, dmg, damage_type="piercing")
                    tname = engine._get_target_name(run, chosen_target)
                    msg += f"\n⚔️ [入场曲] 协作达到了 {rally}！对【{tname}】造成了 {dmg} 点穿刺伤害，并抽了 1 张牌。"
                else:
                    msg += f"\n⚔️ [入场曲] 协作达到了 {rally}！但场上没有活着的敌人，抽了 1 张牌。"
                engine._draw_cards(run.player, 1, run)
            else:
                shield = 4 if self.upgraded else 3
                engine._gain_shield(run, "p0", shield)
                msg += f"\n🛡️ [入场曲] 协作仅为 {rally}，玩家获得了 {shield} 点护盾。"
            return msg
        return "战场已满，召唤失败。"


@register_card("officer_banner_bearer")
class OfficerBannerBearerCard(Card):
    def execute(self, run, target, engine) -> str:
        hp = 8 if self.upgraded else 5
        atk = 2 if self.upgraded else 1
        grid = engine._summon_minion(run, self.id, self.name, hp, atk, 0)
        if grid:
            msg = f"在格子 [{grid}] 召唤了【{self.name}】。"
            has_cmd = any(m.id.startswith("commander_") for m in run.player.minions.values() if m.id != self.id)
            if has_cmd:
                engine._draw_cards(run.player, 1, run)
                if self.upgraded:
                    run.player.actions += 1
                    run.player.bonus_actions += 1
                    msg += f"\n✨ [入场曲] 检测到我方指挥官随从在场，抽了 1 张牌且获得了 1A 1BA！"
                else:
                    run.player.bonus_actions += 1
                    msg += f"\n✨ [入场曲] 检测到我方指挥官随从在场，抽了 1 张牌且获得了 1BA！"
            return msg
        return "战场已满，召唤失败。"


@register_card("commander_patrol_captain")
class CommanderPatrolCaptainCard(Card):
    def execute(self, run, target, engine) -> str:
        hp = 10 if self.upgraded else 7
        atk = 4 if self.upgraded else 3
        grid = engine._summon_minion(run, self.id, self.name, hp, atk, 0)
        if grid:
            msg = f"在格子 [{grid}] 召唤了【{self.name}】。"
            tok_id = "officer_soldier_token+" if self.upgraded else "officer_soldier_token"
            tok_name = "步兵轻卒+" if self.upgraded else "步兵轻卒"
            tok_grid = engine._summon_minion(run, tok_id, tok_name, 4 if self.upgraded else 3, 2 if self.upgraded else 1, 0)
            if tok_grid:
                msg += f"\n📢 [入场曲] 并在格子 [{tok_grid}] 召唤了【{tok_name}】。"
                m = run.player.minions[tok_grid]
                engine._add_buff_to(m, "ward", "守护", "敌方单体攻击只能指向该随从")
            return msg
        return "战场已满，召唤失败。"


@register_card("officer_royal_guard")
class OfficerRoyalGuardCard(Card):
    def execute(self, run, target, engine) -> str:
        hp = 11 if self.upgraded else 8
        atk = 4 if self.upgraded else 3
        grid = engine._summon_minion(run, self.id, self.name, hp, atk, 0)
        if grid:
            msg = f"在格子 [{grid}] 召唤了【{self.name}】。"
            rally = run.node_data.get("rally_count", 0)
            if rally >= 6:
                m = run.player.minions[grid]
                engine._add_buff_to(m, "ward", "守护", "敌方单体攻击只能指向该随从")
                msg += f"\n🛡️ [入场曲] 协作达到了 {rally}！近卫铁骑获得了【守护】！"
            return msg
        return "战场已满，召唤失败。"


@register_card("commander_garrison_leader")
class CommanderGarrisonLeaderCard(Card):
    def execute(self, run, target, engine) -> str:
        hp = 13 if self.upgraded else 9
        atk = 5 if self.upgraded else 4
        grid = engine._summon_minion(run, self.id, self.name, hp, atk, 0)
        if grid:
            msg = f"在格子 [{grid}] 召唤了【{self.name}】。"
            m = run.player.minions[grid]
            engine._add_buff_to(m, "ward", "守护", "敌方单体攻击只能指向该随从")
            buff_hp = 6 if self.upgraded else 4
            for mk, mv in run.player.minions.items():
                if mk != grid and (mv.id.startswith("officer_") or mv.id.startswith("commander_")):
                    mv.max_hp += buff_hp
                    mv.hp += buff_hp
            msg += f"\n🏰 [入场曲] 要塞卫队长自身获得【守护】，并使其他在场士兵最大生命值与血量值提升 {buff_hp} 点！"
            return msg
        return "战场已满，召唤失败。"


@register_card("officer_squad_skirmisher")
class OfficerSquadSkirmisherCard(Card):
    def execute(self, run, target, engine) -> str:
        hp = 8 if self.upgraded else 5
        atk = 4 if self.upgraded else 3
        grid = engine._summon_minion(run, self.id, self.name, hp, atk, 0)
        if grid:
            msg = f"在格子 [{grid}] 召唤了【{self.name}】。"
            rally = run.node_data.get("rally_count", 0)
            chosen_target = target if (target and target.startswith("e")) else engine._get_first_alive_enemy(run)
            if rally >= 8:
                dmg = 9 if self.upgraded else 6
                if chosen_target:
                    engine._damage_target(run, chosen_target, dmg, damage_type="slashing")
                    tname = engine._get_target_name(run, chosen_target)
                    try:
                        f_idx = int(chosen_target.replace("e", "")) - 1
                        if 0 <= f_idx < len(run.enemies):
                            engine._add_buff_to(run.enemies[f_idx], "stun", "眩晕", "下一回合无法行动", 1)
                    except ValueError:
                        pass
                    msg += f"\n⚡ [入场曲] 协作达到了 {rally}！对【{tname}】造成了 {dmg} 点挥砍伤害并使其眩晕了 1 回合！"
                else:
                    msg += f"\n⚡ [入场曲] 协作达到了 {rally}！但场上没有活着的敌人。"
            else:
                dmg = 5 if self.upgraded else 3
                if chosen_target:
                    engine._damage_target(run, chosen_target, dmg, damage_type="slashing")
                    tname = engine._get_target_name(run, chosen_target)
                    msg += f"\n⚔️ [入场曲] 对【{tname}】造成了 {dmg} 点挥砍伤害。"
                else:
                    msg += f"\n⚔️ [入场曲] 没有活着的敌人。"
            return msg
        return "战场已满，召唤失败。"


@register_card("commander_valiant_herald")
class CommanderValiantHeraldCard(Card):
    def execute(self, run, target, engine) -> str:
        hp = 11 if self.upgraded else 8
        atk = 4 if self.upgraded else 3
        grid = engine._summon_minion(run, self.id, self.name, hp, atk, 0)
        if grid:
            msg = f"在格子 [{grid}] 召唤了【{self.name}】。"
            eligible = []
            from .base import ALL_CARDS
            for cid in run.player.draw_pile:
                card = ALL_CARDS.get(cid)
                if card and card.type == "minion" and (card.id.startswith("officer_") or card.id.startswith("commander_")):
                    eligible.append(cid)
            if eligible:
                import random
                chosen = random.choice(eligible)
                run.player.draw_pile.remove(chosen)
                run.player.hand.append(chosen)
                cname = ALL_CARDS.get(chosen).name
                rally = run.node_data.get("rally_count", 0)
                if rally >= 6:
                    run.player.hand.remove(chosen)
                    new_cid = chosen + "+" if (not chosen.endswith("+")) else chosen
                    run.player.hand.append(new_cid)
                    run.node_data.setdefault("temp_retain_cards", []).append(new_cid)
                    msg += f"\n📣 [入场曲] 协作达到了 {rally}！从卡组中检索并抽取了士兵随从牌【{cname}】，并使其本回合获得【保留】且动作费用 A 减少了 1！"
                else:
                    msg += f"\n📣 [入场曲] 从卡组中检索并抽取了士兵随从牌【{cname}】。"
            else:
                msg += "\n📣 [入场曲] 检索失败，卡组中没有士兵随从牌。"
            return msg
        return "战场已满，召唤失败。"


@register_card("commander_steelclad_tactician")
class CommanderSteelcladTacticianCard(Card):
    def execute(self, run, target, engine) -> str:
        hp = 16 if self.upgraded else 12
        atk = 5 if self.upgraded else 4
        grid = engine._summon_minion(run, self.id, self.name, hp, atk, 0)
        if grid:
            return f"在格子 [{grid}] 召唤了【{self.name}】。"
        return "战场已满，召唤失败。"


@register_card("officer_blade_dancer")
class OfficerBladeDancerCard(Card):
    def execute(self, run, target, engine) -> str:
        hp = 12 if self.upgraded else 9
        atk = 6 if self.upgraded else 5
        grid = engine._summon_minion(run, self.id, self.name, hp, atk, 0)
        if grid:
            msg = f"在格子 [{grid}] 召唤了【{self.name}】。"
            m = run.player.minions[grid]
            rally = run.node_data.get("rally_count", 0)
            if rally >= 12:
                m.attack_actions = 2
                bonus = ""
                if self.upgraded:
                    run.player.actions += 1
                    bonus = "，且玩家获得了 1A"
                msg += f"\n⚔️ [入场曲] 协作达到了 {rally}！双刃轻卫本回合可以攻击两次{bonus}！"
            has_cmd = any(mv.id.startswith("commander_") for mv in run.player.minions.values() if mv.id != self.id)
            if has_cmd:
                tok_id = "officer_blade_dancer+" if self.upgraded else "officer_blade_dancer"
                tok_name = "【克隆体】双刃轻卫+" if self.upgraded else "【克隆体】双刃轻卫"
                tok_grid = engine._summon_minion(run, tok_id, tok_name, hp, atk, 0)
                if tok_grid:
                    msg += f"\n👥 [入场曲] 指挥官在场！在格子 [{tok_grid}] 召唤了该随从的克隆体！"
            return msg
        return "战场已满，召唤失败。"


@register_card("commander_aurora_emperor")
class CommanderAuroraEmperorCard(Card):
    def execute(self, run, target, engine) -> str:
        hp = 18 if self.upgraded else 14
        atk = 8 if self.upgraded else 6
        grid = engine._summon_minion(run, self.id, self.name, hp, atk, 0)
        if grid:
            msg = f"在格子 [{grid}] 召唤了【{self.name}】。"
            for mk, mv in run.player.minions.items():
                if mk != grid and (mv.id.startswith("officer_") or mv.id.startswith("commander_")):
                    mv.actions += 2
                    mv.attack_actions = 1
            buff_id = "commander_aurora_emperor+" if self.upgraded else "commander_aurora_emperor"
            buff_name = "极光圣域+" if self.upgraded else "极光圣域"
            buff_desc = "我方随从发起普攻时玩家获得 3 点护盾且抽 1 卡" if self.upgraded else "我方随从发起普攻时玩家获得 2 点护盾"
            engine._add_buff_to(run.player, buff_id, buff_name, buff_desc, 1)
            if self.upgraded:
                engine._gain_shield(run, "p0", 12)
                msg += f"\n🌟 [入场曲] 使在场所有士兵随从行动点 A 增加 2 且能够立刻发起一次攻击！挂载了【极光圣域+】并为玩家提供了 12 点护盾。"
            else:
                msg += f"\n🌟 [入场曲] 使在场所有士兵随从行动点 A 增加 2 且能够立刻发起一次攻击！挂载了【极光圣域】形态。"
            return msg
        return "战场已满，召唤失败。"


@register_card("tactical_barrack")
@register_card("iron_phalanx_seal")
@register_card("grand_coronation")
@register_card("blade_regiment_banner")
class DeployWarriorAmuletCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, countdown, amulet_desc, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, countdown=countdown, desc=desc)
        self.amulet_desc = amulet_desc

    def execute(self, run, target, engine) -> str:
        grid = engine._get_free_grid(run.player)
        from ...data.card_data import CARD_CONFIG
        cfg = CARD_CONFIG.get(self.id.replace("+", ""), {})
        if grid:
            cd = self.countdown
            if "ancient_keyring" in run.player.relics:
                import random
                if random.random() < 0.5:
                    cd = max(1, cd - 1)
            from ...models.state import AmuletState
            run.player.amulets[grid] = AmuletState(self.id, self.name, cd, self.amulet_desc)
            if getattr(run.player, "subclass", "") == "秘钥学者":
                engine._heal_target(run, "p0", 3)
                engine._gain_shield(run, "p0", 4)
            feedback_success = cfg.get("feedback_success", "将【{name}】部署到了格子 [{grid}]。")
            return feedback_success.format(name=self.name, grid=grid)
        return cfg.get("feedback_fail", "战场格子已满，部署失败。")

@register_card("warrior_hell_raider")
class WarriorHellRaiderCard(Card):
    def execute(self, run, target, engine) -> str:
        engine._add_buff_to(run.player, "hell_raider", "地狱狂徒", "抽到 1A 且不消耗 BA 卡牌时自动释放且免费", 1)
        return "你咏唱了【地狱狂徒】，浑身散发出炽热的地狱火光！你将立刻对抽到的 1A 卡牌进行自动连携打出！"

@register_card("warrior_shield_bash")
class WarriorShieldBashCard(Card):
    def execute(self, run, target, engine) -> str:
        dmg = run.player.shield
        name = engine._get_target_name(run, target)
        engine._damage_target(run, target, dmg, damage_type="true", card=self)
        
        kill_msg = ""
        target_enemy = None
        if target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if 0 <= idx < len(run.enemies):
                    target_enemy = run.enemies[idx]
            except ValueError:
                pass
        if target_enemy and 0 < target_enemy.hp < 20:
            engine._damage_target(run, target, target_enemy.hp, damage_type="true", card=self)
            kill_msg = f" 💀 [斩杀成功] 裂伤将【{name}】瞬间抹杀！"
            
        return f"对【{name}】使用【盾牌猛击】，造成了 {dmg} 点盾值真实伤害。{kill_msg}"

@register_card("warrior_blood_fury")
class WarriorBloodFuryCard(Card):
    def execute(self, run, target, engine) -> str:
        loss = min(5, run.player.hp - 1)
        if loss > 0:
            run.player.hp -= loss
        engine._add_buff_to(run.player, "strength", "力量", "造成伤害增加", 2)
        engine._draw_cards(run.player, 2, run)
        return f"你点燃了自身的生命潜能，失去了 {loss} 点生命值，获得了 2 层【力量】并抽了 2 张牌！"
