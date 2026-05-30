import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.manager import SaveManager
from game.core.battle_engine import BattleEngine
from game.core.map_engine import MapEngine
from game.models.state import GameRun, PlayerState, EnemyState, MinionState
from game.renderer.battle import render_battle

class TestIcerainbowwCard(unittest.TestCase):
    def setUp(self):
        self.save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data_legend")
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        self.manager = SaveManager(data_dir=self.save_dir)
        self.battle = BattleEngine(self.manager)
        self.map_eng = MapEngine(self.manager, self.battle)

    def tearDown(self):
        import shutil
        if os.path.exists(self.save_dir):
            shutil.rmtree(self.save_dir)

    def test_ancient_nodes_unlock_logic(self):
        player = PlayerState(
            hp=45, max_hp=45, shield=0, gold=100, stage=0,
            deck=[], draw_pile=[], discard_pile=[], exhaust_pile=[],
            graveyard=[], hand=[], actions=2, bonus_actions=1,
            minions={}, amulets={}, abilities=[], fold_guide=True,
            buffs=[], relics=[], subclass=""
        )
        run = GameRun(
            user_id="test_user_leg", node_type="map_select",
            player=player, enemies=[], node_data={}, map_data={}
        )

        stats = self.manager.load_stats("test_user_leg")
        stats.killed_icerainboww = False
        self.manager.save_stats("test_user_leg", stats)

        self.map_eng.enter_next_stage(run)
        options_stage1 = run.node_data.get("options", [])
        self.assertFalse(any(opt.get("card") == "minion_icerainboww" for opt in options_stage1))

        player.stage = 10
        self.map_eng.enter_next_stage(run)
        options_stage11 = run.node_data.get("options", [])
        self.assertFalse(any(opt.get("card") == "minion_icerainboww" for opt in options_stage11))

        stats.killed_icerainboww = True
        self.manager.save_stats("test_user_leg", stats)

        has_ice_in_stage1 = False
        for _ in range(20):
            player.stage = 0
            run.node_data = {}
            self.map_eng.enter_next_stage(run)
            options_stage1_unlocked = run.node_data.get("options", [])
            for opt in options_stage1_unlocked:
                if opt.get("card") == "minion_icerainboww":
                    has_ice_in_stage1 = True
                    self.assertEqual(opt.get("relic"), "wither_seed")
                    break
            if has_ice_in_stage1:
                break
        
        has_ice_in_stage11 = False
        for _ in range(20):
            player.stage = 10
            run.node_data = {}
            self.map_eng.enter_next_stage(run)
            options_stage11_unlocked = run.node_data.get("options", [])
            if any(opt.get("card") == "minion_icerainboww" for opt in options_stage11_unlocked):
                has_ice_in_stage11 = True
                break
                
        self.assertTrue(has_ice_in_stage11 or has_ice_in_stage1)

    def test_icerainboww_minion_abilities(self):
        player = PlayerState(
            hp=45, max_hp=45, shield=0, gold=100, stage=20,
            deck=[], draw_pile=[], discard_pile=[], exhaust_pile=[],
            graveyard=[], hand=[], actions=2, bonus_actions=1,
            minions={}, amulets={}, abilities=[], fold_guide=True,
            buffs=[], relics=[], subclass=""
        )
        run = GameRun(
            user_id="test_user_leg", node_type="battle",
            player=player, enemies=[
                EnemyState(name="E1", hp=20, max_hp=20, shield=0),
                EnemyState(name="E2", hp=20, max_hp=20, shield=0)
            ],
            node_data={}, map_data={}
        )

        grid = self.battle._summon_minion(run, "minion_icerainboww", "Icerainboww", 24, 6, 0)
        self.assertIsNotNone(grid)
        
        minion = player.minions[grid]
        self.assertEqual(minion.hp, 24)
        self.assertEqual(minion.atk, 6)

        minion.actions = 2
        minion.bonus_actions = 2
        
        self.battle.minion_skill(run, grid, 1)
        self.assertEqual(run.enemies[0].hp, 16)
        self.assertEqual(run.enemies[1].hp, 16)
        
        enemy1_vulnerable = any(b.id == "minor_vulnerable_cold" for b in run.enemies[0].buffs)
        enemy2_vulnerable = any(b.id == "minor_vulnerable_cold" for b in run.enemies[1].buffs)
        self.assertTrue(enemy1_vulnerable)
        self.assertTrue(enemy2_vulnerable)

        player.minions["2"] = MinionState("dummy", "Dummy", 10, 15, 2, 1, 0)
        minion.actions = 2
        minion.bonus_actions = 2
        
        player.shield = 0
        self.battle.minion_skill(run, grid, 2)
        self.assertEqual(player.shield, 12)
        self.assertEqual(player.minions["2"].hp, 14)

    def test_dynamic_intent_rendering(self):
        player = PlayerState(
            hp=45, max_hp=45, shield=0, gold=100, stage=20,
            deck=[], draw_pile=[], discard_pile=[], exhaust_pile=[],
            graveyard=[], hand=[], actions=2, bonus_actions=1,
            minions={}, amulets={}, abilities=[], fold_guide=True,
            buffs=[], relics=[], subclass=""
        )
        run = GameRun(
            user_id="test_user_leg", node_type="battle",
            player=player, enemies=[
                EnemyState(
                    name="TestBoss", hp=50, max_hp=50, shield=0,
                    intent_a_desc="攻击 (造成 10 点伤害)",
                    intent_a2_desc="防御 (获得 10 点护盾)",
                    intent_ba_desc="加攻 (获得 力量)",
                    intent_ba2_desc="虚弱 (下回合少抽牌)"
                )
            ],
            node_data={}, map_data={}
        )

        res = render_battle(run)
        self.assertTrue("A: 攻击 (造成 10 点伤害) + 防御 (获得 10 点护盾)" in res)
        self.assertTrue("BA: 加攻 (获得 力量) + 虚弱 (下回合少抽牌)" in res)

    def test_victory_unlock_settlement_tip(self):
        player = PlayerState(
            hp=45, max_hp=45, shield=0, gold=100, stage=20,
            deck=[], draw_pile=[], discard_pile=[], exhaust_pile=[],
            graveyard=[], hand=[], actions=2, bonus_actions=1,
            minions={}, amulets={}, abilities=[], fold_guide=True,
            buffs=[], relics=[], subclass=""
        )
        run = GameRun(
            user_id="test_user_leg", node_type="battle",
            player=player, enemies=[],
            node_data={"boss_name": "Icerainboww"}, map_data={}
        )

        stats = self.manager.load_stats("test_user_leg")
        stats.killed_icerainboww = True
        self.manager.save_stats("test_user_leg", stats)

        res = self.manager.settle_game_and_delete("test_user_leg", run, is_victory=True)
        self.assertTrue("特别提示：你成功击败了最终BOSS【Icerainboww】" in res)
        self.assertTrue("已永久解锁传奇随从卡" in res)

if __name__ == "__main__":
    unittest.main()
