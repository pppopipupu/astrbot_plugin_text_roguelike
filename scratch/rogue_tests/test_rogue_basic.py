import os
import unittest
import asyncio
from scratch.rogue_tests.base import *

class TestRogueBasic(unittest.TestCase):
    def test_basic_flow(self):
        plugin = MyPlugin(DummyContext())
        save_manager = SaveManager()
        save_manager.delete_save("test_user")
        stats_path = save_manager.get_stats_path("test_user")
        if os.path.exists(stats_path):
            try:
                os.remove(stats_path)
            except:
                pass
        
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

        res_conflict_wiz = list(router.handle_command("test_user", ["c", "wizard"]))
        self.assertIn("使用 /rogue class", res_conflict_wiz[0])
        self.assertIn("选择命令 c 仅用于局内选项选择", res_conflict_wiz[0])

        res_conflict_num = list(router.handle_command("test_user", ["c", "1"]))
        self.assertIn("使用 /rogue class", res_conflict_num[0])

        res_normal_c = list(router.handle_command("test_user", ["c"]))
        self.assertEqual("❌ 你当前没有正在进行的游戏。", res_normal_c[0])

        class DummySaveManagerWithSave:
            def __init__(self):
                self.stats = UserStats()
                self.stats.unlocked_subclasses = ["时序法师", "塑能法师"]
            def load_stats(self, user_id):
                return self.stats
            def save_stats(self, user_id, stats):
                self.stats = stats
                return True
            def load_save(self, user_id):
                player = PlayerState(hp=30, max_hp=30, shield=0, gold=100, stage=2, deck=[], hand=[], draw_pile=[], discard_pile=[], exhaust_pile=[], graveyard=[])
                return GameRun(user_id=user_id, node_type="event", player=player, enemies=[], node_data={"event_id": "test_event"})
        mgr_with_save = DummySaveManagerWithSave()
        router_with_save = CLIRouter(mgr_with_save, None)
        res_in_game = list(router_with_save.handle_command("test_user", ["c", "wizard"]))
        self.assertIn("使用 /rogue class", res_in_game[0])

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
            
            event_town = DummyEvent("主城", sender_id="test_user_rogue")
            await plugin.shortcut_rogue(event_town)
            self.assertTrue(event_town.stopped)
            self.assertIn("先古主城", "\n".join(event_town.results))
            
            event_town_exit = DummyEvent("退出", sender_id="test_user_rogue")
            await plugin.shortcut_rogue(event_town_exit)
            self.assertTrue(event_town_exit.stopped)
            
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

    def test_new_english_aliases(self):
        class DummySaveManager:
            def __init__(self):
                self.stats = UserStats()
                self.stats.unlocked_subclasses = ["时序法师", "塑能法师", "秘钥学者"]
                self.saved_run = None
            def load_stats(self, user_id):
                return self.stats
            def save_stats(self, user_id, stats):
                self.stats = stats
                return True
            def load_save(self, user_id):
                return self.saved_run
            def save_save(self, user_id, run):
                self.saved_run = run
            def settle_game_and_delete(self, user_id, run, is_victory=False):
                self.saved_run = None
                return "游戏已结算。"
        
        mgr = DummySaveManager()
        engine = GameEngine(mgr)
        router = CLIRouter(mgr, engine)
        
        player = PlayerState(hp=30, max_hp=30, shield=0, gold=100, stage=2, deck=[], hand=[], draw_pile=[], discard_pile=[], exhaust_pile=[], graveyard=[])
        mgr.saved_run = GameRun(user_id="test_user", node_type="event", player=player, enemies=[], node_data={"event_id": "test_event"})
        res = list(router.handle_command("test_user", ["start", "confirm"]))
        self.assertIn("已重新开始新的一局游戏", res[0])
        
        mgr.saved_run = None
        list(router.handle_command("test_user", ["class", "choose", "chronomancer"]))
        self.assertEqual(mgr.stats.selected_subclass, "时序法师")
        list(router.handle_command("test_user", ["class", "select", "evoker"]))
        self.assertEqual(mgr.stats.selected_subclass, "塑能法师")
        list(router.handle_command("test_user", ["class", "select", "arcanist"]))
        self.assertEqual(mgr.stats.selected_subclass, "秘钥学者")
        
        mgr.stats.gp = 99999
        mgr.stats.unlocked_subclasses = []
        mgr.stats.town_pos = "shop"
        list(router.handle_command("test_user", ["town"]))
        list(router.handle_command("test_user", ["talk", "神秘店主"]))
        list(router.handle_command("test_user", ["2"]))
        list(router.handle_command("test_user", ["1"]))
        self.assertIn("时序法师", mgr.stats.unlocked_subclasses)
        list(router.handle_command("test_user", ["2"]))
        self.assertIn("塑能法师", mgr.stats.unlocked_subclasses)
        list(router.handle_command("test_user", ["3"]))
        self.assertIn("秘钥学者", mgr.stats.unlocked_subclasses)
        list(router.handle_command("test_user", ["4"]))
        self.assertTrue(mgr.stats.unlocked_gatekey)
        
        player = PlayerState(
            hp=30, max_hp=30, shield=0, gold=100, stage=2, deck=[], hand=[], draw_pile=[], discard_pile=[], exhaust_pile=[], graveyard=[],
            minions={"1": MinionState("mercenary", "雇佣兵", 10, 10, 4, 2, 0)}
        )
        class MockEngine:
            def __init__(self):
                self.attack_called = False
                self.skill_called = False
            def minion_attack(self, run, g, opp):
                self.attack_called = True
                return "攻击成功"
            def minion_skill(self, run, g, idx, target):
                self.skill_called = True
                return "技能成功"
            def is_battle_won(self, run):
                return False
        mock_engine = MockEngine()
        mgr.saved_run = GameRun(user_id="test_user", node_type="battle", player=player, enemies=[EnemyState("e1", 10, 10, 0)])
        router_minion = CLIRouter(mgr, mock_engine)
        res, term = router_minion._execute_sub_action("test_user", mgr.saved_run, ["m", "1", "attack", "e1"])
        self.assertTrue(mock_engine.attack_called)
        res, term = router_minion._execute_sub_action("test_user", mgr.saved_run, ["m", "1", "skill", "e1"])
        self.assertTrue(mock_engine.skill_called)

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

    def test_admin_icerainboww_command(self):
        plugin = MyPlugin(DummyContext())
        user_id = "test_icerainboww_admin_user"
        
        async def go():
            event_check = DummyEvent("/rogueadmin icerainboww", sender_id=user_id)
            generator = plugin.rogueadmin(event_check)
            async for _ in generator:
                pass
            res_text = "\n".join(event_check.results)
            self.assertIn("配置状态", res_text)

            event_off = DummyEvent("/rogueadmin icerainboww off", sender_id=user_id)
            generator = plugin.rogueadmin(event_off)
            async for _ in generator:
                pass
            self.assertIn("成功【关闭】", "\n".join(event_off.results))

            cfg = plugin.save_manager.load_admin_config()
            self.assertFalse(cfg.get("icerainboww_enabled", True))

            event_on = DummyEvent("/rogueadmin icerainboww on", sender_id=user_id)
            generator = plugin.rogueadmin(event_on)
            async for _ in generator:
                pass
            self.assertIn("成功【开启】", "\n".join(event_on.results))

            cfg = plugin.save_manager.load_admin_config()
            self.assertTrue(cfg.get("icerainboww_enabled", True))

        asyncio.run(go())

    def test_admin_add_card_command(self):
        plugin = MyPlugin(DummyContext())
        user_id = "test_add_card_admin_user"
        plugin.save_manager.delete_save(user_id)

        async def go():
            await run_command(plugin, ".rogue 开启", sender_id=user_id)
            await run_command(plugin, ".rogue 选择 1", sender_id=user_id)
            
            event_help = DummyEvent("/rogueadmin", sender_id=user_id)
            generator = plugin.rogueadmin(event_help)
            async for _ in generator:
                pass
            self.assertIn("add_card", "\n".join(event_help.results))

            event_add_1 = DummyEvent(f"/rogueadmin add_card 火球术", sender_id=user_id)
            generator = plugin.rogueadmin(event_add_1)
            async for _ in generator:
                pass
            res_text = "\n".join(event_add_1.results)
            self.assertIn("成功将卡牌", res_text)
            self.assertIn("火球术", res_text)

            run = plugin.save_manager.load_save(user_id)
            self.assertIn("fireball", run.player.deck)

            event_add_2 = DummyEvent(f"/rogueadmin add_card user_other warrior_strike", sender_id=user_id)
            event_add_2_alt = DummyEvent(f"/rogueadmin add_card warrior_strike+ user_other", sender_id=user_id)
            
            plugin.save_manager.delete_save("user_other")
            await run_command(plugin, ".rogue 开启", sender_id="user_other")
            await run_command(plugin, ".rogue 选择 1", sender_id="user_other")

            generator = plugin.rogueadmin(event_add_2)
            async for _ in generator:
                pass
            res_text2 = "\n".join(event_add_2.results)
            self.assertIn("成功将卡牌", res_text2)

            run_other = plugin.save_manager.load_save("user_other")
            self.assertIn("warrior_strike", run_other.player.deck)

            generator = plugin.rogueadmin(event_add_2_alt)
            async for _ in generator:
                pass
            res_text_alt = "\n".join(event_add_2_alt.results)
            self.assertIn("成功将卡牌", res_text_alt)

            run_other = plugin.save_manager.load_save("user_other")
            self.assertIn("warrior_strike+", run_other.player.deck)

            run = plugin.save_manager.load_save(user_id)
            run.node_type = "battle"
            plugin.save_manager.save_save(user_id, run)

            event_add_battle = DummyEvent(f"/rogueadmin add_card fireball+ {user_id}", sender_id=user_id)
            generator = plugin.rogueadmin(event_add_battle)
            async for _ in generator:
                pass
            res_battle = "\n".join(event_add_battle.results)
            self.assertIn("直接加入手牌", res_battle)

            run = plugin.save_manager.load_save(user_id)
            self.assertIn("fireball+", run.player.deck)
            self.assertIn("fireball+", run.player.hand)

            plugin.save_manager.delete_save(user_id)
            plugin.save_manager.delete_save("user_other")

        asyncio.run(go())
