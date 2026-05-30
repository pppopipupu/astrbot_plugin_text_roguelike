import os
import sys
import io

if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.state import EnemyState, current_user_id, BuffState
from game.models.manager import SaveManager
from game.engine import GameEngine

def run_test():
    user_id = "test_user_heart_kill"
    current_user_id.set(user_id)
    save_manager = SaveManager()
    save_manager.delete_save(user_id)
    
    stats_path = save_manager.get_stats_path(user_id)
    if os.path.exists(stats_path):
        os.remove(stats_path)
        
    engine = GameEngine(save_manager)
    run = engine.start_new_game(user_id)
    
    run.node_type = "battle"
    enemy = EnemyState(
        name="腐化之心",
        hp=20,
        max_hp=20,
        shield=0
    )
    run.enemies = [enemy]
    
    run.player.hand = ["magic_missile"]
    run.player.buffs = [BuffState(id="echo_form", name="回响形态", stacks=8, desc="")]
    
    res = engine.play_card(run, 1, "e1")
    print(res)
    
    assert "未知敌人" not in res
    assert "腐化之心" in res
    
    stats = save_manager.load_stats(user_id)
    print(f"STATS - Damage: {stats.total_damage}, Kills: {stats.total_kills}")
    assert stats.total_kills == 1
    
    print("TEST PASSED!")

if __name__ == "__main__":
    run_test()
