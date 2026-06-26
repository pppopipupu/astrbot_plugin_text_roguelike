from typing import List
from ..base import EnemyTemplate, register_enemy
from ....data.enemy_data import ENEMY_CONFIG

@register_enemy("传送门守卫者")
class PortalGuardianTemplate(EnemyTemplate):
    def roll_intents(self, run, engine, enemy) -> List['EnemyIntentState']:
        from ....models.state import EnemyIntentState
        import random
        cfg = ENEMY_CONFIG.get("传送门守卫者", {})
        intents = cfg.get("intents", [])
        chosen = random.choice(intents)
        return [EnemyIntentState(type=chosen["id"], val=chosen["val"], desc=chosen["desc"], cost_a=1, cost_ba=0)]

    def execute_intent(self, run, engine, enemy, intent, logs: List[str] = None):
        if logs is None:
            logs = intent
            from ....models.state import EnemyIntentState
            intent = EnemyIntentState(
                type=getattr(enemy, "intent_type", ""),
                val=getattr(enemy, "intent_val", 0),
                desc=getattr(enemy, "intent_desc", ""),
                cost_a=1,
                cost_ba=0
            )
        strength = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength += b.stacks
        val = intent.val + strength

        if intent.type == "dimensional_tear":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="true")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            logs.append(f"【{enemy.name}】撕裂虚空，对玩家造成真实伤害。{dmg_msg}")
        elif intent.type == "void_shield":
            enemy.shield += intent.val
            to_remove = next((b for b in enemy.buffs if b.id == "stun"), None)
            if not to_remove:
                neg_buffs = [b for b in enemy.buffs if b.id in ("minor_vulnerable_slashing", "minor_vulnerable_piercing", "minor_vulnerable_bludgeoning", "minor_vulnerable_fire", "minor_vulnerable_cold", "minor_vulnerable_lightning", "minor_vulnerable_thunder", "minor_vulnerable_necrotic", "minor_vulnerable_acid", "minor_vulnerable_poison", "minor_vulnerable_psychic", "minor_vulnerable_radiant", "minor_vulnerable_force")]
                if neg_buffs:
                    to_remove = neg_buffs[0]
            if to_remove:
                enemy.buffs.remove(to_remove)
                engine._sync_enemy_intents(enemy)
                logs.append(f"【{enemy.name}】展开虚空屏障，获得 {intent.val} 点护盾，并清除了【{to_remove.name}】负面状态！")
            else:
                logs.append(f"【{enemy.name}】展开虚空屏障，获得 {intent.val} 点护盾。")
        elif intent.type == "portal_instability":
            before_len = len(run.node_data.get("battle_logs", []))
            engine._damage_target(run, "p0", val, source=f"enemy:{enemy.name}", damage_type="psychic")
            after_logs = run.node_data.get("battle_logs", [])
            dmg_msg = after_logs.pop() if len(after_logs) > before_len else ""
            engine._add_buff_to(run.player, "discard_next_turn", "下回合弃牌", "在下一回合开始时，你将随机丢弃等同于此状态层数的手牌", 1)
            logs.append(f"【{enemy.name}】引发传送门不稳定。{dmg_msg}，且使玩家在下一回合开始时将被迫随机丢弃 1 张手牌。")
