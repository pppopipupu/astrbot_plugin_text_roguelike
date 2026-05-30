import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.manager import SaveManager
from game.core.battle_engine import BattleEngine
from game.models.state import GameRun, PlayerState
from game.renderer.battle import render_battle
from game.cards import ALL_CARDS

class TestUnplayableCost(unittest.TestCase):
    def setUp(self):
        self.save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data_unplayable")
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        self.manager = SaveManager(data_dir=self.save_dir)
        self.battle = BattleEngine(self.manager)

    def tearDown(self):
        import shutil
        if os.path.exists(self.save_dir):
            shutil.rmtree(self.save_dir)

    def test_unplayable_card_underlying_cost_is_zero(self):
        dazed = ALL_CARDS.get("curse_dazed")
        self.assertIsNotNone(dazed)
        self.assertEqual(dazed.cost_a, 0)
        self.assertEqual(dazed.cost_ba, 0)
        self.assertTrue(dazed.unplayable)

        agony = ALL_CARDS.get("curse_agony")
        self.assertIsNotNone(agony)
        self.assertEqual(agony.cost_a, 0)
        self.assertEqual(agony.cost_ba, 0)
        self.assertTrue(agony.unplayable)

    def test_unplayable_card_play_prevented(self):
        player = PlayerState(
            hp=45, max_hp=45, shield=0, gold=100, stage=2,
            deck=[], draw_pile=[], discard_pile=[], exhaust_pile=[],
            hand=["curse_dazed"], actions=2, bonus_actions=1,
            minions={}, amulets={}, abilities=[], fold_guide=True,
            buffs=[], relics=[], subclass=""
        )
        run = GameRun(
            user_id="test_user_unplay", node_type="battle",
            player=player, enemies=[], node_data={}, map_data={}
        )

        res = self.battle.play_card(run, 1)
        self.assertTrue("\u4e0d\u80fd\u88ab\u6253\u51fa" in res)

    def test_unplayable_card_rendering(self):
        player = PlayerState(
            hp=45, max_hp=45, shield=0, gold=100, stage=2,
            deck=[], draw_pile=[], discard_pile=[], exhaust_pile=[],
            hand=["curse_dazed", "dagger_throw"], actions=2, bonus_actions=1,
            minions={}, amulets={}, abilities=[], fold_guide=True,
            buffs=[], relics=[], subclass=""
        )
        run = GameRun(
            user_id="test_user_unplay", node_type="battle",
            player=player, enemies=[], node_data={}, map_data={}
        )

        res = render_battle(run)
        lines = res.split("\n")
        dazed_line = ""
        dagger_line = ""
        
        dazed_name = ALL_CARDS["curse_dazed"].name
        dagger_name = ALL_CARDS["dagger_throw"].name
        
        for line in lines:
            if dazed_name in line:
                dazed_line = line
            if dagger_name in line:
                dagger_line = line

        self.assertNotEqual(dazed_line, "")
        self.assertNotEqual(dagger_line, "")

        self.assertFalse("\u6d88\u8017" in dazed_line)
        self.assertTrue("\u6d88\u8017" in dagger_line)

if __name__ == "__main__":
    unittest.main()
