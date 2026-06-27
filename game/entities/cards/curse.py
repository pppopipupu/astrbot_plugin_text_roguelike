from typing import Optional
from ...models.state import Card
from .registry import register_card

@register_card("curse_dazed")
@register_card("curse_agony")
@register_card("curse_dimensional_tear")
@register_card("curse_wound")
class CurseCard(Card):
    def execute(self, run, target, engine) -> str:
        return "该卡牌不能被打出。"

@register_card("curse_indigestion")
class IndigestionCurse(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        p.bonus_actions = max(0, p.bonus_actions - 1)
        return "你忍受着消化不良，动作变得迟缓（流失了 1 个额外动作点）。"

@register_card("curse_mana_backflow")
class ManaBackflowCurse(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        p.hp = max(1, p.hp - 8)
        return "法力逆流撕裂了你的身体（流失了 8 点生命值）。"

@register_card("curse_intangible_whisper")
class IntangibleWhisperCurse(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["draw_penalty_next_turn"] = run.node_data.get("draw_penalty_next_turn", 0) + 3
        return "你忍受着耳边的无形低语，精神极度动摇（在下一回合，你抽取的卡牌数将减少 3 张）。"

