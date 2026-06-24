import unittest
from scratch.rogue_tests.base import *

class TestRogueEnemyStage(unittest.TestCase):
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

        from game.entities.buffs.debuffs import BeatOfDeathBuff
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

    def test_dynamic_boss_victory_message(self):
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
            def settle_game_and_delete(self, user_id, run, is_victory=True):
                return "游戏已成功结算并清理。"
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        router = CLIRouter(sm, engine)
        player = PlayerState(
            hp=50,
            max_hp=50,
            shield=0,
            gold=100,
            stage=20,
            deck=["fire_bolt"],
            hand=["fire_bolt"],
            actions=2,
            bonus_actions=1
        )
        enemy = EnemyState("Icerainboww", 1, 160, 0)
        run = GameRun(
            user_id="test_victory_user",
            node_type="battle",
            player=player,
            enemies=[enemy],
            node_data={"boss_name": "Icerainboww"}
        )
        res, term = router._execute_sub_action("test_victory_user", run, ["使用", "1", "e1"])
        self.assertTrue(term)
        self.assertIn("恭喜你击败了Icerainboww，通关成功！", res)
        self.assertNotIn("腐化之心", res)

    def test_echo_replay_message_compression(self):
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
            stage=2,
            deck=["fire_bolt"],
            hand=["fire_bolt"],
            actions=2,
            bonus_actions=1
        )
        enemy = EnemyState("测试敌人", 500, 500, 0)
        run = GameRun(
            user_id="test_compression_user",
            node_type="battle",
            player=player,
            enemies=[enemy]
        )
        card = ALL_CARDS["fire_bolt"]
        old_replay = getattr(card, "replay", 0)
        card.replay = 12
        try:
            res = engine.play_card(run, 1)
            self.assertIn("x 12次", res)
            self.assertNotIn("[重放触发]", res)
            self.assertEqual(enemy.hp, 500 - 3 * 13)
        finally:
            card.replay = old_replay
