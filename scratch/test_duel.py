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
        self.assertIn("打击", res)
        self.assertIn("火球术", res)
        
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
        
        run = self.save_manager.load_duel_save(u1)
        self.assertIsNotNone(run)
        self.assertEqual(run.player.hp, 200)
        self.assertEqual(run.player2.hp, 200)
        self.assertEqual(run.node_data["player1_name"], "张三")
        self.assertEqual(run.node_data["player2_name"], "李四")
        
        ev = DummyEvent("", u1)
        
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
        
        from game.entities.cards.duel import ALL_DUEL_CARDS
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

if __name__ == "__main__":
    unittest.main()
