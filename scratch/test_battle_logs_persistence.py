import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.manager import SaveManager
from game.models.state import GameRun, PlayerState, EnemyState

def test():
    save_manager = SaveManager()
    user_id = "test_user_logs_persistence"
    save_manager.delete_save(user_id)

    player = PlayerState(
        hp=45,
        max_hp=45,
        shield=0,
        gold=20,
        stage=3,
        deck=[],
        hand=[],
        actions=2,
        bonus_actions=1
    )

    run = GameRun(
        user_id=user_id,
        node_type="battle",
        player=player,
        enemies=[]
    )

    run.node_data["battle_logs"] = ["log1", "log2"]

    save_manager.save_save(user_id, run)

    if "battle_logs" not in run.node_data:
        print("FAIL: battle_logs was permanently popped from memory")
        sys.exit(1)

    loaded_run = save_manager.load_save(user_id)
    if loaded_run is None:
        print("FAIL: loaded_run is None")
        sys.exit(1)

    if "battle_logs" in loaded_run.node_data:
        print("FAIL: battle_logs was saved to disk save file!")
        sys.exit(1)

    save_manager.delete_save(user_id)
    print("SUCCESS: Battle logs persistence test passed perfectly!")

if __name__ == "__main__":
    test()
