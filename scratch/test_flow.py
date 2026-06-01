import os
import sys
import io
import unittest
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from game.models.manager import SaveManager
from game.models.state import GameRun, PlayerState, EnemyState, MinionState, BuffState
from game.core.battle_engine import BattleEngine
from game.core.map_engine import MapEngine
from game.entities.cards.base import ALL_CARDS
from game.renderer.query import render_query_info
from game.core.cli_router import CLIRouter
from game.models.state import UserStats
from game.engine import GameEngine
from main import MyPlugin

class DummyContext:
    pass

class DummyEvent:
    def __init__(self, message_str: str, sender_id: str = "test_user"):
        self.message_str = message_str
        self.sender_id = sender_id
        self.results = []
        self.stopped = False

    def get_sender_id(self) -> str:
        return self.sender_id

    def plain_result(self, text: str):
        self.results.append(text)
        return text

    def stop_event(self):
        self.stopped = True

async def run_command(plugin, cmd_str: str, sender_id: str = "test_user") -> str:
    event = DummyEvent(cmd_str, sender_id)
    await plugin.shortcut_rogue(event)
    if not event.results:
        generator = plugin.rogue(event)
        async for _ in generator:
            pass
    return "\n".join(event.results)

class TestRoguePlugin(unittest.TestCase):

    def test_basic_flow(self):
        plugin = MyPlugin(DummyContext())
        save_manager = SaveManager()
        save_manager.delete_save("test_user")
        
        async def go():
            res = await run_command(plugin, ".rogue 开启 确认")
            self.assertTrue(any(x in res for x in ["先古契约", "深渊契约", "极寒契约"]))
            res = await run_command(plugin, ".rogue 选择 1")
            self.assertIn("契约达成", res)
            res = await run_command(plugin, ".rogue 状态")
            self.assertIn("第 2 层", res)
            res = await run_command(plugin, ".rogue 牌组")
            self.assertIn("当前拥有的卡组", res)
            res = await run_command(plugin, ".rogue 选择 1")
            self.assertTrue(any(x in res for x in ["战斗", "遭遇战", "神秘事件", "商店", "精英战", "营地", "选择"]))
            save_manager.delete_save("test_user")
            
        asyncio.run(go())

    def test_card_retain_and_agile_bypass(self):
        player = PlayerState(
            hp=30,
            max_hp=30,
            shield=0,
            gold=100,
            stage=2,
            deck=["first_aid", "dagger_throw", "agile_strike"],
            draw_pile=["first_aid"] * 8,
            discard_pile=[],
            exhaust_pile=[],
            graveyard=[],
            hand=["first_aid", "dagger_throw", "agile_strike"],
            actions=2,
            bonus_actions=1
        )
        enemy = EnemyState(
            name="测试敌人",
            hp=20,
            max_hp=20,
            shield=0
        )
        run = GameRun(
            user_id="test_user_retain",
            node_type="battle",
            player=player,
            enemies=[enemy]
        )
        plugin = MyPlugin(DummyContext())
        engine = plugin.engine.battle_engine
        engine.end_turn(run)
        self.assertIn("first_aid", player.hand)
        self.assertNotIn("dagger_throw", player.hand)
        self.assertNotIn("agile_strike", player.hand)
        self.assertIn("dagger_throw", player.discard_pile)
        self.assertIn("agile_strike", player.discard_pile)
        self.assertEqual(enemy.hp, 20)

    def test_tactical_focus_effect(self):
        player = PlayerState(
            hp=30,
            max_hp=30,
            shield=0,
            gold=100,
            stage=2,
            deck=["tactical_focus"],
            draw_pile=["dagger_throw", "first_aid", "lucky_coin", "thorns_necklace", "iron_will", "quick_strike", "arcane_spark"],
            discard_pile=[],
            exhaust_pile=[],
            graveyard=[],
            hand=["tactical_focus"],
            actions=2,
            bonus_actions=1
        )
        enemy = EnemyState(
            name="测试敌人",
            hp=20,
            max_hp=20,
            shield=0
        )
        run = GameRun(
            user_id="test_user_focus",
            node_type="battle",
            player=player,
            enemies=[enemy]
        )
        plugin = MyPlugin(DummyContext())
        engine = plugin.engine.battle_engine
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
        engine.save_manager = DummySaveManager()
        self.assertEqual(len(player.hand), 1)
        self.assertEqual(player.hand[0], "tactical_focus")
        engine.play_card(run, 1)
        self.assertNotIn("tactical_focus", player.hand)
        self.assertEqual(len(player.hand), 3)
        self.assertEqual(player.actions, 2)
        self.assertEqual(player.bonus_actions, 1)
        focus_buff = next(b for b in player.buffs if b.id == "tactical_focus")
        self.assertEqual(focus_buff.name, "无法抽牌")
        self.assertEqual(focus_buff.stacks, 1)
        original_hand_len = len(player.hand)
        engine._draw_cards(player, 1, run)
        self.assertEqual(len(player.hand), original_hand_len)
        engine.end_turn(run)
        self.assertFalse(any(b.id == "tactical_focus" for b in player.buffs))
        player.buffs.append(BuffState(id="tactical_focus", name="无法抽牌", desc="本回合无法再抽牌", stacks=2))
        player.draw_pile = ["dagger_throw"] * 10
        player.discard_pile = []
        player.hand = []
        engine.end_turn(run)
        self.assertEqual(len(player.hand), 6)
        self.assertTrue(any(b.id == "tactical_focus" for b in player.buffs))
        self.assertEqual(next(b for b in player.buffs if b.id == "tactical_focus").stacks, 1)
        curr_hand_len = len(player.hand)
        engine._draw_cards(player, 1, run)
        self.assertEqual(len(player.hand), curr_hand_len)
        engine._draw_cards(player, 1, run, ignore_focus=True)
        self.assertEqual(len(player.hand), curr_hand_len + 1)
        engine.end_turn(run)
        self.assertFalse(any(b.id == "tactical_focus" for b in player.buffs))

        player_upg = PlayerState(
            hp=30,
            max_hp=30,
            shield=0,
            gold=100,
            stage=2,
            deck=["tactical_focus+"],
            draw_pile=["dagger_throw", "first_aid", "lucky_coin", "thorns_necklace", "iron_will", "quick_strike", "arcane_spark"],
            discard_pile=[],
            exhaust_pile=[],
            graveyard=[],
            hand=["tactical_focus+"],
            actions=2,
            bonus_actions=1
        )
        run_upg = GameRun(
            user_id="test_user_focus_upgraded",
            node_type="battle",
            player=player_upg,
            enemies=[enemy]
        )
        engine.play_card(run_upg, 1)
        self.assertNotIn("tactical_focus+", player_upg.hand)
        self.assertEqual(len(player_upg.hand), 5)
        self.assertEqual(player_upg.actions, 2)
        self.assertEqual(player_upg.bonus_actions, 1)
        focus_buff_upg = next(b for b in player_upg.buffs if b.id == "tactical_focus")
        self.assertEqual(focus_buff_upg.name, "无法抽牌")
        self.assertEqual(focus_buff_upg.stacks, 1)

    def test_echo_form_logic(self):
        def run_echo_test(stacks, num_cards_to_play):
            player = PlayerState(
                hp=30,
                max_hp=30,
                shield=0,
                gold=100,
                stage=2,
                deck=["fire_bolt"] * 10,
                draw_pile=["fire_bolt"] * 10,
                discard_pile=[],
                exhaust_pile=[],
                graveyard=[],
                hand=["fire_bolt"] * 10,
                actions=99,
                bonus_actions=99,
                buffs=[BuffState(id="echo_form", name="回响形态", stacks=stacks, desc="")]
            )
            enemy = EnemyState(
                name="测试敌人",
                hp=9999,
                max_hp=9999,
                shield=0
            )
            run = GameRun(
                user_id="test_user_echo",
                node_type="battle",
                player=player,
                enemies=[enemy]
            )
            class DummySaveManager:
                def save_save(self, user_id, run):
                    pass
                def delete_save(self, user_id):
                    pass
            engine = BattleEngine(DummySaveManager())
            results = []
            for i in range(num_cards_to_play):
                res = engine.play_card(run, 1)
                echo_count = res.count("[回响触发]")
                results.append(echo_count)
            return results

        res5 = run_echo_test(5, 3)
        self.assertEqual(res5, [5, 0, 0])
        res10 = run_echo_test(10, 3)
        self.assertEqual(res10, [8, 2, 0])
        res24 = run_echo_test(24, 4)
        self.assertEqual(res24, [8, 8, 8, 0])

        player = PlayerState(
            hp=30,
            max_hp=30,
            shield=0,
            gold=100,
            stage=2,
            deck=["echo_form"],
            draw_pile=["echo_form"],
            discard_pile=[],
            exhaust_pile=[],
            graveyard=[],
            hand=["echo_form"],
            actions=99,
            bonus_actions=99
        )
        enemy = EnemyState(
            name="测试敌人",
            hp=100,
            max_hp=100,
            shield=0
        )
        run = GameRun(
            user_id="test_user_echo_self",
            node_type="battle",
            player=player,
            enemies=[enemy]
        )
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
        engine = BattleEngine(DummySaveManager())
        res = engine.play_card(run, 1)
        self.assertEqual(res.count("[回响触发]"), 0)
        self.assertEqual(next(b for b in player.buffs if b.id == "echo_form").stacks, 1)

    def test_inner_shop_flow(self):
        plugin = MyPlugin(DummyContext())
        user_id = "test_inner_shop_user"
        plugin.save_manager.delete_save(user_id)
        
        async def go():
            await run_command(plugin, ".rogue 开启", sender_id=user_id)
            await run_command(plugin, ".rogue 选择 1", sender_id=user_id)
            run = plugin.save_manager.load_save(user_id)
            self.assertIsNotNone(run)
            run.node_type = "shop"
            plugin.engine.map_engine.explore_engine._init_shop_node(run)
            plugin.save_manager.save_save(user_id, run)
            
            status_output = await run_command(plugin, ".rogue 状态", sender_id=user_id)
            self.assertIn("奇妙商店", status_output)
            self.assertIn("净化服务", status_output)
            self.assertIn("离开商店", status_output)
            
            run = plugin.save_manager.load_save(user_id)
            run.player.gold = 500
            plugin.save_manager.save_save(user_id, run)
            initial_gold = 500
            initial_deck_len = len(run.player.deck)
            
            items = run.node_data.get("items", [])
            card_idx = -1
            for idx, item in enumerate(items):
                if item.get("type") == "card":
                    card_idx = idx + 1
                    break
            self.assertNotEqual(card_idx, -1)
            buy_res = await run_command(plugin, f".rogue 选择 {card_idx}", sender_id=user_id)
            self.assertIn("购买成功", buy_res)
            
            run = plugin.save_manager.load_save(user_id)
            self.assertEqual(len(run.player.deck), initial_deck_len + 1)
            self.assertLess(run.player.gold, initial_gold)
            
            relic_idx = -1
            for idx, item in enumerate(items):
                if item.get("type") == "relic":
                    relic_idx = idx + 1
                    break
            if relic_idx != -1:
                run = plugin.save_manager.load_save(user_id)
                run.player.gold = 500
                plugin.save_manager.save_save(user_id, run)
                buy_relic_res = await run_command(plugin, f".rogue 选择 {relic_idx}", sender_id=user_id)
                self.assertIn("购买成功", buy_relic_res)
                run = plugin.save_manager.load_save(user_id)
                relic_id = items[relic_idx - 1].get("relic_id")
                self.assertIn(relic_id, run.player.relics)
                
            leave_idx = -1
            for idx, item in enumerate(items):
                if item.get("type") == "leave":
                    leave_idx = idx + 1
                    break
            self.assertNotEqual(leave_idx, -1)
            leave_res = await run_command(plugin, f".rogue 选择 {leave_idx}", sender_id=user_id)
            self.assertIn("你离开了商店", leave_res)
            run = plugin.save_manager.load_save(user_id)
            self.assertNotEqual(run.node_type, "shop")
            
        asyncio.run(go())

    def test_damage_system_and_real_damage(self):
        class DummySaveManager:
            def __init__(self):
                self.dir = "data_test"
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
        save_mgr = DummySaveManager()
        engine = BattleEngine(save_mgr)
        player = PlayerState(
            hp=50,
            max_hp=100,
            shield=0,
            gold=100,
            stage=1,
            deck=["mass_healing_word", "chain_lightning", "magic_missile"],
            hand=["mass_healing_word", "chain_lightning", "magic_missile"],
            minions={
                "1": MinionState("mercenary", "雇佣兵", 5, 10, 4, 1, 0)
            }
        )
        run = GameRun(
            user_id="test_user",
            node_type="battle",
            player=player,
            enemies=[
                EnemyState("哥布林掠夺者 A", 20, 20, 0),
                EnemyState("哥布林掠夺者 B", 20, 20, 0),
                EnemyState("地底史莱姆", 15, 15, 0)
            ]
        )
        run.player.actions = 10
        run.player.bonus_actions = 10
        card_heal = ALL_CARDS["mass_healing_word"]
        card_heal.execute(run, "p0", engine)
        self.assertEqual(run.player.hp, 58)
        self.assertEqual(run.player.minions["1"].hp, 10)
        card_chain = ALL_CARDS["chain_lightning"]
        card_chain.execute(run, "e1", engine)
        self.assertEqual(len(run.enemies), 3)
        self.assertEqual(run.enemies[0].hp, 8)
        self.assertEqual(run.enemies[1].hp, 8)
        self.assertEqual(run.enemies[2].hp, 15)
        enemy_mm = run.enemies[2]
        enemy_mm.shield = 20
        card_mm = ALL_CARDS["magic_missile"]
        card_mm.execute(run, "e3", engine)
        self.assertEqual(enemy_mm.shield, 20)
        self.assertEqual(enemy_mm.hp, 6)
        self.assertTrue(len(run.node_data.get("battle_logs", [])) > 0)
        last_log = run.node_data["battle_logs"][-1]
        self.assertNotIn("对护盾造成", last_log)
        self.assertIn("对生命造成", last_log)
        self.assertNotIn("（", last_log)

        from game.entities.enemies.minions import ShadowFiendTemplate
        fiend_template = ShadowFiendTemplate("暗影影魔")
        fiend_enemy = EnemyState("暗影影魔", 30, 30, 0, intent_type="shadow_strike", intent_val=6)
        fiend_logs = []
        run.player.hp = 50
        run.player.shield = 10
        fiend_template.execute_intent(run, engine, fiend_enemy, fiend_logs)
        self.assertEqual(run.player.shield, 10)
        self.assertEqual(run.player.hp, 44)
        self.assertEqual(len(fiend_logs), 1)
        self.assertIn("对【玩家】造成 6 点真实伤害，对生命造成 6 伤害", fiend_logs[0])

        from game.entities.buffs.buffs import BeatOfDeathBuff
        beat_buff = BeatOfDeathBuff(2)
        class FakeEvent:
            def __init__(self, run, engine):
                self.run = run
                self.engine = engine
        evt = FakeEvent(run, engine)
        run.player.hp = 50
        run.player.shield = 0
        run.node_data["battle_logs"] = []
        beat_buff.on_card_played(evt, None, None)
        self.assertEqual(run.player.hp, 48)
        self.assertEqual(len(run.node_data["battle_logs"]), 2)
        self.assertIn("造成 2 点力场伤害", run.node_data["battle_logs"][-1])

        run.node_data["battle_logs"] = []
        engine._damage_target(run, "e3", 0, damage_type="cold")
        self.assertEqual(len(run.node_data["battle_logs"]), 1)
        self.assertIn("对【地底史莱姆】造成 0 点寒冷伤害（但地底史莱姆免疫了这次攻击！）", run.node_data["battle_logs"][-1])

    def test_enemy_action_sync_and_stun(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
        mgr = DummySaveManager()
        engine = BattleEngine(mgr)
        enemy = EnemyState(
            name="奥术巨魔",
            hp=50,
            max_hp=50,
            shield=0,
            actions=1,
            bonus_actions=1,
            max_actions=1,
            max_bonus_actions=1,
            intent_a_type="attack",
            intent_a_val=10,
            intent_a_desc="攻击 (造成 10 伤害)",
            intent_ba_type="defend",
            intent_ba_val=5,
            intent_ba_desc="防御 (获得 5 护盾)"
        )
        player = PlayerState(hp=45, max_hp=45, shield=0, gold=10, stage=1)
        run = GameRun(user_id="test_user", node_type="battle", player=player, enemies=[enemy])
        engine._sync_enemy_intents(enemy)
        self.assertEqual(enemy.intent_a_type, "attack")
        self.assertEqual(enemy.intent_ba_type, "defend")
        enemy.actions = 0
        engine._sync_enemy_intents(enemy)
        self.assertEqual(enemy.intent_a_type, "")
        self.assertIn("已取消", enemy.intent_a_desc)
        self.assertEqual(enemy.intent_ba_type, "defend")
        enemy.bonus_actions = 0
        engine._sync_enemy_intents(enemy)
        self.assertEqual(enemy.intent_ba_type, "")
        self.assertIn("已取消", enemy.intent_ba_desc)
        enemy.actions = 1
        enemy.bonus_actions = 1
        enemy.intent_a_type = "attack"
        enemy.intent_a_desc = "攻击 (造成 10 伤害)"
        enemy.intent_ba_type = "defend"
        enemy.intent_ba_desc = "防御 (获得 5 护盾)"
        engine._add_buff_to(enemy, "stun", "眩晕", "无法行动", 1)
        self.assertEqual(enemy.actions, 0)
        self.assertEqual(enemy.bonus_actions, 0)
        self.assertEqual(enemy.intent_a_type, "")
        self.assertIn("眩晕", enemy.intent_a_desc)
        self.assertEqual(enemy.intent_ba_type, "")
        enemy.buffs.clear()
        enemy.actions = 1
        enemy.bonus_actions = 1
        enemy.intent_a_type = "attack"
        enemy.intent_a_val = 10
        enemy.intent_a_desc = "攻击 (造成 10 伤害)"
        enemy.intent_ba_type = "defend"
        enemy.intent_ba_val=5
        enemy.intent_ba_desc = "防御 (获得 5 护盾)"
        enemy.intent_type = "old_temp_type"
        enemy.intent_val = 999
        engine._enemy_turn(run)
        self.assertEqual(enemy.intent_type, "old_temp_type")
        self.assertEqual(enemy.intent_val, 999)

    def test_treasure_three_choices(self):
        player = PlayerState(
            hp=30,
            max_hp=30,
            shield=0,
            gold=10,
            stage=4,
            deck=["first_aid", "dagger_throw", "agile_strike"],
            draw_pile=[],
            discard_pile=[],
            exhaust_pile=[],
            graveyard=[],
            hand=[]
        )
        run = GameRun(
            user_id="test_user_treasure",
            node_type="treasure",
            player=player,
            enemies=[]
        )
        plugin = MyPlugin(DummyContext())
        map_engine = plugin.engine.map_engine
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
            def record_stage_passed(self, user_id):
                pass
        map_engine.save_manager = DummySaveManager()
        map_engine._init_treasure_node(run)
        self.assertEqual(run.node_data.get("state"), "pending_remove")
        map_engine.choose_option(run, 3)
        self.assertEqual(run.node_type, "card_select")
        self.assertEqual(len(run.node_data.get("cards", [])), 3)
        self.assertGreater(player.gold, 10)
        self.assertEqual(len(player.deck), 2)
        self.assertNotIn("first_aid", player.deck)
        map_engine.choose_option(run, 4)
        self.assertEqual(player.stage, 5)
        self.assertEqual(len(player.deck), 2)
        player.stage = 3
        run.node_type = "rest"
        map_engine.choose_option(run, 2)
        self.assertEqual(run.node_type, "card_select")
        self.assertEqual(len(run.node_data.get("cards", [])), 3)
        chosen_card = run.node_data["cards"][0]
        map_engine.choose_option(run, 1)
        self.assertEqual(player.stage, 4)
        self.assertEqual(len(player.deck), 3)
        self.assertIn(chosen_card, player.deck)
        player.stage = 5
        player.gold = 20
        run.node_type = "event"
        from game.entities.events import CoinFountainOption
        opt = CoinFountainOption("投入金币", "coin_fountain")
        opt.execute(run, map_engine)
        self.assertEqual(player.gold, 10)
        self.assertEqual(run.node_type, "card_select")
        self.assertEqual(len(run.node_data.get("cards", [])), 3)
        map_engine.choose_option(run, 4)
        self.assertEqual(player.stage, 6)
        self.assertEqual(len(player.deck), 3)

    def test_rogue_mode_and_shortcut(self):
        plugin = MyPlugin(DummyContext())
        plugin.save_manager.delete_save("test_user_rogue")
        stats_path = plugin.save_manager.get_stats_path("test_user_rogue")
        if os.path.exists(stats_path):
            os.remove(stats_path)
        stats = plugin.save_manager.load_stats("test_user_rogue")
        self.assertFalse(stats.rogue_mode)
        
        async def go():
            event_toggle = DummyEvent(".rogue mode", sender_id="test_user_rogue")
            await plugin.shortcut_rogue(event_toggle)
            loaded_stats = plugin.save_manager.load_stats("test_user_rogue")
            self.assertTrue(loaded_stats.rogue_mode)
            self.assertIn("免前缀肉鸽模式已开启", "\n".join(event_toggle.results))
            
            event_start = DummyEvent("开启", sender_id="test_user_rogue")
            await plugin.shortcut_rogue(event_start)
            self.assertTrue(event_start.stopped)
            self.assertTrue(any(x in "\n".join(event_start.results) for x in ["先古契约", "深渊契约", "极寒契约"]))
            
            event_chat = DummyEvent("你好吗", sender_id="test_user_rogue")
            await plugin.shortcut_rogue(event_chat)
            self.assertFalse(event_chat.stopped)
            
            event_num_with_save = DummyEvent("1", sender_id="test_user_rogue")
            await plugin.shortcut_rogue(event_num_with_save)
            self.assertTrue(event_num_with_save.stopped)
            
            event_alias_deck = DummyEvent("deck", sender_id="test_user_rogue")
            await plugin.shortcut_rogue(event_alias_deck)
            self.assertTrue(event_alias_deck.stopped)
            self.assertIn("当前拥有的卡组", "\n".join(event_alias_deck.results))
            
            event_alias_overview = DummyEvent("overview", sender_id="test_user_rogue")
            await plugin.shortcut_rogue(event_alias_overview)
            self.assertTrue(event_alias_overview.stopped)
            self.assertIn("魔法肉鸽卡牌总览", "\n".join(event_alias_overview.results))
            
            event_alias_abandon = DummyEvent("abandon confirm", sender_id="test_user_rogue")
            await plugin.shortcut_rogue(event_alias_abandon)
            self.assertTrue(event_alias_abandon.stopped)
            self.assertIn("已放弃当前局内游戏", "\n".join(event_alias_abandon.results))
            
            event_num_no_save = DummyEvent("1", sender_id="test_user_rogue")
            await plugin.shortcut_rogue(event_num_no_save)
            self.assertFalse(event_num_no_save.stopped)
            
            event_toggle_off = DummyEvent("模式", sender_id="test_user_rogue")
            await plugin.shortcut_rogue(event_toggle_off)
            off_stats = plugin.save_manager.load_stats("test_user_rogue")
            self.assertFalse(off_stats.rogue_mode)
            
            event_start_disabled = DummyEvent("开启", sender_id="test_user_rogue")
            await plugin.shortcut_rogue(event_start_disabled)
            self.assertFalse(event_start_disabled.stopped)
            
        asyncio.run(go())

    def test_shield_decay_mechanism(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        run = GameRun(
            user_id="test_user",
            node_type="battle",
            node_data={"cards_played_this_turn": 0},
            player=PlayerState(
                hp=30,
                max_hp=30,
                shield=15,
                actions=2,
                bonus_actions=1,
                deck=[],
                hand=[],
                draw_pile=[],
                discard_pile=[],
                exhaust_pile=[],
                graveyard=[],
                amulets={},
                minions={},
                buffs=[],
                gold=100,
                stage=1
            ),
            enemies=[
                EnemyState(
                    name="地精突袭者",
                    hp=12,
                    max_hp=12,
                    shield=9,
                    actions=1,
                    bonus_actions=0,
                    max_actions=1,
                    max_bonus_actions=0,
                    intent_a_type="attack",
                    intent_a_val=0,
                    intent_a_desc="准备防守"
                )
            ]
        )
        engine.end_turn(run)
        self.assertEqual(run.player.shield, 7)
        self.assertEqual(run.enemies[0].shield, 4)

    def test_card_upgrade_and_forge(self):
        fb = ALL_CARDS.get("fireball")
        fb_plus = ALL_CARDS.get("fireball+")
        self.assertIsNotNone(fb)
        self.assertIsNotNone(fb_plus)
        self.assertTrue(fb_plus.upgraded)
        self.assertEqual(fb_plus.base_dmg, 24)
        q_res_normal = render_query_info("fireball")
        self.assertIn("升级变体", q_res_normal)
        self.assertIn("24", q_res_normal)
        q_res_plus = render_query_info("fireball+")
        self.assertIn("升级变体", q_res_plus)
        self.assertIn("24", q_res_plus)
        plugin = MyPlugin(DummyContext())
        save_manager = SaveManager()
        save_manager.delete_save("test_user_upg")
        
        async def go():
            await run_command(plugin, ".rogue 开启 确认", sender_id="test_user_upg")
            await run_command(plugin, ".rogue 选择 1", sender_id="test_user_upg")
            run = save_manager.load_save("test_user_upg")
            run.node_type = "rest"
            run.node_data = {}
            save_manager.save_save("test_user_upg", run)
            res = await run_command(plugin, ".rogue 选择 4", sender_id="test_user_upg")
            self.assertIn("卡牌升级强化已启动", res)
            run = save_manager.load_save("test_user_upg")
            self.assertTrue(run.node_data.get("pending_upgrade"))
            res_upg = await run_command(plugin, ".rogue 选择 1", sender_id="test_user_upg")
            self.assertIn("升级成功", res_upg)
            run = save_manager.load_save("test_user_upg")
            self.assertTrue(any(card.endswith("+") for card in run.player.deck))
            run.node_type = "event"
            run.node_data = {
                "event_id": "forge_furnace",
                "description": "奥术符文熔炉描述",
                "options": [
                    {"text": "使用常规重铸", "action": "forge_fire"},
                    {"text": "过载重铸", "action": "overload_forge"},
                    {"text": "汲取熔炉余温", "action": "forge_backfire"},
                    {"text": "强行破坏熔炉", "action": "shatter_forge"},
                    {"text": "安全离开", "action": "leave_event"}
                ]
            }
            save_manager.save_save("test_user_upg", run)
            res_event_fire = await run_command(plugin, ".rogue 选择 1", sender_id="test_user_upg")
            self.assertIn("卡牌升级强化已启动", res_event_fire)
            run = save_manager.load_save("test_user_upg")
            run.node_type = "event"
            run.node_data = {
                "event_id": "forge_furnace",
                "description": "奥术符文熔炉描述",
                "options": [
                    {"text": "使用常规重铸", "action": "forge_fire"},
                    {"text": "过载重铸", "action": "overload_forge"},
                    {"text": "汲取熔炉余温", "action": "forge_backfire"},
                    {"text": "强行破坏熔炉", "action": "shatter_forge"},
                    {"text": "安全离开", "action": "leave_event"}
                ]
            }
            save_manager.save_save("test_user_upg", run)
            res_backfire = await run_command(plugin, ".rogue 选择 3", sender_id="test_user_upg")
            self.assertIn("炉温反噬", res_backfire)
            run = save_manager.load_save("test_user_upg")
            self.assertTrue(any(b.id == "forge_backfire" for b in run.player.buffs))
            save_manager.delete_save("test_user_upg")
            
        asyncio.run(go())

    def test_class_command_aliases(self):
        class DummySaveManagerLocal:
            def __init__(self):
                self.stats = UserStats()
                self.stats.unlocked_subclasses = ["时序法师", "塑能法师"]
            def load_stats(self, user_id):
                return self.stats
            def save_stats(self, user_id, stats):
                self.stats = stats
                return True
            def load_save(self, user_id):
                return None
        mgr = DummySaveManagerLocal()
        router = CLIRouter(mgr, None)
        res = list(router.handle_command("test_user", ["class"]))
        self.assertIn("魔法肉鸽卡牌职业系统", res[0])
        list(router.handle_command("test_user", ["class", "c", "1"]))
        self.assertEqual(mgr.stats.selected_subclass, "时序法师")
        list(router.handle_command("test_user", ["class", "c", "2"]))
        self.assertEqual(mgr.stats.selected_subclass, "塑能法师")
        list(router.handle_command("test_user", ["class", "2"]))
        self.assertEqual(mgr.stats.selected_subclass, "塑能法师")
        list(router.handle_command("test_user", ["class", "0"]))
        self.assertEqual(mgr.stats.selected_subclass, "")
        list(router.handle_command("test_user", ["class", "c", "0"]))
        self.assertEqual(mgr.stats.selected_subclass, "")
        res = list(router.handle_command("test_user", ["class", "c", "4"]))
        self.assertIn("无效的子职业", res[0])
        list(router.handle_command("test_user", ["class", "c", "时序法师"]))
        self.assertEqual(mgr.stats.selected_subclass, "时序法师")
        list(router.handle_command("test_user", ["class", "无"]))
        self.assertEqual(mgr.stats.selected_subclass, "")

    def test_fragile_card_mechanism(self):
        player = PlayerState(
            hp=30,
            max_hp=30,
            shield=0,
            gold=100,
            stage=2,
            deck=["thunderwave"],
            draw_pile=["thunderwave"],
            discard_pile=[],
            exhaust_pile=[],
            graveyard=[],
            hand=["thunderwave"],
            actions=10,
            bonus_actions=10
        )
        enemy = EnemyState(
            name="测试敌人",
            hp=50,
            max_hp=50,
            shield=0
        )
        run = GameRun(
            user_id="test_user_fragile",
            node_type="battle",
            player=player,
            enemies=[enemy]
        )
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
        engine = BattleEngine(DummySaveManager())
        card_wave = ALL_CARDS.get("thunderwave")
        self.assertEqual(card_wave.fragile, 3)
        self.assertIn("(易碎 3)", card_wave.name)
        self.assertIn("易碎 3。", card_wave.desc)
        
        engine.play_card(run, 1)
        self.assertIn("thunderwave:fragile:2", player.discard_pile)
        self.assertEqual(len(player.deck), 1)
        self.assertEqual(player.deck[0], "thunderwave")
        
        player.hand = ["thunderwave:fragile:2"]
        card_fragile_2 = ALL_CARDS.get("thunderwave:fragile:2")
        self.assertEqual(card_fragile_2.fragile, 2)
        self.assertIn("(易碎 2)", card_fragile_2.name)
        self.assertIn("易碎 2。", card_fragile_2.desc)
        
        engine.play_card(run, 1)
        self.assertIn("thunderwave:fragile:1", player.discard_pile)
        self.assertEqual(len(player.deck), 1)
        
        player.discard_pile.clear()
        player.hand = ["thunderwave:fragile:1"]
        engine.play_card(run, 1)
        self.assertNotIn("thunderwave:fragile:0", player.discard_pile)
        self.assertNotIn("thunderwave", player.discard_pile)
        self.assertNotIn("thunderwave:fragile:1", player.discard_pile)
        self.assertEqual(len(player.deck), 0)
        
        card_wave_plus = ALL_CARDS.get("thunderwave+")
        self.assertEqual(card_wave_plus.fragile, 3)
        self.assertIn("(易碎 3)", card_wave_plus.name)
        self.assertIn("雷鸣波+", card_wave_plus.name)
        self.assertIn("易碎 3。", card_wave_plus.desc)
        
        card_wave_plus_2 = ALL_CARDS.get("thunderwave+:fragile:2")
        self.assertEqual(card_wave_plus_2.fragile, 2)
        self.assertIn("雷鸣波+", card_wave_plus_2.name)
        self.assertIn("(易碎 2)", card_wave_plus_2.name)

        from game.renderer.query import render_query_info
        q_fragile = render_query_info("易碎")
        self.assertIn("易碎", q_fragile)
        self.assertIn("从牌组中永久移除", q_fragile)
        q_recall = render_query_info("死者召回")
        self.assertIn("死者召回", q_recall)
        self.assertIn("阵亡随从", q_recall)

    def test_awaiting_target_cancel(self):
        save_manager = SaveManager()
        engine = GameEngine(save_manager)
        router = CLIRouter(save_manager, engine)
        user_id = "test_user_awaiting_cancel"
        save_manager.delete_save(user_id)
        player = PlayerState(
            hp=45,
            max_hp=45,
            shield=0,
            gold=20,
            stage=3,
            deck=["fleeting_spark", "fleeting_spark"],
            hand=["fleeting_spark", "fleeting_spark"],
            actions=2,
            bonus_actions=1
        )
        enemies = [
            EnemyState(
                name="哥布林 A",
                hp=18,
                max_hp=18,
                shield=0,
                intent_type="attack",
                intent_val=6,
                intent_desc="攻击",
                intent_a_type="attack",
                intent_a_val=6,
                intent_a_desc="攻击"
            ),
            EnemyState(
                name="哥布林 B",
                hp=18,
                max_hp=18,
                shield=0,
                intent_type="shield",
                intent_val=7,
                intent_desc="防御",
                intent_a_type="shield",
                intent_a_val=7,
                intent_a_desc="防御"
            )
        ]
        run = GameRun(
            user_id=user_id,
            node_type="battle",
            player=player,
            enemies=enemies
        )
        run.node_data["state_stack"] = [{
            "type": "awaiting_target",
            "action": "play_card",
            "hand_idx": 1
        }]
        save_manager.save_save(user_id, run)
        generator = router.handle_command(user_id, ["p", "2"])
        results = list(generator)
        output_text = "\n".join(results)
        loaded_run = save_manager.load_save(user_id)
        state_stack = loaded_run.node_data.get("state_stack", [])
        self.assertNotIn("❌ 取消使用操作。", output_text)
        self.assertTrue(len(state_stack) > 0)
        top_state = state_stack[-1]
        self.assertEqual(top_state.get("type"), "awaiting_target")
        self.assertEqual(top_state.get("hand_idx"), 2)
        save_manager.delete_save(user_id)

    def test_battle_logs_persistence(self):
        save_manager = SaveManager()
        user_id = "test_user_logs_persistence"
        save_manager.delete_save(user_id)
        player = PlayerState(
            hp=45,
            max_hp=45,
            shield=0,
            gold=20,
            stage=3,
            deck=[],
            hand=[],
            actions=2,
            bonus_actions=1
        )
        run = GameRun(
            user_id=user_id,
            node_type="battle",
            player=player,
            enemies=[]
        )
        run.node_data["battle_logs"] = ["log1", "log2"]
        save_manager.save_save(user_id, run)
        self.assertIn("battle_logs", run.node_data)
        loaded_run = save_manager.load_save(user_id)
        self.assertIsNotNone(loaded_run)
        self.assertNotIn("battle_logs", loaded_run.node_data)
        save_manager.delete_save(user_id)

    def test_sunburst_effects(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=50,
            max_hp=100,
            shield=0,
            gold=100,
            stage=1,
            deck=["sunburst", "sunburst+"],
            hand=["sunburst", "sunburst+"],
            minions={
                "1": MinionState("mercenary", "雇佣兵", 30, 30, 4, 1, 0),
                "2": MinionState("shield_guard", "盾卫", 10, 10, 2, 1, 0)
            }
        )
        player.minions["1"].buffs.append(BuffState(id="burning", name="燃烧", desc="每回合受伤害", stacks=2))
        run = GameRun(
            user_id="test_user_sunburst",
            node_type="battle",
            player=player,
            enemies=[EnemyState("测试敌人", 30, 30, 0)]
        )
        card_sunburst = ALL_CARDS["sunburst"]
        card_sunburst.execute(run, None, engine)
        self.assertEqual(run.enemies[0].hp, 14)
        self.assertEqual(player.minions["1"].hp, 14)
        self.assertEqual(len(player.minions["1"].buffs), 1)
        self.assertEqual(player.minions["1"].atk, 4)
        self.assertNotIn("2", player.minions)
        
        player_upg = PlayerState(
            hp=50,
            max_hp=100,
            shield=0,
            gold=100,
            stage=1,
            deck=["sunburst", "sunburst+"],
            hand=["sunburst", "sunburst+"],
            minions={
                "1": MinionState("mercenary", "雇佣兵", 30, 30, 4, 1, 0),
                "2": MinionState("shield_guard", "盾卫", 10, 10, 2, 1, 0)
            }
        )
        player_upg.minions["1"].buffs.append(BuffState(id="burning", name="燃烧", desc="每回合受伤害", stacks=2))
        run_upg = GameRun(
            user_id="test_user_sunburst_upg",
            node_type="battle",
            player=player_upg,
            enemies=[EnemyState("测试敌人", 30, 30, 0)]
        )
        card_sunburst_upg = ALL_CARDS["sunburst+"]
        card_sunburst_upg.execute(run_upg, None, engine)
        self.assertEqual(run_upg.enemies[0].hp, 8)
        self.assertEqual(player_upg.minions["1"].hp, 8)
        self.assertEqual(len(player_upg.minions["1"].buffs), 0)
        self.assertEqual(player_upg.minions["1"].atk, 7)
        self.assertNotIn("2", player_upg.minions)

    def test_chain_lightning_default_target(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=50,
            max_hp=100,
            shield=0,
            gold=100,
            stage=1,
            deck=["chain_lightning"],
            hand=["chain_lightning"],
            actions=2,
            bonus_actions=1
        )
        run = GameRun(
            user_id="test_user_chain",
            node_type="battle",
            player=player,
            enemies=[EnemyState("哥布林 A", 20, 20, 0)]
        )
        res = engine.play_card(run, 1, None)
        self.assertIn("释放【链式闪电】", res)
        self.assertEqual(run.enemies[0].hp, 8)

    def test_blacklist_spell_targeting(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=20,
            max_hp=50,
            shield=0,
            gold=100,
            stage=1,
            deck=["first_aid", "magic_missile"],
            hand=["first_aid", "magic_missile"],
            actions=5,
            bonus_actions=5
        )
        run = GameRun(
            user_id="test_user_blacklist_targeting",
            node_type="battle",
            player=player,
            enemies=[EnemyState("哥布林 A", 20, 20, 0)]
        )
        engine.play_card(run, 1, None)
        self.assertEqual(player.hp, 24)
        engine.play_card(run, 1, None)
        self.assertEqual(run.enemies[0].hp, 11)

    def test_iron_will_upgrade_and_stack(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=20,
            max_hp=40,
            shield=0,
            gold=100,
            stage=1,
            deck=["iron_will+", "first_aid"],
            hand=["iron_will+", "first_aid"],
            actions=5,
            bonus_actions=5
        )
        run = GameRun(
            user_id="test_user_iron_will_upg",
            node_type="battle",
            player=player,
            enemies=[EnemyState("测试敌人", 100, 100, 0, max_actions=0)]
        )
        engine.play_card(run, 1, None)
        self.assertEqual(player.shield, 8)
        self.assertEqual(player.hp, 35)
        engine.play_card(run, 1, None)
        self.assertEqual(player.hp, 43)
        engine.end_turn(run)
        player.actions = 5
        player.bonus_actions = 5
        player.hand = ["first_aid", "first_aid"]
        engine.play_card(run, 1, None)
        self.assertEqual(player.hp, 51)
        engine.end_turn(run)
        player.actions = 5
        player.bonus_actions = 5
        player.hand = ["first_aid"]
        engine.play_card(run, 1, None)
        self.assertEqual(player.hp, 55)

    def test_minion_reindexing(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=50,
            max_hp=100,
            shield=0,
            gold=100,
            stage=1,
            deck=["quick_strike"],
            hand=["quick_strike"],
            actions=5,
            bonus_actions=5,
            minions={
                "1": MinionState("mercenary", "雇佣兵 1", 20, 20, 4, 1, 0),
                "2": MinionState("mercenary", "雇佣兵 2", 10, 10, 4, 1, 0),
                "3": MinionState("mercenary", "雇佣兵 3", 30, 30, 4, 1, 0)
            }
        )
        run = GameRun(
            user_id="test_user_reindexing",
            node_type="battle",
            player=player,
            enemies=[EnemyState("测试敌人", 30, 30, 0)]
        )
        engine._damage_target(run, "p2", 10, damage_type="true")
        self.assertNotIn("2", player.minions)
        self.assertIn("3", player.minions)
        engine.play_card(run, 1, None)
        self.assertEqual(len(player.minions), 2)
        self.assertEqual(player.minions["1"].name, "雇佣兵 1")
        self.assertEqual(player.minions["2"].name, "雇佣兵 3")
        self.assertNotIn("3", player.minions)

    def test_gatekey_and_ancient_mechanics(self):
        class DummySaveManager:
            def __init__(self):
                self.stats = UserStats()
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
            def load_stats(self, user_id):
                return self.stats
            def save_stats(self, user_id, stats):
                self.stats = stats
                return True
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=40,
            max_hp=40,
            shield=0,
            gold=100,
            stage=20,
            deck=["arcane_torrent", "arcane_barrier"],
            hand=["arcane_torrent", "arcane_barrier"],
            actions=3,
            bonus_actions=2,
            minion_graveyard=["mercenary"]
        )
        run = GameRun(
            user_id="test_ancient_user",
            node_type="battle",
            player=player,
            enemies=[EnemyState("虚空之门·尤格-索托斯", 5, 5, 0, max_actions=0)]
        )
        engine.combat_resolver.damage_target(run, "e1", 10, damage_type="bludgeoning")
        self.assertEqual(run.enemies[0].name, "【觉醒】虚空之门·尤格-索托斯")
        self.assertEqual(run.enemies[0].hp, 260)
        self.assertTrue(any(b.id == "end_gate_passive" for b in run.enemies[0].buffs))
        msg = engine.combat_resolver.recall_dead_minion(run, 15)
        self.assertIn("召回", msg)
        self.assertEqual(len(player.minion_graveyard), 0)
        self.assertEqual(player.minions["1"].id, "mercenary")
        res = engine.play_card(run, 1, "e1")
        self.assertEqual(player.actions, 0, f"Actions not zero! Result: {res}")
        self.assertEqual(run.node_data.get("last_x_cost_a"), 3)
        player.actions = 3
        player.bonus_actions = 2
        player.relics.append("chemical_x")
        res2 = engine.play_card(run, 1, "e1")
        self.assertEqual(player.bonus_actions, 0, f"Bonus actions not zero! Result: {res2}")
        self.assertEqual(run.node_data.get("last_x_cost_ba"), 4)
        self.assertEqual(player.actions, 3)
        enemy_test = EnemyState("测试敌人", 10, 10, 0, actions=2, max_actions=2)
        run.enemies = [enemy_test]
        player.relics = ["ancient_compass"]
        engine._init_battle_node(run)
        self.assertEqual(enemy_test.actions, 1)
        run.node_type = "battle"
        player.stage = 20
        sm.stats.unlocked_gatekey = False
        engine.card_player.handle_battle_win(run)
        self.assertEqual(run.node_type, "victory")
        run.node_type = "battle"
        player.stage = 20
        sm.stats.unlocked_gatekey = True
        engine.card_player.handle_battle_win(run)
        self.assertEqual(run.node_type, "reward")
        player.hand = ["void_beacon"]
        player.actions = 2
        player.bonus_actions = 1
        player.amulets = {}
        enemy_test2 = EnemyState("测试敌人", 10, 10, 0, actions=2, max_actions=2)
        run.enemies = [enemy_test2]
        run.node_type = "battle"
        engine.play_card(run, 1, None)
        self.assertIn("1", player.amulets)
        self.assertEqual(player.amulets["1"].id, "void_beacon")
        engine.end_turn(run)
        self.assertTrue(any(b.id == "vulnerable_force" for b in enemy_test2.buffs))
        run.node_type = "battle"
        player.stage = 25
        engine.card_player.handle_battle_win(run)
        self.assertEqual(run.node_type, "victory")
        self.assertTrue(sm.stats.killed_yog_sothoth)

    def test_non_battle_play_card(self):
        class DummySaveManager:
            def __init__(self):
                self.stats = UserStats()
                self.saved_run = None
            def save_save(self, user_id, run):
                self.saved_run = run
            def delete_save(self, user_id):
                pass
            def load_stats(self, user_id):
                return self.stats
            def save_stats(self, user_id, stats):
                self.stats = stats
                return True
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        router = CLIRouter(sm, engine)
        player = PlayerState(
            hp=45,
            max_hp=45,
            shield=0,
            gold=20,
            stage=1,
            deck=["arcane_torrent"],
            hand=["arcane_torrent"]
        )
        run = GameRun(
            user_id="test_non_battle_user",
            node_type="covenant",
            player=player,
            enemies=[]
        )
        res, should_terminate = router._execute_sub_action("test_non_battle_user", run, ["使用", "1"])
        self.assertEqual(res, "❌ 只有在战斗中才能使用卡牌。")
        self.assertFalse(should_terminate)
        self.assertEqual(run.node_type, "covenant")

    def test_arcane_barrier_and_buffer_buff(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=30,
            max_hp=30,
            shield=0,
            gold=100,
            stage=1,
            deck=["arcane_barrier", "arcane_barrier+"],
            hand=["arcane_barrier", "arcane_barrier+"],
            actions=3,
            bonus_actions=3
        )
        enemy = EnemyState("测试敌人", 50, 50, 0)
        run = GameRun(
            user_id="test_buffer_user",
            node_type="battle",
            player=player,
            enemies=[enemy]
        )
        
        run.node_data["last_x_cost_ba"] = 1
        card_barrier = ALL_CARDS["arcane_barrier"]
        card_barrier.execute(run, None, engine)
        self.assertEqual(player.shield, 6)
        self.assertFalse(any(b.id == "buffer" for b in player.buffs))
        
        player.shield = 0
        run.node_data["last_x_cost_ba"] = 2
        card_barrier.execute(run, None, engine)
        self.assertEqual(player.shield, 12)
        self.assertTrue(any(b.id == "buffer" for b in player.buffs))
        buffer_buff = next(b for b in player.buffs if b.id == "buffer")
        self.assertEqual(buffer_buff.stacks, 1)
        
        engine.combat_resolver.damage_target(run, "p0", 15, damage_type="bludgeoning")
        self.assertEqual(player.hp, 30)
        self.assertEqual(player.shield, 12)
        self.assertFalse(any(b.id == "buffer" for b in player.buffs))
        
        player.shield = 0
        run.node_data["last_x_cost_ba"] = 1
        card_barrier_plus = ALL_CARDS["arcane_barrier+"]
        card_barrier_plus.execute(run, None, engine)
        self.assertEqual(player.shield, 9)
        self.assertFalse(any(b.id == "buffer" for b in player.buffs))
        
        player.shield = 0
        run.node_data["last_x_cost_ba"] = 2
        card_barrier_plus.execute(run, None, engine)
        self.assertEqual(player.shield, 18)
        self.assertTrue(any(b.id == "buffer" for b in player.buffs))

    def test_arcane_torrent_aoe(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=30,
            max_hp=30,
            shield=0,
            gold=100,
            stage=1,
            deck=["arcane_torrent", "arcane_torrent+"],
            hand=["arcane_torrent", "arcane_torrent+"],
            actions=3,
            bonus_actions=3
        )
        enemies = [
            EnemyState("测试敌人A", 50, 50, 0),
            EnemyState("测试敌人B", 50, 50, 0)
        ]
        run = GameRun(
            user_id="test_torrent_user",
            node_type="battle",
            player=player,
            enemies=enemies
        )
        
        run.node_data["last_x_cost_a"] = 1
        card_torrent = ALL_CARDS["arcane_torrent"]
        card_torrent.execute(run, None, engine)
        self.assertEqual(enemies[0].hp, 44)
        self.assertEqual(enemies[1].hp, 44)
        
        enemies[0].hp = 50
        enemies[1].hp = 50
        run.node_data["last_x_cost_a"] = 3
        card_torrent.execute(run, None, engine)
        self.assertEqual(enemies[0].hp, 14)
        self.assertEqual(enemies[1].hp, 14)

    def test_new_ancient_features(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=30,
            max_hp=30,
            shield=0,
            gold=100,
            stage=1,
            deck=["break_limits", "abyss_collapse", "demon_contract", "frost_nova", "glacier_fortress"],
            hand=["break_limits", "abyss_collapse", "demon_contract", "frost_nova", "glacier_fortress"],
            actions=5,
            bonus_actions=5,
            buffs=[]
        )
        enemies = [
            EnemyState("测试敌人A", 50, 50, 0)
        ]
        run = GameRun(
            user_id="test_new_features_user",
            node_type="battle",
            player=player,
            enemies=enemies
        )
        engine._add_buff_to(player, "strength", "力量", "造成的伤害增加", 3)
        engine._add_buff_to(player, "stun", "眩晕", "无法行动", 1)
        card_limits = ALL_CARDS["break_limits"]
        card_limits.execute(run, None, engine)
        strength_buff = next(b for b in player.buffs if b.id == "strength")
        stun_buff = next(b for b in player.buffs if b.id == "stun")
        self.assertEqual(strength_buff.stacks, 6)
        self.assertEqual(stun_buff.stacks, 1)
        card_collapse = ALL_CARDS["abyss_collapse"]
        enemies[0].hp = 50
        card_collapse.execute(run, None, engine)
        self.assertEqual(enemies[0].hp, 26)
        engine._add_buff_to(enemies[0], "stun", "眩晕", "无法行动", 1)
        enemies[0].hp = 50
        card_collapse.execute(run, None, engine)
        self.assertEqual(enemies[0].hp, 2)

    def test_more_ancient_relics_and_cards(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def load_stats(self, user_id):
                class DummyStats:
                    def __init__(self):
                        self.unlocked_gatekey = True
                        self.killed_icerainboww = True
                        self.killed_yog_sothoth = False
                return DummyStats()
            def save_stats(self, user_id, stats):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=40,
            max_hp=40,
            shield=20,
            gold=100,
            stage=1,
            deck=[],
            hand=["abyss_altar", "abyss_erosion", "glacier_tempest", "abyss_altar+"],
            actions=5,
            bonus_actions=5,
            buffs=[],
            relics=["abyss_contract", "glacier_core"]
        )
        enemies = [
            EnemyState("测试敌人A", 600, 600, 0)
        ]
        run = GameRun(
            user_id="test_more_features_user",
            node_type="battle",
            player=player,
            enemies=enemies
        )
        engine.card_player.end_turn(run)
        self.assertEqual(enemies[0].hp, 595)
        self.assertEqual(player.shield, 10)
        player.draw_pile = ["mass_healing_word"]
        initial_hand_len = len(player.hand)
        engine._damage_target(run, "p0", 2, damage_type="true", source="test")
        self.assertEqual(len(player.hand), initial_hand_len + 1)
        self.assertIn("mass_healing_word", player.hand)
        card_erosion = ALL_CARDS["abyss_erosion"]
        card_erosion.execute(run, "e1", engine)
        self.assertEqual(enemies[0].hp, 585)
        weakness_buff = next(b for b in enemies[0].buffs if b.id == "void_weakness")
        self.assertEqual(weakness_buff.stacks, 3)
        player.minions["1"] = MinionState("mercenary", "雇佣兵", 5, 5, 4, 1, 0)
        card_tempest = ALL_CARDS["glacier_tempest"]
        card_tempest.execute(run, None, engine)
        self.assertEqual(enemies[0].hp, 573)
        self.assertEqual(player.shield, 16)
        card_altar_up = ALL_CARDS["abyss_altar+"]
        card_altar_up.execute(run, None, engine)
        self.assertIn("2", player.amulets)
        self.assertEqual(player.amulets["2"].id, "abyss_altar_awaken")
        card_altar = ALL_CARDS["abyss_altar"]
        card_altar.execute(run, None, engine)
        self.assertIn("3", player.amulets)
        self.assertEqual(player.amulets["3"].id, "abyss_altar")
        engine.card_player.end_turn(run)
        self.assertEqual(player.amulets["3"].id, "abyss_altar_awaken")
        engine.card_player.end_turn(run)
        self.assertEqual(player.amulets["3"].id, "abyss_altar_converge")
        engine.card_player.end_turn(run)
        self.assertEqual(player.amulets["3"].id, "abyss_altar_burst")
        engine.card_player.end_turn(run)
        self.assertEqual(player.amulets["3"].id, "abyss_altar_end")
        prev_player_hp = player.hp
        engine.card_player.end_turn(run)
        self.assertNotIn("3", player.amulets)
        self.assertEqual(player.hp, prev_player_hp - 10)

    def test_amulet_exhaust_and_graveyard(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def load_stats(self, user_id):
                class DummyStats:
                    def __init__(self):
                        self.unlocked_gatekey = False
                        self.killed_icerainboww = False
                        self.killed_yog_sothoth = False
                return DummyStats()
            def save_stats(self, user_id, stats):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=40,
            max_hp=40,
            shield=20,
            gold=100,
            stage=1,
            deck=["lucky_coin", "thorns_necklace"],
            hand=["lucky_coin", "thorns_necklace"],
            actions=5,
            bonus_actions=5,
            buffs=[],
            relics=[]
        )
        enemies = [
            EnemyState("测试敌人A", 50, 50, 0)
        ]
        run = GameRun(
            user_id="test_amulet_user",
            node_type="battle",
            player=player,
            enemies=enemies
        )
        engine.card_player.play_card(run, 1)
        self.assertIn("1", player.amulets)
        self.assertEqual(player.amulets["1"].id, "lucky_coin")
        self.assertNotIn("lucky_coin", player.discard_pile)
        self.assertNotIn("lucky_coin", player.exhaust_pile)
        engine.card_player.end_turn(run)
        self.assertEqual(player.amulets["1"].countdown, 2)
        engine.card_player.end_turn(run)
        self.assertEqual(player.amulets["1"].countdown, 1)
        prev_gold = player.gold
        engine.card_player.end_turn(run)
        self.assertNotIn("1", player.amulets)
        self.assertIn("lucky_coin", player.minion_graveyard)
        self.assertNotIn("lucky_coin", player.discard_pile)
        self.assertEqual(player.gold, prev_gold + 13)
        res = engine.combat_resolver.recall_dead_minion(run, 999)
        self.assertIn("没有符合条件的随从", res)
        player.hand = ["master_key"]
        player.actions = 2
        player.bonus_actions = 1
        card_thorns = ALL_CARDS["thorns_necklace"]
        card_thorns.execute(run, None, engine)
        engine.card_player._handle_card_post_play(run, card_thorns, "thorns_necklace")
        self.assertIn("1", player.amulets)
        self.assertEqual(player.amulets["1"].id, "thorns_necklace")
        self.assertNotIn("thorns_necklace", player.discard_pile)
        engine.card_player.play_card(run, 1)
        self.assertNotIn("1", player.amulets)
        self.assertIn("thorns_necklace", player.minion_graveyard)

    def test_admin_jump_command(self):
        plugin = MyPlugin(DummyContext())
        user_id = "test_jump_user"
        plugin.save_manager.delete_save(user_id)

        async def go():
            await run_command(plugin, ".rogue 开启", sender_id=user_id)
            await run_command(plugin, ".rogue 选择 1", sender_id=user_id)
            run = plugin.save_manager.load_save(user_id)
            self.assertIsNotNone(run)

            event_help = DummyEvent("/rogueadmin", sender_id=user_id)
            generator = plugin.rogueadmin(event_help)
            async for _ in generator:
                pass
            self.assertIn("立即跳到某一层", "\n".join(event_help.results))

            event_jump_11 = DummyEvent(f"/rogueadmin jump {user_id} 11", sender_id=user_id)
            generator = plugin.rogueadmin(event_jump_11)
            async for _ in generator:
                pass
            res_text = "\n".join(event_jump_11.results)
            self.assertIn("成功跳转到第 11 层", res_text)
            self.assertIn("赐福", res_text)

            run = plugin.save_manager.load_save(user_id)
            self.assertEqual(run.player.stage, 11)
            self.assertEqual(run.node_type, "ancient")

            event_jump_20 = DummyEvent(f"/rogueadmin jump {user_id} 20", sender_id=user_id)
            generator = plugin.rogueadmin(event_jump_20)
            async for _ in generator:
                pass
            res_text = "\n".join(event_jump_20.results)
            self.assertIn("成功跳转到第 20 层", res_text)
            self.assertIn("战斗阶段", res_text)

            run = plugin.save_manager.load_save(user_id)
            self.assertEqual(run.player.stage, 20)
            self.assertEqual(run.node_type, "battle")

            event_jump_15 = DummyEvent(f"/rogueadmin jump {user_id} 15", sender_id=user_id)
            generator = plugin.rogueadmin(event_jump_15)
            async for _ in generator:
                pass
            res_text = "\n".join(event_jump_15.results)
            self.assertIn("成功跳转到第 15 层", res_text)
            self.assertTrue(any(x in res_text for x in ["路线选择", "遭遇战", "神秘事件", "奇妙商店", "篝火营地", "古老宝箱"]))

            run = plugin.save_manager.load_save(user_id)
            self.assertEqual(run.player.stage, 15)
            self.assertEqual(run.node_type, "map_select")

            plugin.save_manager.delete_save(user_id)

        asyncio.run(go())

    def test_warrior_class_and_features(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
            def load_stats(self, user_id):
                class DummyStats:
                    def __init__(self):
                        self.selected_class = "战士"
                        self.selected_subclass = ""
                return DummyStats()
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        
        player = PlayerState(
            hp=80,
            max_hp=80,
            shield=0,
            gold=20,
            stage=1,
            deck=["warrior_strike", "warrior_defend", "power_through", "barricade", "heavy_blade", "bludgeon"],
            hand=["warrior_strike", "warrior_defend", "power_through", "barricade", "heavy_blade", "bludgeon"],
            actions=2,
            bonus_actions=1
        )
        enemies = [EnemyState("测试敌人A", 100, 100, 0)]
        run = GameRun(
            user_id="test_warrior_user",
            node_type="battle",
            player=player,
            enemies=enemies
        )
        run.node_data["action_surge_uses"] = 2
        
        card_strike = ALL_CARDS["warrior_strike"]
        card_strike.execute(run, "e1", engine)
        self.assertEqual(enemies[0].hp, 94)
        
        card_defend = ALL_CARDS["warrior_defend"]
        card_defend.execute(run, None, engine)
        self.assertEqual(player.shield, 5)
        
        card_power = ALL_CARDS["power_through"]
        card_power.execute(run, None, engine)
        self.assertEqual(player.shield, 20)
        self.assertEqual(player.hand.count("curse_wound"), 2)
        
        card_wound = ALL_CARDS["curse_wound"]
        self.assertTrue(getattr(card_wound, "unplayable", False))
        
        card_barricade = ALL_CARDS["barricade"]
        card_barricade.execute(run, None, engine)
        self.assertTrue(any(b.id == "barricade" for b in player.buffs))
        
        prev_shield = player.shield
        engine.card_player.end_turn(run)
        self.assertEqual(player.shield, prev_shield)
        
        engine._add_buff_to(player, "strength", "力量", "伤害加成", 3)
        card_heavy = ALL_CARDS["heavy_blade"]
        enemies[0].hp = 100
        engine.combat_resolver.card_player = engine.card_player
        
        damage = engine.combat_resolver.get_modified_spell_damage(run, card_heavy, 14)
        self.assertEqual(damage, 14 + 3 * 3)
        
        card_heavy_up = ALL_CARDS["heavy_blade+"]
        damage_up = engine.combat_resolver.get_modified_spell_damage(run, card_heavy_up, 18)
        self.assertEqual(damage_up, 18 + 3 * 5)
        
        router = CLIRouter(sm, engine)
        run.node_data["action_surge_uses"] = 2
        
        class DummySaveManagerWithSave:
            def __init__(self, run):
                self.run = run
                class DummyStats:
                    def __init__(self):
                        self.selected_class = "战士"
                        self.selected_subclass = ""
                self.stats = DummyStats()
            def load_save(self, user_id):
                return self.run
            def save_save(self, user_id, run):
                self.run = run
            def delete_save(self, user_id):
                pass
            def load_stats(self, user_id):
                return self.stats
            def save_stats(self, user_id, stats):
                pass
        
        router.save_manager = DummySaveManagerWithSave(run)
        generator = router.handle_command("test_warrior_user", ["技能", "as"])
        res_list = list(generator)
        res_text = "\n".join(res_list)
        self.assertIn("额外", res_text)
        self.assertEqual(run.player.actions, 4)
        self.assertEqual(run.node_data["action_surge_uses"], 1)

if __name__ == "__main__":
    unittest.main()

