import os
import sys
import io

if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.state import GameRun, PlayerState, EnemyState, BuffState
from game.core.battle_engine import BattleEngine

class DummySaveManager:
    def save_save(self, user_id, run):
        pass
    def delete_save(self, user_id):
        pass

def run_echo_test(stacks, num_cards_to_play):
    player = PlayerState(
        hp=30,
        max_hp=30,
        shield=0,
        gold=100,
        stage=2,
        deck=["fire_bolt"] * 10,
        draw_pile=["fire_bolt"] * 10,
        discard_pile=[],
        exhaust_pile=[],
        graveyard=[],
        hand=["fire_bolt"] * 10,
        actions=99,
        bonus_actions=99,
        buffs=[BuffState(id="echo_form", name="回响形态", stacks=stacks, desc="")]
    )
    enemy = EnemyState(
        name="测试敌人",
        hp=9999,
        max_hp=9999,
        shield=0
    )
    run = GameRun(
        user_id="test_user_echo",
        node_type="battle",
        player=player,
        enemies=[enemy]
    )
    engine = BattleEngine(DummySaveManager())
    
    results = []
    for i in range(num_cards_to_play):
        res = engine.play_card(run, 1)
        echo_count = res.count("[回响触发]")
        results.append(echo_count)
    return results

def test_echo_form():
    res5 = run_echo_test(5, 3)
    assert res5 == [5, 0, 0]

    res10 = run_echo_test(10, 3)
    assert res10 == [8, 2, 0]

    res24 = run_echo_test(24, 4)
    assert res24 == [8, 8, 8, 0]

    print("Echo Form logic test passed successfully!")

if __name__ == "__main__":
    test_echo_form()
