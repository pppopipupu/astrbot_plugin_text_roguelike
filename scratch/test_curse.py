import os
import sys
import io
import random

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

def test_innate_curse():
    player = PlayerState(
        hp=30,
        max_hp=30,
        shield=0,
        gold=100,
        stage=2,
        deck=["dagger_throw", "first_aid", "curse_agony"],
        draw_pile=[],
        discard_pile=[],
        exhaust_pile=[],
        graveyard=[],
        hand=[],
        actions=3,
        bonus_actions=3
    )
    run = GameRun(
        user_id="test_user",
        node_type="battle",
        player=player,
        enemies=[EnemyState(name="史莱姆", hp=10, max_hp=10, shield=0)]
    )
    engine = BattleEngine(DummySaveManager())
    engine._init_battle_node(run, "normal")
    assert "curse_agony" in player.hand
    print("Test 1: Innate curse in initial hand passed!")

def test_ethereal_curse():
    player = PlayerState(
        hp=30,
        max_hp=30,
        shield=0,
        gold=100,
        stage=2,
        deck=["dagger_throw"],
        draw_pile=["dagger_throw"] * 10,
        discard_pile=[],
        exhaust_pile=[],
        graveyard=[],
        hand=["curse_dazed", "dagger_throw"],
        actions=3,
        bonus_actions=3
    )
    run = GameRun(
        user_id="test_user",
        node_type="battle",
        player=player,
        enemies=[EnemyState(name="史莱姆", hp=10, max_hp=10, shield=0)]
    )
    engine = BattleEngine(DummySaveManager())
    engine.end_turn(run)
    assert "curse_dazed" in player.exhaust_pile
    assert "curse_dazed" not in player.discard_pile
    assert "dagger_throw" in player.discard_pile
    print("Test 2: Ethereal dazed card moved to exhaust_pile passed!")

def test_unplayable_curse():
    player = PlayerState(
        hp=30,
        max_hp=30,
        shield=0,
        gold=100,
        stage=2,
        deck=["dagger_throw"],
        draw_pile=[],
        discard_pile=[],
        exhaust_pile=[],
        graveyard=[],
        hand=["curse_dazed", "curse_agony"],
        actions=3,
        bonus_actions=3
    )
    run = GameRun(
        user_id="test_user",
        node_type="battle",
        player=player,
        enemies=[EnemyState(name="史莱姆", hp=10, max_hp=10, shield=0)]
    )
    engine = BattleEngine(DummySaveManager())
    res = engine.play_card(run, 1)
    assert "该卡牌不能被打出" in res
    res2 = engine.play_card(run, 2)
    assert "该卡牌不能被打出" in res2
    print("Test 3: Unplayable dazed and agony cards blocked passed!")

def test_curse_events():
    from game.event_impl import (
        TakeNecklaceOption,
        ShatterPortalOption,
        JumpCartOption,
        LootBodyOption,
        ReadScrollOption,
        AbsorbVoidOption
    )
    random.seed(42)
    
    player = PlayerState(hp=30, max_hp=30, shield=0, gold=100, stage=2, deck=["dagger_throw"])
    run = GameRun(user_id="test_user", node_type="event", player=player, node_data={})
    engine = MyPlugin(DummyContext()).engine
    
    opt = TakeNecklaceOption("冒险捞取项链", "take_necklace")
    res = opt.execute(run, engine)
    assert "curse_dazed" in player.deck
    assert player.hp == 30
    print("Event Test 1 (Take Necklace Option) passed!")
    
    player.hp = 30
    opt2 = ShatterPortalOption("摧毁传送门", "shatter_portal")
    res2 = opt2.execute(run, engine)
    assert "curse_agony" in player.deck
    assert player.hp == 30
    print("Event Test 2 (Shatter Portal Option) passed!")
    
    player.hp = 30
    opt3 = JumpCartOption("果断跳车", "jump_cart")
    res3 = opt3.execute(run, engine)
    assert "curse_dazed" in player.deck
    assert player.hp == 30
    print("Event Test 3 (Jump Cart Option) passed!")
    
    player.hp = 20
    opt4 = LootBodyOption("搜刮干尸", "loot_body")
    res4 = opt4.execute(run, engine)
    assert "curse_agony" in player.deck
    assert player.hp == 24
    print("Event Test 4 (Loot Body Option) passed!")
    
    player.hp = 30
    opt5 = ReadScrollOption("解读残卷", "read_scroll")
    res5 = opt5.execute(run, engine)
    assert "curse_dazed" in player.deck
    assert player.hp == 30
    print("Event Test 5 (Read Scroll Option) passed!")
    
    player.hp = 20
    opt6 = AbsorbVoidOption("将虚空吞噬", "absorb_void")
    res6 = opt6.execute(run, engine)
    assert "curse_agony" in player.deck
    assert player.hp == 26
    print("Event Test 6 (Absorb Void Option) passed!")

if __name__ == "__main__":
    test_innate_curse()
    test_ethereal_curse()
    test_unplayable_curse()
    test_curse_events()
    print("ALL CURSE & NEW CARD TYPES TESTS PASSED SUCCESSFULLY!")
