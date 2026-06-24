import re
from .base import RelicImpl
from .registry import register_relic

class AncientPageRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.hp_loss = 4
        self.spark_count = 2

    def on_battle_start(self, run, engine):
        p = run.player
        p.hp = max(1, p.hp - self.hp_loss)
        engine._log_event(run, f"📖 [先古残页] 触发：失去 {self.hp_loss} 点生命值。")
        max_hand = 9 if "mask_of_void" in p.relics else 12
        spark_added = 0
        for _ in range(self.spark_count):
            if len(p.hand) < max_hand:
                p.hand.append("arcane_spark")
                spark_added += 1
        if spark_added > 0:
            engine._log_event(run, f"📖 [先古残页] 触发：将 {spark_added} 张【奥术星火】加入手牌。")

class HeavyArmorRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.shield_gain = 8

    def on_battle_start(self, run, engine):
        p = run.player
        p.shield += self.shield_gain
        engine._log_event(run, f"🛡️ [重装甲片] 触发：获得 {self.shield_gain} 点初始护盾。")

class GreedyContractRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.hp_loss = 3

    def on_battle_start(self, run, engine):
        p = run.player
        p.hp = max(1, p.hp - self.hp_loss)
        engine._log_event(run, f"🪙 [贪婪契约] 触发：失去 {self.hp_loss} 点生命值。")

class AncientEyeRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.draw_bonus = 2

    def on_battle_start(self, run, engine):
        engine._log_event(run, f"👁️ [先古之眼] 触发：初始抽牌数量 +{self.draw_bonus}。")

    def modify_initial_draw(self, run, draw_count: int, engine) -> int:
        return draw_count + self.draw_bonus

class DragonBloodRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.heal_amount = 5

    def on_battle_win(self, run, engine):
        p = run.player
        p.hp = min(p.max_hp, p.hp + self.heal_amount)
        engine._log_event(run, f"🩸 [红龙之血] 触发：回复了 {self.heal_amount} 点生命值。")

class UnstableCrystalRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.spell_dmg_bonus = 1
        self.turn_ba_bonus = 1
        self.recoil_damage = 1

    def on_damage_calculate(self, event, run, engine):
        if event.damage_type == "spell" and event.source == "p0":
            event.modified_damage += self.spell_dmg_bonus

    def on_turn_start(self, event, run, engine):
        if event.is_player:
            run.player.bonus_actions += self.turn_ba_bonus

    def on_card_played(self, event, run, engine):
        if event.card.type == "spell":
            engine._damage_target(run, "p0", self.recoil_damage)
            engine._log_event(run, f"⚡ [不稳定水晶] 受到 {self.recoil_damage} 点法术反噬伤害。")

class VampiricTouchRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.heal_amount = 1

    def on_card_played(self, event, run, engine):
        if event.card.type == "spell" and event.card.id in (
            "dagger_throw", "fire_bolt", "fireball", "thunderwave",
            "magic_missile", "quick_strike", "arcane_spark", "doomsday_judgment", "meteor_swarm"
        ):
            old_hp = run.player.hp
            engine._heal_target(run, "p0", self.heal_amount)
            if run.player.hp > old_hp:
                engine._log_event(run, f"❤️ [吸血之触] 回复了 {self.heal_amount} 点生命值。")

class MarkOfFuryRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.spell_bonus = 2

    def on_damage_calculate(self, event, run, engine):
        if event.damage_type == "spell" and event.source == "p0":
            event.modified_damage += self.spell_bonus

class EnergyCoreRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.action_bonus = 1

    def on_turn_start(self, event, run, engine):
        if event.is_player:
            run.player.actions += self.action_bonus

class PortalFragmentRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        import random
        p = run.player
        max_hand = 9 if "mask_of_void" in p.relics else 12
        if len(p.hand) < max_hand:
            chosen = random.choice(["key_resonance", "gate_guard", "master_key", "void_beacon", "ancient_wisdom"])
            p.hand.append(chosen)
            from ...data.card_data import CARD_CONFIG
            name = CARD_CONFIG.get(chosen, {}).get("name", chosen)
            engine._log_event(run, f"🌀 [门扉碎片] 触发：随机将一张中立牌【{name}】加入手牌。")

