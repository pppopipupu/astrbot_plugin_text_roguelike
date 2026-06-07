import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from game.models.state import GameRun, PlayerState, EnemyState, MinionState
from game.core.battle_engine import BattleEngine

class DummySaveManager:
    def save_save(self, user_id, run):
        pass
    def delete_save(self, user_id):
        pass

def main():
    player = PlayerState(
        hp=50,
        max_hp=50,
        shield=0,
        gold=100,
        stage=1,
        deck=[],
        hand=[],
        minions={
            "1": MinionState("mercenary", "雇佣兵", 10, 10, 4, 1, 0)
        }
    )
    enemy = EnemyState("哥布林", 20, 20, 0)
    run = GameRun(
        user_id="test_user",
        node_type="battle",
        player=player,
        enemies=[enemy]
    )
    engine = BattleEngine(DummySaveManager())
    print("Enemy HP before attack:", enemy.hp)
    res = engine.card_player.minion_attack(run, "1", "1")
    print("Result of attack:")
    print(res)
    print("Enemy HP after attack:", enemy.hp)
    print("Battle logs:")
    for log in run.node_data.get("battle_logs", []):
        print(log)

if __name__ == "__main__":
    main()
