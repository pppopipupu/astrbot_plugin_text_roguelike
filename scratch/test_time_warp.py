import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.state import GameRun, PlayerState, EnemyState
from game.core.battle_engine import BattleEngine
from game.entities.cards import ALL_CARDS

class DummySaveManager:
    def save_save(self, user_id, run):
        pass
    def delete_save(self, user_id):
        pass

def run_test():
    player = PlayerState(
        hp=30,
        max_hp=30,
        shield=0,
        gold=100,
        stage=2,
        deck=["quick_strike", "quick_strike", "time_warp", "first_aid"],
        draw_pile=["quick_strike"],
        discard_pile=["first_aid"],
        exhaust_pile=[],
        graveyard=[],
        hand=["time_warp", "quick_strike"],
        actions=2,
        bonus_actions=1
    )
    enemy = EnemyState(
        name="冰霜史莱姆",
        hp=10,
        max_hp=10,
        shield=0
    )
    run = GameRun(
        user_id="test_user",
        node_type="battle",
        player=player,
        enemies=[enemy]
    )

    engine = BattleEngine(DummySaveManager())
    
    print("Before playing time_warp:")
    print("hand:", player.hand)
    print("draw_pile:", player.draw_pile)
    print("discard_pile:", player.discard_pile)
    print("exhaust_pile:", player.exhaust_pile)

    res = engine.play_card(run, 1)
    print("Play result:", res)

    print("After playing time_warp:")
    print("hand:", player.hand)
    print("draw_pile:", player.draw_pile)
    print("discard_pile:", player.discard_pile)
    print("exhaust_pile:", player.exhaust_pile)

    assert "time_warp" in player.exhaust_pile
    assert "time_warp" not in player.hand
    assert "time_warp" not in player.discard_pile
    assert "time_warp" not in player.draw_pile
    print("Success: Time Warp card was successfully exhausted!")

if __name__ == "__main__":
    run_test()
