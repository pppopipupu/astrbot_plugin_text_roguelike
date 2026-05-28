from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from contextvars import ContextVar
import sys

if not hasattr(sys, "_rogue_current_user_id"):
    sys._rogue_current_user_id = ContextVar("current_user_id", default="")
if not hasattr(sys, "_rogue_fallback_user_id"):
    sys._rogue_fallback_user_id = ""

current_user_id = sys._rogue_current_user_id

def set_user_id(user_id: str):
    current_user_id.set(user_id)
    sys._rogue_fallback_user_id = user_id

def get_user_id() -> str:
    val = current_user_id.get()
    if not val:
        return getattr(sys, "_rogue_fallback_user_id", "")
    return val

@dataclass
class UserStats:
    total_damage: int = 0
    total_kills: int = 0
    total_stages: int = 0

_stat_recorder = None

def register_stat_recorder(recorder):
    global _stat_recorder
    _stat_recorder = recorder

@dataclass
class BuffState:
    id: str
    name: str
    stacks: int = 1
    desc: str = ""

@dataclass
class Card:
    id: str
    name: str
    color: str
    type: str
    cost_a: int
    cost_ba: int
    countdown: int = 0
    desc: str = ""
    exhaust: bool = False
    rarity: str = "common"
    fleeting: bool = False
    agile: bool = False
    retain: bool = False

    def execute(self, run: 'GameRun', target: Optional[str] = None, engine = None) -> str:
        return ""

    def special_action(self, run: 'GameRun', target: Optional[str] = None) -> str:
        return f"激活了【{self.name}】的特殊行动！"

@dataclass
class MinionState:
    id: str
    name: str
    hp: int
    max_hp: int
    atk: int
    actions: int
    bonus_actions: int
    attack_actions: int = 1
    buffs: List[BuffState] = field(default_factory=list)

@dataclass
class AmuletState:
    id: str
    name: str
    countdown: int
    desc: str

@dataclass
class PlayerState:
    hp: int
    max_hp: int
    shield: int
    gold: int
    stage: int
    deck: List[str] = field(default_factory=list)
    draw_pile: List[str] = field(default_factory=list)
    discard_pile: List[str] = field(default_factory=list)
    exhaust_pile: List[str] = field(default_factory=list)
    graveyard: List[str] = field(default_factory=list)
    hand: List[str] = field(default_factory=list)
    actions: int = 1
    bonus_actions: int = 1
    minions: Dict[str, MinionState] = field(default_factory=dict)
    amulets: Dict[str, AmuletState] = field(default_factory=dict)
    abilities: List[str] = field(default_factory=list)
    fold_guide: bool = False
    buffs: List[BuffState] = field(default_factory=list)
    relics: List[str] = field(default_factory=list)

@dataclass
class EnemyState:
    name: str
    hp: int
    max_hp: int
    shield: int
    intent_type: str = ""
    intent_val: int = 0
    intent_desc: str = ""
    actions: int = 1
    bonus_actions: int = 1
    buffs: List[BuffState] = field(default_factory=list)
    is_summon: bool = False
    max_actions: int = 1
    max_bonus_actions: int = 0
    intent_a_type: str = ""
    intent_a_val: int = 0
    intent_a_desc: str = ""
    intent_ba_type: str = ""
    intent_ba_val: int = 0
    intent_ba_desc: str = ""
    intent_ba2_type: str = ""
    intent_ba2_val: int = 0
    intent_ba2_desc: str = ""

    def __setattr__(self, key, value):
        if key == "hp":
            try:
                old_hp = self.__dict__.get("hp")
            except AttributeError:
                old_hp = None
            if old_hp is not None and value < old_hp:
                dmg = old_hp - value
                if _stat_recorder:
                    _stat_recorder(self.name, dmg, (value <= 0 and old_hp > 0))
        elif key == "shield":
            try:
                old_shield = self.__dict__.get("shield")
            except AttributeError:
                old_shield = None
            if old_shield is not None and value < old_shield:
                dmg = old_shield - value
                if _stat_recorder:
                    _stat_recorder(self.name, dmg, False)
        super().__setattr__(key, value)

@dataclass
class GameRun:
    user_id: str
    node_type: str
    player: PlayerState
    enemies: List[EnemyState] = field(default_factory=list)
    node_data: Dict = field(default_factory=dict)
    map_data: Dict = field(default_factory=dict)
