import random
from .base import EventOption
from ...data.event_data import EVENT_CONFIG

class AbsorbAltarOption(EventOption, action="absorb_altar", text="汲取奥术"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.deck.append("arcane_charge")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你吸收了奥术波动的力量，将【奥术充能】加入卡组。已前往下一关。"

class BreakAltarOption(EventOption, action="break_altar", text="摧毁水晶"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.gold += 20
        p.hp = max(1, p.hp - 4)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你用法杖敲碎了祭坛上的水晶并收集了碎片（获得 20 金币），但被震荡的爆风伤及（失去 4 点生命值）。已前往下一关。"

class MeditateAltarOption(EventOption, action="meditate_altar", text="在祭坛前冥想"):
    def _run_effect(self, run, engine) -> str:
        cfg = EVENT_CONFIG["altar_portal"]
        run.node_data["event_id"] = "altar_portal"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你在祭坛前盘膝坐下，闭目静思..."

class EnterPortalOption(EventOption, action="enter_portal", text="跨入传送门"):
    def _run_effect(self, run, engine) -> str:
        if random.random() < 0.5:
            run.node_type = "shop"
            engine.explore_engine._init_shop_node(run)
            if "items" in run.node_data:
                for item in run.node_data["items"]:
                    item["price"] = max(0, int(item["price"] * 0.5))
            engine.save_manager.save_save(run.user_id, run)
            return "🌀 传送门闪烁！你被一股平稳的引力吸入，竟然直接降落在了一个神秘的流浪旅商营地，且这次流浪旅商给予了你 5 折全店优惠！"
        else:
            run.node_type = "battle"
            engine.battle_engine._init_battle_node(run, "elite")
            if run.enemies:
                run.enemies[0].name = "传送门守卫者"
            engine.save_manager.save_save(run.user_id, run)
            return engine.battle_engine._append_logs_to_res(run, "⚠️ 空间发生强烈扭曲！传送门能量崩溃，你被卷入一处荒野废墟，前方出现了一只凶猛的【传送门守卫者】！进入战斗。")

class ShatterPortalOption(EventOption, action="shatter_portal", text="摧毁传送门"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.gold += 40
        p.deck.append("curse_agony")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "💥 你用法术强行轰碎了虚空传送门！空间之门产生了剧烈爆炸，巨大的余波让你心神苦恼（1张【苦恼】卡牌已加入卡组），但破碎的裂隙中获得 40 金币。"
