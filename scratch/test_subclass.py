import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.state import GameRun, PlayerState, EnemyState, UserStats, check_and_replace_fireball
from game.core.battle_engine import BattleEngine
from game.models.manager import SaveManager
from game.entities.cards import ALL_CARDS
from game.entities.buffs import apply_modify_spell_damage

class DummySaveManager:
    def __init__(self):
        self.stats = UserStats()
    def load_stats(self, user_id):
        return self.stats
    def save_stats(self, user_id, stats):
        self.stats = stats
        return True
    def save_save(self, user_id, run):
        pass
    def delete_save(self, user_id):
        pass
    def settle_game_and_delete(self, user_id, run, is_victory=False):
        stage = run.player.stage
        gold = run.player.gold
        if stage < 5:
            return "0 GP"
        gp_gained = gold * 10
        if is_victory:
            gp_gained += 1000
        self.stats.gp += gp_gained
        return f"{gp_gained} GP"

def test_user_stats():
    stats = UserStats()
    stats.gp = 100
    stats.unlocked_subclasses = ["时序法师"]
    stats.selected_subclass = "时序法师"
    assert stats.gp == 100
    assert "时序法师" in stats.unlocked_subclasses
    assert stats.selected_subclass == "时序法师"

def test_fireball_replacement():
    p = PlayerState(hp=45, max_hp=45, shield=0, gold=20, stage=1, subclass="塑能法师")
    run = GameRun(user_id="test", node_type="battle", player=p)
    replaced = [check_and_replace_fireball(run, "fireball") for _ in range(1000)]
    swarm_count = replaced.count("meteor_swarm")
    assert 300 < swarm_count < 500

    p2 = PlayerState(hp=45, max_hp=45, shield=0, gold=20, stage=1, subclass="时序法师")
    run2 = GameRun(user_id="test", node_type="battle", player=p2)
    replaced2 = [check_and_replace_fireball(run2, "fireball") for _ in range(1000)]
    assert replaced2.count("meteor_swarm") == 0

def test_elementalist_damage_boost():
    p = PlayerState(hp=45, max_hp=45, shield=0, gold=20, stage=1, subclass="塑能法师")
    run = GameRun(user_id="test", node_type="battle", player=p)
    card = ALL_CARDS["fire_bolt"]
    boosted = apply_modify_spell_damage(run, card, 10, None)
    assert boosted == 11

    p2 = PlayerState(hp=45, max_hp=45, shield=0, gold=20, stage=1, subclass="时序法师")
    run2 = GameRun(user_id="test", node_type="battle", player=p2)
    normal = apply_modify_spell_damage(run2, card, 10, None)
    assert normal == 10

def test_time_stop_mechanics():
    p = PlayerState(hp=45, max_hp=45, shield=0, gold=20, stage=2, subclass="时序法师")
    e = EnemyState(name="冰霜史莱姆", hp=10, max_hp=10, shield=0)
    run = GameRun(user_id="test", node_type="battle", player=p, enemies=[e])
    
    mgr = DummySaveManager()
    engine = BattleEngine(mgr)
    
    run.node_data["extra_turns_left"] = 3
    
    res_turn = engine.end_turn(run)
    assert run.node_data["extra_turns_left"] == 2
    assert "时间停止" in res_turn
    
    initial_status = [(e.hp, e.shield) for e in run.enemies]
    e.hp -= 2
    
    has_damaged = False
    for idx, enemy in enumerate(run.enemies):
        if idx < len(initial_status):
            old_hp, old_shield = initial_status[idx]
            if enemy.hp < old_hp or enemy.shield < old_shield:
                has_damaged = True
                break
                
    if has_damaged and run.node_data.get("extra_turns_left", 0) > 0:
        end_turn_res = engine.end_turn(run)
        assert run.node_data["extra_turns_left"] == 1

def test_gp_settlement():
    mgr = DummySaveManager()
    p_early = PlayerState(hp=45, max_hp=45, shield=0, gold=50, stage=3)
    run_early = GameRun(user_id="test", node_type="battle", player=p_early)
    msg_early = mgr.settle_game_and_delete("test", run_early, False)
    assert mgr.stats.gp == 0

    p_late = PlayerState(hp=45, max_hp=45, shield=0, gold=50, stage=5)
    run_late = GameRun(user_id="test", node_type="battle", player=p_late)
    msg_late = mgr.settle_game_and_delete("test", run_late, False)
    assert mgr.stats.gp == 500

    p_win = PlayerState(hp=45, max_hp=45, shield=0, gold=50, stage=20)
    run_win = GameRun(user_id="test", node_type="battle", player=p_win)
    msg_win = mgr.settle_game_and_delete("test", run_win, True)
    assert mgr.stats.gp == 2000

def test_shop_mechanics():
    stats = UserStats()
    stats.gp = 100000
    price_1 = 2888
    stats.gp -= price_1
    stats.unlocked_subclasses.append("时序法师")
    assert stats.gp == 100000 - 2888
    assert "时序法师" in stats.unlocked_subclasses
    price_3 = 66666
    stats.gp -= price_3
    stats.unlocked_subclasses.append("神秘物品")
    assert stats.gp == 100000 - 2888 - 66666
    assert "神秘物品" in stats.unlocked_subclasses

if __name__ == "__main__":
    test_user_stats()
    test_fireball_replacement()
    test_elementalist_damage_boost()
    test_time_stop_mechanics()
    test_gp_settlement()
    test_shop_mechanics()
    print("All subclass tests passed successfully!")
