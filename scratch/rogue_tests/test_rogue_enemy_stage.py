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

        from game.entities.enemies.elite.shadow_fiend import ShadowFiendTemplate
        fiend_template = ShadowFiendTemplate("暗影影魔")
        fiend_enemy = EnemyState("暗影影魔测试", 30, 30, 0, intent_type="shadow_strike", intent_val=6)
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
            stage=25,
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

    def test_expanded_monsters_and_mechanics(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
        sm = DummySaveManager()
        engine = BattleEngine(sm)

        cultist = EnemyState("邪教徒咔咔", 15, 15, 0)
        p_state = PlayerState(hp=50, max_hp=50, shield=0, gold=10, stage=1)
        run = GameRun(user_id="test_exp", node_type="battle", player=p_state, enemies=[cultist])

        from game.entities.enemies.normal.cultist_kaka import CultistKakaTemplate
        c_temp = CultistKakaTemplate("邪教徒咔咔")

        intents_1 = c_temp.roll_intents(run, engine, cultist)
        self.assertEqual(len(intents_1), 1)
        self.assertEqual(intents_1[0].type, "caw")

        c_logs_1 = []
        c_temp.execute_intent(run, engine, cultist, intents_1[0], c_logs_1)
        self.assertTrue(any(b.id == "ritual" for b in cultist.buffs))
        self.assertIn("咔咔", "".join(c_logs_1))

        from game.models.events import TurnStartEvent
        evt_start = TurnStartEvent(run, is_player=False)
        engine.event_bus.dispatch(evt_start)
        self.assertTrue(any(b.id == "strength" and b.stacks == 1 for b in cultist.buffs))

        intents_2 = c_temp.roll_intents(run, engine, cultist)
        self.assertEqual(intents_2[0].type, "peck")

        run.player.hp = 50
        c_logs_2 = []
        c_temp.execute_intent(run, engine, cultist, intents_2[0], c_logs_2)
        self.assertEqual(run.player.hp, 43)

        flayer = EnemyState("夺心魔", 48, 48, 0, max_actions=1, max_bonus_actions=1)
        run.enemies = [flayer]

        from game.entities.enemies.elite.mind_flayer import MindFlayerTemplate
        f_temp = MindFlayerTemplate("夺心魔")

        run.player.buffs.clear()
        intents_f1 = f_temp.roll_intents(run, engine, flayer)
        self.assertEqual(len(intents_f1), 2)

        tentacles_intent = next((it for it in intents_f1 if it.type == "tentacles"), None)
        if not tentacles_intent:
            from game.models.state import EnemyIntentState
            tentacles_intent = EnemyIntentState(type="tentacles", val=8, desc="触须袭击")
        f_logs_1 = []
        f_temp.execute_intent(run, engine, flayer, tentacles_intent, f_logs_1)
        self.assertTrue(any(b.id == "grappled" for b in run.player.buffs))

        import random
        old_random = random.random
        random.random = lambda: 0.0
        try:
            intents_f2 = f_temp.roll_intents(run, engine, flayer)
        finally:
            random.random = old_random
        self.assertTrue(any(it.type == "extract_brain" for it in intents_f2))

        eb_intent = next(it for it in intents_f2 if it.type == "extract_brain")
        run.player.hp = 50
        f_logs_2 = []
        f_temp.execute_intent(run, engine, flayer, eb_intent, f_logs_2)
        self.assertEqual(run.player.hp, 25)

        blast_intent = next((it for it in intents_f1 if it.type == "mind_blast"), None)
        if not blast_intent:
            from game.models.state import EnemyIntentState
            blast_intent = EnemyIntentState(type="mind_blast", val=8, desc="心灵震爆")
        f_logs_3 = []
        f_temp.execute_intent(run, engine, flayer, blast_intent, f_logs_3)
        self.assertTrue(any(b.id == "stun" for b in run.player.buffs))

        run.player.actions = 2
        run.player.bonus_actions = 1
        evt_p_start = TurnStartEvent(run, is_player=True)
        engine.event_bus.dispatch(evt_p_start)
        self.assertEqual(run.player.actions, 0)
        self.assertEqual(run.player.bonus_actions, 0)
        self.assertFalse(any(b.id == "stun" for b in run.player.buffs))

        pirate = EnemyState("吉斯洋基海盗", 18, 18, 0, max_actions=1, max_bonus_actions=0)
        run.enemies = [pirate]

        from game.entities.enemies.normal.githyanki_pirate import GithyankiPirateTemplate
        p_temp = GithyankiPirateTemplate("吉斯洋基海盗")

        run.player.shield = 10
        run.player.hp = 50
        slash_intent = next((it for it in p_temp.roll_intents(run, engine, pirate) if it.type == "silver_sword"), None)
        if not slash_intent:
            from game.models.state import EnemyIntentState
            slash_intent = EnemyIntentState(type="silver_sword", val=7, desc="银剑")
        p_logs_1 = []
        p_temp.execute_intent(run, engine, pirate, slash_intent, p_logs_1)
        self.assertEqual(run.player.shield, 0)
        self.assertEqual(run.player.hp, 49)

        step_intent = next((it for it in p_temp.roll_intents(run, engine, pirate) if it.type == "astral_step"), None)
        if not step_intent:
            from game.models.state import EnemyIntentState
            step_intent = EnemyIntentState(type="astral_step", val=6, desc="跃迁")
        p_logs_2 = []
        p_temp.execute_intent(run, engine, pirate, step_intent, p_logs_2)
        self.assertTrue(any(b.id == "astral_speed" for b in pirate.buffs))

        intents_p3 = p_temp.roll_intents(run, engine, pirate)
        self.assertEqual(len(intents_p3), 2)
        self.assertFalse(any(b.id == "astral_speed" for b in pirate.buffs))

        commander = EnemyState("吉斯洋基至高指挥官", 55, 55, 0, max_actions=1, max_bonus_actions=1)
        run.enemies = [commander]

        from game.entities.enemies.elite.githyanki_supreme_commander import GithyankiSupremeCommanderTemplate
        cmd_temp = GithyankiSupremeCommanderTemplate("吉斯洋基至高指挥官")

        cmd_logs_1 = []
        sh_intent = next((it for it in cmd_temp.roll_intents(run, engine, commander) if it.type == "summon_hound"), None)
        if not sh_intent:
            from game.models.state import EnemyIntentState
            sh_intent = EnemyIntentState(type="summon_hound", val=0, desc="星界呼唤")
        cmd_temp.execute_intent(run, engine, commander, sh_intent, cmd_logs_1)
        self.assertEqual(len(run.enemies), 2)
        self.assertEqual(run.enemies[1].name, "星界幼犬")

        cmd_logs_2 = []
        cp_intent = next((it for it in cmd_temp.roll_intents(run, engine, commander) if it.type == "commanding_presence"), None)
        if not cp_intent:
            from game.models.state import EnemyIntentState
            cp_intent = EnemyIntentState(type="commanding_presence", val=2, desc="指挥")
        cmd_temp.execute_intent(run, engine, commander, cp_intent, cmd_logs_2)
        self.assertTrue(any(b.id == "strength" and b.stacks == 2 for b in commander.buffs))
        self.assertTrue(any(b.id == "strength" and b.stacks == 2 for b in run.enemies[1].buffs))

    def test_enemy_trash_talk(self):
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
            deck=["fire_bolt"],
            hand=["fire_bolt"],
            actions=1,
            bonus_actions=1
        )
        run = GameRun(
            user_id="test_trash",
            node_type="battle",
            player=player,
            enemies=[]
        )
        run.node_data["turn"] = 1

        from game.entities.enemies.summon.astral_puppy import AstralPuppyTemplate
        puppy_enemy = EnemyState("星界幼犬", 15, 15, 0)
        puppy_temp = AstralPuppyTemplate("星界幼犬")
        puppy_intents = puppy_temp.roll_intents(run, engine, puppy_enemy)
        logs = []
        puppy_temp.execute_intent(run, engine, puppy_enemy, puppy_intents[0], logs)
        self.assertFalse(any("【" in log and "】说" in log for log in logs))

        from game.entities.enemies.town_enemies import NoobSlayer99Template
        noob_enemy = EnemyState("NoobSlayer99", 50, 50, 0)
        noob_temp = NoobSlayer99Template("NoobSlayer99")
        noob_intents = noob_temp.roll_intents(run, engine, noob_enemy)
        
        logs_noob = []
        noob_temp.execute_intent(run, engine, noob_enemy, noob_intents[0], logs_noob)
        self.assertEqual(len(logs_noob), 2)
        
        logs_noob_2 = []
        noob_temp.execute_intent(run, engine, noob_enemy, noob_intents[0], logs_noob_2)
        self.assertEqual(len(logs_noob_2), 1)

        run.node_data["turn"] = 2
        player.hp = 20
        player.max_hp = 100
        noob_intents_2 = noob_temp.roll_intents(run, engine, noob_enemy)
        logs_noob_3 = []
        noob_temp.execute_intent(run, engine, noob_enemy, noob_intents_2[0], logs_noob_3)
        self.assertTrue(any("单手" in log or "送你一程" in log or "双手离开" in log for log in logs_noob_3))

        run.node_data["turn"] = 3
        player.hp = 80
        player.shield = 20
        noob_intents_3 = noob_temp.roll_intents(run, engine, noob_enemy)
        logs_noob_4 = []
        noob_temp.execute_intent(run, engine, noob_enemy, noob_intents_3[0], logs_noob_4)
        self.assertTrue(any("乌龟壳" in log or "最厚的甲" in log or "属乌龟" in log for log in logs_noob_4))

        run.node_data["turn"] = 4
        player.shield = 0
        player.hand = ["fire_bolt"] * 12
        noob_intents_4 = noob_temp.roll_intents(run, engine, noob_enemy)
        logs_noob_5 = []
        noob_temp.execute_intent(run, engine, noob_enemy, noob_intents_4[0], logs_noob_5)
        self.assertTrue(any("斗地主" in log or "废纸" in log for log in logs_noob_5))

        run.node_data["turn"] = 5
        player.hand = ["fire_bolt"]
        noob_intents_5 = noob_temp.roll_intents(run, engine, noob_enemy)
        logs_noob_6 = []
        noob_temp.execute_intent(run, engine, noob_enemy, noob_intents_5[0], logs_noob_6)
        self.assertTrue(any("没牌" in log or "空手" in log or "个人秀" in log or "血虐" in log for log in logs_noob_6))

    def test_boss_selection_by_stage(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
            def load_stats(self, user_id):
                return None
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        
        stages_12_bosses = set()
        for _ in range(50):
            player = PlayerState(hp=100, max_hp=100, shield=0, gold=100, stage=12)
            run = GameRun(user_id="test_boss", node_type="battle", player=player)
            engine._init_battle_node(run, "boss")
            stages_12_bosses.add(run.enemies[0].name)
        self.assertEqual(stages_12_bosses, {"远古红龙", "雷霆领主"})
        
        stages_25_bosses = set()
        for _ in range(50):
            player = PlayerState(hp=100, max_hp=100, shield=0, gold=100, stage=25)
            run = GameRun(user_id="test_boss", node_type="battle", player=player)
            engine._init_battle_node(run, "boss")
            stages_25_bosses.add(run.enemies[0].name)
        self.assertEqual(stages_25_bosses, {"腐化之心", "Icerainboww"})
        
        player31 = PlayerState(hp=100, max_hp=100, shield=0, gold=100, stage=31)
        run31 = GameRun(user_id="test_boss", node_type="battle", player=player31)
        engine._init_battle_node(run31, "boss")
        self.assertEqual(run31.enemies[0].name, "亚弗戈蒙")
        
        player32 = PlayerState(hp=100, max_hp=100, shield=0, gold=100, stage=32)
        run32 = GameRun(user_id="test_boss", node_type="battle", player=player32)
        engine._init_battle_node(run32, "boss")
        self.assertEqual(run32.enemies[0].name, "虚空之门·尤格-索托斯")

    def test_unyielding_buff(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
            def load_stats(self, user_id):
                return None
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(hp=100, max_hp=100, shield=0, gold=100, stage=25)
        run = GameRun(user_id="test_user", node_type="battle", player=player)
        engine._init_battle_node(run, "boss")
        
        corrupted_heart = None
        for enemy in run.enemies:
            if enemy.name == "腐化之心":
                corrupted_heart = enemy
                break
        
        if corrupted_heart:
            self.assertEqual(corrupted_heart.max_hp, 200)
            self.assertEqual(corrupted_heart.hp, 200)
            unyielding_buff = next((b for b in corrupted_heart.buffs if b.id == "unyielding"), None)
            self.assertIsNotNone(unyielding_buff)
            self.assertEqual(unyielding_buff.stacks, 40)

        enemy = EnemyState("测试敌人", 200, 200, 0)
        from game.models.state import BuffState
        enemy.buffs.append(BuffState("unyielding", "坚不可摧", 40))
        run.enemies = [enemy]

        engine._damage_target(run, "e1", 30, damage_type="fire")
        self.assertEqual(enemy.hp, 170)
        
        engine._damage_target(run, "e1", 20, damage_type="fire")
        self.assertEqual(enemy.hp, 160)
        
        engine._damage_target(run, "e1", 15, damage_type="fire")
        self.assertEqual(enemy.hp, 160)

        engine._damage_target(run, "e1", 10, damage_type="true")
        self.assertEqual(enemy.hp, 150)

        from game.models.events import TurnEndEvent
        evt = TurnEndEvent(run=run, is_player=False)
        engine.event_bus.dispatch(evt)

        engine._damage_target(run, "e1", 30, damage_type="fire")
        self.assertEqual(enemy.hp, 120)

    def test_aforgomon_boss_mechanisms(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
            def load_stats(self, user_id):
                return None
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(hp=100, max_hp=100, shield=0, gold=100, stage=31, name="测试玩家")
        run = GameRun(user_id="test_user", node_type="battle", player=player)
        engine._init_battle_node(run, "boss")
        
        boss = run.enemies[0]
        self.assertEqual(boss.name, "亚弗戈蒙")
        self.assertEqual(boss.hp, 180)
        
        from game.renderer import render_query_info
        res_afor = render_query_info("【时空主宰】亚弗戈蒙")
        self.assertFalse("未找到" in res_afor)
        res_yog = render_query_info("【终焉】虚空之门·尤格-索托斯")
        self.assertFalse("未找到" in res_yog)
        
        intents_p1 = engine.enemy_controller.roll_enemy_intent(run)
        self.assertTrue(len(boss.intents) >= 2)
        
        engine._damage_target(run, "e1", 180, damage_type="true")
        self.assertEqual(boss.name, "【时空主宰】亚弗戈蒙")
        self.assertEqual(boss.hp, 220)
        self.assertEqual(boss.max_hp, 220)
        
        has_res = any(b.id == "pendulum_resonance" for b in player.buffs)
        self.assertTrue(has_res)
        
        intents_p2 = engine.enemy_controller.roll_enemy_intent(run)
        self.assertTrue(len(boss.intents) >= 3)
        
        from game.entities.enemies.boss import BossAforgomonTemplate
        from game.models.state import EnemyIntentState, CardState
        aforgomon_temp = BossAforgomonTemplate("亚弗戈蒙")
        
        player.hand = [CardState("strike"), CardState("defend"), CardState("strike")]
        intent_tf = EnemyIntentState(type="time_fracture", val=12, desc="", cost_a=1, cost_ba=0)
        logs_tf = []
        aforgomon_temp.execute_intent(run, engine, boss, intent_tf, logs_tf)
        self.assertEqual(player.hand[0].fragile, 0)
        self.assertEqual(player.hand[1].fragile, 1)
        self.assertEqual(player.hand[2].fragile, 1)
        
        player.buffs = [b for b in player.buffs if b.id != "pendulum_resonance"]
        intent_sbc = EnemyIntentState(type="silver_bell_clang", val=15, desc="", cost_a=1, cost_ba=0)
        logs_sbc = []
        aforgomon_temp.execute_intent(run, engine, boss, intent_sbc, logs_sbc)
        has_res2 = any(b.id == "pendulum_resonance" for b in player.buffs)
        self.assertTrue(has_res2)
        
        player.hp = 100
        logs_sbc2 = []
        aforgomon_temp.execute_intent(run, engine, boss, intent_sbc, logs_sbc2)
        self.assertEqual(player.hp, 80)
        
        boss.hp = 100
        boss.shield = 0
        intent_tr = EnemyIntentState(type="time_reflux", val=0, desc="", cost_a=1, cost_ba=0)
        logs_tr = []
        aforgomon_temp.execute_intent(run, engine, boss, intent_tr, logs_tr)
        self.assertEqual(boss.hp, 125)
        self.assertEqual(boss.shield, 20)
        
        player.hand = [CardState("strike")]
        intent_tl = EnemyIntentState(type="temporal_lock", val=5, desc="", cost_a=0, cost_ba=1)
        logs_tl = []
        aforgomon_temp.execute_intent(run, engine, boss, intent_tl, logs_tl)
        self.assertEqual(len(player.hand), 0)
        
        import unittest.mock as mock
        with mock.patch("random.random", return_value=0.1):
            from game.models.events import TurnStartEvent
            evt = TurnStartEvent(run=run, is_player=False)
            engine.event_bus.dispatch(evt)
            
        self.assertTrue(any(e.name == "时空残影" for e in run.enemies))
        
        echo_enemy = next(e for e in run.enemies if e.name == "时空残影")
        self.assertEqual(echo_enemy.hp, 15)
        
        player.hp = 100
        boss.hp = 220
        boss.shield = 0
        engine._damage_target(run, "e1", 20, damage_type="slashing")
        self.assertEqual(boss.hp, 210)
        self.assertEqual(echo_enemy.hp, 5)
        self.assertEqual(player.hp, 97)
        
        player.actions = 0
        player.bonus_actions = 1
        run.node_data["cards_played_this_turn"] = 3
        player.hp = 100
        from game.models.events import TurnEndEvent
        evt_end = TurnEndEvent(run=run, is_player=True)
        engine.event_bus.dispatch(evt_end)
        self.assertEqual(player.hp, 94)
        
        player.actions = 1
        player.bonus_actions = 1
        run.node_data["cards_played_this_turn"] = 3
        player.hp = 100
        evt_end2 = TurnEndEvent(run=run, is_player=True)
        engine.event_bus.dispatch(evt_end2)
        self.assertEqual(player.hp, 100)
        self.assertEqual(run.node_data.get("draw_penalty_next_turn"), -2)

    def test_coc_creatures_and_relics(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
            def load_stats(self, user_id):
                return None
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(hp=80, max_hp=80, shield=10, gold=100, stage=1, relics=["leng_spider_venom", "migo_lightning_gun", "shoggoth_slime", "star_vampire_proboscis", "starspawn_core"])
        
        from game.entities.enemies.normal.coc_creatures import DeepOneTemplate, GhoulTemplate, ShantakTemplate
        from game.entities.enemies.elite.coc_elites import MigoTemplate, StarspawnOfCthulhuTemplate
        from game.models.state import EnemyIntentState, CardState
        
        deep_one = EnemyState("深潜者", 20, 20, 0)
        run = GameRun(user_id="test_coc", node_type="battle", player=player, enemies=[deep_one])
        deep_temp = DeepOneTemplate("深潜者")
        logs_deep = []
        intent_deep = EnemyIntentState(type="tsunami_strike", val=5, desc="")
        deep_temp.execute_intent(run, engine, deep_one, intent_deep, logs_deep)
        self.assertTrue(player.shield < 10)
        
        migo = EnemyState("米·戈", 30, 30, 0)
        run_migo = GameRun(user_id="test_coc_migo", node_type="battle", player=player, enemies=[migo])
        migo_temp = MigoTemplate("米·戈")
        logs_migo = []
        intent_migo = EnemyIntentState(type="bio_shield", val=10, desc="")
        engine._add_buff_to(migo, "stun", "眩晕", "", 1)
        migo_temp.execute_intent(run_migo, engine, migo, intent_migo, logs_migo)
        self.assertFalse(any(b.id == "stun" for b in migo.buffs))
        
        migo.shield = 0
        from game.models.events import BattleStartEvent
        evt_start = BattleStartEvent(run=run_migo)
        engine.event_bus.dispatch(evt_start)
        self.assertEqual(migo.hp, 25)
        
        engine._damage_target(run_migo, "p0", 10, damage_type="slashing")
        self.assertEqual(player.shield, 4)
        
        from game.models.events import CardPlayedEvent, Card
        card_dummy = Card(id="test_card", name="测试牌", cost_a=1, cost_ba=0, type="spell", rarity="common", desc="", color="neutral")
        setattr(card_dummy, "exhaust", True)
        evt_played = CardPlayedEvent(run=run, card=card_dummy, target="e1")
        engine.event_bus.dispatch(evt_played)
        self.assertTrue(player.hp > 70)
        
        player.bonus_actions = 1
        from game.models.events import TurnEndEvent
        evt_end = TurnEndEvent(run=run_migo, is_player=True)
        engine.event_bus.dispatch(evt_end)
        self.assertEqual(migo.hp, 15)

    def test_mindflayer_brain_modification(self):
        class DummySaveManager:
            def save_save(self, user_id, run):
                pass
            def delete_save(self, user_id):
                pass
            def load_stats(self, user_id):
                return None
        sm = DummySaveManager()
        engine = BattleEngine(sm)
        player = PlayerState(hp=80, max_hp=80, shield=10, gold=100, stage=1, relics=["mindflayer_brain"])
        enemy = EnemyState("测试敌人", 50, 50, 0)
        run = GameRun(user_id="test_mindflayer", node_type="battle", player=player, enemies=[enemy])
        
        from game.models.state import CardState
        player.hand = [CardState("strike")]
        engine.card_player.discard_card(run, player.hand[0])
        self.assertEqual(enemy.hp, 47)
        
        enemy.hp = 50
        player.hand = [CardState("strike")]
        engine.card_player.end_turn(run)
        self.assertEqual(enemy.hp, 50)

