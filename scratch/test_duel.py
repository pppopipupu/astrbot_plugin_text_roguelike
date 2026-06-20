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
        
        run.player.minions["1"] = MinionState(
            id="water_elemental",
            name="寒冰元素",
            hp=15,
            max_hp=15,
            atk=3,
            actions=3,
            bonus_actions=0,
            attack_actions=1
        )
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
        
        run.player.minions["1"] = MinionState(
            id="commander_patrol_captain",
            name="巡逻队长",
            hp=10,
            max_hp=20,
            atk=4,
            actions=3,
            bonus_actions=1,
            attack_actions=1
        )
        run.player.minions["2"] = MinionState(
            id="officer_banner_bearer",
            name="军旗手",
            hp=10,
            max_hp=15,
            atk=2,
            actions=3,
            bonus_actions=1,
            attack_actions=1
        )
        self.save_manager.save_duel_save(u1, run)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["m", "1", "sk", "1"])
        self.assertIn("恢复了", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player.minions["1"].hp, 13)
        self.assertEqual(run.player.minions["2"].hp, 13)
        self.assertEqual(run.player.shield, 3)
        
        res, term, p1, dm1, p2, dm2 = self.router.route_in_game_action(run, u1, "张三", ["m", "2", "sk", "1"])
        self.assertIn("激励了", res)
        run = self.save_manager.load_duel_save(u1)
        self.assertEqual(run.player.minions["1"].atk, 6)

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
        self.assertIsNotNone(card_obj)
        self.assertEqual(card_obj.name, "对决·打击")
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

if __name__ == "__main__":
    unittest.main()
