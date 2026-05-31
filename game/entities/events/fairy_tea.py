import random
from .base import EventOption
from ..cards import ALL_CARDS

class DrinkNectarOption(EventOption, action="drink_nectar", text="饮用红色花蜜茶"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        if "wither_seed" not in p.relics:
            p.hp = min(p.max_hp, p.hp + 12)
            res = "🌸 你饮下了甜美的红色花蜜茶，感到浑身暖洋洋的，生命值回复了 12 点。"
        else:
            res = "🌸 你饮下了甜美的红色花蜜茶，口感很好，但因为有枯萎之种，你没有获得任何治疗效果。"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return res

class EatCookieOption(EventOption, action="eat_cookie", text="享用绿色坚果饼"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.max_hp += 4
        p.hp += 4
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "🍪 你享用了绿色坚果饼。这奇妙的茶点永久提升了你的生命力，最大生命值上限 +4 且当前生命值 +4。"

class ListenMusicOption(EventOption, action="listen_music", text="倾听妖精的八音盒"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        agile_cards = [cid for cid, c in ALL_CARDS.items() if getattr(c, "agile", False) and not cid.startswith("curse_")]
        got_card = random.choice(agile_cards) if agile_cards else "agile_strike"
        p.deck.append(got_card)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return f"🎵 你闭上双眼，静静倾听妖精的八音盒。美妙的旋律启发了你的身手，你获得了灵巧卡牌【{ALL_CARDS[got_card].name}】。"
