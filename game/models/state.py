from dataclasses import dataclass, field
from typing import List, Dict, Optional
from contextvars import ContextVar
from enum import Enum
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

class DamageType(Enum):
    ACID = "acid"
    BLUDGEONING = "bludgeoning"
    COLD = "cold"
    FIRE = "fire"
    FORCE = "force"
    LIGHTNING = "lightning"
    NECROTIC = "necrotic"
    PIERCING = "piercing"
    POISON = "poison"
    PSYCHIC = "psychic"
    RADIANT = "radiant"
    SLASHING = "slashing"
    THUNDER = "thunder"
    TRUE = "true"

@dataclass
class UserStats:
    total_damage: int = 0
    total_kills: int = 0
    total_stages: int = 0
    rogue_mode: bool = False
    gp: int = 0
    unlocked_subclasses: List[str] = field(default_factory=list)
    selected_class: str = "法师"
    selected_subclass: str = ""
    killed_icerainboww: bool = False
    unlocked_gatekey: bool = False
    killed_yog_sothoth: bool = False


if not hasattr(sys, "_rogue_stat_recorder"):
    sys._rogue_stat_recorder = None

def register_stat_recorder(recorder):
    sys._rogue_stat_recorder = recorder

@dataclass
class BuffState:
    id: str
    name: str
    stacks: int = 1
    stacks2: Optional[int] = None
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
    innate: bool = False
    ethereal: bool = False
    unplayable: bool = False
    damage_type: str = "effect"
    upgraded: bool = False
    fragile: int = 0

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
    minion_graveyard: List[str] = field(default_factory=list)
    enemy_graveyard: List[str] = field(default_factory=list)
    hand: List[str] = field(default_factory=list)
    actions: int = 1
    bonus_actions: int = 1
    minions: Dict[str, MinionState] = field(default_factory=dict)
    amulets: Dict[str, AmuletState] = field(default_factory=dict)
    abilities: List[str] = field(default_factory=list)
    fold_guide: bool = False
    buffs: List[BuffState] = field(default_factory=list)
    relics: List[str] = field(default_factory=list)
    subclass: str = ""
    selected_class: str = "法师"

@dataclass
class EnemyIntentState:
    type: str = ""
    val: int = 0
    desc: str = ""
    cost_a: int = 1
    cost_ba: int = 0
    cancelled: bool = False
    cancelled_desc: str = ""

@dataclass
class EnemyState:
    name: str
    hp: int
    max_hp: int
    shield: int
    actions: int = 1
    bonus_actions: int = 1
    buffs: List[BuffState] = field(default_factory=list)
    is_summon: bool = False
    max_actions: int = 1
    max_bonus_actions: int = 0
    intents: List[EnemyIntentState] = field(default_factory=list)
    intent_type: str = ""
    intent_val: int = 0
    intent_desc: str = ""
    intent_a_type: str = ""
    intent_a_val: int = 0
    intent_a_desc: str = ""
    intent_a2_type: str = ""
    intent_a2_val: int = 0
    intent_a2_desc: str = ""
    intent_ba_type: str = ""
    intent_ba_val: int = 0
    intent_ba_desc: str = ""
    intent_ba2_type: str = ""
    intent_ba2_val: int = 0
    intent_ba2_desc: str = ""

    def __post_init__(self):
        if not self.intents:
            if self.intent_type or self.intent_desc:
                self.intents.append(EnemyIntentState(
                    type=self.intent_type,
                    val=self.intent_val,
                    desc=self.intent_desc,
                    cost_a=1,
                    cost_ba=0
                ))
            else:
                if self.intent_a_desc:
                    self.intents.append(EnemyIntentState(
                        type=self.intent_a_type,
                        val=self.intent_a_val,
                        desc=self.intent_a_desc,
                        cost_a=1,
                        cost_ba=0
                    ))
                if self.intent_a2_desc:
                    self.intents.append(EnemyIntentState(
                        type=self.intent_a2_type,
                        val=self.intent_a2_val,
                        desc=self.intent_a2_desc,
                        cost_a=1,
                        cost_ba=0
                    ))
                if self.intent_ba_desc:
                    self.intents.append(EnemyIntentState(
                        type=self.intent_ba_type,
                        val=self.intent_ba_val,
                        desc=self.intent_ba_desc,
                        cost_a=0,
                        cost_ba=1
                    ))
                if self.intent_ba2_desc:
                    self.intents.append(EnemyIntentState(
                        type=self.intent_ba2_type,
                        val=self.intent_ba2_val,
                        desc=self.intent_ba2_desc,
                        cost_a=0,
                        cost_ba=1
                    ))

    def __setattr__(self, key, value):
        if key == "hp":
            try:
                old_hp = self.__dict__.get("hp")
            except AttributeError:
                old_hp = None
            if old_hp is not None and value < old_hp:
                dmg = old_hp - value
                if getattr(sys, "_rogue_stat_recorder", None):
                    sys._rogue_stat_recorder(self.name, dmg, (value <= 0 and old_hp > 0))
        elif key == "shield":
            try:
                old_shield = self.__dict__.get("shield")
            except AttributeError:
                old_shield = None
            if old_shield is not None and value < old_shield:
                dmg = old_shield - value
                if getattr(sys, "_rogue_stat_recorder", None):
                    sys._rogue_stat_recorder(self.name, dmg, False)
        super().__setattr__(key, value)

@dataclass
class GameRun:
    user_id: str
    node_type: str
    player: PlayerState
    enemies: List[EnemyState] = field(default_factory=list)
    node_data: Dict = field(default_factory=dict)
    map_data: Dict = field(default_factory=dict)

def check_and_replace_fireball(run: 'GameRun', card_id: str) -> str:
    import random
    if getattr(run.player, "subclass", "") == "塑能法师" and card_id == "fireball":
        if random.random() < 0.40:
            return "meteor_swarm"
    return card_id
