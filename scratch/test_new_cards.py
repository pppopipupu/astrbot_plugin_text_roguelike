import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.state import GameRun, PlayerState, EnemyState, MinionState
from game.core.battle_engine import BattleEngine
from game.models.manager import SaveManager
from game.entities.cards.base import ALL_CARDS

def test_refresh_spirit():
    save_mgr = SaveManager("data_test")
    engine = BattleEngine(save_mgr)
    
    player = PlayerState(
        hp=50,
        max_hp=100,
        shield=0,
        gold=100,
        stage=1,
        deck=["refresh_spirit", "magic_missile", "mercenary", "fire_bolt"],
        hand=["magic_missile", "mercenary", "fire_bolt"],
        minions={}
    )
    
    run = GameRun(
        user_id="test_user",
        node_type="battle",
        player=player,
        enemies=[EnemyState("哥布林掠夺者", 20, 20, 0)]
    )
    
    card = ALL_CARDS["refresh_spirit"]
    res = card.execute(run, "p0", engine)
    
    assert run.player.shield == 12
    assert "magic_missile" in run.player.exhaust_pile
    assert "fire_bolt" in run.player.exhaust_pile
    assert "mercenary" not in run.player.exhaust_pile
    assert len(run.player.hand) == 1
    assert run.player.hand[0] == "mercenary"
    assert "消耗了 2 张非随从牌" in res
    assert "获得了 12 点护盾" in res

def test_sunburst():
    save_mgr = SaveManager("data_test")
    engine = BattleEngine(save_mgr)
    
    player = PlayerState(
        hp=50,
        max_hp=100,
        shield=0,
        gold=100,
        stage=1,
        deck=["sunburst"],
        hand=[],
        minions={
            "1": MinionState("mercenary", "雇佣兵 A", 10, 10, 4, 1, 0),
            "2": MinionState("mercenary", "雇佣兵 B", 10, 10, 4, 1, 0)
        }
    )
    
    run = GameRun(
        user_id="test_user",
        node_type="battle",
        player=player,
        enemies=[
            EnemyState("哥布林掠夺者 A", 20, 20, 0),
            EnemyState("哥布林掠夺者 B", 20, 20, 0)
        ]
    )
    
    card = ALL_CARDS["sunburst"]
    res = card.execute(run, "p0", engine)
    
    assert len(run.player.minions) == 0
    assert len(run.enemies) == 2
    assert run.enemies[0].hp == 4
    assert run.enemies[1].hp == 4
    assert "释放【阳炎爆】" in res

if __name__ == "__main__":
    test_refresh_spirit()
    test_sunburst()
    print("ALL NEW CARD TESTS PASSED!")
