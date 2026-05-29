import os
import sys
import io

if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.state import GameRun, PlayerState, EnemyState
from game.core.battle_engine import BattleEngine
from main import MyPlugin

class DummyContext:
    pass

class DummySaveManager:
    def save_save(self, user_id, run):
        pass
    def delete_save(self, user_id):
        pass

def test_card_retain_and_agile_bypass():
    player = PlayerState(
        hp=30,
        max_hp=30,
        shield=0,
        gold=100,
        stage=2,
        deck=["first_aid", "dagger_throw", "agile_strike"],
        draw_pile=["first_aid", "first_aid", "first_aid", "first_aid", "first_aid", "first_aid", "first_aid", "first_aid"],
        discard_pile=[],
        exhaust_pile=[],
        graveyard=[],
        hand=["first_aid", "dagger_throw", "agile_strike"],
        actions=2,
        bonus_actions=1
    )
    enemy = EnemyState(
        name="测试敌人",
        hp=20,
        max_hp=20,
        shield=0
    )
    run = GameRun(
        user_id="test_user_retain",
        node_type="battle",
        player=player,
        enemies=[enemy]
    )

    plugin = MyPlugin(DummyContext())
    engine = plugin.engine.battle_engine

    engine.end_turn(run)

    assert "first_aid" in player.hand
    assert "dagger_throw" not in player.hand
    assert "agile_strike" not in player.hand

    assert "dagger_throw" in player.discard_pile
    assert "agile_strike" in player.discard_pile

    assert enemy.hp == 20

    print("Retain and Agile Turn End Discard Bypass test passed!")

if __name__ == "__main__":
    test_card_retain_and_agile_bypass()
