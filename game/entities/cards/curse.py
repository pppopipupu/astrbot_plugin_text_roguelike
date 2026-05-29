from typing import Optional
from ...models.state import Card
from .registry import register_card

@register_card("curse_dazed")
@register_card("curse_agony")
class CurseCard(Card):
    def execute(self, run, target, engine) -> str:
        return "该卡牌不能被打出。"
