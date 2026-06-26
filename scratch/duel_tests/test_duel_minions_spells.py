import unittest
from scratch.duel_tests.base import *

class TestDuelMinionsSpells(TestDuelSystem):
    def test_aoe_empty_grid_filtering(self):
        u1 = "user1"
        u2 = "user2"
        self.router.handle_deck_cmd(u1, ["创建", "p1deck"])
        for c in ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam"]:
            self.router.handle_deck_cmd(u1, ["添加", c, "4"])
        self.router.handle_deck_cmd(u1, ["添加", "duel_meteor_swarm", "2"])
        self.router.handle_deck_cmd(u1, ["添加", "duel_frost_nova", "2"])
        self.router.handle_deck_cmd(u2, ["创建", "p2deck"])
        for c in ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam", "duel_fireball"]:
            self.router.handle_deck_cmd(u2, ["添加", c, "4"])
            
        self.router.handle_duel_cmd(u1, "张三", [f"@user2"])
        self.router.handle_duel_cmd(u2, "李四", ["接受"])
        
        run = self.save_manager.load_duel_save(u1)
        run.player.hand = ["duel_meteor_swarm", "duel_frost_nova"]
        run.player.actions = 10
        
        from game.models.state import MinionState
        run.player2.minions["1"] = MinionState(id="water_elemental", name="水元素", hp=9999, max_hp=9999, atk=2, actions=1, bonus_actions=0)
        self.save_manager.save_duel_save(u1, run)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1"])
        self.assertNotIn("【空】", res)
        self.assertNotIn("对手", res)
        self.assertIn("水元素", res)
        
        run = self.save_manager.load_duel_save(u1)
        self.assertLess(run.player2.hp, 200)
        self.assertLess(run.player2.minions["1"].hp, 9999)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1"])
        self.assertNotIn("【空】", res)
        self.assertNotIn("对手", res)
        self.assertIn("水元素", res)

    def test_aoe_spells_redesign_and_balancing(self):
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
        run.player.hand = ["duel_meteor_swarm", "duel_doomsday_judgment", "duel_shockwave"]
        run.player.actions = 10
        run.player.bonus_actions = 10
        
        from game.models.state import MinionState
        run.player2.minions["1"] = MinionState(id="water_elemental", name="水元素", hp=100, max_hp=100, atk=2, actions=1, bonus_actions=0)
        self.save_manager.save_duel_save(u1, run)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1"])
        self.assertNotIn("❌", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertLess(run.player2.hp, 200)
        self.assertLess(run.player2.minions["1"].hp, 100)
        
        run.player.hand = ["duel_doomsday_judgment", "duel_shockwave"]
        run.player.actions = 10
        self.save_manager.save_duel_save(u1, run)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1"])
        self.assertNotIn("❌", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertLess(run.player2.hp, 180)
        
        leader_has_stun = any(b.id == "stun" for b in run.player2.buffs)
        minion_has_stun = any(b.id == "stun" for b in run.player2.minions["1"].buffs)
        self.assertTrue(leader_has_stun)
        self.assertTrue(minion_has_stun)
        
        run.player.hand = ["duel_shockwave"]
        run.player.actions = 10
        self.save_manager.save_duel_save(u1, run)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1"])
        self.assertNotIn("❌", res)
        run = self.save_manager.load_duel_save(u1)
        
        leader_has_vuln = any(b.id == "minor_vulnerable" for b in run.player2.buffs)
        minion_has_vuln = any(b.id == "minor_vulnerable" for b in run.player2.minions["1"].buffs)
        self.assertTrue(leader_has_vuln)
        self.assertTrue(minion_has_vuln)

    def test_tiered_limits_and_complex_rare_cards(self):
        from game.data.duel_card_data import DUEL_CARD_CONFIG
        DUEL_CARD_CONFIG["duel_mythic_test"] = {"name": "神话测试", "rarity": "mythic", "type": "spell", "color": "neutral", "cost_a": 1, "cost_ba": 0, "desc": "神话测试"}
        
        u1 = "user1"
        self.router.handle_deck_cmd(u1, ["创建", "limitdeck"])
        
        res, _ = self.router.handle_deck_cmd(u1, ["添加", "duel_mythic_test", "2"])
        self.assertIn("只能携带 1 张", res)
        
        self.router.handle_deck_cmd(u1, ["添加", "duel_mythic_test", "1"])
        res, _ = self.router.handle_deck_cmd(u1, ["添加", "duel_meteor_swarm", "3"])
        self.assertIn("只能携带 2 张", res)
        
        u2 = "user2"
        self.router.handle_deck_cmd(u2, ["创建", "p2deck"])
        for c in ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam"]:
            self.router.handle_deck_cmd(u2, ["添加", c, "4"])
        self.router.handle_deck_cmd(u2, ["添加", "duel_meteor_swarm", "2"])
        
        self.router.handle_deck_cmd(u1, ["创建", "p1deck"])
        for c in ["duel_warrior_strike", "duel_warrior_defend", "duel_warrior_bash", "duel_iron_wave", "duel_warrior_anger", "duel_body_slam"]:
            self.router.handle_deck_cmd(u1, ["添加", c, "4"])
        self.router.handle_deck_cmd(u1, ["添加", "duel_meteor_swarm", "2"])
            
        self.router.handle_duel_cmd(u1, "张三", [f"@user2"])
        self.router.handle_duel_cmd(u2, "李四", ["接受"])
        
        run = self.save_manager.load_duel_save(u1)
        run.player.hand = ["duel_mana_overload", "duel_destiny_scales", "duel_ancient_blessing", "duel_storm_barrier"]
        run.player.actions = 10
        run.player.bonus_actions = 0
        run.player.hp = 70
        
        from game.models.state import MinionState
        run.player2.minions["1"] = MinionState(id="water_elemental", name="水元素", hp=15, max_hp=30, atk=2, actions=1, bonus_actions=0)
        self.save_manager.save_duel_save(u1, run)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "e2"])
        self.assertNotIn("❌", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertNotIn("1", run.player2.minions)
        self.assertEqual(run.player.bonus_actions, 2)
        
        run.player.hand = ["duel_destiny_scales"]
        run.player.actions = 10
        run.player2.minions["2"] = MinionState(id="fam", name="魔宠", hp=10, max_hp=30, atk=25, actions=1, bonus_actions=0)
        from game.models.state import BuffState
        run.player2.minions["2"].buffs.append(BuffState(id="vulnerable", name="易伤", desc="", stacks=2))
        self.save_manager.save_duel_save(u1, run)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1", "e3"])
        self.assertNotIn("❌", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertIn("2", run.player2.minions)
        self.assertEqual(run.player2.minions["2"].atk, 10)
        
        run.player.hand = ["duel_ancient_blessing"]
        run.player.actions = 10
        run.player.minions.clear()
        self.save_manager.save_duel_save(u1, run)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1"])
        self.assertNotIn("❌", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(len(run.player.hand), 2)
        
        run.player.hand = ["duel_ancient_blessing"]
        run.player.actions = 10
        run.player.minions["1"] = MinionState(id="m1", name="m1", hp=4, max_hp=4, atk=2, actions=1, bonus_actions=0)
        run.player.minions["2"] = MinionState(id="m2", name="m2", hp=4, max_hp=4, atk=2, actions=1, bonus_actions=0)
        run.player.minions["3"] = MinionState(id="m3", name="m3", hp=4, max_hp=4, atk=2, actions=1, bonus_actions=0)
        self.save_manager.save_duel_save(u1, run)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1"])
        self.assertNotIn("❌", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player.minions["1"].atk, 4)
        self.assertEqual(run.player.minions["1"].hp, 6)
        self.assertEqual(run.player.shield, 8)
        
        run.player.hand = ["duel_storm_barrier"]
        run.player.actions = 10
        run.player.hp = 70
        run.player.shield = 0
        run.player2.minions.clear()
        run.player2.minions["1"] = MinionState(id="m1", name="m1", hp=10, max_hp=10, atk=2, actions=1, bonus_actions=0)
        self.save_manager.save_duel_save(u1, run)
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1"])
        self.assertNotIn("❌", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player.shield, 20)
        self.assertEqual(run.player2.minions["1"].hp, 4)
        has_weak = any(b.id == "weak" for b in run.player2.minions["1"].buffs)
        self.assertTrue(has_weak)

    def test_player_lord_buff_rendering_and_effects(self):
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
        run.player.hand = ["duel_reward_fury"]
        run.player.actions = 10
        self.save_manager.save_duel_save(u1, run)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["使用", "1"])
        self.assertNotIn("❌", res)
        self.assertIn("狂怒", res)
        
        run = self.save_manager.load_duel_save(u1)
        has_fury = any(b.id == "duel_fury_buff" for b in run.player.buffs)
        self.assertTrue(has_fury)
        
        public_view = render_duel_battle_public(run)
        self.assertIn("狂怒", public_view)
        
        private_view = render_duel_battle_private(run)
        self.assertIn("狂怒", private_view)

    def test_duel_query_isolation(self):
        u1 = "user1"
        res, _, _, _, _, _ = self.router.handle_duel_cmd(u1, "张三", ["查询", "duel_warrior_strike"])
        self.assertNotIn("未找到", res)
        self.assertNotIn("未知", res)
        self.assertIn("卡牌：", res)
        
        res_relic, _, _, _, _, _ = self.router.handle_duel_cmd(u1, "张三", ["查询", "ancient_eye"])
        self.assertIn("未在对决模式中匹配到", res_relic)
