import unittest
from scratch.duel_tests.base import *

class TestDuelFlow(TestDuelSystem):
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
        
        run = self.save_manager.load_duel_save(u1)
        self.assertIsNotNone(run)
        self.assertEqual(run.player.hp, 200)
        self.assertEqual(run.player2.hp, 200)
        self.assertEqual(run.node_data["player1_name"], "张三")
        self.assertEqual(run.node_data["player2_name"], "李四")
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["幸运币"])
        self.assertIn("没有幸运币", res)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["进化", "1"])
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.node_data["player1_name"], "张三")
        self.assertEqual(run.node_data["player2_name"], "李四")
        self.assertEqual(run.player.hp, 200)
        self.assertEqual(run.player2.hp, 200)
        self.assertEqual(len(run.player.hand), 6)
        self.assertEqual(len(run.player2.hand), 6)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "e1"])
        
        run = self.save_manager.load_duel_save(u2)
        
        run.node_data["p1_turns_count"] = 2
        run.node_data["turn_count"] = 3
        self.save_manager.save_duel_save(u2, run)
        run = self.save_manager.load_duel_save(u2)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u2, "李四", ["结束"])
        
        run = self.save_manager.load_duel_save(u1)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["结束"])
        self.assertEqual(p1, u1)
        self.assertEqual(p2, u2)
        latest_run = self.save_manager.load_duel_save(u2)
        self.assertEqual(latest_run.user_id, u2)
        expected_dm2 = render_duel_battle_private(latest_run)
        expected_dm2 = self.router.engine._append_logs_to_res(latest_run, expected_dm2)
        latest_run.player, latest_run.player2 = latest_run.player2, latest_run.player
        latest_run.user_id = u1
        expected_dm1 = render_duel_battle_private(latest_run)
        expected_dm1 = self.router.engine._append_logs_to_res(latest_run, expected_dm1)
        latest_run.player, latest_run.player2 = latest_run.player2, latest_run.player
        latest_run.user_id = u2
        self.assertEqual(dm1, expected_dm1)
        self.assertEqual(dm2, expected_dm2)
        
        run = self.save_manager.load_duel_save(u2)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u2, "李四", ["结束"])
        
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.node_data["turn_count"], 3)
        self.assertEqual(run.player.actions, 2)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["进化", "1"])
        self.assertIn("进化", res)
        
        res, term, p1, dm1, p2, dm2 = self.router.handle_duel_cmd(u1, "张三", ["放弃"])
        self.assertIn("认输了", res)
        self.assertTrue(term)
        
        self.assertIsNone(self.save_manager.load_duel_save(u1))

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

    def test_duel_system_commands_penetration(self):
        u1 = "user_penetrate_1"
        u2 = "user_penetrate_2"
        self.router.handle_deck_cmd(u1, ["创建", "p1deck"])
        cards = ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam"]
        for c in cards:
            self.router.handle_deck_cmd(u1, ["添加", c, "4"])
        self.router.handle_deck_cmd(u1, ["添加", "duel_double_tap", "1"])
        self.router.handle_deck_cmd(u2, ["创建", "p2deck"])
        for c in cards:
            self.router.handle_deck_cmd(u2, ["添加", c, "4"])
        self.router.handle_deck_cmd(u2, ["添加", "duel_double_tap", "1"])
        
        self.router.handle_duel_cmd(u1, "张三", ["邀请", u2])
        self.router.handle_duel_cmd(u2, "李四", ["接受"])
        
        run = self.save_manager.load_duel_save(u1)
        self.assertIsNotNone(run)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["帮助"])
        self.assertIn("帮助手册", res)
        self.assertFalse(term)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["iv", "99999"])
        self.assertIn("向你发起了 TCG 卡牌对决", res)

    def test_duel_queue_action(self):
        u1 = "user1"
        u2 = "user2"
        self.router.handle_deck_cmd(u1, ["创建", "p1deck"])
        for c in ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam"]:
            self.router.handle_deck_cmd(u1, ["添加", c, "4"])
        self.router.handle_deck_cmd(u1, ["添加", "duel_meteor_swarm", "2"])
        self.router.handle_deck_cmd(u2, ["创建", "p2deck"])
        for c in ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam"]:
            self.router.handle_deck_cmd(u2, ["添加", c, "4"])
        self.router.handle_deck_cmd(u2, ["添加", "duel_meteor_swarm", "2"])
        self.router.handle_duel_cmd(u1, "张三", [f"@user2"])
        self.router.handle_duel_cmd(u2, "李四", ["接受"])
        run = self.save_manager.load_duel_save(u1)
        run.player.hand = ["duel_warrior_strike", "duel_warrior_defend"]
        run.player.actions = 10
        self.save_manager.save_duel_save(u1, run)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["队列", "[使用 1 e1, 使用 1]"])
        self.assertIn("打出了卡牌【打击】", res)
        self.assertIn("打出了卡牌【防御】", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player2.hp, 194)
        self.assertEqual(run.player.shield, 5)
