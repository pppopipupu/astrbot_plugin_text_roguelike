import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.core.battle_engine import BattleEngine
from game.models.manager import SaveManager
from game.models.state import GameRun, PlayerState, EnemyState, BuffState, Card
from game.cards import ALL_CARDS

class TestIcerainboww(unittest.TestCase):
    def setUp(self):
        self.save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data_icerainboww")
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        self.manager = SaveManager(data_dir=self.save_dir)
        self.engine = BattleEngine(self.manager)

    def tearDown(self):
        import shutil
        if os.path.exists(self.save_dir):
            shutil.rmtree(self.save_dir)

    def test_boss_initialization_and_intents(self):
        player = PlayerState(
            hp=80,
            max_hp=80,
            shield=0,
            gold=100,
            stage=20,
            deck=["dagger_throw", "adrenaline"],
            draw_pile=["dagger_throw"],
            discard_pile=[],
            exhaust_pile=[],
            graveyard=[],
            hand=[],
            actions=2,
            bonus_actions=1,
            minions={},
            amulets={},
            abilities=[],
            fold_guide=True,
            buffs=[],
            relics=[],
            subclass="时序法师"
        )
        run = GameRun(
            user_id="test_user_ice",
            node_type="battle",
            player=player,
            enemies=[],
            node_data={},
            map_data={}
        )
        
        self.engine._init_battle_node(run, "boss")
        
        run.enemies = [EnemyState(
            name="Icerainboww",
            hp=160,
            max_hp=160,
            shield=0,
            actions=2,
            bonus_actions=0,
            max_actions=2,
            max_bonus_actions=0
        )]
        run.node_data["boss_name"] = "Icerainboww"
        run.node_data["icerainboww_turn"] = 1
        
        self.assertEqual(run.enemies[0].max_actions, 2)
        
        self.engine._roll_enemy_intent(run)
        enemy = run.enemies[0]
        
        self.assertEqual(enemy.intent_a_type, "icerain_shoot")
        self.assertEqual(enemy.intent_a2_type, "fury")
        
        player.hp = 80
        player.shield = 0
        enemy.hp = 160
        enemy.shield = 0
        
        enemy.actions = 2
        enemy.bonus_actions = 0
        
        logs = []
        self.engine._enemy_turn(run)
        
        self.assertEqual(player.hp, 78)
        self.assertTrue(run.node_data.get("drain_a"))
        
        has_fury = any(b.id == "fury" for b in enemy.buffs)
        self.assertTrue(has_fury)
        
        player.hand = ["adrenaline"]
        player.actions = 2
        player.bonus_actions = 1
        
        if run.node_data.get("drain_a"):
            player.actions = max(0, player.actions - 1)
            run.node_data.pop("drain_a", None)
            
        self.assertEqual(player.actions, 1)
        
        self.engine.play_card(run, 1)
        
        strength_stacks = 0
        for b in enemy.buffs:
            if b.id == "strength":
                strength_stacks += b.stacks
        self.assertEqual(strength_stacks, 1)

    def test_vulnerable_damage_calculation(self):
        player = PlayerState(
            hp=80,
            max_hp=80,
            shield=0,
            gold=100,
            stage=20,
            deck=[],
            draw_pile=[],
            discard_pile=[],
            exhaust_pile=[],
            graveyard=[],
            hand=[],
            actions=2,
            bonus_actions=1,
            minions={},
            amulets={},
            abilities=[],
            fold_guide=True,
            buffs=[],
            relics=[],
            subclass=""
        )
        run = GameRun(
            user_id="test_user_ice",
            node_type="battle",
            player=player,
            enemies=[EnemyState(
                name="Icerainboww",
                hp=160,
                max_hp=160,
                shield=0,
                actions=2,
                bonus_actions=0,
                max_actions=2,
                max_bonus_actions=0
            )],
            node_data={},
            map_data={}
        )
        
        self.engine._add_buff_to(player, "minor_vulnerable_cold", "轻度寒冷易伤", "", 2)
        
        player.hp = 80
        self.engine._damage_target(run, "p0", 10, source="test", damage_type="cold")
        self.assertEqual(player.hp, 65)
        
        player.hp = 80
        self.engine._damage_target(run, "p0", 10, source="test", damage_type="fire")
        self.assertEqual(player.hp, 70)
        
        self.engine._add_buff_to(player, "vulnerable_fire", "火焰易伤", "", 1)
        
        player.hp = 80
        self.engine._damage_target(run, "p0", 10, source="test", damage_type="fire")
        self.assertEqual(player.hp, 60)
        
        run.enemies[0].max_actions = 0
        run.enemies[0].actions = 0
        
        self.engine.end_turn(run)
        
        minor_buff = next((b for b in player.buffs if b.id == "minor_vulnerable_cold"), None)
        self.assertIsNotNone(minor_buff)
        self.assertEqual(minor_buff.stacks, 1)
        
        vul_buff = next((b for b in player.buffs if b.id == "vulnerable_fire"), None)
        self.assertIsNone(vul_buff)
        
        self.engine.end_turn(run)
        minor_buff = next((b for b in player.buffs if b.id == "minor_vulnerable_cold"), None)
        self.assertIsNone(minor_buff)

    def test_boss_kill_stat_flag(self):
        player = PlayerState(
            hp=80,
            max_hp=80,
            shield=0,
            gold=100,
            stage=20,
            deck=[],
            draw_pile=[],
            discard_pile=[],
            exhaust_pile=[],
            graveyard=[],
            hand=[],
            actions=2,
            bonus_actions=1,
            minions={},
            amulets={},
            abilities=[],
            fold_guide=True,
            buffs=[],
            relics=[],
            subclass=""
        )
        run = GameRun(
            user_id="test_user_ice",
            node_type="battle",
            player=player,
            enemies=[EnemyState(
                name="Icerainboww",
                hp=10,
                max_hp=160,
                shield=0,
                actions=2,
                bonus_actions=0,
                max_actions=2,
                max_bonus_actions=0
            )],
            node_data={"boss_name": "Icerainboww"},
            map_data={}
        )
        
        self.engine._damage_target(run, "e1", 10, source="player", damage_type="true")
        self.assertEqual(len(run.enemies), 0)
        
        self.engine._handle_battle_win(run)
        self.assertEqual(run.node_type, "victory")
        
        stats = self.manager.load_stats("test_user_ice")
        self.assertTrue(stats.killed_icerainboww)

if __name__ == "__main__":
    unittest.main()
