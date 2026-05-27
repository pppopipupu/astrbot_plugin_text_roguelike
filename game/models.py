from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

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

@dataclass
class GameRun:
    user_id: str
    node_type: str
    player: PlayerState
    enemies: List[EnemyState] = field(default_factory=list)
    node_data: Dict = field(default_factory=dict)
