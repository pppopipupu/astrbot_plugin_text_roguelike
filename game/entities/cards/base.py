from ...data.card_data import CARD_CONFIG
from .registry import CARD_CLASS_REGISTRY
import inspect

from . import neutral
from . import wizard
from . import legendary
from . import curse

ALL_CARDS = {}

for cid, cfg in CARD_CONFIG.items():
    name = cfg["name"]
    color = cfg["color"]
    ctype = cfg["type"]
    cost_a = cfg["cost_a"]
    cost_ba = cfg["cost_ba"]
    desc = cfg["desc"]
    rarity = cfg.get("rarity", "common")
    exhaust = cfg.get("exhaust", False)
    fleeting = cfg.get("fleeting", False)
    agile = cfg.get("agile", False)
    retain = cfg.get("retain", False)

    if cid in CARD_CLASS_REGISTRY:
        cls, decorator_kwargs = CARD_CLASS_REGISTRY[cid]
        inst_kwargs = {
            "id": cid,
            "name": name,
            "color": color,
            "type": ctype,
            "cost_a": cost_a,
            "cost_ba": cost_ba,
            "desc": desc,
        }
        for key in ("base_dmg", "heal_amount", "countdown", "amulet_desc", "minion_hp", "minion_atk", "exhaust"):
            if key in cfg:
                inst_kwargs[key] = cfg[key]
        inst_kwargs.update(decorator_kwargs)
        
        sig = inspect.signature(cls.__init__)
        has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
        if has_kwargs:
            filtered = inst_kwargs
        else:
            filtered = {k: v for k, v in inst_kwargs.items() if k in sig.parameters}
        ALL_CARDS[cid] = cls(**filtered)

    if cid in ALL_CARDS:
        ALL_CARDS[cid].rarity = rarity
        ALL_CARDS[cid].exhaust = exhaust
        ALL_CARDS[cid].fleeting = fleeting
        ALL_CARDS[cid].agile = agile
        ALL_CARDS[cid].retain = retain
        ALL_CARDS[cid].innate = cfg.get("innate", False)
        ALL_CARDS[cid].ethereal = cfg.get("ethereal", False)
        ALL_CARDS[cid].unplayable = cfg.get("unplayable", False)
