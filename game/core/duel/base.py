from typing import Tuple, Optional
from ...models.state import GameRun

class DuelCommandHandler:
    registry = {}

    def __init_subclass__(cls, names: list[str] = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if names:
            for name in names:
                cls.registry[name.lower()] = cls()

    def execute(self, router, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        raise NotImplementedError

class DuelActionHandler:
    registry = {}

    def __init_subclass__(cls, names: list[str] = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if names:
            for name in names:
                cls.registry[name.lower()] = cls()

    def execute(self, router, run: GameRun, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        raise NotImplementedError
