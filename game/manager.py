import os
import json
from dataclasses import asdict
from .models import GameRun, PlayerState, EnemyState, MinionState, AmuletState, BuffState

class SaveManager:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(os.path.dirname(current_dir), "data")
        else:
            self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def get_save_path(self, user_id: str) -> str:
        safe_id = "".join([c for c in user_id if c.isalnum() or c in ("-", "_")])
        return os.path.join(self.data_dir, f"user_{safe_id}.json")

    def load_save(self, user_id: str) -> GameRun:
        path = self.get_save_path(user_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            return self.from_dict(d)
        except:
            return None

    def save_save(self, user_id: str, run: GameRun) -> bool:
        path = self.get_save_path(user_id)
        try:
            d = self.to_dict(run)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

    def delete_save(self, user_id: str) -> bool:
        path = self.get_save_path(user_id)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except:
                return False
        return False

    def to_dict(self, run: GameRun) -> dict:
        if not run:
            return {}
        return asdict(run)

    def from_dict(self, d: dict) -> GameRun:
        if not d:
            return None
        
        p_data = d["player"]
        p_minions = {}
        for k, v in p_data.get("minions", {}).items():
            m_buffs = []
            for b in v.get("buffs", []):
                m_buffs.append(BuffState(
                    id=b["id"],
                    name=b["name"],
                    stacks=b.get("stacks", 1),
                    desc=b.get("desc", "")
                ))
            p_minions[k] = MinionState(
                id=v["id"],
                name=v["name"],
                hp=v["hp"],
                max_hp=v["max_hp"],
                atk=v["atk"],
                actions=v.get("actions", 1),
                bonus_actions=v.get("bonus_actions", 1),
                attack_actions=v.get("attack_actions", 1),
                buffs=m_buffs
            )
        p_amulets = {k: AmuletState(**v) for k, v in p_data.get("amulets", {}).items()}
        p_buffs = []
        for b in p_data.get("buffs", []):
            p_buffs.append(BuffState(
                id=b["id"],
                name=b["name"],
                stacks=b.get("stacks", 1),
                desc=b.get("desc", "")
            ))
        player = PlayerState(
            hp=p_data["hp"],
            max_hp=p_data["max_hp"],
            shield=p_data["shield"],
            gold=p_data["gold"],
            stage=p_data["stage"],
            deck=p_data.get("deck", []),
            draw_pile=p_data.get("draw_pile", []),
            discard_pile=p_data.get("discard_pile", []),
            exhaust_pile=p_data.get("exhaust_pile", []),
            graveyard=p_data.get("graveyard", []),
            hand=p_data.get("hand", []),
            actions=p_data.get("actions", 1),
            bonus_actions=p_data.get("bonus_actions", 1),
            minions=p_minions,
            amulets=p_amulets,
            abilities=p_data.get("abilities", []),
            fold_guide=p_data.get("fold_guide", False),
            buffs=p_buffs
        )
        
        enemies = []
        if "enemies" in d:
            for ed in d["enemies"]:
                e_buffs = []
                for b in ed.get("buffs", []):
                    e_buffs.append(BuffState(
                        id=b["id"],
                        name=b["name"],
                        stacks=b.get("stacks", 1),
                        desc=b.get("desc", "")
                    ))
                enemies.append(EnemyState(
                    name=ed["name"],
                    hp=ed["hp"],
                    max_hp=ed["max_hp"],
                    shield=ed["shield"],
                    intent_type=ed.get("intent_type", ""),
                    intent_val=ed.get("intent_val", 0),
                    intent_desc=ed.get("intent_desc", ""),
                    actions=ed.get("actions", 1),
                    bonus_actions=ed.get("bonus_actions", 1),
                    buffs=e_buffs,
                    is_summon=ed.get("is_summon", False),
                    max_actions=ed.get("max_actions", 1),
                    max_bonus_actions=ed.get("max_bonus_actions", 0),
                    intent_a_type=ed.get("intent_a_type", ""),
                    intent_a_val=ed.get("intent_a_val", 0),
                    intent_a_desc=ed.get("intent_a_desc", ""),
                    intent_ba_type=ed.get("intent_ba_type", ""),
                    intent_ba_val=ed.get("intent_ba_val", 0),
                    intent_ba_desc=ed.get("intent_ba_desc", ""),
                    intent_ba2_type=ed.get("intent_ba2_type", ""),
                    intent_val_ba2=ed.get("intent_ba2_val", 0),
                    intent_ba2_desc=ed.get("intent_ba2_desc", "")
                ))
            
        return GameRun(
            user_id=d["user_id"],
            node_type=d["node_type"],
            player=player,
            enemies=enemies,
            node_data=d.get("node_data", {})
        )
