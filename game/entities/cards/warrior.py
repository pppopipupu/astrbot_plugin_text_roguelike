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
        shield = 40 if self.upgraded else 30
        engine._gain_shield(run, "p0", shield)
        return f"使用了【岿然不动】，获得了 {shield} 点护盾。"
