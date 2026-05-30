import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.renderer.query import render_query_info
from game.core.cli_router import CLIRouter
from game.models.manager import SaveManager
from game.core.battle_engine import BattleEngine

class TestQueryBuff(unittest.TestCase):
    def setUp(self):
        self.save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data_query_buff")
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        self.manager = SaveManager(data_dir=self.save_dir)
        self.battle = BattleEngine(self.manager)
        self.router = CLIRouter(self.manager, self.battle)

    def tearDown(self):
        import shutil
        if os.path.exists(self.save_dir):
            shutil.rmtree(self.save_dir)

    def test_query_all_buffs(self):
        res = render_query_info("buff")
        self.assertTrue("✨ 【全体战斗效果 (Buff) 一览】" in res)
        self.assertTrue("魔网天成" in res)
        self.assertTrue("祈愿奥术" in res)
        self.assertTrue("眩晕" in res)

    def test_query_single_buff_chinese(self):
        res = render_query_info("力量")
        self.assertTrue("✨ 战斗效果 (Buff)：力量" in res)
        self.assertTrue("造成的伤害增加" in res)

    def test_query_single_buff_by_id(self):
        res = render_query_info("stun")
        self.assertTrue("✨ 战斗效果 (Buff)：眩晕" in res)
        self.assertTrue("无法行动" in res)

    def test_router_query_guidance_no_save(self):
        generator = self.router.handle_command("test_user", ["查询"])
        res = list(generator)[0]
        self.assertTrue("❌ 你当前没有正在进行的游戏" in res)
        self.assertTrue("💡 提示" in res)
        self.assertTrue("查询 buff" in res)

if __name__ == "__main__":
    unittest.main()
