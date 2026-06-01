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
