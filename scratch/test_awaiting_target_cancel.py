import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.manager import SaveManager
from game.models.state import GameRun, PlayerState, EnemyState
from game.engine import GameEngine
from game.core.cli_router import CLIRouter

def test():
    save_manager = SaveManager()
    engine = GameEngine(save_manager)
    router = CLIRouter(save_manager, engine)
    user_id = "test_user_awaiting_cancel"
    save_manager.delete_save(user_id)

    player = PlayerState(
        hp=45,
        max_hp=45,
        shield=0,
        gold=20,
        stage=3,
        deck=["fleeting_spark", "fleeting_spark"],
        hand=["fleeting_spark", "fleeting_spark"],
        actions=2,
        bonus_actions=1
    )

    enemies = [
        EnemyState(
            name="哥布林 A",
            hp=18,
            max_hp=18,
            shield=0,
            intent_type="attack",
            intent_val=6,
            intent_desc="攻击",
            intent_a_type="attack",
            intent_a_val=6,
            intent_a_desc="攻击"
        ),
        EnemyState(
            name="哥布林 B",
            hp=18,
            max_hp=18,
            shield=0,
            intent_type="shield",
            intent_val=7,
            intent_desc="防御",
            intent_a_type="shield",
            intent_a_val=7,
            intent_a_desc="防御"
        )
    ]

    run = GameRun(
        user_id=user_id,
        node_type="battle",
        player=player,
        enemies=enemies
    )

    run.node_data["state_stack"] = [{
        "type": "awaiting_target",
        "action": "play_card",
        "hand_idx": 1
    }]

    save_manager.save_save(user_id, run)

    generator = router.handle_command(user_id, ["p", "2"])
    results = list(generator)
    output_text = "\n".join(results)

    loaded_run = save_manager.load_save(user_id)
    state_stack = loaded_run.node_data.get("state_stack", [])

    if "❌ 取消使用操作。" in output_text:
        print("FAIL: Still got cancel warning message")
        sys.exit(1)

    if not state_stack:
        print("FAIL: state_stack is empty, should contain new awaiting_target for second card")
        sys.exit(1)

    top_state = state_stack[-1]
    if top_state.get("type") != "awaiting_target" or top_state.get("hand_idx") != 2:
        print(f"FAIL: unexpected top state: {top_state}")
        sys.exit(1)

    save_manager.delete_save(user_id)
    print("SUCCESS: Awaiting target auto-cancel and transition test passed perfectly!")

if __name__ == "__main__":
    test()
