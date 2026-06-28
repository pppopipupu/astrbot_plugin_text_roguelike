import random
from .base import EventOption
from ...data.event_data import EVENT_CONFIG
from ..relics import get_relic_name

class MazeFireOption(EventOption, action="maze_fire", text="循着远处的微弱火光走"):
    def _run_effect(self, run, engine) -> str:
        cfg = EVENT_CONFIG["maze_guard"]
        run.node_data["event_id"] = "maze_guard"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你跟着红色的火光，在湿润的石壁甬道中穿行..."

class MazeWaterOption(EventOption, action="maze_water", text="沿着潺潺的水流声走"):
    def _run_effect(self, run, engine) -> str:
        cfg = EVENT_CONFIG["maze_pool"]
        run.node_data["event_id"] = "maze_pool"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你顺着潺潺的水流声，在布满青苔的石墙中摸行..."

class MazeMarkOption(EventOption, action="maze_mark", text="在墙壁做标记，小心翼翼前行"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.gold += 10
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "🧭 你在每个路口用小刀刻下记号。虽然多花了一些时间，但你安稳地走出了迷宫，且在出口处捡到了前人遗留的 10 金币。"

class BribeGuardOption(EventOption, action="bribe_guard", text="贿赂守卫"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        if p.gold < 20:
            return "❌ 你的金币不足 20 点，火元素守卫拒绝放行，并发出愤怒的嘶吼！"
        p.gold -= 20
        relics_pool = ["lucky_coin", "red_bottle", "leather_armor", "whetstone", "ready_pack", "arcane_rune"]
        available_relics = [r for r in relics_pool if r not in p.relics]
        got_relic = ""
        if available_relics:
            got_relic = random.choice(available_relics)
            p.relics.append(got_relic)
            if got_relic == "red_bottle":
                p.max_hp += 5
                p.hp += 5
        relic_msg = f"，并在宝座后的石盒中获得遗物【{get_relic_name(got_relic)}】" if got_relic else ""
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return f"🪙 你向火元素守卫进献了 20 金币。它满意地让开道路{relic_msg}。已离开迷宫。"

class FightGuardOption(EventOption, action="fight_guard", text="与守卫战斗"):
    def _run_effect(self, run, engine) -> str:
        run.node_data["quest"] = "maze_fight"
        engine.battle_engine._init_battle_node(run, "elite")
        run.node_type = "battle"
        if run.enemies:
            run.enemies[0].name = "火元素守卫"
            run.enemies[0].hp = 30 + run.player.stage * 2
            run.enemies[0].max_hp = run.enemies[0].hp
        engine.save_manager.save_save(run.user_id, run)
        return engine.battle_engine._append_logs_to_res(run, "🔥 谈和破裂！火元素守卫扬起法杖，滚滚热浪席卷而来！进入战斗。")

class BathePoolOption(EventOption, action="bathe_pool", text="在泉水中沐浴"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.max_hp += 3
        if "wither_seed" not in p.relics:
            p.hp = min(p.max_hp, p.hp + 15)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "💚 泉水温热且充盈着生命气息。你在池中休整，最大生命值永久增加了 3 点，且生命值回复了 15 点（若有枯萎之种则只加生命上限不回血）。"

class FishPoolOption(EventOption, action="fish_pool", text="捞取水底的遗物"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        if random.random() < 0.5:
            relics_pool = ["lucky_coin", "red_bottle", "leather_armor", "whetstone", "ready_pack", "arcane_rune"]
            available_relics = [r for r in relics_pool if r not in p.relics]
            got_relic = ""
            if available_relics:
                got_relic = random.choice(available_relics)
                p.relics.append(got_relic)
                if got_relic == "red_bottle":
                    p.max_hp += 5
                    p.hp += 5
            res = f"🍀 运气不错！池水没有反应，你安全地摸出了一个发光的神明宝物，获得遗物【{get_relic_name(got_relic)}】！" if got_relic else "池底空无一物。"
        else:
            p.max_hp = max(5, p.max_hp - 2)
            p.hp = min(p.hp, p.max_hp)
            res = "👹 突然水流旋动！一只守护水蛇从池底窜出，咬住了你的手臂并释放毒液！你的最大生命上限减少了 2 点！"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return res
