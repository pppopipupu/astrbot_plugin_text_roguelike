from typing import Tuple, Generator

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

class ActionHandler:
    registry = {}

    def __init_subclass__(cls, actions: list[str] = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if actions:
            for action in actions:
                cls.registry[action] = cls()

    def execute(self, router, user_id: str, run, parts: list[str]) -> Tuple[str, bool]:
        raise NotImplementedError

class CommandHandler:
    registry = {}

    def __init_subclass__(cls, names: list[str] = None, allowed_states: list[str] = None, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.names = names or []
        cls.allowed_states = allowed_states if allowed_states is not None else ["menu", "town", "explore", "battle", "dialog"]
        if names:
            inst = cls()
            inst.names = cls.names
            inst.allowed_states = cls.allowed_states
            for name in names:
                cls.registry[name] = inst

    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        raise NotImplementedError
