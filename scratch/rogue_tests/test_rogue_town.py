import os
import unittest
import asyncio
import sys
from scratch.rogue_tests.base import *

class TestRogueTown(unittest.TestCase):
    def test_town_full_loop(self):
        plugin = MyPlugin(DummyContext())
        save_manager = SaveManager()
        stats_path = save_manager.get_stats_path("test_user")
        if os.path.exists(stats_path):
            try:
                os.remove(stats_path)
            except:
                pass
        save_manager.delete_save("test_user")

        async def run_test():
            res = await run_command(plugin, ".rogue 主城")
            self.assertIn("中心广场", res)
            self.assertIn("向导长老", res)

            res = await run_command(plugin, ".rogue talk Guide_Elder")
            self.assertIn("与向导长老闲聊", res)

            res = await run_command(plugin, ".rogue 2")
            self.assertIn("游览商业 A 区", res)
            stats = save_manager.load_stats("test_user")
            self.assertEqual(stats.town_flags.get("quest_town_tour_state"), "started")
            
            res = await run_command(plugin, ".rogue exit")
            self.assertIn("你结束了与【向导长老】的交谈", res)

            moves = [
                ("right", "fountain"),
                ("right", "shop"),
                ("up", "tavern"),
                ("right", "vip_room"),
                ("left", "tavern"),
                ("down", "shop"),
                ("left", "fountain"),
                ("left", "square"),
                ("down", "market"),
                ("left", "blacksmith"),
                ("right", "market"),
                ("up", "square"),
                ("left", "alley"),
                ("left", "west_gate"),
                ("up", "watch_tower"),
                ("down", "west_gate"),
                ("right", "alley"),
                ("right", "square"),
                ("up", "range"),
                ("down", "square")
            ]

            for direction, expected_room in moves:
                res = await run_command(plugin, f".rogue {direction}")
                stats = save_manager.load_stats("test_user")
                self.assertEqual(stats.town_pos, expected_room)

            stats = save_manager.load_stats("test_user")
            visited = stats.town_flags.get("quest_town_tour_visited", [])
            self.assertEqual(len(visited), 11)

            res = await run_command(plugin, f".rogue up")
            stats = save_manager.load_stats("test_user")
            self.assertEqual(stats.town_pos, "range")
            res = await run_command(plugin, f".rogue up")
            self.assertIn("往这个方向没有路", res)

            res = await run_command(plugin, f".rogue home")
            stats = save_manager.load_stats("test_user")
            self.assertEqual(stats.town_pos, "square")

            await run_command(plugin, ".rogue talk 向导长老")
            res = await run_command(plugin, ".rogue 2")
            self.assertIn("这是奖励你的 2000 GP", res)
            stats = save_manager.load_stats("test_user")
            self.assertEqual(stats.town_flags.get("quest_town_tour_state"), "completed")
            self.assertEqual(stats.gp, 2000)

            await run_command(plugin, ".rogue exit")

            await run_command(plugin, ".rogue right")
            res = await run_command(plugin, ".rogue take lucky_coin")
            self.assertIn("成功拿取", res)
            stats = save_manager.load_stats("test_user")
            self.assertIn("lucky_coin", stats.town_inventory)

            await run_command(plugin, ".rogue right")
            await run_command(plugin, ".rogue up")
            await run_command(plugin, ".rogue right")
            res = await run_command(plugin, ".rogue pick lost_notebook")
            self.assertIn("成功拿取", res)
            
            res = await run_command(plugin, ".rogue use lost_notebook")
            self.assertIn("先古冒险者秘籍", res)

            await run_command(plugin, ".rogue talk Chest")
            res = await run_command(plugin, ".rogue 1")
            print("CHEST RES IS:", repr(res))
            self.assertIn("结束了与", res)

            await run_command(plugin, ".rogue left")
            await run_command(plugin, ".rogue down")
            await run_command(plugin, ".rogue left")
            await run_command(plugin, ".rogue left")
            await run_command(plugin, ".rogue down")
            await run_command(plugin, ".rogue left")
            res = await run_command(plugin, ".rogue pick strange_ore")
            self.assertIn("成功拿取", res)

            await run_command(plugin, ".rogue right")
            await run_command(plugin, ".rogue up")
            await run_command(plugin, ".rogue left")
            res = await run_command(plugin, ".rogue take wine_glass")
            self.assertIn("成功拿取", res)

            await run_command(plugin, ".rogue left")
            await run_command(plugin, ".rogue up")
            res = await run_command(plugin, ".rogue take rusty_key")
            self.assertIn("成功拿取", res)

            await run_command(plugin, ".rogue down")
            await run_command(plugin, ".rogue right")
            await run_command(plugin, ".rogue right")
            await run_command(plugin, ".rogue right")
            await run_command(plugin, ".rogue right")
            await run_command(plugin, ".rogue up")
            await run_command(plugin, ".rogue right")
            await run_command(plugin, ".rogue talk Chest")
            res = await run_command(plugin, ".rogue 1")
            self.assertIn("你使用锈蚀的钥匙开启了宝箱", res)
            stats = save_manager.load_stats("test_user")
            self.assertEqual(stats.guaranteed_card, "discover")
            self.assertNotIn("rusty_key", stats.town_inventory)
            await run_command(plugin, ".rogue exit")

            await run_command(plugin, ".rogue left")
            await run_command(plugin, ".rogue talk Bartender_Jack")
            res = await run_command(plugin, ".rogue 2")
            self.assertIn("答谢金", res)
            stats = save_manager.load_stats("test_user")
            self.assertNotIn("wine_glass", stats.town_inventory)
            await run_command(plugin, ".rogue exit")

            await run_command(plugin, ".rogue down")
            await run_command(plugin, ".rogue left")
            await run_command(plugin, ".rogue left")
            await run_command(plugin, ".rogue down")
            await run_command(plugin, ".rogue left")
            await run_command(plugin, ".rogue talk Blacksmith_Ironclad")
            res = await run_command(plugin, ".rogue 2")
            self.assertIn("铁匠艾恩克拉德满意地接过", res)
            await run_command(plugin, ".rogue exit")

            await run_command(plugin, ".rogue right")
            await run_command(plugin, ".rogue up")
            await run_command(plugin, ".rogue right")
            await run_command(plugin, ".rogue talk Fountain")
            res = await run_command(plugin, ".rogue 1")
            self.assertIn("许愿喷泉", res)
            await run_command(plugin, ".rogue exit")

            await run_command(plugin, ".rogue left")
            await run_command(plugin, ".rogue left")
            await run_command(plugin, ".rogue left")
            await run_command(plugin, ".rogue talk West_Gate")
            res = await run_command(plugin, ".rogue 1")
            res = await run_command(plugin, ".rogue 1")
            res = await run_command(plugin, ".rogue 1")
            self.assertIn("先古支票", res)

            for _ in range(6):
                await run_command(plugin, ".rogue 1")
            res = await run_command(plugin, ".rogue 1")
            self.assertIn("Gate_Guardian", res)
            self.assertIn("Gate_Guardian 破门而出", res)

            stats = save_manager.load_stats("test_user")
            run = save_manager.load_save("test_user")
            self.assertIsNotNone(run)
            self.assertTrue(run.node_data.get("is_town_combat"))

            res = await run_command(plugin, ".rogue 放弃 确认")
            self.assertIn("回到了靶场房间", res)
            run = save_manager.load_save("test_user")
            self.assertIsNone(run)

            res = await run_command(plugin, ".rogue talk NoobSlayer99")
            res = await run_command(plugin, ".rogue 1")
            self.assertTrue(any(x in res for x in ["地精大军克星", "NoobSlayer99"]))
            await run_command(plugin, ".rogue exit")

            res = await run_command(plugin, ".rogue quit")
            self.assertIn("回到主菜单", res)

            save_manager.delete_save("test_user")

        asyncio.run(run_test())

    def test_pppopipupu_awakening(self):
        plugin = MyPlugin(DummyContext())
        save_manager = SaveManager()
        save_manager.delete_save("test_user")
        stats_path = save_manager.get_stats_path("test_user")
        if os.path.exists(stats_path):
            try:
                os.remove(stats_path)
            except:
                pass

        async def run_p_test():
            await run_command(plugin, ".rogue 主城")
            await run_command(plugin, ".rogue home")
            await run_command(plugin, ".rogue up")
            await run_command(plugin, ".rogue talk pppopipupu")
            res = await run_command(plugin, ".rogue 2")
            self.assertIn("pppopipupu", res)

            run = save_manager.load_save("test_user")
            self.assertEqual(len(run.enemies), 1)
            enemy = run.enemies[0]
            self.assertEqual(enemy.name, "pppopipupu")
            self.assertEqual(enemy.hp, 1)

            plugin.engine.battle_engine.combat_resolver.damage_target(
                run, "e1", 10, source="player", damage_type="slashing"
            )

            self.assertEqual(enemy.name, "【觉醒】pppopipupu")
            self.assertEqual(enemy.hp, 9999)

            plugin.engine.battle_engine.enemy_controller.roll_enemy_intent(run)

            res = plugin.engine.battle_engine.enemy_controller.enemy_turn(run)
            self.assertIn("猛击", res)

            save_manager.delete_save("test_user")

        asyncio.run(run_p_test())
