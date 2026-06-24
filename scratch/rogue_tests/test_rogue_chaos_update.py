import unittest
import random
from scratch.rogue_tests.base import *
from game.models.state import PlayerState, GameRun, EnemyState
from game.entities.cards.base import ALL_CARDS
from game.core.battle_engine import BattleEngine
from game.entities.events.chaos_events import (
    ReadVoidTomeOption, BurnVoidBooksOption, SacrificeMindOption,
    BuyBlackmarketRelicOption, RobBlackmarketOption, SellFleshOption,
    DrinkTimeSandOption, AccelerateCinderOption, TouchTimeRiftOption,
    LootWreckageOption, RepairEngineOption, BraveStormOption,
    DigGraveOption, ReadEpitaphOption, CarveOwnNameOption
)

class TestRogueChaosUpdate(unittest.TestCase):
    def test_source_of_cinder(self):
        class DummySaveManager:
            def save_save(self, user_id, run): pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=40, max_hp=40, shield=0, gold=100, stage=1,
            deck=["warrior_source_of_cinder"], hand=["warrior_source_of_cinder"],
            actions=3, bonus_actions=2, buffs=[]
        )
        run = GameRun(user_id="test_cinder", node_type="battle", player=player, enemies=[EnemyState("e1", 10, 10, 0)])
        
        card = ALL_CARDS["warrior_source_of_cinder"]
        self.assertEqual(card.cost_a, 2)
        self.assertEqual(card.cost_ba, 1)
        
        card_up = ALL_CARDS["warrior_source_of_cinder+"]
        self.assertEqual(card_up.cost_a, 1)
        self.assertEqual(card_up.cost_ba, 1)
        self.assertTrue(card_up.exhaust)
        
        card.execute(run, None, engine)
        cinder_buff = next((b for b in player.buffs if b.id == "source_of_cinder"), None)
        self.assertIsNotNone(cinder_buff)
        self.assertEqual(cinder_buff.stacks, 1)
        
        player.actions = 2
        player.bonus_actions = 1
        from game.models.events import TurnStartEvent
        evt = TurnStartEvent(run, is_player=True)
        engine.event_bus.dispatch(evt)
        self.assertEqual(player.actions, 3)
        self.assertEqual(player.bonus_actions, 2)

    def test_emperor_eye_no_hand(self):
        class DummySaveManager:
            def save_save(self, user_id, run): pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=40, max_hp=40, shield=0, gold=100, stage=1,
            deck=["neutral_emperor_eye"], hand=[],
            actions=3, bonus_actions=2, buffs=[]
        )
        run = GameRun(user_id="test_eye_no_hand", node_type="battle", player=player, enemies=[EnemyState("e1", 10, 10, 0)])
        card = ALL_CARDS["neutral_emperor_eye"]
        res = card.execute(run, None, engine)
        self.assertIn("保留了手牌中的【无】", res)
        self.assertEqual(len(player.hand), 0)

    def test_emperor_eye_with_param(self):
        class DummySaveManager:
            def save_save(self, user_id, run): pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=40, max_hp=40, shield=0, gold=100, stage=1,
            deck=["neutral_emperor_eye", "fire_bolt", "warrior_defend"],
            hand=["fire_bolt", "warrior_defend"],
            actions=3, bonus_actions=2, buffs=[]
        )
        run = GameRun(user_id="test_eye_param", node_type="battle", player=player, enemies=[EnemyState("e1", 10, 10, 0)])
        card = ALL_CARDS["neutral_emperor_eye"]
        run.node_data["current_playing_card_hand_idx"] = 0
        res = card.execute(run, "2", engine)
        self.assertIn("保留了手牌中的【火焰弹】", res)

    def test_emperor_eye_no_param(self):
        class DummySaveManager:
            def save_save(self, user_id, run): pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=40, max_hp=40, shield=0, gold=100, stage=1,
            deck=["neutral_emperor_eye", "fire_bolt", "warrior_defend"],
            hand=["fire_bolt", "warrior_defend"],
            actions=3, bonus_actions=2, buffs=[]
        )
        run = GameRun(user_id="test_eye_no_param", node_type="battle", player=player, enemies=[EnemyState("e1", 10, 10, 0)])
        card = ALL_CARDS["neutral_emperor_eye"]
        res = card.execute(run, None, engine)
        self.assertIn("请选择你要保留的手牌", res)
        self.assertEqual(run.node_data["state_stack"][-1]["type"], "overload_star_select")

    def test_no_retreat_events(self):
        class DummyEngine:
            def __init__(self):
                self.stage_entered = False
                class DummySaveManager:
                    def save_save(self, user_id, run): pass
                self.save_manager = DummySaveManager()
                class DummyExploreEngine:
                    def start_gem_insert_flow(self, run, gem_id, next_type, next_data):
                        return "inserted"
                self.explore_engine = DummyExploreEngine()
                class DummyBattleEngine:
                    def _init_battle_node(self, run, node_type): pass
                    def _append_logs_to_res(self, run, msg): return msg
                self.battle_engine = DummyBattleEngine()
            def enter_next_stage(self, run):
                self.stage_entered = True

        eng = DummyEngine()
        player = PlayerState(
            hp=30, max_hp=30, shield=0, gold=100, stage=1,
            deck=["fire_bolt", "shield_block"], hand=[], actions=3, bonus_actions=2
        )
        run = GameRun(user_id="test_events", node_type="event", player=player, enemies=[])
        
        opt1 = ReadVoidTomeOption()
        res1 = opt1.execute(run, eng)
        self.assertEqual(player.hp, 20)
        self.assertIn("curse_dimensional_tear", player.deck)
        self.assertTrue(eng.stage_entered)

        player.hp = 30
        player.max_hp = 30
        eng.stage_entered = False
        opt2 = BurnVoidBooksOption()
        res2 = opt2.execute(run, eng)
        self.assertEqual(player.max_hp, 15)
        self.assertEqual(player.hp, 15)
        self.assertIn("doomsday_core", player.relics)
        self.assertTrue(eng.stage_entered)

        player.hp = 30
        eng.stage_entered = False
        opt3 = SacrificeMindOption()
        res3 = opt3.execute(run, eng)
        self.assertEqual(player.hp, 22)
        self.assertIn("curse_dazed", player.deck)
        self.assertTrue(eng.stage_entered)

        player.gold = 100
        eng.stage_entered = False
        opt4 = BuyBlackmarketRelicOption()
        res4 = opt4.execute(run, eng)
        self.assertEqual(player.gold, 50)
        self.assertTrue(eng.stage_entered)

        player.gold = 10
        player.hp = 30
        eng.stage_entered = False
        opt5 = BuyBlackmarketRelicOption()
        res5 = opt5.execute(run, eng)
        self.assertEqual(player.hp, 15)
        self.assertTrue(eng.stage_entered)

        eng.stage_entered = False
        opt6 = RobBlackmarketOption()
        res6 = opt6.execute(run, eng)
        self.assertTrue(eng.stage_entered or run.node_type == "battle")

        player.max_hp = 30
        player.hp = 30
        player.gold = 10
        eng.stage_entered = False
        opt7 = SellFleshOption()
        res7 = opt7.execute(run, eng)
        self.assertEqual(player.max_hp, 20)
        self.assertEqual(player.hp, 20)
        self.assertEqual(player.gold, 90)
        self.assertTrue(eng.stage_entered)

        player.max_hp = 30
        player.hp = 30
        eng.stage_entered = False
        opt8 = DrinkTimeSandOption()
        res8 = opt8.execute(run, eng)
        self.assertEqual(player.max_hp, 15)
        self.assertEqual(player.hp, 15)
        self.assertIn("time_sand_blessing", player.relics)
        self.assertTrue(eng.stage_entered)

        player.hp = 30
        eng.stage_entered = False
        opt9 = AccelerateCinderOption()
        res9 = opt9.execute(run, eng)
        self.assertEqual(player.hp, 18)
        self.assertIn("warrior_source_of_cinder", player.deck)
        self.assertTrue(eng.stage_entered)

        player.hp = 30
        player.deck = ["fire_bolt", "shield_block", "arcane_torrent"]
        eng.stage_entered = False
        opt10 = TouchTimeRiftOption()
        res10 = opt10.execute(run, eng)
        self.assertEqual(player.hp, 24)
        self.assertIn("curse_dimensional_tear", player.deck)
        self.assertTrue(eng.stage_entered)

        player.hp = 30
        player.gold = 10
        eng.stage_entered = False
        opt11 = LootWreckageOption()
        res11 = opt11.execute(run, eng)
        self.assertEqual(player.hp, 18)
        self.assertEqual(player.gold, 130)
        self.assertIn("curse_dazed", player.deck)
        self.assertTrue(eng.stage_entered)

        player.max_hp = 30
        player.hp = 30
        player.gold = 100
        eng.stage_entered = False
        opt12 = RepairEngineOption()
        res12 = opt12.execute(run, eng)
        self.assertEqual(player.gold, 70)
        self.assertEqual(player.max_hp, 20)
        self.assertEqual(player.hp, 20)
        self.assertTrue(eng.stage_entered)

        player.hp = 30
        eng.stage_entered = False
        opt13 = BraveStormOption()
        res13 = opt13.execute(run, eng)
        self.assertEqual(player.hp, 18)
        self.assertTrue(eng.stage_entered)

        player.deck = ["fire_bolt"]
        eng.stage_entered = False
        opt14 = DigGraveOption()
        res14 = opt14.execute(run, eng)
        self.assertIn("necromancer_skull", player.relics)
        self.assertTrue(eng.stage_entered)

        player.max_hp = 30
        player.hp = 30
        player.gold = 100
        eng.stage_entered = False
        opt15 = ReadEpitaphOption()
        res15 = opt15.execute(run, eng)
        self.assertEqual(player.max_hp, 50)
        self.assertEqual(player.hp, 50)
        self.assertEqual(player.gold, 0)
        self.assertIn("curse_agony", player.deck)
        self.assertTrue(eng.stage_entered)

        player.hp = 30
        eng.stage_entered = False
        opt16 = CarveOwnNameOption()
        res16 = opt16.execute(run, eng)
        self.assertEqual(player.hp, 15)
        self.assertTrue(eng.stage_entered)
