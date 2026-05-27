import os
import sys
import io
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game.models import EnemyState, current_user_id
from game.manager import SaveManager
from game.engine import GameEngine

def run_test():
    user_id = "test_user_stats"
    current_user_id.set(user_id)
    save_manager = SaveManager()
    
    save_manager.delete_save(user_id)
    stats_path = save_manager.get_stats_path(user_id)
    if os.path.exists(stats_path):
        os.remove(stats_path)
        
    engine = GameEngine(save_manager)
    run = engine.start_new_game(user_id)
    
    enemy = EnemyState(
        name="测试怪物",
        hp=20,
        max_hp=20,
        shield=5
    )
    run.enemies = [enemy]
    
    enemy.shield -= 3
    
    enemy.shield -= 2
    enemy.hp -= 5
    
    enemy.hp -= 15
    
    engine.enter_next_stage(run)
    engine.enter_next_stage(run)
    
    stats = save_manager.load_stats(user_id)
    print(f"STATS - Damage: {stats.total_damage}, Kills: {stats.total_kills}, Stages: {stats.total_stages}")
    
    assert stats.total_damage == 25, f"Expected 25 damage, got {stats.total_damage}"
    assert stats.total_kills == 1, f"Expected 1 kill, got {stats.total_kills}"
    assert stats.total_stages == 2, f"Expected 2 stages, got {stats.total_stages}"
    
    from game.renderer import GameRenderer
    rendered = GameRenderer.render_stats(stats)
    print(rendered)
    print("ALL TESTS PASSED!")

if __name__ == "__main__":
    run_test()
