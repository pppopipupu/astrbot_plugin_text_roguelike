from typing import Tuple, List
from .base import EnemyTemplate
from ...data.enemy_data import ENEMY_CONFIG

class GoblinCenturionTemplate(EnemyTemplate):
    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        import random
        cfg = ENEMY_CONFIG.get("地精百夫长", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return chosen["id"], chosen["val"], chosen["desc"]

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        if enemy.intent_type == "heavy_strike":
            self._perform_attack(run, engine, enemy, enemy.intent_val, logs)
        elif enemy.intent_type == "defend":
            enemy.shield += enemy.intent_val
            logs.append(f"【{enemy.name}】举起盾牌，获得 {enemy.intent_val} 点护盾。")
        elif enemy.intent_type == "command":
            enemy.actions += 1
            logs.append(f"【{enemy.name}】发出咆哮，获得 1 个额外动作点。")

class GargoylePriestTemplate(EnemyTemplate):
    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        import random
        cfg = ENEMY_CONFIG.get("石像鬼祭司", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return chosen["id"], chosen["val"], chosen["desc"]

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        if enemy.intent_type == "attack":
            self._perform_attack(run, engine, enemy, enemy.intent_val, logs)
        elif enemy.intent_type == "defend":
            enemy.shield += enemy.intent_val
            logs.append(f"【{enemy.name}】施展暗影护盾，获得 {enemy.intent_val} 点护盾。")
        elif enemy.intent_type == "drain":
            self._perform_attack(run, engine, enemy, enemy.intent_val, logs)
            if run.enemies:
                min_hp_enemy = min(run.enemies, key=lambda e: e.hp)
                min_hp_enemy.hp = min(min_hp_enemy.max_hp, min_hp_enemy.hp + 4)
                logs.append(f"【{enemy.name}】汲取生命，为【{min_hp_enemy.name}】恢复了 4 点生命值。")

class BeastMasterTemplate(EnemyTemplate):
    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        import random
        cfg = ENEMY_CONFIG.get("狂暴兽王", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return chosen["id"], chosen["val"], chosen["desc"]

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        if enemy.intent_type == "attack":
            self._perform_attack(run, engine, enemy, enemy.intent_val, logs)
        elif enemy.intent_type == "defend":
            enemy.shield += enemy.intent_val
            logs.append(f"【{enemy.name}】收缩防线，获得 {enemy.intent_val} 点护盾。")
        elif enemy.intent_type == "summon_beast":
            from ...models.state import EnemyState
            cfg = ENEMY_CONFIG.get("狂暴兽王", {})
            sh = cfg.get("summon_hound", {})
            new_hound = EnemyState(
                name=sh.get("name", "狂暴猎犬"),
                hp=sh.get("hp", 8),
                max_hp=sh.get("max_hp", 8),
                shield=0,
                intent_type="attack",
                intent_val=sh.get("intent_val", 2),
                intent_desc=sh.get("intent_desc", "扑咬 (造成 2 伤害)"),
                actions=1,
                bonus_actions=0,
                is_summon=True,
                max_actions=1,
                max_bonus_actions=0
            )
            run.enemies.append(new_hound)
            logs.append(f"【{enemy.name}】召唤了一只【狂暴猎犬】加入战场。")

class ObsidianDjinnTemplate(EnemyTemplate):
    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        import random
        cfg = ENEMY_CONFIG.get("黑曜石巨灵", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return chosen["id"], chosen["val"], chosen["desc"]

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        p = run.player
        if enemy.intent_type == "quake":
            self._perform_attack(run, engine, enemy, enemy.intent_val, logs)
            p.bonus_actions = max(0, p.bonus_actions - 1)
            logs.append(f"【{enemy.name}】引发地震，剥夺了玩家 1 个附赠动作点 (BA)。")
        elif enemy.intent_type == "defend":
            enemy.shield += enemy.intent_val
            logs.append(f"【{enemy.name}】加固外壳，获得 {enemy.intent_val} 点护盾。")

class GhostArchmageTemplate(EnemyTemplate):
    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        import random
        cfg = ENEMY_CONFIG.get("幽灵大魔法师", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return chosen["id"], chosen["val"], chosen["desc"]

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        p = run.player
        import random
        if enemy.intent_type == "spell_burst":
            self._perform_attack(run, engine, enemy, enemy.intent_val, logs)
        elif enemy.intent_type == "mana_drain":
            self._perform_attack(run, engine, enemy, enemy.intent_val, logs)
            if p.hand:
                discarded = p.hand.pop(random.randint(0, len(p.hand) - 1))
                from ..cards import ALL_CARDS
                card_name = ALL_CARDS[discarded].name if discarded in ALL_CARDS else "未知卡牌"
                agile_msg = engine._discard_card(run, discarded)
                logs.append(f"【{enemy.name}】施展虹吸，迫使玩家随机丢弃了卡牌【{card_name}】。")
                if agile_msg:
                    logs.append(agile_msg)

class ShadowFiendTemplate(EnemyTemplate):
    def roll_intent(self, run, engine, enemy) -> Tuple[str, int, str]:
        import random
        cfg = ENEMY_CONFIG.get("暗影影魔", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return chosen["id"], chosen["val"], chosen["desc"]

    def execute_intent(self, run, engine, enemy, logs: List[str]):
        p = run.player
        if enemy.intent_type == "shadow_strike":
            dmg = enemy.intent_val
            p.hp -= dmg
            logs.append(f"【{enemy.name}】施展影袭，直接对玩家造成 {dmg} 点生命伤害。")
        elif enemy.intent_type == "defend":
            enemy.shield += enemy.intent_val
            logs.append(f"【{enemy.name}】进入虚化，获得 {enemy.intent_val} 点护盾。")
