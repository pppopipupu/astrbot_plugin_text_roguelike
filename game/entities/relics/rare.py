import re
from .base import RelicImpl
from .registry import register_relic

class ReadyPackRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.draw_bonus = 1
        self.ba_bonus = 1

    def on_battle_start(self, run, engine):
        engine._log_event(run, f"🎒 [准备背包] 触发：本场战斗初始附赠动作（BA）+{self.ba_bonus}。")

    def modify_initial_draw(self, run, draw_count: int, engine) -> int:
        return draw_count + self.draw_bonus

class WhetstoneRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.attack_bonus = 1

    def on_damage_calculate(self, event, run, engine):
        if event.source.startswith("p") and event.source != "p0" and event.damage_type == "attack":
            event.modified_damage += self.attack_bonus

class ArcaneRuneRelic(RelicImpl):
    def __init__(self, relic_id: str):
        super().__init__(relic_id)
        self.spell_bonus = 1

    def on_damage_calculate(self, event, run, engine):
        if event.damage_type == "spell" and event.source == "p0":
            event.modified_damage += self.spell_bonus

class ChemicalXRelic(RelicImpl):
    pass

class AncientCompassRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        for e in run.enemies:
            e.actions = max(0, e.actions - 1)
        engine._log_event(run, "🧭 [古老罗盘] 触发：所有敌人首回合动作点（A）减少 1。")

class VoidLensRelic(RelicImpl):
    def on_damage_calculate(self, event, run, engine):
        if event.card and event.card.color == "neutral" and event.source == "p0":
            event.modified_damage += 2

    def on_shield_gain(self, event, run, engine):
        curr_cid = run.node_data.get("current_playing_card_id", "")
        if curr_cid:
            from ..cards.base import ALL_CARDS
            card = ALL_CARDS.get(curr_cid)
            if card and card.color == "neutral":
                event.modified_amount += 2

class CenturionMailRelic(RelicImpl):
    def on_damage_calculate(self, event, run, engine):
        if event.target == "p0" and event.damage_type in ("slashing", "piercing", "bludgeoning", "attack"):
            event.modified_damage = max(0, event.modified_damage - 2)

class PriestCharmRelic(RelicImpl):
    def on_heal(self, event, run, engine):
        if event.target == "p0":
            engine._gain_shield(run, "p0", 3)

class BeastmasterClawRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        for m in run.player.minions.values():
            m.atk += 1

    def on_minion_summon(self, event, run, engine):
        event.minion_state.atk += 1

class DjinnShardRelic(RelicImpl):
    def on_turn_start(self, event, run, engine):
        if event.is_player:
            run.node_data["djinn_shard_fired"] = False

    def on_card_played(self, event, run, engine):
        if not run.node_data.get("djinn_shard_fired", False) and event.card.type == "spell":
            run.node_data["djinn_shard_fired"] = True
            alive = [e for e in run.enemies if e.hp > 0]
            if alive:
                import random
                target_enemy = random.choice(alive)
                idx = run.enemies.index(target_enemy) + 1
                engine._log_event(run, f"💎 [巨灵碎晶] 触发！本回合打出第一张法术，对【{target_enemy.name}】造成 5 点力场伤害！")
                engine.combat_resolver.damage_target(run, f"e{idx}", 5, source="relic:djinn_shard", damage_type="force")

class ArchmageRobeRelic(RelicImpl):
    pass

class ShadowTentacleRelic(RelicImpl):
    pass

class MindflayerBrainRelic(RelicImpl):
    pass

class LengSpiderVenomRelic(RelicImpl):
    def on_damage_take(self, event, run, engine):
        if event.source == "p0" and event.target.startswith("e"):
            dtype = event.damage_type
            if dtype in ("slashing", "piercing", "bludgeoning", "attack"):
                import random
                if random.random() < 0.5:
                    try:
                        idx = int(event.target[1:]) - 1
                        if 0 <= idx < len(run.enemies):
                            enemy = run.enemies[idx]
                            engine._add_buff_to(enemy, "minor_vulnerable", "轻度物理易伤", "受到的物理伤害增加 50%", 1)
                            engine._log_event(run, f"🕷️ [冷蛛毒腺] 触发！使【{enemy.name}】获得 1 层【轻度物理易伤】。")
                    except ValueError:
                        pass

class MigoLightningGunRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        engine._log_event(run, "🔫 [米·戈电击枪] 触发！释放高频电磁波！")
        for idx in range(len(run.enemies) - 1, -1, -1):
            target_str = f"e{idx+1}"
            engine.combat_resolver.damage_target(run, target_str, 5, source="relic:migo_lightning_gun", damage_type="lightning")

class ShoggothSlimeRelic(RelicImpl):
    def on_damage_take(self, event, run, engine):
        if event.target == "p0" and event.amount > 0:
            is_true = (event.damage_type == "true" or event.damage_type == "TRUE")
            last_shield = run.node_data.get("last_shield_before_dmg", 0)
            if is_true or event.amount > last_shield:
                engine._log_event(run, "🦠 [修格斯粘液] 触发！受伤失去生命，获得 4 点护盾。")
                engine._gain_shield(run, "p0", 4)

class StarVampireProboscisRelic(RelicImpl):
    def on_card_played(self, event, run, engine):
        card = event.card
        if getattr(card, "exhaust", False) or getattr(card, "id", "") == "curse_dimensional_tear":
            engine._log_event(run, "🩸 [星之吸管] 触发！打出消耗牌，回复 2 点生命值。")
            engine._heal_target(run, "p0", 2)



for name, obj in list(globals().items()):
    if isinstance(obj, type) and issubclass(obj, RelicImpl) and obj is not RelicImpl:
        snake = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        if snake.endswith('_relic'):
            relic_id = snake[:-6]
            register_relic(relic_id)(obj)
