import unittest
import os
import shutil
import tempfile
import sys

from game.models.manager import SaveManager
from game.core.duel_router import DuelRouter
from game.models.state import GameRun, PlayerState, MinionState, AmuletState, BuffState
from game.renderer.duel_renderer import render_duel_battle_public, render_duel_battle_private

class DummyEvent:
    def __init__(self, message_str: str, sender_id: str):
        self.message_str = message_str
        self.sender_id = sender_id
        self.stopped = False
        self.bot = DummyBot()
        self.result_text = ""

    def get_sender_id(self) -> str:
        return self.sender_id

    def stop_event(self):
        self.stopped = True

    def plain_result(self, text: str):
        self.result_text = text
        return text

class DummyBot:
    def __init__(self):
        self.sent_messages = []

    async def call_api(self, api_name: str, **kwargs):
        self.sent_messages.append((api_name, kwargs))

class TestDuelSystem(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.save_manager = SaveManager(self.temp_dir)
        self.router = DuelRouter(self.save_manager)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_deck_management(self):
        uid = "user123"
        res, _ = self.router.handle_deck_cmd(uid, ["创建", "主力卡组"])
        self.assertIn("成功创建", res)
        
        active_name, deck = self.router.get_user_active_deck(uid)
        self.assertEqual(active_name, "主力卡组")
        self.assertEqual(len(deck), 0)
        
        valid, reason = self.router.check_deck_validity(deck)
        self.assertFalse(valid)
        
        for _ in range(4):
            res, _ = self.router.handle_deck_cmd(uid, ["添加", "duel_warrior_strike"])
            self.assertIn("添加", res)
            
        res, _ = self.router.handle_deck_cmd(uid, ["添加", "duel_warrior_strike"])
        self.assertIn("单卡超限", res)
        
        res, _ = self.router.handle_deck_cmd(uid, ["添加", "duel_fireball", "4"])
        self.assertIn("添加了 4 张", res)
        
        res, _ = self.router.handle_deck_cmd(uid, ["详情"])
        self.assertIn("对决·打击", res)
        self.assertIn("对决·火球术", res)
        
        res, _ = self.router.handle_deck_cmd(uid, ["移除", "1", "2"])
        self.assertIn("移除了 2 张", res)

    def test_duel_flow(self):
        u1 = "user1"
        u2 = "user2"
        
        res, _ = self.router.handle_deck_cmd(u1, ["创建", "p1deck"])
        cards = ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam"]
        for c in cards:
            self.router.handle_deck_cmd(u1, ["添加", c, "4"])
        self.router.handle_deck_cmd(u1, ["添加", "duel_double_tap", "1"])
        
        res, _ = self.router.handle_deck_cmd(u2, ["创建", "p2deck"])
        for c in cards:
            self.router.handle_deck_cmd(u2, ["添加", c, "4"])
        self.router.handle_deck_cmd(u2, ["添加", "duel_double_tap", "1"])
        
        pub, term, p1, dm1, p2, dm2 = self.router.handle_duel_cmd(u1, "张三", [f"@user2"])
        self.assertIn("对决", pub)
        self.assertEqual(p1, "user2")
        
        pub, term, p1, dm1, p2, dm2 = self.router.handle_duel_cmd(u2, "李四", ["接受"])
        self.assertIn("公开战局简报", pub)
        self.assertEqual(p1, "user1")
        
        run = self.save_manager.load_save(u1)
        self.assertIsNotNone(run)
        self.assertEqual(run.player.hp, 200)
        self.assertEqual(run.player2.hp, 200)
        self.assertEqual(run.node_data["player1_name"], "张三")
        self.assertEqual(run.node_data["player2_name"], "李四")
        
        ev = DummyEvent("", u1)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["幸运币"])
        self.assertIn("没有幸运币", res)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["进化", "1"])
        self.assertIn("第 3 回合起", res)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["结束"])
        self.assertIn("李四", res)
        
        run = self.save_manager.load_save(u2)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u2, "李四", ["幸运币"])
        self.assertIn("幸运币", res)
        run = self.save_manager.load_save(u2)
        self.assertEqual(run.player.actions, 2)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u2, "李四", ["结束"])
        
        run = self.save_manager.load_save(u1)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["结束"])
        
        run = self.save_manager.load_save(u2)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u2, "李四", ["结束"])
        
        run = self.save_manager.load_save(u1)
        self.assertEqual(run.node_data["turn_count"], 3)
        self.assertEqual(run.player.actions, 2)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["进化", "1"])
        self.assertIn("进化", res)
        
        res, term, p1, dm1, p2, dm2 = self.router.handle_duel_cmd(u1, "张三", ["放弃"])
        self.assertIn("认输了", res)
        self.assertTrue(term)
        
        self.assertIsNone(self.save_manager.load_save(u1))

    def test_duel_help(self):
        res, _, _, _, _, _ = self.router.handle_duel_cmd("user1", "张三", ["帮助"])
        self.assertIn("帮助手册", res)
        
        res2, _, _, _, _, _ = self.router.handle_duel_cmd("user1", "张三", ["对决", "帮助"])
        self.assertIn("帮助手册", res2)
        
        res3, _, _, _, _, _ = self.router.handle_duel_cmd("user1", "张三", ["duel", "help"])
        self.assertIn("帮助手册", res3)

    def test_matrix_user_duel_flow(self):
        u1 = "@alice:matrix.org"
        u2 = "@bob:matrix.org"
        res, _ = self.router.handle_deck_cmd(u1, ["创建", "p1deck"])
        cards = ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam"]
        for c in cards:
            self.router.handle_deck_cmd(u1, ["添加", c, "4"])
        self.router.handle_deck_cmd(u1, ["添加", "duel_double_tap", "1"])
        res, _ = self.router.handle_deck_cmd(u2, ["创建", "p2deck"])
        for c in cards:
            self.router.handle_deck_cmd(u2, ["添加", c, "4"])
        self.router.handle_deck_cmd(u2, ["添加", "duel_double_tap", "1"])
        pub, term, p1, dm1, p2, dm2 = self.router.handle_duel_cmd(u1, "Alice", ["@bob:matrix.org"])
        self.assertIn("对决", pub)
        self.assertEqual(p1, "bob:matrix.org")
        pub, term, p1, dm1, p2, dm2 = self.router.handle_duel_cmd(u2, "Bob", ["接受"])
        self.assertIn("公开战局简报", pub)
        self.assertEqual(p1, "@alice:matrix.org")

    def test_duel_invite_subcommand(self):
        u1 = "user1"
        u2 = "user2"
        res, _ = self.router.handle_deck_cmd(u1, ["创建", "p1deck"])
        cards = ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam"]
        for c in cards:
            self.router.handle_deck_cmd(u1, ["添加", c, "4"])
        self.router.handle_deck_cmd(u1, ["添加", "duel_double_tap", "1"])
        
        pub, term, p1, dm1, p2, dm2 = self.router.handle_duel_cmd(u1, "张三", ["邀请", "user2"])
        self.assertIn("发起了 TCG 卡牌对决", pub)
        self.assertEqual(p1, "user2")
        
        pub, term, p1, dm1, p2, dm2 = self.router.handle_duel_cmd(u1, "张三", ["invite", "@user2"])
        self.assertIn("发起了 TCG 卡牌对决", pub)
        self.assertEqual(p1, "user2")
        
        pub, term, p1, dm1, p2, dm2 = self.router.handle_duel_cmd(u1, "张三", ["iv", "[At:qq=12345]"])
        self.assertIn("发起了 TCG 卡牌对决", pub)
        self.assertEqual(p1, "12345")

    def test_duel_aliases_and_play_tips(self):
        u1 = "user1"
        u2 = "user2"
        res, _ = self.router.handle_deck_cmd(u1, ["创建", "p1deck"])
        cards = ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam"]
        for c in cards:
            self.router.handle_deck_cmd(u1, ["添加", c, "4"])
        self.router.handle_deck_cmd(u1, ["添加", "duel_double_tap", "1"])
        res, _ = self.router.handle_deck_cmd(u2, ["创建", "p2deck"])
        for c in cards:
            self.router.handle_deck_cmd(u2, ["添加", c, "4"])
        self.router.handle_deck_cmd(u2, ["添加", "duel_double_tap", "1"])
        pub, term, p1, dm1, p2, dm2 = self.router.handle_duel_cmd(u1, "张三", ["@user2"])
        pub, term, p1, dm1, p2, dm2 = self.router.handle_duel_cmd(u2, "李四", ["接受"])
        
        run = self.save_manager.load_save(u1)
        pub_s, _, _, dm1_s, _, _ = self.router.route_in_game_action(run, u1, "张三", ["s"])
        self.assertIn("公开战局简报", pub_s)
        self.assertIn("能量 1A 1BA", pub_s)
        self.assertIn("幸运币: 0 个", pub_s)
        self.assertIn("你的回合", dm1_s)
        
        run = self.save_manager.load_save(u1)
        run.player.hand[0] = "duel_warrior_defend"
        self.save_manager.save_save(u1, run)
        pub_play, _, _, _, _, _ = self.router.route_in_game_action(run, u1, "张三", ["p", "1"])
        self.assertIn("📢 玩家【张三】打出了卡牌【防御】！", pub_play)
        
        run = self.save_manager.load_save(u1)
        run.node_data["p1_coins"] = 1
        self.save_manager.save_save(u1, run)
        pub_coin, _, _, _, _, _ = self.router.route_in_game_action(run, u1, "张三", ["cn"])
        self.assertIn("📢 玩家【张三】使用了幸运币，获得了 1 点动作点！", pub_coin)
        
        run = self.save_manager.load_save(u1)
        run.player.hand.append("duel_officer_recruit_vanguard")
        run.player.actions = 5
        self.save_manager.save_save(u1, run)
        pub_summon, _, _, _, _, _ = self.router.route_in_game_action(run, u1, "张三", ["p", str(len(run.player.hand))])
        
        run = self.save_manager.load_save(u1)
        self.assertIn("1", run.player.minions)
        
        run.node_data["turn_count"] = 3
        run.node_data["p1_evolve_points"] = 4
        run.node_data["p1_evolved_this_turn"] = False
        self.save_manager.save_save(u1, run)
        pub_evolve, _, _, _, _, _ = self.router.route_in_game_action(run, u1, "张三", ["ev", "p1"])
        self.assertIn("📢 玩家【张三】将随从【新兵前锋】进化了！", pub_evolve)
        
        run = self.save_manager.load_save(u1)
        m = run.player.minions["1"]
        m.attack_actions = 1
        m.buffs.clear()
        self.save_manager.save_save(u1, run)
        pub_atk, _, _, _, _, _ = self.router.route_in_game_action(run, u1, "张三", ["m", "1", "e1"])
        self.assertIn("📢 玩家【张三】指挥随从【新兵前锋】攻击了【李四】！", pub_atk)
        
        run = self.save_manager.load_save(u1)
        pub_e, _, _, _, _, _ = self.router.route_in_game_action(run, u1, "张三", ["e"])
        self.assertIn("📢 玩家【张三】结束了回合！", pub_e)
        self.assertIn("李四 的回合", pub_e)

if __name__ == "__main__":
    unittest.main()
