from typing import Generator

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