class AncientKeyringRelic(RelicImpl):
    pass

class AbyssGazeRelic(RelicImpl):
    def on_damage_calculate(self, event, run, engine):
        if event.damage_type == "spell" and event.source == "p0":
            event.modified_damage += 4

    def on_damage_take(self, event, run, engine):
        if event.target == "p0" and event.amount > 0 and event.source != "abyss_gaze":
            engine._damage_target(run, "p0", 2, source="abyss_gaze", damage_type="true")
            engine._log_event(run, "👁️ [深渊凝视] 触发：额外受到 2 点真实伤害。")

class GlacierArmorRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        run.player.shield += 12
        engine._log_event(run, "🛡️ [冰川装甲] 触发：获得 12 点初始护盾。")

class AbyssWhisperRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        if run.enemies:
            import random
            enemy = random.choice(run.enemies)
            engine._add_buff_to(enemy, "stun", "眩晕", "无法行动", 1)
            engine._log_event(run, f"👁️ [深渊低语] 触发：使【{enemy.name}】在首回合陷入眩晕！")

class FrostBladeRelic(RelicImpl):
    def on_damage_calculate(self, event, run, engine):
        dtype_str = event.damage_type.value if hasattr(event.damage_type, "value") else str(event.damage_type)
        if dtype_str == "cold" and event.source == "p0":
            event.modified_damage += 4

class AbyssContractRelic(RelicImpl):
    def on_damage_take(self, event, run, engine):
        dtype_str = event.damage_type.value if hasattr(event.damage_type, "value") else str(event.damage_type)
        if event.target == "p0" and dtype_str == "true" and event.amount > 0:
            engine._draw_cards(run.player, 1, run)
            engine._log_event(run, "📖 [深渊契约书] 触发：受到真实伤害，抽取 1 张卡牌。")

class GlacierCoreRelic(RelicImpl):
    def on_shield_decay(self, event, run, engine):
        if event.target == "p0" and event.amount > 0:
            lost = event.amount
            dmg = lost // 2
            if dmg > 0:
                feedback_parts = []
                for idx in range(len(run.enemies) - 1, -1, -1):
                    enemy = run.enemies[idx]
                    engine._damage_target(run, f"e{idx+1}", dmg, damage_type="cold", source="glacier_core")
                    feedback_parts.append(f"【{enemy.name}】受到 {dmg} 点冰霜伤害")
                if feedback_parts:
                    engine._log_event(run, "🏔️ [极寒之核] 触发：" + "，".join(feedback_parts) + "。")

class DoomsdayCoreRelic(RelicImpl):
    def on_turn_end(self, event, run, engine):
        if event.is_player:
            played_count = run.node_data.get("cards_played_this_turn", 0)
            if played_count >= 3:
                engine._draw_cards(run.player, 1, run)
                engine._log_event(run, "💎 [末日核心] 触发！本回合打出 >=3 张牌，额外抽 1 张牌！")

class NecromancerSkullRelic(RelicImpl):
    def on_minion_death(self, event, run, engine):
        engine._heal_target(run, "p0", 2)
        engine._log_event(run, "💀 [巫师颅骨] 触发！有单位死亡，玩家回复 2 点生命值！")

class ArcanistHandRelic(RelicImpl):
    def on_card_played(self, event, run, engine):
        if event.card.cost_a == 0 and event.card.cost_ba == 0:
            alive = [e for e in run.enemies if e.hp > 0]
            if alive:
                target_enemy = alive[0]
                idx = run.enemies.index(target_enemy) + 1
                engine._log_event(run, f"✋ [奥术师之手] 触发！使用 0 费卡牌，对【{target_enemy.name}】造成 3 点力场伤害！")
                engine.combat_resolver.damage_target(run, f"e{idx}", 3, source="relic:arcanist_hand", damage_type="force")

class CommanderMedalRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        for m in run.player.minions.values():
            m.actions += 1
            m.bonus_actions += 1
        engine._log_event(run, "🏅 [至高勋章] 触发！所有在场随从本回合获得的行动点数 +1！")

