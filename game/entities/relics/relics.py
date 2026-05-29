from typing import Dict, List, Optional
from ...data.relic_data import RELIC_CONFIG

class RelicImpl:
    def __init__(self, relic_id: str):
        self.id = relic_id

    def on_battle_start(self, run, engine):
        pass

    def on_battle_win(self, run, engine):
        pass

    def modify_initial_draw(self, run, draw_count: int, engine) -> int:
        return draw_count

class AncientPageRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        p = run.player
        p.hp = max(1, p.hp - 4)
        engine._log_event(run, "📖 [先古残页] 触发：失去 4 点生命值。")
        max_hand = 9 if "mask_of_void" in p.relics else 12
        spark_count = 0
        for _ in range(2):
            if len(p.hand) < max_hand:
                p.hand.append("arcane_spark")
                spark_count += 1
        if spark_count > 0:
            engine._log_event(run, f"📖 [先古残页] 触发：将 {spark_count} 张【奥术星火】加入手牌。")

class HeavyArmorRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        run.player.shield += 8
        engine._log_event(run, "🛡️ [重装甲片] 触发：获得 8 点初始护盾。")

class LeatherArmorRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        run.player.shield += 4
        engine._log_event(run, "🛡️ [坚固皮革] 触发：获得 4 点初始护盾。")

class RustShackleRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        p = run.player
        p.hp = max(1, p.hp - 4)
        engine._log_event(run, "🔒 [铁锈之锁] 触发：失去 4 点生命值。")

class GreedyContractRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        p = run.player
        p.hp = max(1, p.hp - 3)
        engine._log_event(run, "🪙 [贪婪契约] 触发：失去 3 点生命值。")

class ReadyPackRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        engine._log_event(run, "🎒 [准备背包] 触发：本场战斗初始附赠动作（BA）+1。")

    def modify_initial_draw(self, run, draw_count: int, engine) -> int:
        return draw_count + 1

class AncientEyeRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        engine._log_event(run, "👁️ [先古之眼] 触发：初始抽牌数量 +2。")

    def modify_initial_draw(self, run, draw_count: int, engine) -> int:
        return draw_count + 2

class BlindSpotRelic(RelicImpl):
    def on_battle_start(self, run, engine):
        engine._log_event(run, "👁️ [盲目之障] 触发：首回合少抽 2 张牌。")

    def modify_initial_draw(self, run, draw_count: int, engine) -> int:
        return max(0, draw_count - 2)

class DragonBloodRelic(RelicImpl):
    def on_battle_win(self, run, engine):
        p = run.player
        p.hp = min(p.max_hp, p.hp + 5)
        engine._log_event(run, "🩸 [红龙之血] 触发：回复了 5 点生命值。")

RELIC_IMPLS = {
    "ancient_page": AncientPageRelic,
    "heavy_armor": HeavyArmorRelic,
    "leather_armor": LeatherArmorRelic,
    "rust_shackle": RustShackleRelic,
    "greedy_contract": GreedyContractRelic,
    "ready_pack": ReadyPackRelic,
    "ancient_eye": AncientEyeRelic,
    "blind_spot": BlindSpotRelic,
    "dragon_blood": DragonBloodRelic,
}

def get_relic_impl(relic_id: str) -> Optional[RelicImpl]:
    cls = RELIC_IMPLS.get(relic_id)
    if cls:
        return cls(relic_id)
    return None

def get_relic_name(relic_id: str) -> str:
    return RELIC_CONFIG.get(relic_id, {}).get("name", relic_id)

def get_relic_desc(relic_id: str) -> str:
    return RELIC_CONFIG.get(relic_id, {}).get("desc", "")

def get_relic_rarity(relic_id: str) -> str:
    return RELIC_CONFIG.get(relic_id, {}).get("rarity", "common")

ALL_RELIC_IDS = list(RELIC_CONFIG.keys())
