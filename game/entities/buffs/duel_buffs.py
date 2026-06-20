from typing import Optional
from .duel_registry import DUEL_BUFF_CLASS_REGISTRY
from .registry import BUFF_CLASS_REGISTRY
from . import buffs

DUEL_BUFF_CLASS_REGISTRY.update(BUFF_CLASS_REGISTRY)


class DuelBuffImpl:
    def __init__(self, stacks: int):
        self.stacks = stacks
        self.upgraded = False

def get_duel_buff_impl(buff_id: str, stacks: int, stacks2: Optional[int] = None) -> Optional[DuelBuffImpl]:
    upgraded = False
    if isinstance(buff_id, str) and buff_id.endswith("+"):
        upgraded = True
        buff_id = buff_id[:-1]
    if isinstance(buff_id, str) and buff_id.startswith("duel_"):
        buff_id = buff_id[5:]
    cls = DUEL_BUFF_CLASS_REGISTRY.get(buff_id)
    if cls:
        inst = cls(stacks)
        inst.stacks2 = stacks2
        inst.upgraded = upgraded
        return inst
    return None
