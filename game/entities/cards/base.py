from ...data.card_data import CARD_CONFIG
from .registry import CARD_CLASS_REGISTRY
import inspect

from . import neutral
from . import wizard
from . import legendary
from . import curse

import copy

class CardRegistryDict(dict):
    def __getitem__(self, key):
        if isinstance(key, str) and key.endswith("+"):
            base_key = key[:-1]
            if base_key not in self:
                raise KeyError(key)
            base_card = super().__getitem__(base_key)
            upgraded_card = copy.copy(base_card)
            upgraded_card.id = key
            if not upgraded_card.name.endswith("+"):
                upgraded_card.name += "+"
            upgraded_card.upgraded = True
            
            from ...data.card_upgrade_data import CARD_UPGRADE_CONFIG
            up_cfg = CARD_UPGRADE_CONFIG.get(base_key, {})
            
            if "cost_a" in up_cfg:
                upgraded_card.cost_a = up_cfg["cost_a"]
            if "cost_ba" in up_cfg:
                upgraded_card.cost_ba = up_cfg["cost_ba"]
            if "desc" in up_cfg:
                upgraded_card.desc = up_cfg["desc"]
            if "innate" in up_cfg:
                upgraded_card.innate = up_cfg["innate"]
            if "exhaust" in up_cfg:
                upgraded_card.exhaust = up_cfg["exhaust"]
                
            for prop in ("base_dmg", "heal_amount", "shield_amount", "minion_hp", "minion_atk", "countdown", "amulet_desc"):
                if prop in up_cfg:
                    setattr(upgraded_card, prop, up_cfg[prop])
            return upgraded_card
        return super().__getitem__(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        if isinstance(key, str) and key.endswith("+"):
            return super().__contains__(key[:-1])
        return super().__contains__(key)

ALL_CARDS = CardRegistryDict()

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
        for key in ("base_dmg", "heal_amount", "countdown", "amulet_desc", "minion_hp", "minion_atk", "exhaust", "damage_type"):
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
        ALL_CARDS[cid].damage_type = cfg.get("damage_type", "effect")
