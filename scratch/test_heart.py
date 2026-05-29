import os
import sys
import io
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from game.models.state import GameRun, PlayerState, EnemyState
from game.models.manager import SaveManager
from game.core.battle_engine import BattleEngine

class DummySaveManager:
    def save_save(self, user_id, run):
        pass
    def delete_save(self, user_id):
        pass

def test_heart_battle():
    sm = DummySaveManager()
    engine = BattleEngine(sm)

    player = PlayerState(
        hp=50,
        max_hp=50,
        shield=10,
        gold=100,
        stage=20,
        deck=["dagger_throw", "dagger_throw", "dagger_throw"],
        draw_pile=[],
        discard_pile=[],
        hand=[],
        actions=2,
        bonus_actions=2
    )
    run = GameRun(
        user_id="test_heart_user",
        node_type="battle",
        player=player,
        enemies=[],
        node_data={"difficulty": "boss"},
        map_data={}
    )

    print("=== 1. 初始化第20层BOSS战 ===")
    engine._init_battle_node(run, "boss")

    assert len(run.enemies) == 1
    heart = run.enemies[0]
    assert heart.name == "腐化之心"
    assert heart.hp == 120
    assert heart.max_hp == 120
    assert heart.max_actions == 1
    assert heart.max_bonus_actions == 2

    has_beat = any(b.id == "beat_of_death" for b in heart.buffs)
    assert has_beat
    print("✅ 腐化之心初始化验证通过！")

    print("\n=== 2. 验证死亡律动伤害扣减 ===")
    player.shield = 10
    player.hand = ["dagger_throw"]
    old_shield = player.shield
    old_hp = player.hp
    
    res = engine.play_card(run, 1)
    print(f"出牌反馈: {res}")
    assert player.shield == old_shield - 1
    assert player.hp == old_hp
    assert "死亡律动" in res

    player.shield = 0
    player.hand = ["dagger_throw"]
    player.actions = 2
    old_hp = player.hp
    res = engine.play_card(run, 1)
    print(f"无盾出牌反馈: {res}")
    assert player.shield == 0
    assert player.hp == old_hp - 1
    print("✅ 死亡律动伤害与护盾/生命扣减验证通过！")

    print("\n=== 3. 验证腐化之心的4回合意图循环 ===")
    assert heart.intent_a_type == "debuff"
    assert "邪恶之语" in heart.intent_a_desc
    assert heart.intent_ba_type == "defend_large"
    assert "暗影护盾" in heart.intent_ba_desc
    assert heart.intent_ba2_type == "drain_ba"
    assert "虚空之歌" in heart.intent_ba2_desc
    print("✅ 回合 1 意图符合预期！")

    player.hp = 50
    engine.end_turn(run)
    assert run.node_data.get("heart_turn") == 2
    assert heart.intent_a_type == "multi_attack"
    assert "血弹喷射" in heart.intent_a_desc
    assert heart.intent_ba_type == "defend_normal"
    assert heart.intent_ba2_type == "heart_strike"
    print("✅ 回合 2 意图符合预期！")

    engine.end_turn(run)
    assert run.node_data.get("heart_turn") == 3
    assert heart.intent_a_type == "big_attack"
    assert "毁灭之痛" in heart.intent_a_desc
    assert heart.intent_ba_type == "defend_normal"
    assert heart.intent_ba2_type == "gaze_discard"
    print("✅ 回合 3 意图符合预期！")

    engine.end_turn(run)
    assert run.node_data.get("heart_turn") == 4
    assert heart.intent_a_type == "strength_buff"
    assert "充能" in heart.intent_a_desc
    assert heart.intent_ba_type == "defend_large"
    assert heart.intent_ba2_type == "heart_heal"
    print("✅ 回合 4 意图符合预期！")

    engine.end_turn(run)
    assert run.node_data.get("heart_turn") == 5
    assert heart.intent_a_type == "debuff"
    assert heart.intent_ba_type == "defend_large"
    assert heart.intent_ba2_type == "drain_ba"
    print("✅ 意图循环回到回合 1 验证通过！")

    print("\n=== 4. 验证意图执行逻辑与减BA机制 ===")
    run.node_data["heart_turn"] = 1
    engine._roll_enemy_intent(run)
    
    logs = []
    engine._enemy_turn(run)
    assert run.node_data.get("drain_ba") is True
    
    engine.end_turn(run)
    assert player.bonus_actions == 0
    assert "drain_ba" not in run.node_data
    print("✅ 减BA结算机制校验通过！")

if __name__ == "__main__":
    test_heart_battle()
    print("\n🎉 所有测试均已成功通过！")
