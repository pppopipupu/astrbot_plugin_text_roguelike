from .base import EventOption
from ...data.event_data import EVENT_CONFIG

class HelpKnightOption(EventOption, action="help_knight", text="施以援手"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        has_aid = False
        for idx, cid in enumerate(p.deck):
            if cid == "first_aid":
                p.deck.pop(idx)
                has_aid = True
                break
        if not has_aid:
            return "❌ 你的卡组中没有【绷带包扎】卡牌！"
        p.deck.append("shield_guard")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你将绷带给予骑士治疗。为了答谢，【盾卫】加入了你的卡组。已前往下一关。"

class RobKnightOption(EventOption, action="rob_knight", text="趁火打劫"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.gold += 25
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你不顾骑士的反抗夺走了他的财物，获得 25 金币。已前往下一关。"

class AskKnightOption(EventOption, action="ask_knight", text="询问他的来历"):
    def _run_effect(self, run, engine) -> str:
        cfg = EVENT_CONFIG["knight_story"]
        run.node_data["event_id"] = "knight_story"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你向受伤的骑士询问缘由..."

class CaveQuestOption(EventOption, action="cave_quest", text="帮他去洞穴取回长剑"):
    def _run_effect(self, run, engine) -> str:
        cfg = EVENT_CONFIG["knight_cave"]
        run.node_data["event_id"] = "knight_cave"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你答应帮他去取回佩剑，顺着他的指引来到了山洞深处。"

class CaveFightOption(EventOption, action="cave_fight", text="进入战斗"):
    def _run_effect(self, run, engine) -> str:
        run.node_data["quest"] = "knight_cave"
        engine.battle_engine._init_battle_node(run, "normal")
        run.node_type = "battle"
        if run.enemies:
            run.enemies[0].name = "魔仆"
            run.enemies[0].hp = 15
            run.enemies[0].max_hp = 15
        engine.save_manager.save_save(run.user_id, run)
        return engine.battle_engine._append_logs_to_res(run, "你跨入洞穴，一只面目狰狞的【魔仆】冲了过来！进入战斗。")
