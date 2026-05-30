import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game.models.state import GameRun, PlayerState, EnemyState, BuffState
from game.core.battle_engine import BattleEngine

class DummySaveManager:
    def save_save(self, user_id, run):
        pass

def run_tests():
    mgr = DummySaveManager()
    engine = BattleEngine(mgr)

    enemy = EnemyState(
        name="奥术巨魔",
        hp=50,
        max_hp=50,
        shield=0,
        actions=1,
        bonus_actions=1,
        max_actions=1,
        max_bonus_actions=1,
        intent_a_type="attack",
        intent_a_val=10,
        intent_a_desc="攻击 (造成 10 伤害)",
        intent_ba_type="defend",
        intent_ba_val=5,
        intent_ba_desc="防御 (获得 5 护盾)"
    )

    player = PlayerState(hp=45, max_hp=45, shield=0, gold=10, stage=1)
    run = GameRun(user_id="test_user", node_type="battle", player=player, enemies=[enemy])

    engine._sync_enemy_intents(enemy)
    assert enemy.intent_a_type == "attack"
    assert enemy.intent_ba_type == "defend"

    enemy.actions = 0
    engine._sync_enemy_intents(enemy)
    assert enemy.intent_a_type == ""
    assert "已取消" in enemy.intent_a_desc
    assert enemy.intent_ba_type == "defend"

    enemy.bonus_actions = 0
    engine._sync_enemy_intents(enemy)
    assert enemy.intent_ba_type == ""
    assert "已取消" in enemy.intent_ba_desc

    enemy.actions = 1
    enemy.bonus_actions = 1
    enemy.intent_a_type = "attack"
    enemy.intent_a_desc = "攻击 (造成 10 伤害)"
    enemy.intent_ba_type = "defend"
    enemy.intent_ba_desc = "防御 (获得 5 护盾)"
    engine._add_buff_to(enemy, "stun", "眩晕", "无法行动", 1)

    assert enemy.actions == 0
    assert enemy.bonus_actions == 0
    assert enemy.intent_a_type == ""
    assert "眩晕" in enemy.intent_a_desc
    assert enemy.intent_ba_type == ""

    enemy.buffs.clear()
    enemy.actions = 1
    enemy.bonus_actions = 1
    enemy.intent_a_type = "attack"
    enemy.intent_a_val = 10
    enemy.intent_a_desc = "攻击 (造成 10 伤害)"
    enemy.intent_ba_type = "defend"
    enemy.intent_ba_val = 5
    enemy.intent_ba_desc = "防御 (获得 5 护盾)"

    logs = []
    enemy.intent_type = "old_temp_type"
    enemy.intent_val = 999
    engine._enemy_turn(run)

    assert enemy.intent_type == "old_temp_type"
    assert enemy.intent_val == 999

    print("Enemy intent sync and temporary pointer recovery tests passed successfully!")

if __name__ == "__main__":
    run_tests()
