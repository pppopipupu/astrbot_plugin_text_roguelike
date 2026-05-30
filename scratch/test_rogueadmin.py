import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.manager import SaveManager
from game.core.battle_engine import BattleEngine
from game.models.state import GameRun, PlayerState
from main import MyPlugin

class MockContext:
    pass

class MockEvent:
    def __init__(self, message_str: str):
        self.message_str = message_str
        self.results = []

    def get_sender_id(self) -> str:
        return "admin_test_user"

    def plain_result(self, text: str):
        self.results.append(text)
        return text

class TestRogueAdmin(unittest.TestCase):
    def setUp(self):
        self.save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data_admin")
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        self.manager = SaveManager(data_dir=self.save_dir)
        self.engine = BattleEngine(self.manager)
        self.plugin = MyPlugin(MockContext())
        self.plugin.save_manager = self.manager
        self.plugin.engine = self.engine

    def tearDown(self):
        import shutil
        if os.path.exists(self.save_dir):
            shutil.rmtree(self.save_dir)

    def test_admin_config_file_read_write(self):
        self.manager.save_admin_config({"final_boss": "Icerainboww"})
        cfg = self.manager.load_admin_config()
        self.assertEqual(cfg.get("final_boss"), "Icerainboww")

        self.manager.save_admin_config({"final_boss": "random"})
        cfg = self.manager.load_admin_config()
        self.assertEqual(cfg.get("final_boss"), "random")

    def test_boss_generation_by_admin_config(self):
        player = PlayerState(
            hp=80, max_hp=80, shield=0, gold=100, stage=20,
            deck=[], draw_pile=[], discard_pile=[], exhaust_pile=[],
            graveyard=[], hand=[], actions=2, bonus_actions=1,
            minions={}, amulets={}, abilities=[], fold_guide=True,
            buffs=[], relics=[], subclass=""
        )
        run = GameRun(
            user_id="test_user_admin", node_type="battle",
            player=player, enemies=[], node_data={}, map_data={}
        )

        self.manager.save_admin_config({"final_boss": "Icerainboww"})
        self.engine._init_battle_node(run, "boss")
        self.assertEqual(run.enemies[0].name, "Icerainboww")

        self.manager.save_admin_config({"final_boss": "腐化之心"})
        self.engine._init_battle_node(run, "boss")
        self.assertEqual(run.enemies[0].name, "腐化之心")

    def test_plugin_command_routing(self):
        async def run_test():
            event_help = MockEvent("/rogueadmin")
            async for _ in self.plugin.rogueadmin(event_help):
                pass
            self.assertTrue(any("管理指令帮助" in r for r in event_help.results))

            event_show = MockEvent("/rogueadmin boss")
            async for _ in self.plugin.rogueadmin(event_show):
                pass
            self.assertTrue(any("当前最终BOSS配置" in r for r in event_show.results))

            event_set_ice = MockEvent("/rogueadmin boss set Icerainboww")
            async for _ in self.plugin.rogueadmin(event_set_ice):
                pass
            self.assertTrue(any("最终BOSS已成功固定为" in r for r in event_set_ice.results))
            cfg = self.manager.load_admin_config()
            self.assertEqual(cfg.get("final_boss"), "Icerainboww")

            event_set_invalid = MockEvent("/rogueadmin boss set invalid_boss")
            async for _ in self.plugin.rogueadmin(event_set_invalid):
                pass
            self.assertTrue(any("无效的BOSS名称" in r for r in event_set_invalid.results))

        import asyncio
        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
