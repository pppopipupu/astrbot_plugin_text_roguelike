from typing import Tuple, Optional
from ...models.state import GameRun

def split_by_comma_with_brackets(s: str) -> list[str]:
    parts = []
    current = []
    bracket_depth = 0
    for char in s:
        if char == '[':
            bracket_depth += 1
            current.append(char)
        elif char == ']':
            bracket_depth -= 1
            current.append(char)
        elif char == ',' and bracket_depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        parts.append("".join(current).strip())
    return [p for p in parts if p]

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
