import unittest
from scratch.rogue_tests.base import *

class TestRogueCardMech2(unittest.TestCase):
    def test_unmined_gem_and_replay_logic(self):
        card_normal = ALL_CARDS.get("unmined_gem")
        self.assertIsNotNone(card_normal)
        self.assertEqual(card_normal.cost_a, 0)
        self.assertEqual(card_normal.cost_ba, 0)
        self.assertTrue(card_normal.exhaust)
        self.assertIn("重放 3", card_normal.desc)

        card_plus = ALL_CARDS.get("unmined_gem+")
        self.assertIsNotNone(card_plus)
        self.assertEqual(card_plus.cost_a, 0)
        self.assertEqual(card_plus.cost_ba, 0)
        self.assertTrue(card_plus.exhaust)
        self.assertIn("重放 4", card_plus.desc)

        card_replay = ALL_CARDS.get("fire_bolt:replay:3")
        self.assertIsNotNone(card_replay)
        self.assertEqual(card_replay.replay, 3)
        self.assertEqual(card_replay.name, ALL_CARDS.get("fire_bolt").name)
        self.assertIn("重放 3", card_replay.desc)

        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
            def load_stats(self, user_id):
                class DummyStats:
                    selected_class = "法师"
                    killed_icerainboww = False
                return DummyStats()
            def record_stage_passed(self, user_id):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=50,
            max_hp=50,
            shield=0,
            gold=100,
            stage=1,
            deck=["fire_bolt", "unmined_gem", "unmined_gem+"],
            hand=["fire_bolt", "unmined_gem", "unmined_gem+"],
            actions=10,
            bonus_actions=10
        )
        run = GameRun(
            user_id="test_user_replay",
            node_type="battle",
            player=player,
            enemies=[EnemyState("测试敌人", 100, 100, 0)]
        )

        engine.play_card(run, 2)
        self.assertTrue(any(":replay:3" in cid for cid in player.hand))
        self.assertIn("unmined_gem", player.exhaust_pile)

        engine.play_card(run, 2)
        self.assertTrue(any(":replay:7" in cid or ":replay:16" in cid for cid in player.hand))
        self.assertTrue(any(cid.startswith("unmined_gem+") for cid in player.exhaust_pile))

        self.assertEqual(len(player.hand), 1)
        target_card_id = player.hand[0]
        self.assertTrue(":replay:" in target_card_id)

        hp_before = run.enemies[0].hp
        engine.play_card(run, 1)
        hp_after = run.enemies[0].hp
        self.assertIn(hp_before - hp_after, (24, 51))

        player.hand = ["fire_bolt:replay:3"]
        player.buffs = [BuffState(id="echo_form", name="回响形态", stacks=1, desc="")]
        run.node_data["cards_played_this_turn"] = 0
        hp_before2 = run.enemies[0].hp
        engine.play_card(run, 1)
        hp_after2 = run.enemies[0].hp
        self.assertEqual(hp_before2 - hp_after2, 24)

        player.hand = ["fire_bolt:replay:3", "unmined_gem+"]
        player.actions = 10
        player.bonus_actions = 10
        engine.play_card(run, 2)
        self.assertEqual(player.hand[0], "fire_bolt:replay:7")

        from game.core.map_engine import MapEngine
        map_eng = MapEngine(sm, engine)
        
        found_in_1 = False
        for _ in range(50):
            player1 = PlayerState(hp=50, max_hp=50, shield=0, gold=100, stage=0)
            run1 = GameRun(user_id="test_map_ancient", node_type="map_select", player=player1)
            map_eng.enter_next_stage(run1)
            options1 = run1.node_data.get("options", [])
            if any(opt.get("card") == "unmined_gem" for opt in options1 if "card" in opt):
                found_in_1 = True
                break
        self.assertTrue(found_in_1)

        found_in_11 = False
        for _ in range(50):
            player11 = PlayerState(hp=50, max_hp=50, shield=0, gold=100, stage=12)
            run11 = GameRun(user_id="test_map_ancient", node_type="map_select", player=player11)
            map_eng.enter_next_stage(run11)
            from game.core.cafe_engine import CafeEngine
            CafeEngine(sm, map_eng).leave_cafe(run11)
            options11 = run11.node_data.get("options", [])
            if any(opt.get("card") == "unmined_gem" for opt in options11 if "card" in opt):
                found_in_11 = True
                break
        self.assertTrue(found_in_11)

        player.hand = ["echo_form:replay:3"]
        player.actions = 10
        player.bonus_actions = 10
        player.buffs.clear()
        engine.play_card(run, 1)
        self.assertTrue(any(b.id == "echo_form" and b.name == "回响形态" for b in player.buffs))

        player.hand = ["echo_form+:replay:4"]
        player.actions = 10
        player.bonus_actions = 10
        player.buffs.clear()
        engine.play_card(run, 1)
        self.assertTrue(any(b.id == "echo_form" and b.name == "回响形态" for b in player.buffs))

        player.hand = ["iron_will+:replay:3"]
        player.actions = 10
        player.bonus_actions = 10
        player.buffs.clear()
        engine.play_card(run, 1)
        self.assertTrue(any(b.id == "iron_will+" and b.name == "钢铁意志+" for b in player.buffs))

        player.hand = ["quicken:replay:3"]
        player.actions = 10
        player.bonus_actions = 10
        player.buffs.clear()
        engine.play_card(run, 1)
        self.assertTrue(any(b.id == "quicken" and b.name == "超魔-瞬发" for b in player.buffs))

        player.hand = ["magic_network+:replay:2"]
        player.actions = 10
        player.bonus_actions = 10
        player.buffs.clear()
        engine.play_card(run, 1)
        self.assertTrue(any(b.id == "magic_network+" and b.name == "魔网天成+" for b in player.buffs))

    def test_shockwave_with_echo_form(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=50,
            max_hp=50,
            shield=0,
            gold=100,
            stage=1,
            deck=["shockwave"],
            hand=["shockwave"],
            actions=10,
            bonus_actions=10,
            buffs=[BuffState(id="echo_form", name="回响形态", stacks=1, desc="")]
        )
        run = GameRun(
            user_id="test_user_shockwave",
            node_type="battle",
            player=player,
            enemies=[EnemyState("测试敌人", 100, 100, 0)]
        )
        run.node_data["cards_played_this_turn"] = 0
        res = engine.play_card(run, 1)
        self.assertIn("震荡波", res)
        self.assertTrue(any(b.id == "minor_vulnerable" for b in run.enemies[0].buffs))
        self.assertTrue(any(b.id == "weak" for b in run.enemies[0].buffs))

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

    def test_flow_more_special_cards_and_buffs(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(
            hp=30,
            max_hp=100,
            shield=15,
            actions=10,
            bonus_actions=10,
            deck=["barricade"],
            hand=["barricade"],
            draw_pile=["arcane_spark", "arcane_spark"],
            discard_pile=[],
            exhaust_pile=[],
            graveyard=[],
            amulets={},
            minions={},
            buffs=[],
            gold=100,
            stage=1
        )
        run = GameRun(
            user_id="test_user_sp",
            node_type="battle",
            node_data={"cards_played_this_turn": 0},
            player=player,
            enemies=[EnemyState(name="地精", hp=9999, max_hp=9999, shield=0, actions=0, bonus_actions=0, max_actions=0, max_bonus_actions=0)]
        )
        engine.play_card(run, 1)
        self.assertTrue(any(b.id == "buffer" for b in player.buffs))
        self.assertTrue(any(b.id == "barricade" for b in player.buffs))
        engine._damage_target(run, "p0", 10, damage_type="slash")
        self.assertEqual(player.hp, 30)
        self.assertFalse(any(b.id == "buffer" for b in player.buffs))
        player.shield = 15
        engine.end_turn(run)
        self.assertEqual(player.shield, 15)
        
        player.hand = ["glacier_fortress"]
        player.actions = 2
        engine.play_card(run, 1)
        self.assertEqual(player.shield, 35)
        self.assertTrue(any(b.id == "glacier_fortress_buff" for b in player.buffs))
        engine.end_turn(run)
        self.assertEqual(player.shield, 39)
        
        player.hand = ["archmage_wish", "fire_bolt"]
        player.actions = 4
        player.bonus_actions = 4
        engine.play_card(run, 1)
        self.assertTrue(any(b.id == "wish_power" for b in player.buffs))
        enemy = run.enemies[0]
        engine.play_card(run, 1, "e1")
        self.assertEqual(enemy.hp, 9992)
        
        player.hand = ["demon_form"]
        player.actions = 2
        engine.play_card(run, 1)
        self.assertTrue(any(b.id == "demon_form" for b in player.buffs))
        self.assertEqual(next(b for b in player.buffs if b.id == "demon_form").stacks, 3)
        from game.models.events import TurnStartEvent
        engine.event_bus.dispatch(TurnStartEvent(run, is_player=True))
        self.assertTrue(any(b.id == "strength" for b in player.buffs))
        self.assertEqual(next(b for b in player.buffs if b.id == "strength").stacks, 3)
        
        player.hand = ["time_warp", "arcane_spark"]
        player.discard_pile = ["arcane_spark"]
        player.actions = 2
        engine.play_card(run, 1)
        self.assertEqual(len(player.discard_pile), 0)
        self.assertEqual(len(player.hand), 2)
        
        player.buffs = [BuffState(id="strength", name="力量", desc="", stacks=2)]
        player.hand = ["break_limits"]
        player.actions = 2
        engine.play_card(run, 1)
        self.assertEqual(next(b for b in player.buffs if b.id == "strength").stacks, 4)
        
        enemy.buffs = []
        player.hand = ["abyss_collapse"]
        player.actions = 2
        engine.play_card(run, 1, "e1")
        self.assertEqual(enemy.hp, 9968)
        
        engine._add_buff_to(enemy, "stun", "眩晕", "无法行动", 1)
        player.hand = ["abyss_collapse"]
        player.actions = 2
        engine.play_card(run, 1, "e1")
        self.assertEqual(enemy.hp, 9920)
        
        player.hand = ["demon_contract"]
        player.actions = 2
        player.bonus_actions = 1
        engine.play_card(run, 1)
        self.assertTrue(any(b.id == "demon_contract_buff" for b in player.buffs))
        self.assertEqual(player.bonus_actions, 3)
        
        enemy.buffs = []
        player.hand = ["frost_nova"]
        player.actions = 2
        engine.play_card(run, 1)
        self.assertTrue(any(b.id == "stun" for b in enemy.buffs))
        self.assertTrue(any(b.id == "minor_vulnerable_cold" for b in enemy.buffs))
        
        enemy.buffs = []
        player.hand = ["abyss_erosion"]
        player.actions = 2
        engine.play_card(run, 1, "e1")
        self.assertTrue(any(b.id == "void_weakness" for b in enemy.buffs))
        
        player.minions = {"1": MinionState(id="mercenary", name="雇佣兵", hp=10, max_hp=10, atk=4, actions=1, bonus_actions=0)}
        player.shield = 0
        player.hand = ["glacier_tempest"]
        player.actions = 4
        engine.play_card(run, 1)
        self.assertEqual(player.shield, 6)
        
        player.hand = ["time_stop"]
        player.actions = 2
        engine.play_card(run, 1)
        self.assertEqual(run.node_data["extra_turns_left"], 3)
