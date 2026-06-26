import unittest
from scratch.duel_tests.base import *

class TestDuelAdvanced(TestDuelSystem):
    def test_quicken_and_echo_form(self):
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
        
        self.router.handle_duel_cmd(u1, "张三", ["@user2"])
        self.router.handle_duel_cmd(u2, "李四", ["接受"])
        
        run = self.save_manager.load_duel_save(u1)
        run.player.hand = ["duel_quicken", "duel_echo_form", "duel_fireball"]
        run.player.actions = 10
        run.player.bonus_actions = 10
        self.save_manager.save_duel_save(u1, run)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "p0"])
        self.assertNotIn("❌", res)
        run = self.save_manager.load_duel_save(u1)
        has_quicken = any(b.id == "quicken" for b in run.player.buffs)
        self.assertTrue(has_quicken)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "p0"])
        self.assertNotIn("❌", res)
        run = self.save_manager.load_duel_save(u1)
        has_echo = any(b.id == "echo_form" for b in run.player.buffs)
        self.assertTrue(has_echo)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["结束"])
        run = self.save_manager.load_duel_save(u2)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u2, "李四", ["结束"])
        
        run = self.save_manager.load_duel_save(u1)
        run.player.hand = ["duel_fireball"]
        run.player.actions = 10
        self.save_manager.save_duel_save(u1, run)
        
        initial_opp_hp = run.player2.hp
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "e1"])
        self.assertNotIn("❌", res)
        self.assertIn("回响触发", res)
        run = self.save_manager.load_duel_save(u1)
        final_opp_hp = run.player2.hp
        self.assertEqual(initial_opp_hp - final_opp_hp, 24)

    def test_time_stop_mechanic(self):
        u1 = "user1"
        u2 = "user2"
        self.router.handle_deck_cmd(u1, ["创建", "p1deck"])
        for c in ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam", "duel_time_stop", "duel_fireball"]:
            self.router.handle_deck_cmd(u1, ["添加", c, "4"])
        self.router.handle_deck_cmd(u2, ["创建", "p2deck"])
        for c in ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam", "duel_fireball"]:
            self.router.handle_deck_cmd(u2, ["添加", c, "4"])
            
        self.router.handle_duel_cmd(u1, "张三", [f"@user2"])
        self.router.handle_duel_cmd(u2, "李四", ["接受"])
        
        run = self.save_manager.load_duel_save(u1)
        run.player.hand = ["duel_time_stop", "duel_warrior_strike", "duel_fireball"]
        run.player.actions = 10
        self.save_manager.save_duel_save(u1, run)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1"])
        self.assertIn("时间停止", res)
        
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.node_data.get("extra_turns_left"), 3)
        self.assertEqual(run.node_data.get("current_turn_id"), u1)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["结束"])
        self.assertIn("额外回合进行中", res)
        
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.node_data.get("extra_turns_left"), 2)
        self.assertEqual(run.node_data.get("current_turn_id"), u1)
        
        run.player.actions = 5
        self.save_manager.save_duel_save(u1, run)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "2", "e1"])
        self.assertIn("提前结束", res)
        
        run = self.save_manager.load_duel_save(u2)
        self.assertEqual(run.node_data.get("extra_turns_left"), 0)
        self.assertEqual(run.node_data.get("current_turn_id"), u2)

    def test_duel_time_warp_unmined_gem_and_queries(self):
        u1 = "user_q_1"
        u2 = "user_q_2"
        self.router.handle_deck_cmd(u1, ["创建", "p1deck"])
        cards = ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam", "duel_double_tap"]
        for c in cards:
            self.router.handle_deck_cmd(u1, ["添加", c, "4"])
        self.router.handle_deck_cmd(u2, ["创建", "p2deck"])
        for c in cards:
            self.router.handle_deck_cmd(u2, ["添加", c, "4"])
        
        self.router.handle_duel_cmd(u1, "张三", [f"@{u2}"])
        self.router.handle_duel_cmd(u2, "李四", ["接受"])
        
        run = self.save_manager.load_duel_save(u1)
        self.assertIsNotNone(run)
        
        run.player.hand = ["duel_warrior_strike"]
        run.player.actions = 2
        self.save_manager.save_duel_save(u1, run)
        
        run.player.hand.append("duel_unmined_gem")
        run.player.actions = 2
        self.save_manager.save_duel_save(u1, run)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "2", "p0"])
        self.assertIn("使用了【未掘宝石】", res)
        
        run = self.save_manager.load_duel_save(u1)
        self.assertTrue(any(":replay:" in c for c in run.player.hand))
        
        from astrbot_plugin_text_roguelike.game.entities.cards.duel import ALL_DUEL_CARDS
        mod_cid = [c for c in run.player.hand if ":replay:" in c][0]
        card_obj = ALL_DUEL_CARDS.get(mod_cid)
        self.assertEqual(card_obj.name, "打击")
        self.assertIn("重放 3", card_obj.desc)
        
        run.player.hand = ["duel_time_warp"]
        run.player.discard_pile = ["duel_warrior_strike"] * 6
        run.player.draw_pile = ["duel_warrior_defend"] * 4
        run.player.actions = 2
        self.save_manager.save_duel_save(u1, run)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "p0"])
        self.assertIn("时光倒流", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(len(run.player.discard_pile), 0)
        self.assertTrue(len(run.player.hand) > 0)
        
        run.player.hand = ["duel_warrior_bash"]
        run.player.actions = 2
        run.player2.hp = 100
        run.player2.buffs = []
        self.save_manager.save_duel_save(u1, run)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "e1"])
        self.assertNotIn("❌", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player2.hp, 95)
        self.assertTrue(any(b.id == "vulnerable" for b in run.player2.buffs))
        
        run.player.hand = ["duel_body_slam"]
        run.player.shield = 25
        run.player.actions = 2
        run.player2.hp = 100
        run.player2.buffs = []
        self.save_manager.save_duel_save(u1, run)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "e1"])
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player2.hp, 75)
        
        run.player.hand = ["duel_warrior_anger"]
        run.player.actions = 2
        run.player.discard_pile = []
        self.save_manager.save_duel_save(u1, run)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "e1"])
        run = self.save_manager.load_duel_save(u1)
        self.assertIn("duel_warrior_anger", run.player.discard_pile)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["查询", "痛击"])
        self.assertIn("对决卡牌：【痛击】", res)
        self.assertIn("类型：spell", res)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["抽牌堆"])
        self.assertIn("已通过私聊发送给你", res)
        self.assertIsNotNone(dm1)
        self.assertIn("抽牌堆", dm1)

    def test_duel_advanced_mechanics(self):
        u1 = "user_adv_1"
        u2 = "user_adv_2"
        self.router.handle_deck_cmd(u1, ["创建", "p1deck"])
        cards = ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam"]
        for c in cards:
            self.router.handle_deck_cmd(u1, ["添加", c, "4"])
        self.router.handle_deck_cmd(u1, ["添加", "duel_double_tap", "1"])
        self.router.handle_deck_cmd(u2, ["创建", "p2deck"])
        for c in cards:
            self.router.handle_deck_cmd(u2, ["添加", c, "4"])
        self.router.handle_deck_cmd(u2, ["添加", "duel_double_tap", "1"])
        
        self.router.handle_duel_cmd(u1, "张三", [f"@{u2}"])
        self.router.handle_duel_cmd(u2, "李四", ["接受"])
        
        run = self.save_manager.load_duel_save(u1)
        self.assertIsNotNone(run)
        
        run.player.hand.append("duel_water_elemental")
        run.player.actions = 2
        self.save_manager.save_duel_save(u1, run)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", str(len(run.player.hand)), "p1"])
        self.assertIn("召唤了", res)
        run = self.save_manager.load_duel_save(u1)
        m = run.player.minions["1"]
        m.actions = 3
        self.save_manager.save_duel_save(u1, run)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["m", "1", "sk", "1"])
        self.assertIn("寒冰触碰", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player.minions["1"].actions, 1)
        self.assertEqual(run.player2.bonus_actions, 0)
        
        run.player.hand.append("duel_warrior_strike")
        run.player.actions = 2
        run.player.buffs.append(BuffState(id="strength", name="力量", stacks=3))
        self.save_manager.save_duel_save(u1, run)
        
        initial_opp_hp = run.player2.hp
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", str(len(run.player.hand)), "e1"])
        self.assertIn("打出了卡牌【打击】", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player2.hp, initial_opp_hp - 12)
        
        run.player.hand.append("duel_warrior_strike")
        run.player.actions = 2
        run.player.buffs = [BuffState(id="echo_form", name="回响形态", stacks=2)]
        run.node_data["cards_played_this_turn"] = 0
        self.save_manager.save_duel_save(u1, run)
        
        initial_opp_hp = run.player2.hp
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", str(len(run.player.hand)), "e1"])
        self.assertIn("打出了卡牌【打击】", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player2.hp, initial_opp_hp - 18)
        
        run.player.hand.append("duel_double_tap")
        run.player.actions = 2
        self.save_manager.save_duel_save(u1, run)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", str(len(run.player.hand)), "p0"])
        run = self.save_manager.load_duel_save(u1)
        self.assertTrue(any(b.id == "double_tap_buff" for b in run.player.buffs))
        
        run.player.hand.append("duel_warrior_strike")
        run.player.actions = 2
        self.save_manager.save_duel_save(u1, run)
        initial_opp_hp = run.player2.hp
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", str(len(run.player.hand)), "e1"])
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player2.hp, initial_opp_hp - 12)
        self.assertFalse(any(b.id == "double_tap_buff" for b in run.player.buffs))
        
        run.player.hand.append("duel_arcane_torrent")
        run.player.actions = 3
        run.player2.shield = 20
        self.save_manager.save_duel_save(u1, run)
        initial_opp_hp = run.player2.hp
        initial_opp_shield = run.player2.shield
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", str(len(run.player.hand)), "e1"])
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.node_data["last_x_cost_a"], 3)
        self.assertEqual(run.player.actions, 0)
        self.assertEqual(run.player2.shield, initial_opp_shield)
        self.assertEqual(run.player2.hp, initial_opp_hp - 36)
        
        run.player.hand.append("duel_mage_ward")
        run.player.actions = 2
        self.save_manager.save_duel_save(u1, run)
        hand_len = len(run.player.hand)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", str(hand_len), "p0"])
        run = self.save_manager.load_duel_save(u1)
        self.assertNotIn("duel_mage_ward", run.player.hand)
        self.assertNotIn("duel_mage_ward", run.player.discard_pile)
        self.assertNotIn("duel_mage_ward", run.player.exhaust_pile)
        self.assertEqual(len(run.player.amulets), 1)
        
        amulet_key = list(run.player.amulets.keys())[0]
        run.player.amulets[amulet_key].countdown = 1
        self.save_manager.save_duel_save(u1, run)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["结束"])
        run = self.save_manager.load_duel_save(u2)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u2, "李四", ["结束"])
        run = self.save_manager.load_duel_save(u1)
        self.assertIn("duel_mage_ward", run.player.minion_graveyard)
        self.assertEqual(len(run.player.amulets), 0)
        self.assertEqual(run.player.shield, 4)
        
        run.player.buffs.append(BuffState(id="tactical_focus", name="无法抽牌", stacks=2))
        run.player.draw_pile = ["duel_warrior_strike"]
        run.player.hand = []
        self.save_manager.save_duel_save(u1, run)
        self.router.engine._draw_cards(run.player, 2, run)
        self.assertEqual(len(run.player.hand), 0)

    def test_duel_advanced_cascading_and_skills(self):
        u1 = "user_casc_1"
        u2 = "user_casc_2"
        self.router.handle_deck_cmd(u1, ["创建", "p1deck"])
        cards = ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam", "duel_double_tap"]
        for c in cards:
            self.router.handle_deck_cmd(u1, ["添加", c, "4"])
        self.router.handle_deck_cmd(u2, ["创建", "p2deck"])
        for c in cards:
            self.router.handle_deck_cmd(u2, ["添加", c, "4"])
        
        self.router.handle_duel_cmd(u1, "张三", [f"@{u2}"])
        self.router.handle_duel_cmd(u2, "李四", ["接受"])
        
        run = self.save_manager.load_duel_save(u1)
        self.assertIsNotNone(run)
        
        run.player.hand = ["duel_warrior_strike", "duel_warrior_strike", "duel_warrior_strike"]
        run.player.actions = 6
        run.player.buffs = [BuffState(id="echo_form", name="回响形态", stacks=12)]
        run.node_data["cards_played_this_turn"] = 0
        self.save_manager.save_duel_save(u1, run)
        
        initial_opp_hp = run.player2.hp
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "e1"])
        self.assertIn("打出了卡牌【打击】", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player2.hp, initial_opp_hp - 66)
        
        initial_opp_hp = run.player2.hp
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "e1"])
        self.assertIn("打出了卡牌【打击】", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player2.hp, initial_opp_hp - 18)
        
        initial_opp_hp = run.player2.hp
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "e1"])
        self.assertIn("打出了卡牌【打击】", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player2.hp, initial_opp_hp - 6)
        
        run.player.hand = ["duel_commander_patrol_captain", "duel_officer_banner_bearer"]
        run.player.actions = 6
        run.player.bonus_actions = 2
        self.save_manager.save_duel_save(u1, run)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "p1"])
        self.assertIn("召唤了", res)
        
        run = self.save_manager.load_duel_save(u1)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "p2"])
        self.assertIn("召唤了", res)
        
        run = self.save_manager.load_duel_save(u1)
        run.player.minions.pop("2", None)
        m1 = run.player.minions["1"]
        m1.max_hp = 20
        m1.hp = 10
        m1.actions = 3
        m1.bonus_actions = 1
        
        m2_grid = [k for k, v in run.player.minions.items() if v.id == "officer_banner_bearer"][0]
        m2 = run.player.minions[m2_grid]
        m2.max_hp = 15
        m2.hp = 10
        m2.actions = 3
        m2.bonus_actions = 1
        self.save_manager.save_duel_save(u1, run)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["m", "1", "sk", "1"])
        self.assertIn("恢复了", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player.minions["1"].hp, 13)
        self.assertEqual(run.player.minions[m2_grid].hp, 13)
        self.assertEqual(run.player.shield, 3)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["m", m2_grid, "sk", "1"])
        self.assertIn("激励了", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player.minions["1"].atk, 5)

    def test_duel_more_special_cards_and_buffs(self):
        u1 = "user_sp_1"
        u2 = "user_sp_2"
        self.router.handle_deck_cmd(u1, ["创建", "p1deck"])
        cards = ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam", "duel_fireball"]
        for c in cards:
            self.router.handle_deck_cmd(u1, ["添加", c, "4"])
        self.router.handle_deck_cmd(u2, ["创建", "p2deck"])
        for c in cards:
            self.router.handle_deck_cmd(u2, ["添加", c, "4"])
        
        self.router.handle_duel_cmd(u1, "张三", [f"@{u2}"])
        self.router.handle_duel_cmd(u2, "李四", ["接受"])
        
        run = self.save_manager.load_duel_save(u1)
        self.assertIsNotNone(run)
        
        run.player.hand = ["duel_barricade"]
        run.player.actions = 2
        self.save_manager.save_duel_save(u1, run)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "p0"])
        self.assertIn("缓冲", res)
        
        run = self.save_manager.load_duel_save(u1)
        self.assertTrue(any(b.id == "buffer" for b in run.player.buffs))
        
        run.player.hand = ["duel_barricade", "duel_glacier_fortress"]
        run.player.actions = 6
        self.save_manager.save_duel_save(u1, run)
        
        self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "p0"])
        run = self.save_manager.load_duel_save(u1)
        self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "p0"])
        
        run = self.save_manager.load_duel_save(u1)
        self.assertTrue(any(b.id == "barricade" for b in run.player.buffs))
        self.assertTrue(any(b.id == "glacier_fortress_buff" for b in run.player.buffs))
        
        run.player.shield = 10
        self.save_manager.save_duel_save(u1, run)
        
        self.router.route_in_game_action(run, u1, "张三", ["结束"])
        run = self.save_manager.load_duel_save(u2)
        self.router.route_in_game_action(run, u2, "李四", ["结束"])
        
        run = self.save_manager.load_duel_save(u1)
        self.assertGreaterEqual(run.player.shield, 10)
        
        run.player.hand = ["duel_archmage_wish", "duel_demon_form"]
        run.player.actions = 6
        run.player.bonus_actions = 2
        self.save_manager.save_duel_save(u1, run)
        
        self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "p0"])
        run = self.save_manager.load_duel_save(u1)
        self.assertTrue(any(b.id == "wish_power" for b in run.player.buffs))
        
        self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "p0"])
        run = self.save_manager.load_duel_save(u1)
        self.assertTrue(any(b.id == "demon_form" for b in run.player.buffs))

    def test_duel_overview_reader(self):
        res, term, p1, dm1, p2, dm2 = self.router.handle_duel_cmd("user_duel_reader", "张三", ["总览"])
        self.assertIn("对决卡牌总览", res)
        self.assertIn("第 1 /", res)
        stats = self.save_manager.load_stats("user_duel_reader")
        self.assertTrue(stats.reader_active)
        self.assertEqual(stats.reader_page, 1)
        self.assertEqual(stats.reader_mode, "duel")
        
        u1 = "user_ov_1"
        u2 = "user_ov_2"
        self.router.handle_deck_cmd(u1, ["创建", "p1deck"])
        cards = ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam", "duel_fireball"]
        for c in cards:
            self.router.handle_deck_cmd(u1, ["添加", c, "4"])
        self.router.handle_deck_cmd(u2, ["创建", "p2deck"])
        for c in cards:
            self.router.handle_deck_cmd(u2, ["添加", c, "4"])
            
        self.router.handle_duel_cmd(u1, "张三", [f"@{u2}"])
        self.router.handle_duel_cmd(u2, "李四", ["接受"])
        
        run = self.save_manager.load_duel_save(u1)
        self.assertIsNotNone(run)
        
        res_in_game, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["overview"])
        self.assertIn("对决卡牌总览", res_in_game)
        self.assertIn("第 1 /", res_in_game)
        
        self.save_manager.delete_duel_save(u1)
