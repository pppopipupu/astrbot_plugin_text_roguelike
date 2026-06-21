import unittest
from scratch.duel_tests.base import *

class TestDuelBasic(TestDuelSystem):
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
        self.assertIn("打击", res)
        self.assertIn("火球术", res)
        
        res, _ = self.router.handle_deck_cmd(uid, ["移除", "1", "2"])
        self.assertIn("移除了 2 张", res)

    def test_deck_share_code(self):
        u1 = "user1"
        u2 = "user2"
        self.router.handle_deck_cmd(u1, ["创建", "sharedeck"])
        self.router.handle_deck_cmd(u1, ["添加", "duel_warrior_strike", "4"])
        self.router.handle_deck_cmd(u1, ["添加", "duel_warrior_defend", "2"])
        
        res, _ = self.router.handle_deck_cmd(u1, ["导出", "sharedeck"])
        self.assertIn("导出成功", res)
        lines = res.split("\n")
        code = ""
        for line in lines:
            if not line.startswith("✨") and not line.startswith("可以使用") and not line.startswith("/rogue") and line.strip():
                code = line.strip()
                break
        self.assertTrue(len(code) > 0)
        
        self.router.handle_deck_cmd(u2, ["创建", "temp"])
        res_imp, _ = self.router.handle_deck_cmd(u2, ["导入", code])
        self.assertIn("成功导入牌组", res_imp)
        self.assertIn("sharedeck", res_imp)
        
        decks_u2 = self.save_manager.load_duel_decks(u2)["decks"]
        self.assertIn("sharedeck", decks_u2)
        self.assertEqual(len(decks_u2["sharedeck"]), 6)
        
        res_imp2, _ = self.router.handle_deck_cmd(u2, ["导入", code])
        self.assertIn("sharedeck_导入1", res_imp2)
        decks_u2_new = self.save_manager.load_duel_decks(u2)["decks"]
        self.assertIn("sharedeck_导入1", decks_u2_new)
        
        res_imp_custom, _ = self.router.handle_deck_cmd(u2, ["导入", code, "my_custom_name"])
        self.assertIn("my_custom_name", res_imp_custom)
        
        res_fail, _ = self.router.handle_deck_cmd(u2, ["导入", "invalid_base64_string_here_!!!"])
        self.assertIn("解析分享码失败", res_fail)
        
        import base64
        import json
        bad_payload = json.dumps({"name": "bad", "cards": ["non_existent_card_id"]})
        bad_code = base64.b64encode(bad_payload.encode("utf-8")).decode("utf-8")
        res_fail_card, _ = self.router.handle_deck_cmd(u2, ["导入", bad_code])
        self.assertIn("包含未知的对决卡牌ID", res_fail_card)

    def test_duel_outside_menu_and_status(self):
        u1 = "user1"
        self.router.handle_deck_cmd(u1, ["创建", "p1deck"])
        for c in ["duel_warrior_strike"]:
            self.router.handle_deck_cmd(u1, ["添加", c, "4"])
        res, term, p1, dm1, p2, dm2 = self.router.handle_duel_cmd(u1, "张三", [])
        self.assertIn("对决模式", res)
        self.assertIn("当前活动牌组", res)
        res_s, _, _, _, _, _ = self.router.handle_duel_cmd(u1, "张三", ["s"])
        self.assertEqual(res, res_s)

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

    def test_duel_help(self):
        res, _, _, _, _, _ = self.router.handle_duel_cmd("user1", "张三", ["帮助"])
        self.assertIn("帮助手册", res)
        
        res2, _, _, _, _, _ = self.router.handle_duel_cmd("user1", "张三", ["对决", "帮助"])
        self.assertIn("帮助手册", res2)
        
        res3, _, _, _, _, _ = self.router.handle_duel_cmd("user1", "张三", ["duel", "help"])
        self.assertIn("帮助手册", res3)

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
        
        run = self.save_manager.load_duel_save(u1)
        pub_s, _, _, dm1_s, _, _ = self.router.route_in_game_action(run, u1, "张三", ["s"])
        self.assertIn("公开战局简报", pub_s)
        self.assertIn("能量 1A 1BA", pub_s)
        self.assertIn("幸运币: 0 个", pub_s)
        self.assertIn("你的回合", dm1_s)
        
        run = self.save_manager.load_duel_save(u1)
        run.player.hand[0] = "duel_warrior_defend"
        self.save_manager.save_duel_save(u1, run)
        pub_play, _, _, _, _, _ = self.router.route_in_game_action(run, u1, "张三", ["p", "1"])
        self.assertIn("📢 玩家【张三】打出了卡牌【防御】！", pub_play)
        
        run = self.save_manager.load_duel_save(u1)
        run.node_data["p1_coins"] = 1
        self.save_manager.save_duel_save(u1, run)
        pub_coin, _, _, _, _, _ = self.router.route_in_game_action(run, u1, "张三", ["cn"])
        self.assertIn("📢 玩家【张三】使用了幸运币，获得了 1 点动作点！", pub_coin)
        
        run = self.save_manager.load_duel_save(u1)
        run.player.hand.append("duel_officer_recruit_vanguard")
        run.player.actions = 5
        self.save_manager.save_duel_save(u1, run)
        pub_summon, _, _, _, _, _ = self.router.route_in_game_action(run, u1, "张三", ["p", str(len(run.player.hand))])
        
        run = self.save_manager.load_duel_save(u1)
        self.assertIn("1", run.player.minions)
        
        run.node_data["turn_count"] = 3
        run.node_data["p1_evolve_points"] = 4
        run.node_data["p1_evolved_this_turn"] = False
        self.save_manager.save_duel_save(u1, run)
        pub_evolve, _, _, _, _, _ = self.router.route_in_game_action(run, u1, "张三", ["ev", "p1"])
        self.assertIn("📢 玩家【张三】将随从【新兵前锋】进化了！", pub_evolve)
        
        run = self.save_manager.load_duel_save(u1)
        m = run.player.minions["1"]
        m.attack_actions = 1
        m.buffs.clear()
        self.save_manager.save_duel_save(u1, run)
        pub_atk, _, _, _, _, _ = self.router.route_in_game_action(run, u1, "张三", ["m", "1", "e1"])
        self.assertIn("📢 玩家【张三】指挥随从【新兵前锋】攻击了【李四】！", pub_atk)
        
        run = self.save_manager.load_duel_save(u1)
        pub_e, _, _, _, _, _ = self.router.route_in_game_action(run, u1, "张三", ["e"])
        self.assertIn("📢 玩家【张三】结束了回合！", pub_e)
        self.assertIn("李四 的回合", pub_e)
