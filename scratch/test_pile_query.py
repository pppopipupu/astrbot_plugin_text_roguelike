import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.manager import SaveManager
from game.core.battle_engine import BattleEngine
from game.core.cli_router import CLIRouter
from game.models.state import GameRun, PlayerState
from game.renderer.battle import (
    render_draw_pile, render_discard_pile, render_exhaust_pile,
    render_minion_graveyard, render_enemy_graveyard
)
from game.cards import ALL_CARDS
from game.data.minion_data import MINION_CONFIG

class TestPileQuery(unittest.TestCase):
    def setUp(self):
        self.save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data_pile")
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        self.manager = SaveManager(data_dir=self.save_dir)
        self.battle = BattleEngine(self.manager)
        self.router = CLIRouter(self.manager, self.battle)

    def tearDown(self):
        import shutil
        if os.path.exists(self.save_dir):
            shutil.rmtree(self.save_dir)

    def test_pile_rendering_logic(self):
        player = PlayerState(
            hp=45, max_hp=45, shield=0, gold=100, stage=2,
            deck=[],
            draw_pile=["dagger_throw", "fire_bolt", "dagger_throw"],
            discard_pile=["first_aid", "first_aid"],
            exhaust_pile=["quick_strike"],
            minion_graveyard=["mercenary", "mercenary"],
            enemy_graveyard=["\u8fdc\u53e4\u7115\u9f99", "\u8fdc\u53e4\u7115\u9f99"],
            hand=[], actions=2, bonus_actions=1,
            minions={}, amulets={}, abilities=[], fold_guide=True,
            buffs=[], relics=[], subclass=""
        )
        run = GameRun(
            user_id="test_user_pile", node_type="battle",
            player=player, enemies=[], node_data={}, map_data={}
        )

        res_draw = render_draw_pile(run)
        self.assertTrue(ALL_CARDS["dagger_throw"].name in res_draw)
        self.assertTrue("x2" in res_draw)
        self.assertTrue(ALL_CARDS["fire_bolt"].name in res_draw)
        self.assertTrue("x1" in res_draw)

        res_discard = render_discard_pile(run)
        self.assertTrue(ALL_CARDS["first_aid"].name in res_discard)
        self.assertTrue("x2" in res_discard)

        res_exhaust = render_exhaust_pile(run)
        self.assertTrue(ALL_CARDS["quick_strike"].name in res_exhaust)
        self.assertTrue("x1" in res_exhaust)

        res_minion_gy = render_minion_graveyard(run)
        m_name = MINION_CONFIG["mercenary"]["name"]
        self.assertTrue(m_name in res_minion_gy)
        self.assertTrue("x2" in res_minion_gy)

        res_enemy_gy = render_enemy_graveyard(run)
        self.assertTrue("\u8fdc\u53e4\u7115\u9f99" in res_enemy_gy)
        self.assertTrue("x2" in res_enemy_gy)

    def test_pile_commands_under_battle(self):
        player = PlayerState(
            hp=45, max_hp=45, shield=0, gold=100, stage=2,
            deck=[],
            draw_pile=["dagger_throw"],
            discard_pile=["first_aid"],
            exhaust_pile=["quick_strike"],
            minion_graveyard=["mercenary"],
            enemy_graveyard=["\u8fdc\u53e4\u7115\u9f99"],
            hand=[], actions=2, bonus_actions=1,
            minions={}, amulets={}, abilities=[], fold_guide=True,
            buffs=[], relics=[], subclass=""
        )
        run = GameRun(
            user_id="test_user_pile", node_type="battle",
            player=player, enemies=[], node_data={}, map_data={}
        )
        self.manager.save_save("test_user_pile", run)

        generator = self.router.handle_command("test_user_pile", ["draw"])
        res = list(generator)[0]
        self.assertTrue(ALL_CARDS["dagger_throw"].name in res)

        generator = self.router.handle_command("test_user_pile", ["query", "discard"])
        res = list(generator)[0]
        self.assertTrue(ALL_CARDS["first_aid"].name in res)

        generator = self.router.handle_command("test_user_pile", ["mg"])
        res = list(generator)[0]
        m_name = MINION_CONFIG["mercenary"]["name"]
        self.assertTrue(m_name in res)

        generator = self.router.handle_command("test_user_pile", ["query", "eg"])
        res = list(generator)[0]
        self.assertTrue("\u8fdc\u53e4\u7115\u9f99" in res)

    def test_pile_commands_not_in_battle(self):
        player = PlayerState(
            hp=45, max_hp=45, shield=0, gold=100, stage=2,
            deck=[], draw_pile=[], discard_pile=[], exhaust_pile=[],
            minion_graveyard=[], enemy_graveyard=[],
            hand=[], actions=2, bonus_actions=1,
            minions={}, amulets={}, abilities=[], fold_guide=True,
            buffs=[], relics=[], subclass=""
        )
        run = GameRun(
            user_id="test_user_pile", node_type="map_select",
            player=player, enemies=[], node_data={}, map_data={}
        )
        self.manager.save_save("test_user_pile", run)

        generator = self.router.handle_command("test_user_pile", ["draw"])
        res = list(generator)[0]
        self.assertTrue("\u274c" in res or "❌" in res)

        generator = self.router.handle_command("test_user_pile", ["\u67e5\u8be2", "discard"])
        res = list(generator)[0]
        self.assertTrue("\u274c" in res or "❌" in res)

        generator = self.router.handle_command("test_user_pile", ["mg"])
        res = list(generator)[0]
        self.assertTrue("\u274c" in res or "❌" in res)

    def test_backward_compatibility_old_graveyard(self):
        old_data = {
            "user_id": "test_user_pile",
            "player": {
                "hp": 45, "max_hp": 45, "shield": 0, "gold": 100, "stage": 2,
                "graveyard": ["minion:mercenary", "enemy:\u8fdc\u53e4\u7115\u9f99"],
                "minions": {}, "amulets": {}, "buffs": []
            },
            "enemies": [],
            "node_type": "battle",
            "node_data": {}
        }
        run = self.manager.from_dict(old_data)
        self.assertIsNotNone(run)
        self.assertEqual(run.player.minion_graveyard, ["mercenary"])
        self.assertEqual(run.player.enemy_graveyard, ["\u8fdc\u53e4\u7115\u9f99"])

if __name__ == "__main__":
    unittest.main()
