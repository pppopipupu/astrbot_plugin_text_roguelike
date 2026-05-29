import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.manager import SaveManager
from game.models.state import GameRun, PlayerState, EnemyState

def test():
    save_manager = SaveManager()
    user_id = "test_user_save_load"
    save_manager.delete_save(user_id)

    player = PlayerState(
        hp=30,
        max_hp=30,
        shield=0,
        gold=20,
        stage=1,
        deck=["迅捷打击", "防御"],
        hand=["迅捷打击"],
        actions=2,
        bonus_actions=1
    )

    enemies = [
        EnemyState(
            name="冰霜史莱姆 A",
            hp=12,
            max_hp=12,
            shield=0,
            intent_type="shield",
            intent_val=6,
            intent_desc="防御",
            intent_a_type="shield",
            intent_a_val=6,
            intent_a_desc="防御",
            intent_ba2_type="attack",
            intent_ba2_val=3,
            intent_ba2_desc="攻击"
        )
    ]

    run = GameRun(
        user_id=user_id,
        node_type="battle",
        player=player,
        enemies=enemies
    )

    success = save_manager.save_save(user_id, run)
    if not success:
        print("FAIL: save_save returned False")
        sys.exit(1)

    loaded_run = save_manager.load_save(user_id)
    if loaded_run is None:
        print("FAIL: loaded_run is None")
        sys.exit(1)

    if loaded_run.user_id != user_id:
        print(f"FAIL: user_id mismatch: {loaded_run.user_id} vs {user_id}")
        sys.exit(1)

    if not loaded_run.enemies:
        print("FAIL: enemies list is empty")
        sys.exit(1)

    enemy = loaded_run.enemies[0]
    if enemy.name != "冰霜史莱姆 A":
        print(f"FAIL: enemy name mismatch: {enemy.name}")
        sys.exit(1)

    if enemy.intent_ba2_val != 3:
        print(f"FAIL: enemy intent_ba2_val mismatch: {enemy.intent_ba2_val}")
        sys.exit(1)

    save_manager.delete_save(user_id)
    print("SUCCESS: Save and Load test passed perfectly!")

if __name__ == "__main__":
    test()
