from ...data.card_data import CARD_CONFIG
from .registry import CARD_CLASS_REGISTRY
import inspect

from . import neutral
from . import wizard
from . import legendary
from . import curse
from . import warrior
from . import duel

import copy

class CardRegistryDict(dict):
    def _lazy_load_card(self, key):
        from ...data.card_data import CARD_CONFIG
        if key in CARD_CONFIG:
            cfg = CARD_CONFIG[key]
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

            from ...models.state import Card
            from .registry import CARD_CLASS_REGISTRY
            import inspect
            if key in CARD_CLASS_REGISTRY:
                cls, decorator_kwargs = CARD_CLASS_REGISTRY[key]
            else:
                from .duel import get_duel_card_class
                cls = get_duel_card_class(key) or Card
                decorator_kwargs = {}

            inst_kwargs = {
                "id": key,
                "name": name,
                "color": color,
                "type": ctype,
                "cost_a": cost_a,
                "cost_ba": cost_ba,
                "desc": desc,
            }
            for prop in ("base_dmg", "heal_amount", "countdown", "amulet_desc", "minion_hp", "minion_atk", "exhaust", "damage_type"):
                if prop in cfg:
                    inst_kwargs[prop] = cfg[prop]
            inst_kwargs.update(decorator_kwargs)
            
            sig = inspect.signature(cls.__init__)
            has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            if has_kwargs:
                filtered = inst_kwargs
            else:
                filtered = {k: v for k, v in inst_kwargs.items() if k in sig.parameters}
            
            inst = cls(**filtered)
            inst.rarity = rarity
            inst.exhaust = exhaust
            inst.fleeting = fleeting
            inst.agile = agile
            inst.retain = retain
            inst.innate = cfg.get("innate", False)
            inst.ethereal = cfg.get("ethereal", False)
            inst.unplayable = cfg.get("unplayable", False)
            inst.damage_type = cfg.get("damage_type", "effect")
            inst.fragile = cfg.get("fragile", 0)
            if inst.fragile > 0:
                if " (易碎 " not in inst.name:
                    inst.name = f"{inst.name} (易碎 {inst.fragile})"
            self[key] = inst
            return inst
        return None

    def __getitem__(self, key):
        if isinstance(key, str) and ":replay:" in key:
            parts = key.rsplit(":replay:", 1)
            base_key = parts[0]
            replay_val = int(parts[1])
            base_card = self[base_key]
            replay_card = copy.copy(base_card)
            replay_card.id = key
            replay_card.replay = replay_val
            replay_card.name = base_card.name
            import re
            clean_desc = re.sub(r"重放 \d+。", "", base_card.desc)
            if clean_desc.endswith("。") or clean_desc.endswith("！"):
                replay_card.desc = clean_desc + f"重放 {replay_val}。"
            else:
                replay_card.desc = clean_desc + f"。重放 {replay_val}。"
            return replay_card

        if isinstance(key, str) and ":fragile:" in key:
            parts = key.split(":fragile:")
            base_key = parts[0]
            fragile_val = int(parts[1])
            base_card = self[base_key]
            fragile_card = copy.copy(base_card)
            fragile_card.id = key
            fragile_card.fragile = fragile_val
            clean_name = base_card.name
            if " (易碎 " in clean_name:
                clean_name = clean_name.split(" (易碎 ")[0]
            fragile_card.name = f"{clean_name} (易碎 {fragile_val})"
            import re
            fragile_card.desc = re.sub(r"易碎 \d+。", f"易碎 {fragile_val}。", base_card.desc)
            return fragile_card

        if isinstance(key, str) and key.endswith("+"):
            base_key = key[:-1]
            if base_key not in self:
                self._lazy_load_card(base_key)
            if base_key not in self:
                raise KeyError(key)
            base_card = super().__getitem__(base_key)
            upgraded_card = copy.copy(base_card)
            upgraded_card.id = key
            if " (易碎 " in upgraded_card.name:
                parts = upgraded_card.name.split(" (易碎 ")
                name_part = parts[0]
                fragile_part = " (易碎 " + parts[1]
                upgraded_card.name = name_part + "+" + fragile_part
            else:
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
        
        if key not in self:
            self._lazy_load_card(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        if isinstance(key, str) and key.endswith("+"):
            base_key = key[:-1]
            if super().__contains__(base_key):
                return True
            from ...data.card_data import CARD_CONFIG
            return base_key in CARD_CONFIG
        if super().__contains__(key):
            return True
        from ...data.card_data import CARD_CONFIG
        return key in CARD_CONFIG

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

    from ...models.state import Card
    if cid in CARD_CLASS_REGISTRY:
        cls, decorator_kwargs = CARD_CLASS_REGISTRY[cid]
    else:
        from .duel import get_duel_card_class
        cls = get_duel_card_class(cid) or Card
        decorator_kwargs = {}

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
        ALL_CARDS[cid].fragile = cfg.get("fragile", 0)
        if ALL_CARDS[cid].fragile > 0:
            if " (易碎 " not in ALL_CARDS[cid].name:
                ALL_CARDS[cid].name = f"{ALL_CARDS[cid].name} (易碎 {ALL_CARDS[cid].fragile})"
