import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.state import GameRun, PlayerState, EnemyState, MinionState, Card
from game.core.battle_engine import BattleEngine
from game.models.manager import SaveManager
from game.entities.cards.base import ALL_CARDS

def test_all():
    save_mgr = SaveManager("data_test")
    engine = BattleEngine(save_mgr)
    
    player = PlayerState(
        hp=50,
        max_hp=100,
        shield=0,
        gold=100,
        stage=1,
        deck=["mass_healing_word", "chain_lightning", "magic_missile"],
        hand=["mass_healing_word", "chain_lightning", "magic_missile"],
        minions={
            "1": MinionState("mercenary", "雇佣兵", 5, 10, 4, 1, 0)
        }
    )
    
    run = GameRun(
        user_id="test_user",
        node_type="battle",
        player=player,
        enemies=[
            EnemyState("哥布林掠夺者 A", 20, 20, 0),
            EnemyState("哥布林掠夺者 B", 20, 20, 0),
            EnemyState("地底史莱姆", 15, 15, 0)
        ]
    )
    
    run.player.actions = 10
    run.player.bonus_actions = 10
    
    card_heal = ALL_CARDS["mass_healing_word"]
    card_heal.execute(run, "p0", engine)
    assert run.player.hp == 58
    assert run.player.minions["1"].hp == 10
    
    card_chain = ALL_CARDS["chain_lightning"]
    card_chain.execute(run, "e1", engine)
    assert len(run.enemies) == 3
    assert run.enemies[0].hp == 8
    assert run.enemies[1].hp == 8
    assert run.enemies[2].hp == 15
    
    enemy_mm = run.enemies[2]
    enemy_mm.shield = 20
    card_mm = ALL_CARDS["magic_missile"]
    card_mm.execute(run, "e3", engine)
    assert enemy_mm.shield == 20
    assert enemy_mm.hp == 6
    
    assert len(run.node_data.get("battle_logs", [])) > 0
    last_log = run.node_data["battle_logs"][-1]
    assert "对护盾造成" not in last_log
    assert "对生命造成" in last_log
    assert "（" not in last_log

    from game.entities.enemies.minions import ShadowFiendTemplate
    fiend_template = ShadowFiendTemplate("暗影影魔")
    fiend_enemy = EnemyState("暗影影魔", 30, 30, 0, intent_type="shadow_strike", intent_val=6)
    fiend_logs = []
    run.player.hp = 50
    run.player.shield = 10
    fiend_template.execute_intent(run, engine, fiend_enemy, fiend_logs)
    assert run.player.shield == 10
    assert run.player.hp == 44
    assert len(fiend_logs) == 1
    assert "对【玩家】造成 6 点真实伤害，对生命造成 6 伤害" in fiend_logs[0]

    from game.entities.buffs.buffs import BeatOfDeathBuff
    beat_buff = BeatOfDeathBuff(2)
    class FakeEvent:
        def __init__(self, run, engine):
            self.run = run
            self.engine = engine
    evt = FakeEvent(run, engine)
    run.player.hp = 50
    run.player.shield = 0
    run.node_data["battle_logs"] = []
    beat_buff.on_card_played(evt, None, None)
    assert run.player.hp == 48
    assert len(run.node_data["battle_logs"]) == 2
    assert "造成 2 点力场伤害" in run.node_data["battle_logs"][-1]

    run.node_data["battle_logs"] = []
    engine._damage_target(run, "e3", 0, damage_type="cold")
    assert len(run.node_data["battle_logs"]) == 1
    assert "对【地底史莱姆】造成 0 点寒冷伤害（但地底史莱姆免疫了这次攻击！）" in run.node_data["battle_logs"][-1]

    print("ALL TESTS PASSED!")

if __name__ == "__main__":
    test_all()
