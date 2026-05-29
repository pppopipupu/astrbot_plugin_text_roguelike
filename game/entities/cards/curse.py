from typing import Optional
from ...models.state import Card

class CurseCard(Card):
    def execute(self, run, target, engine) -> str:
        return "该卡牌不能被打出。"
