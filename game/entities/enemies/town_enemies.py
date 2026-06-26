from typing import Tuple, List
from .base import EnemyTemplate, register_enemy
from ...models.state import EnemyIntentState, BuffState

@register_enemy("训练假人")
class DummyTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List[EnemyIntentState]:
        return []

@register_enemy("NoobSlayer99")
class NoobSlayer99Template(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List[EnemyIntentState]:
        turn = run.node_data.get("noob_turn", 1)
        run.node_data["noob_turn"] = turn + 1
        intents_list = []
        if turn % 2 == 1:
            intents_list.append(EnemyIntentState(
                type="attack",
                val=8,
                desc="施法火球 (造成 8 点火焰伤害)",
                cost_a=1,
                cost_ba=0
            ))
        else:
            intents_list.append(EnemyIntentState(
                type="defend",
                val=8,
                desc="凝聚冰甲 (获得 8 点护盾)",
                cost_a=1,
                cost_ba=0
            ))
        return intents_list

@register_enemy("xXx_SniperElite_xXx")
class SniperEliteTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List[EnemyIntentState]:
        turn = run.node_data.get("sniper_turn", 1)
        run.node_data["sniper_turn"] = turn + 1
        intents_list = []
        if turn % 2 == 1:
            intents_list.append(EnemyIntentState(
                type="aim",
                val=0,
                desc="精准瞄准 (锁定目标，下回合伤害增加)",
                cost_a=1,
                cost_ba=0
            ))
        else:
            intents_list.append(EnemyIntentState(
                type="attack",
                val=18,
                desc="穿甲射击 (造成 18 点穿刺伤害)",
                cost_a=1,
                cost_ba=0
            ))
        return intents_list

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = intent
            from ...models.state import EnemyIntentState
            intent = EnemyIntentState(
                type=getattr(enemy, "intent_type", ""),
                val=getattr(enemy, "intent_val", 0),
                desc=getattr(enemy, "intent_desc", ""),
                cost_a=1,
                cost_ba=0
            )
        from .trash_talk_actions import try_trash_talk
        try_trash_talk(run, enemy, logs)
        if intent.type == "aim":
            enemy.buffs.append(BuffState(id="strength", name="力量", stacks=3, desc="造成伤害增加 3"))
            logs.append(f"敌人【{enemy.name}】进入了瞄准状态，获得了 3 层力量。")
        else:
            for b in list(enemy.buffs):
                if b.id == "strength":
                    enemy.buffs.remove(b)
            super().execute_intent(run, engine, enemy, intent, logs)

@register_enemy("pppopipupu")
class PppopipupuTemplate(EnemyTemplate):
    def on_enemy_before_death(self, run, enemy, event, engine):
        if enemy.name == "pppopipupu":
            event.cancel()
            enemy.name = "【觉醒】pppopipupu"
            enemy.max_hp = 9999
            enemy.hp = 9999
            enemy.shield = 0
            enemy.actions = 1
            enemy.bonus_actions = 0
            enemy.max_actions = 1
            enemy.max_bonus_actions = 0
            enemy.buffs.clear()
            run.node_data["pppopipupu_phase"] = 2
            enemy.intents.clear()
            engine._log_event(run, "🌟 pppopipupu 在致命伤下苏醒了！无尽的力场虚空能重新充满了他的身躯！他进入了神级觉醒形态！")

    def roll_intents(self, run, engine, enemy) -> List[EnemyIntentState]:
        phase = run.node_data.get("pppopipupu_phase", 1)
        intents_list = []
        if phase == 2:
            intents_list.append(EnemyIntentState(
                type="force_strike",
                val=100,
                desc="猛击 (对玩家造成 100 点力场伤害)",
                cost_a=1,
                cost_ba=0
            ))
        else:
            intents_list.append(EnemyIntentState(
                type="fish",
                val=0,
                desc="钓鱼 (无所事事地在靶场旁钓鱼)",
                cost_a=1,
                cost_ba=0
            ))
        return intents_list

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = intent
            from ...models.state import EnemyIntentState
            intent = EnemyIntentState(
                type=getattr(enemy, "intent_type", ""),
                val=getattr(enemy, "intent_val", 0),
                desc=getattr(enemy, "intent_desc", ""),
                cost_a=1,
                cost_ba=0
            )
        from .trash_talk_actions import try_trash_talk
        try_trash_talk(run, enemy, logs)
        if intent.type == "force_strike":
            engine._damage_target(run, "p0", 100, source=f"enemy:{enemy.name}", damage_type="force")
            logs.append(f"敌人【{enemy.name}】发出了撕裂空间的猛击，对玩家造成了 100 点真实力场伤害！")
        else:
            logs.append(f"敌人【{enemy.name}】在一旁悠闲地钓鱼。")

register_enemy("【觉醒】pppopipupu")(PppopipupuTemplate)

@register_enemy("Gate_Guardian")
class GateGuardianTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List[EnemyIntentState]:
        turn = run.node_data.get("guardian_turn", 1)
        run.node_data["guardian_turn"] = turn + 1
        intents_list = []
        cycle = (turn - 1) % 3 + 1
        if cycle == 1:
            intents_list.append(EnemyIntentState(
                type="attack",
                val=12,
                desc="强力挥砍 (造成 12 点挥砍伤害)",
                cost_a=1,
                cost_ba=0
            ))
        elif cycle == 2:
            intents_list.append(EnemyIntentState(
                type="defend",
                val=15,
                desc="铁盾格挡 (获得 15 点护盾)",
                cost_a=1,
                cost_ba=0
            ))
        else:
            intents_list.append(EnemyIntentState(
                type="attack",
                val=20,
                desc="重力盾击 (造成 20 点钝击伤害)",
                cost_a=1,
                cost_ba=0
            ))
        return intents_list
