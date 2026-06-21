import os
import unittest
import asyncio
from scratch.rogue_tests.base import *

class TestRogueSystem(unittest.TestCase):
    def test_duel_mode_and_exclusivity(self):
        plugin = MyPlugin(DummyContext())
        plugin.save_manager.delete_save("test_user_excl")
        stats_path = plugin.save_manager.get_stats_path("test_user_excl")
        if os.path.exists(stats_path):
            os.remove(stats_path)
            
        async def go():
            event_help = DummyEvent(".duel 帮助", sender_id="test_user_excl")
            async for res in plugin.duel_cmd(event_help):
                event_help.results.append(res)
            self.assertTrue(any("对决模式" in r for r in event_help.results))
            
            event_shortcut_duel = DummyEvent(".duel 帮助", sender_id="test_user_excl")
            await plugin.shortcut_rogue(event_shortcut_duel)
            self.assertTrue(event_shortcut_duel.stopped)
            self.assertTrue(any("对决模式" in r for r in event_shortcut_duel.results))
            
            stats = plugin.save_manager.load_stats("test_user_excl")
            stats.rogue_mode = True
            plugin.save_manager.save_stats("test_user_excl", stats)
            
            event_toggle_duel = DummyEvent(".duel 模式", sender_id="test_user_excl")
            async for res in plugin.duel_cmd(event_toggle_duel):
                event_toggle_duel.results.append(res)
            self.assertTrue(any("免前缀对决模式已开启" in r for r in event_toggle_duel.results))
            
            stats = plugin.save_manager.load_stats("test_user_excl")
            self.assertTrue(stats.duel_mode)
            self.assertFalse(stats.rogue_mode)
            
            event_duel_help = DummyEvent("帮助", sender_id="test_user_excl")
            await plugin.shortcut_rogue(event_duel_help)
            self.assertTrue(event_duel_help.stopped)
            
            event_rogue_start = DummyEvent("开启", sender_id="test_user_excl")
            await plugin.shortcut_rogue(event_rogue_start)
            self.assertFalse(event_rogue_start.stopped)
            
            event_toggle_rogue = DummyEvent(".rogue 模式", sender_id="test_user_excl")
            await plugin.shortcut_rogue(event_toggle_rogue)
            
            stats = plugin.save_manager.load_stats("test_user_excl")
            self.assertTrue(stats.rogue_mode)
            self.assertFalse(stats.duel_mode)
            
            event_rogue_duel = DummyEvent(".rogue 对决 帮助", sender_id="test_user_excl")
            await plugin.shortcut_rogue(event_rogue_duel)
            self.assertTrue(any("未知子命令" in r for r in event_rogue_duel.results))
            
        asyncio.run(go())

        sm = plugin.save_manager
        sm.delete_save("test_user_excl")
        sm.delete_duel_save("test_user_excl")
        
        run_rogue = GameRun(
            user_id="test_user_excl",
            node_type="battle",
            player=PlayerState(hp=50, max_hp=50, shield=0, gold=10, stage=1),
            enemies=[]
        )
        sm.save_save("test_user_excl", run_rogue)
        
        sm.bind_duel_game("test_user_excl", "another_user_excl", "game_excl_123")
        run_duel = GameRun(
            user_id="test_user_excl",
            node_type="duel_battle",
            player=PlayerState(hp=200, max_hp=200, shield=0, gold=0, stage=1),
            enemies=[],
            player2=PlayerState(hp=200, max_hp=200, shield=0, gold=0, stage=1),
            node_data={"player1_id": "test_user_excl", "player2_id": "another_user_excl"}
        )
        sm.save_duel_save("test_user_excl", run_duel)
        
        loaded_rogue = sm.load_save("test_user_excl")
        self.assertIsNotNone(loaded_rogue)
        self.assertEqual(loaded_rogue.node_type, "battle")
        self.assertEqual(loaded_rogue.player.hp, 50)
        
        loaded_duel = sm.load_duel_save("test_user_excl")
        self.assertIsNotNone(loaded_duel)
        self.assertEqual(loaded_duel.node_type, "duel_battle")
        self.assertEqual(loaded_duel.player.hp, 200)
        
        loaded_rogue.player.hp = 35
        sm.save_save("test_user_excl", loaded_rogue)
        
        loaded_duel_check = sm.load_duel_save("test_user_excl")
        self.assertEqual(loaded_duel_check.player.hp, 200)
        
        loaded_duel.player.hp = 180
        sm.save_duel_save("test_user_excl", loaded_duel)
        
        loaded_rogue_check = sm.load_save("test_user_excl")
        self.assertEqual(loaded_rogue_check.player.hp, 35)
        
        sm.delete_save("test_user_excl")
        self.assertIsNone(sm.load_save("test_user_excl"))
        
        loaded_duel_after_rogue_del = sm.load_duel_save("test_user_excl")
        self.assertIsNotNone(loaded_duel_after_rogue_del)
        self.assertEqual(loaded_duel_after_rogue_del.player.hp, 180)
        
        sm.delete_duel_save("test_user_excl")
        self.assertIsNone(sm.load_duel_save("test_user_excl"))

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

        run.node_data["action_surge_uses"] = 2
        run.player.actions = 2
        generator_sk = router.handle_command("test_warrior_user", ["sk"])
        res_text_sk = "\n".join(list(generator_sk))
        self.assertIn("额外", res_text_sk)
        self.assertEqual(run.player.actions, 4)
        self.assertEqual(run.node_data["action_surge_uses"], 1)

        run.node_data["action_surge_uses"] = 2
        run.player.actions = 2
        generator_k = router.handle_command("test_warrior_user", ["k"])
        res_text_k = "\n".join(list(generator_k))
        self.assertIn("额外", res_text_k)
        self.assertEqual(run.player.actions, 4)
        self.assertEqual(run.node_data["action_surge_uses"], 1)

    def test_warrior_ward_and_rally(self):
        from game.core.battle_engine import BattleEngine
        from game.models.state import GameRun, PlayerState, EnemyState, MinionState, Card
        from game.entities.enemies.base import EnemyTemplate
        class DummySaveManager:
            def load_admin_config(self):
                return {}
            def load_stats(self, uid):
                class DummyStats:
                    def __init__(self):
                        self.selected_class = "战士"
                        self.selected_subclass = ""
                return DummyStats()
            def save_save(self, uid, run):
                pass
            def save_stats(self, uid, stats):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=80,
            max_hp=80,
            shield=0,
            gold=100,
            stage=1,
            deck=["officer_recruit_vanguard"],
            hand=["officer_recruit_vanguard"],
            actions=2,
            bonus_actions=1
        )
        run = GameRun("test_user_w", "battle", player=player, enemies=[EnemyState("测试史莱姆", 20, 20, 0, 1, 0, 1, 0)])
        p = run.player
        p.selected_class = "战士"
        engine._init_battle_node(run)
        self.assertIn("rally_count", run.node_data)
        self.assertEqual(run.node_data["rally_count"], 0)
        engine._summon_minion(run, "shield_guard", "盾卫", 6, 2, 0)
        self.assertEqual(run.node_data["rally_count"], 1)
        self.assertIn("1", p.minions)
        m = p.minions["1"]
        self.assertTrue(any(b.id == "ward" for b in m.buffs))
        enemy_template = EnemyTemplate("test_slime")
        run.enemies[0].hp = 20
        enemy_template._perform_attack(run, engine, run.enemies[0], 5, [])
        self.assertEqual(p.minions["1"].hp, 1)
        p.hand = ["officer_recruit_vanguard"]
        run.node_data["free_minion_cards"] = ["officer_recruit_vanguard"]
        engine.play_card(run, 1, "e1")
        self.assertEqual(run.player.actions, 2)

    def test_deck_contains_all_class_cards(self):
        player = PlayerState(
            hp=80,
            max_hp=80,
            shield=0,
            gold=20,
            stage=1,
            deck=["warrior_strike", "doomsday_judgment", "time_warp", "arcane_spark"],
            draw_pile=[],
            discard_pile=[],
            hand=[],
            actions=1,
            bonus_actions=1,
            selected_class="战士"
        )
        run = GameRun(
            user_id="test_user_class_cards",
            node_type="map_select",
            player=player,
            enemies=[],
            node_data={}
        )
        from game.renderer import GameRenderer
        output = GameRenderer.render_deck(run)
        self.assertIn("奥术星火", output)
        self.assertIn("末日审判", output)
        self.assertIn("时光倒流", output)
        self.assertIn("打击", output)

    def test_rogue_query_isolation(self):
        res = render_query_info("ancient_eye")
        self.assertNotIn("未找到", res)
        self.assertIn("🎒 遗物", res)
        
        res_duel = render_query_info("duel_warrior_strike")
        self.assertIn("未找到", res_duel)
