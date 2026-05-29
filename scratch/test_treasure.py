import os
import sys
import io

if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models import GameRun, PlayerState, EnemyState
from game.map_engine import MapEngine
from game.battle_engine import BattleEngine
from main import MyPlugin

class DummyContext:
    pass

class DummySaveManager:
    def save_save(self, user_id, run):
        pass
    def delete_save(self, user_id):
        pass
    def record_stage_passed(self, user_id):
        pass

def test_treasure_and_camp_card_select():
    player = PlayerState(
        hp=30,
        max_hp=30,
        shield=0,
        gold=10,
        stage=4,
        deck=["first_aid", "dagger_throw", "agile_strike"],
        draw_pile=[],
        discard_pile=[],
        exhaust_pile=[],
        graveyard=[],
        hand=[]
    )
    run = GameRun(
        user_id="test_user_treasure",
        node_type="treasure",
        player=player,
        enemies=[]
    )

    plugin = MyPlugin(DummyContext())
    map_engine = plugin.engine.map_engine
    map_engine.save_manager = DummySaveManager()
    
    map_engine._init_treasure_node(run)
    assert run.node_data.get("state") == "pending_remove"

    res = map_engine.choose_option(run, 3)
    assert run.node_type == "card_select"
    assert len(run.node_data.get("cards", [])) == 3
    assert player.gold > 10
    assert len(player.deck) == 2
    assert "first_aid" not in player.deck

    cards_to_select = run.node_data["cards"]
    res = map_engine.choose_option(run, 4)
    assert player.stage == 5
    assert len(player.deck) == 2

    player.stage = 3
    run.node_type = "rest"
    res = map_engine.choose_option(run, 2)
    assert run.node_type == "card_select"
    assert len(run.node_data.get("cards", [])) == 3

    chosen_card = run.node_data["cards"][0]
    res = map_engine.choose_option(run, 1)
    assert player.stage == 4
    assert len(player.deck) == 3
    assert chosen_card in player.deck

    player.stage = 5
    player.gold = 20
    run.node_type = "event"
    from game.event_impl import CoinFountainOption
    opt = CoinFountainOption("投入金币", "coin_fountain")
    res = opt.execute(run, map_engine)
    assert player.gold == 10
    assert run.node_type == "card_select"
    assert len(run.node_data.get("cards", [])) == 3
    
    res = map_engine.choose_option(run, 4)
    assert player.stage == 6
    assert len(player.deck) == 3

    print("Treasure and Camp Meditation card select test passed!")

if __name__ == "__main__":
    test_treasure_and_camp_card_select()
