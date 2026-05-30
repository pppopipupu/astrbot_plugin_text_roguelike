import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.state import GameRun, PlayerState, EnemyState, EnemyIntentState
from game.core.battle_engine import BattleEngine
from game.models.manager import SaveManager
from game.renderer.battle import render_battle, render_detailed_battle

def test_dynamic_intent():
    mgr = SaveManager()
    engine = BattleEngine(mgr)
    
    player = PlayerState(
        hp=50,
        max_hp=50,
        shield=0,
        gold=100,
        stage=10
    )
    
    dragon = EnemyState(
        name="远古红龙",
        hp=140,
        max_hp=140,
        shield=0,
        actions=1,
        bonus_actions=2,
        max_actions=1,
        max_bonus_actions=2
    )
    
    run = GameRun(
        user_id="test_user",
        node_type="battle",
        player=player,
        enemies=[dragon]
    )
    
    engine._roll_enemy_intent(run)
    assert len(dragon.intents) == 3
    assert dragon.intents[0].cost_a == 1
    assert dragon.intents[0].cost_ba == 0
    assert dragon.intents[1].cost_a == 0
    assert dragon.intents[1].cost_ba == 1
    assert dragon.intents[2].cost_a == 0
    assert dragon.intents[2].cost_ba == 1

    dragon.intents = [
        EnemyIntentState(type="summon", val=0, desc="召唤魔仆", cost_a=1, cost_ba=0),
        EnemyIntentState(type="defend", val=10, desc="获得 10 护盾", cost_a=0, cost_ba=1),
        EnemyIntentState(type="attack", val=8, desc="攻击 (造成 8 伤害)", cost_a=0, cost_ba=1)
    ]
    engine._sync_enemy_intents(dragon)
    
    battle_output = render_battle(run)
    assert "远古红龙" in battle_output
    assert "A: 召唤魔仆" in battle_output
    assert "BA: 获得 10 护盾 + 攻击" in battle_output
    
    logs = []
    res_logs = engine._enemy_turn(run)
    
    assert len(run.enemies) == 2
    assert run.enemies[1].name == "魔仆"
    assert run.enemies[0].shield == 10
    
    engine._add_buff_to(dragon, "stun", "眩晕", "本回合无法行动", 1)
    engine._sync_enemy_intents(dragon)
    
    assert len(dragon.intents) == 1
    assert dragon.intents[0].type == "stun"
    assert "眩晕" in dragon.intents[0].desc
    
    battle_output_stun = render_battle(run)
    assert "A: 眩晕 (本回合无法行动)" in battle_output_stun
    
    print("Success: All dynamic intent tests passed!")

if __name__ == "__main__":
    test_dynamic_intent()
