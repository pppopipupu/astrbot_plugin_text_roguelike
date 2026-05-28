import os
import sys
import io
import asyncio

if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models import GameRun, PlayerState, EnemyState
from game.battle_engine import BattleEngine
from main import MyPlugin

class DummyContext:
    pass

class DummySaveManager:
    def save_save(self, user_id, run):
        pass
    def delete_save(self, user_id):
        pass

def test_fleeting_and_agile():
    player = PlayerState(
        hp=30,
        max_hp=30,
        shield=0,
        gold=100,
        stage=2,
        deck=["agile_strike", "fleeting_spark", "first_aid"],
        draw_pile=["first_aid", "first_aid"],
        discard_pile=[],
        exhaust_pile=[],
        graveyard=[],
        hand=["fleeting_spark", "agile_strike"],
        actions=3,
        bonus_actions=3
    )
    enemy = EnemyState(
        name="冰霜史莱姆",
        hp=20,
        max_hp=20,
        shield=0
    )
    run = GameRun(
        user_id="test_user",
        node_type="battle",
        player=player,
        enemies=[enemy]
    )

    plugin = MyPlugin(DummyContext())
    plugin.save_manager.save_save("test_user", run)

    res, term = plugin._execute_sub_action("test_user", run, ["使用", "1"])
    print("Play fleeting_spark output:\n", res)
    assert run.node_data.get("pending_discard") is True
    assert enemy.hp == 14
    assert len(player.hand) == 3
    assert "fleeting_spark" not in player.deck
    assert "fleeting_spark" not in player.hand
    assert "fleeting_spark" not in player.discard_pile
    assert "fleeting_spark" not in player.exhaust_pile
    print("Test 1 (Fleeting Spark & Permanent Deck Removal) Passed!")

    res, term = plugin._execute_sub_action("test_user", run, ["使用", "1"])
    print("Try normal action output:\n", res)
    assert "你必须先丢弃一张卡牌" in res
    print("Test 2 (Pending Discard Interception) Passed!")

    res, term = plugin._execute_sub_action("test_user", run, ["选择", "2"])
    print("Discard normal card output:\n", res)
    assert "你丢弃了手牌中的【绷带包扎】" in res
    assert "first_aid" in player.discard_pile
    assert run.node_data.get("pending_discard") is None
    print("Test 3 (Manual Discard Normal Card) Passed!")

    run.node_data["pending_discard"] = True
    res, term = plugin._execute_sub_action("test_user", run, ["选择", "1"])
    print("Discard agile card output:\n", res)
    assert "你丢弃了手牌中的【灵巧打击】" in res
    assert "触发[灵巧]" in res
    assert "对【冰霜史莱姆】造成了 4 点伤害" in res
    assert enemy.hp == 10
    assert "agile_strike" in player.discard_pile
    print("Test 4 (Manual Discard Agile Card & Auto-play) Passed!")

    player.hand = ["agile_strike"]
    from game.enemy_impl import GhostArchmageTemplate
    template = GhostArchmageTemplate("幽灵大魔法师")
    logs = []
    enemy.intent_type = "mana_drain"
    enemy.intent_val = 0
    engine = plugin.engine.battle_engine
    template.execute_intent(run, engine, enemy, logs)
    logs_str = "\n".join(logs)
    print("Enemy drain output:\n", logs_str)
    assert "迫使玩家随机丢弃了卡牌【灵巧打击】" in logs_str
    assert "触发[灵巧]" in logs_str
    assert "对【冰霜史莱姆】造成了 4 点伤害" in logs_str
    assert enemy.hp == 6
    print("Test 5 (Enemy Drain Agile Card & Auto-play) Passed!")

if __name__ == "__main__":
    test_fleeting_and_agile()
    print("ALL NEW MECHANICS TESTS PASSED!")