class StalkerEyeRelic(RelicImpl):
    def on_damage_calculate(self, event, run, engine):
        if event.source == "p0" and event.card and getattr(event.card, "exhaust", False):
            event.modified_damage += 4
            engine._log_event(run, f"👁️ [潜伏者眼球] 触发！消耗卡牌【{event.card.name}】伤害提升 4 点！")

    def on_shield_gain(self, event, run, engine):
        if event.target == "p0":
            from ...entities import ALL_CARDS
            playing_cid = run.node_data.get("current_playing_card_id", "")
            card = ALL_CARDS.get(playing_cid)
            if card and getattr(card, "exhaust", False):
                event.modified_amount += 4
                engine._log_event(run, f"👁️ [潜伏者眼球] 触发！使用消耗卡牌【{card.name}】获得护盾，护盾提升 4 点！")
class GladiatorBeltRelic(RelicImpl):
    def on_turn_start(self, event, run, engine):
        if event.is_player and run.player.minions:
            p = run.player
            p.shield += 2
            engine._log_event(run, "🎗️ [角斗士皮带] 触发！有随从在场，你获得 2 点护盾！")

class ShieldBatteryRelic(RelicImpl):
    def on_shield_gain(self, event, run, engine):
        if event.target == "p0":
            import random
            if random.random() < 0.5:
                event.modified_amount += 2
                engine._log_event(run, "🔋 [能量护盾电池] 触发！你额外获得 2 点护盾！")

class CrimsonHeartRelic(RelicImpl):
    def on_damage_calculate(self, event, run, engine):
        p = run.player
        if event.source == "p0" and p.hp / p.max_hp < 0.3:
            event.modified_damage = int(event.modified_damage * 2)
            engine._log_event(run, "❤️ [绯红之心] 触发！生命值低于 30%，造成的伤害翻倍！")

    def on_card_played(self, event, run, engine):
        p = run.player
        if p.hp / p.max_hp < 0.3:
            old_hp = p.hp
            p.hp = min(p.max_hp, p.hp + 2)
            if p.hp > old_hp:
                engine._log_event(run, f"❤️ [绯红之心] 触发！打出卡牌回复了 {p.hp - old_hp} 点生命值！")

@register_relic("espresso_relic")
class EspressoRelic(RelicImpl):
    def on_turn_start(self, event, run, engine):
        if event.is_player:
            run.player.actions += 1
            engine._log_event(run, "☕ [特制浓缩咖啡] 触发！本回合额外获得 1A！")

@register_relic("anthem_relic_3")
class AnthemRelic3(RelicImpl):
    def on_battle_start(self, run, engine):
        p = run.player
        p.shield += 2
        engine._log_event(run, "🎵 [赞歌] 触发！获得 2 点初始护盾。")
        if "anthem_relic_3" in p.relics:
            p.relics.remove("anthem_relic_3")
            p.relics.append("anthem_relic_2")

@register_relic("anthem_relic_2")
class AnthemRelic2(RelicImpl):
    def on_battle_start(self, run, engine):
        p = run.player
        p.shield += 2
        engine._log_event(run, "🎵 [赞歌] 触发！获得 2 点初始护盾。")
        if "anthem_relic_2" in p.relics:
            p.relics.remove("anthem_relic_2")
            p.relics.append("anthem_relic_1")

@register_relic("anthem_relic_1")
class AnthemRelic1(RelicImpl):
    def on_battle_start(self, run, engine):
        p = run.player
        p.shield += 2
        engine._log_event(run, "🎵 [赞歌] 触发！获得 2 点初始护盾（次数已耗尽）。")
        if "anthem_relic_1" in p.relics:
            p.relics.remove("anthem_relic_1")



for name, obj in list(globals().items()):
    if isinstance(obj, type) and issubclass(obj, RelicImpl) and obj is not RelicImpl:
        snake = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        if snake.endswith('_relic'):
            relic_id = snake[:-6]
            register_relic(relic_id)(obj)
