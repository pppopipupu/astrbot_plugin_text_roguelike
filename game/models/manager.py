import os
import json
from dataclasses import asdict
from .state import GameRun, PlayerState, EnemyState, MinionState, AmuletState, BuffState, UserStats, current_user_id, register_stat_recorder, get_user_id

class SaveManager:
    _default_data_dir = None

    def __init__(self, data_dir: str = None):
        if data_dir is not None:
            SaveManager._default_data_dir = data_dir
            self.data_dir = data_dir
        else:
            if SaveManager._default_data_dir is not None:
                self.data_dir = SaveManager._default_data_dir
            else:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                self.data_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "data")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def get_save_path(self, user_id: str) -> str:
        safe_id = "".join([c for c in user_id if c.isalnum() or c in ("-", "_")])
        return os.path.join(self.data_dir, f"user_{safe_id}.json")

    def get_stats_path(self, user_id: str) -> str:
        safe_id = "".join([c for c in user_id if c.isalnum() or c in ("-", "_")])
        return os.path.join(self.data_dir, f"stats_{safe_id}.json")

    def load_stats(self, user_id: str) -> UserStats:
        path = self.get_stats_path(user_id)
        if not os.path.exists(path):
            return UserStats()
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            return UserStats(
                total_damage=d.get("total_damage", 0),
                total_kills=d.get("total_kills", 0),
                total_stages=d.get("total_stages", 0),
                rogue_mode=d.get("rogue_mode", False),
                gp=d.get("gp", 0),
                unlocked_subclasses=d.get("unlocked_subclasses", []),
                selected_class=d.get("selected_class", "法师"),
                selected_subclass=d.get("selected_subclass", ""),
                killed_icerainboww=d.get("killed_icerainboww", False)
            )
        except:
            return UserStats()

    def save_stats(self, user_id: str, stats: UserStats) -> bool:
        path = self.get_stats_path(user_id)
        try:
            d = asdict(stats)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

    def record_damage(self, user_id: str, amount: int):
        if not user_id or amount <= 0:
            return
        stats = self.load_stats(user_id)
        stats.total_damage += amount
        self.save_stats(user_id, stats)

    def record_kill(self, user_id: str):
        if not user_id:
            return
        stats = self.load_stats(user_id)
        stats.total_kills += 1
        self.save_stats(user_id, stats)

    def record_stage_passed(self, user_id: str):
        if not user_id:
            return
        stats = self.load_stats(user_id)
        stats.total_stages += 1
        self.save_stats(user_id, stats)

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
        logs = None
        if run.node_data is not None:
            logs = run.node_data.pop("battle_logs", None)
        try:
            res = asdict(run)
        finally:
            if logs is not None and run.node_data is not None:
                run.node_data["battle_logs"] = logs
        return res

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
        minion_gy = list(p_data.get("minion_graveyard", []))
        enemy_gy = list(p_data.get("enemy_graveyard", []))
        if not minion_gy and not enemy_gy and "graveyard" in p_data:
            for item in p_data["graveyard"]:
                if item.startswith("minion:"):
                    minion_gy.append(item[len("minion:"):])
                elif item.startswith("enemy:"):
                    enemy_gy.append(item[len("enemy:"):])
                else:
                    enemy_gy.append(item)
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
            minion_graveyard=minion_gy,
            enemy_graveyard=enemy_gy,
            hand=p_data.get("hand", []),
            actions=p_data.get("actions", 1),
            bonus_actions=p_data.get("bonus_actions", 1),
            minions=p_minions,
            amulets=p_amulets,
            abilities=p_data.get("abilities", []),
            fold_guide=p_data.get("fold_guide", False),
            buffs=p_buffs,
            relics=p_data.get("relics", []),
            subclass=p_data.get("subclass", "")
        )
        
        enemies = []
        if "enemies" in d:
            from .state import EnemyIntentState
            for ed in d["enemies"]:
                e_buffs = []
                for b in ed.get("buffs", []):
                    e_buffs.append(BuffState(
                        id=b["id"],
                        name=b["name"],
                        stacks=b.get("stacks", 1),
                        desc=b.get("desc", "")
                    ))
                intent_list = []
                if "intents" in ed:
                    for it in ed["intents"]:
                        intent_list.append(EnemyIntentState(
                            type=it.get("type", ""),
                            val=it.get("val", 0),
                            desc=it.get("desc", ""),
                            cost_a=it.get("cost_a", 1),
                            cost_ba=it.get("cost_ba", 0),
                            cancelled=it.get("cancelled", False),
                            cancelled_desc=it.get("cancelled_desc", "")
                        ))
                enemies.append(EnemyState(
                    name=ed["name"],
                    hp=ed["hp"],
                    max_hp=ed["max_hp"],
                    shield=ed["shield"],
                    actions=ed.get("actions", 1),
                    bonus_actions=ed.get("bonus_actions", 1),
                    buffs=e_buffs,
                    is_summon=ed.get("is_summon", False),
                    max_actions=ed.get("max_actions", 1),
                    max_bonus_actions=ed.get("max_bonus_actions", 0),
                    intents=intent_list,
                    intent_type=ed.get("intent_type", ""),
                    intent_val=ed.get("intent_val", 0),
                    intent_desc=ed.get("intent_desc", ""),
                    intent_a_type=ed.get("intent_a_type", ""),
                    intent_a_val=ed.get("intent_a_val", 0),
                    intent_a_desc=ed.get("intent_a_desc", ""),
                    intent_a2_type=ed.get("intent_a2_type", ""),
                    intent_a2_val=ed.get("intent_a2_val", 0),
                    intent_a2_desc=ed.get("intent_a2_desc", ""),
                    intent_ba_type=ed.get("intent_ba_type", ""),
                    intent_ba_val=ed.get("intent_ba_val", 0),
                    intent_ba_desc=ed.get("intent_ba_desc", ""),
                    intent_ba2_type=ed.get("intent_ba2_type", ""),
                    intent_ba2_val=ed.get("intent_ba2_val", 0),
                    intent_ba2_desc=ed.get("intent_ba2_desc", "")
                ))
            
        return GameRun(
            user_id=d["user_id"],
            node_type=d["node_type"],
            player=player,
            enemies=enemies,
            node_data=d.get("node_data", {}),
            map_data=d.get("map_data", {})
        )

    def settle_game_and_delete(self, user_id: str, run: GameRun, is_victory: bool = False) -> str:
        if not run or not run.player:
            self.delete_save(user_id)
            return "本局结算：未找到有效的角色进度，未获得 GP。"
        stage = run.player.stage
        gold = run.player.gold
        if stage < 5:
            self.delete_save(user_id)
            return f"本局结算：由于在第 {stage} 层结束，未获得 GP。"
        gp_gained = gold * 10
        victory_bonus = ""
        unlock_msg = ""
        if is_victory:
            gp_gained += 1000
            victory_bonus = "（含通关奖励 1000 GP）"
            if run.node_data.get("boss_name") == "Icerainboww":
                unlock_msg = "\n\n🎉 特别提示：你成功击败了最终BOSS【Icerainboww】！在先古祭坛和先古赐福石碑中已永久解锁传奇随从卡【Icerainboww】！"
        stats = self.load_stats(user_id)
        stats.gp += gp_gained
        self.save_stats(user_id, stats)
        self.delete_save(user_id)
        return f"本局结算：剩余金币 {gold}，折算获得 {gp_gained} GP{victory_bonus}！当前总 GP：{stats.gp}。{unlock_msg}"

    def get_admin_config_path(self) -> str:
        return os.path.join(self.data_dir, "admin_config.json")

    def load_admin_config(self) -> dict:
        path = self.get_admin_config_path()
        if not os.path.exists(path):
            return {"final_boss": "random"}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"final_boss": "random"}

    def save_admin_config(self, cfg: dict) -> bool:
        path = self.get_admin_config_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

def stat_recorder_callback(enemy_name: str, amount: int, is_defeat: bool):
    user_id = get_user_id()
    if not user_id:
        return
    mgr = SaveManager()
    if amount > 0:
        mgr.record_damage(user_id, amount)
    if is_defeat:
        mgr.record_kill(user_id)

register_stat_recorder(stat_recorder_callback)
