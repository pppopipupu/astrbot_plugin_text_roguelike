import random
from typing import Optional, List, Dict
from ..models.state import GameRun, PlayerState, EnemyState, MinionState, AmuletState, Card
from .explore_engine import ExploreEngine

class MapEngine:
    def __init__(self, save_manager, battle_engine):
        self.save_manager = save_manager
        self.battle_engine = battle_engine
        self.explore_engine = ExploreEngine(save_manager, self)

    def enter_next_stage(self, run: GameRun):
        p = run.player
        p.stage += 1
        if p.stage > 1:
            self.save_manager.record_stage_passed(run.user_id)
        p.shield = 0
        p.minions.clear()
        p.amulets.clear()
        p.abilities.clear()
        run.enemies.clear()
        run.node_data.clear()

        if "lucky_coin" in p.relics:
            p.gold += 5
        if "tax_contract" in p.relics:
            p.gold = max(0, p.gold - 6)

        if p.stage == 1:
            run.node_type = "start_ancient"
            style = random.choice(["default", "abyss", "glacier"])
            stats = self.save_manager.load_stats(run.user_id)
            p_class = getattr(stats, "selected_class", "法师")
            if p_class == "战士":
                relics_pool = [
                    {"type": "double", "relic": "mark_of_fury"},
                    {"type": "double", "relic": "greedy_contract"},
                    {"type": "double", "relic": "mask_of_void"},
                    {"type": "double", "relic": "unstable_crystal"},
                    {"type": "double", "relic": "vampiric_touch"},
                    {"type": "double", "relic": "ancient_page"}
                ]
                cards_pool = [
                    {"type": "contract", "relic": "rust_shackle", "card": "demon_form"},
                    {"type": "contract", "relic": "fool_oath", "card": "impervious"},
                    {"type": "contract", "relic": "blind_spot", "card": "demon_form"},
                    {"type": "contract", "relic": "tax_contract", "card": "impervious"}
                ]
                cards_pool.append({"type": "contract", "relic": "blind_spot", "card": "break_limits"})
                if getattr(stats, "killed_icerainboww", False):
                    cards_pool.append({"type": "contract", "relic": "wither_seed", "card": "minion_icerainboww"})
            else:
                if style == "default":
                    relics_pool = [
                        {"type": "double", "relic": "mark_of_fury"},
                        {"type": "double", "relic": "greedy_contract"},
                        {"type": "double", "relic": "mask_of_void"},
                        {"type": "double", "relic": "unstable_crystal"},
                        {"type": "double", "relic": "vampiric_touch"},
                        {"type": "double", "relic": "ancient_page"}
                    ]
                    cards_pool = [
                        {"type": "contract", "relic": "rust_shackle", "card": "doomsday_judgment"},
                        {"type": "contract", "relic": "fool_oath", "card": "time_warp"},
                        {"type": "contract", "relic": "wither_seed", "card": "magic_network"},
                        {"type": "contract", "relic": "blind_spot", "card": "meteor_swarm"},
                        {"type": "contract", "relic": "tax_contract", "card": "archmage_wish"}
                    ]
                    cards_pool.append({"type": "contract", "relic": "blind_spot", "card": "break_limits"})
                    if getattr(stats, "killed_icerainboww", False):
                        cards_pool.append({"type": "contract", "relic": "wither_seed", "card": "minion_icerainboww"})
                elif style == "abyss":
                    relics_pool = [
                        {"type": "double", "relic": "abyss_gaze"},
                        {"type": "double", "relic": "mark_of_fury"},
                        {"type": "double", "relic": "greedy_contract"},
                        {"type": "double", "relic": "abyss_contract"}
                    ]
                    cards_pool = [
                        {"type": "contract", "relic": "shadow_curse", "card": "abyss_collapse"},
                        {"type": "contract", "relic": "shadow_curse", "card": "demon_contract"},
                        {"type": "contract", "relic": "shadow_curse", "card": "abyss_erosion"},
                        {"type": "contract", "relic": "shadow_curse", "card": "abyss_altar"}
                    ]
                    cards_pool.append({"type": "contract", "relic": "shadow_curse", "card": "break_limits"})
                    if getattr(stats, "killed_icerainboww", False):
                        cards_pool.append({"type": "contract", "relic": "shadow_curse", "card": "minion_icerainboww"})
                else:
                    relics_pool = [
                        {"type": "double", "relic": "glacier_armor"},
                        {"type": "double", "relic": "unstable_crystal"},
                        {"type": "double", "relic": "vampiric_touch"},
                        {"type": "double", "relic": "glacier_core"}
                    ]
                    cards_pool = [
                        {"type": "contract", "relic": "glacier_chill", "card": "frost_nova"},
                        {"type": "contract", "relic": "glacier_chill", "card": "glacier_fortress"},
                        {"type": "contract", "relic": "glacier_chill", "card": "glacier_tempest"}
                    ]
                    cards_pool.append({"type": "contract", "relic": "glacier_chill", "card": "break_limits"})
                    if getattr(stats, "killed_icerainboww", False):
                        cards_pool.append({"type": "contract", "relic": "glacier_chill", "card": "minion_icerainboww"})
            
            num_relics = random.choice([1, 2])
            selected_relics = random.sample(relics_pool, min(len(relics_pool), num_relics))
            selected_cards = random.sample(cards_pool, min(len(cards_pool), 3 - len(selected_relics)))
            from ..models.state import check_and_replace_fireball
            for item in selected_cards:
                if "card" in item:
                    item["card"] = check_and_replace_fireball(run, item["card"])
            options = selected_relics + selected_cards
            random.shuffle(options)
            run.node_data = {"options": options, "style": style}
        elif p.stage == 11:
            run.node_type = "ancient"
            style = random.choice(["default", "abyss", "glacier"])
            stats = self.save_manager.load_stats(run.user_id)
            p_class = getattr(stats, "selected_class", "法师")
            if p_class == "战士":
                legends_pool = ["demon_form", "impervious"]
                relics_pool = ["ancient_eye", "gold_compass", "dragon_blood", "energy_core", "heavy_armor"]
            else:
                if style == "default":
                    legends_pool = ["doomsday_judgment", "time_warp", "magic_network", "meteor_swarm", "archmage_wish"]
                    relics_pool = ["ancient_eye", "gold_compass", "dragon_blood", "energy_core", "heavy_armor"]
                elif style == "abyss":
                    legends_pool = ["abyss_collapse", "demon_contract", "abyss_erosion", "abyss_altar"]
                    relics_pool = ["abyss_whisper", "gold_compass", "dragon_blood", "abyss_contract"]
                else:
                    legends_pool = ["frost_nova", "glacier_fortress", "glacier_tempest"]
                    relics_pool = ["frost_blade", "energy_core", "heavy_armor", "glacier_core"]
            
            legends_pool.append("break_limits")
            if getattr(stats, "killed_icerainboww", False):
                legends_pool.append("minion_icerainboww")
                
            available_relics = [r for r in relics_pool if r not in p.relics]
            if not available_relics:
                available_relics = relics_pool.copy()
            random.shuffle(legends_pool)
            random.shuffle(available_relics)
            options = []
            from ..models.state import check_and_replace_fireball
            for i in range(3):
                options.append({
                    "card": check_and_replace_fireball(run, legends_pool[i % len(legends_pool)]),
                    "relic": available_relics[i % len(available_relics)]
                })
            run.node_data = {"options": options, "style": style}
        elif p.stage == 20:
            run.node_type = "battle"
            self.battle_engine._init_battle_node(run, "boss")
        elif p.stage == 25:
            run.node_type = "battle"
            self.battle_engine._init_battle_node(run, "boss")
        else:
            if p.stage == 2:
                self._generate_map_network(run, 2, 10)
            elif p.stage == 12:
                self._generate_map_network(run, 12, 20)
            elif p.stage == 21:
                self._generate_map_network(run, 21, 25)
            
            run.node_type = "map_select"
            nodes_layer = run.map_data.get("nodes", {}).get(str(p.stage), [])
            curr_id = run.map_data.get("current_node_id")
            
            opts = []
            if not curr_id:
                opts = nodes_layer
            else:
                nodes_dict = {}
                for layer in run.map_data.get("nodes", {}).values():
                    for node in layer:
                        nodes_dict[node["id"]] = node
                curr_node = nodes_dict.get(curr_id)
                if curr_node:
                    next_ids = curr_node.get("next", [])
                    opts = [nodes_dict[nid] for nid in next_ids if nid in nodes_dict]
            
            if not opts and nodes_layer:
                opts = nodes_layer
                
            options_data = []
            desc_map = {
                "battle": "遭遇战 (遇到 1~3 个普通的敌人)",
                "elite": "精英战 (遭遇强力敌人，获胜金币更多)",
                "event": "神秘事件 (可能获得宝物或遭遇危险)",
                "shop": "奇妙商店 (购买强力卡牌、遗物或移除卡牌)",
                "rest": "篝火营地 (恢复生命值或冥想领悟卡牌)",
                "treasure": "古老宝箱 (献祭卡牌以获取稀有遗物及宝藏)",
                "boss": "首领战 (击败守关的首领)"
            }
            emoji_map = {
                "battle": "遭遇战",
                "elite": "精英战",
                "event": "神秘事件",
                "shop": "奇妙商店",
                "rest": "篝火营地",
                "treasure": "古老宝箱",
                "boss": "首领战"
            }
            for o in opts:
                options_data.append({
                    "node_id": o["id"],
                    "node_type": o["type"],
                    "desc": f"{emoji_map.get(o['type'], o['type'])} ({desc_map.get(o['type'], o['type'])})"
                })
            run.node_data = {"options": options_data}

    def _generate_map_network(self, run: GameRun, start_s: int, end_s: int):
        nodes = {}
        for s in range(start_s, end_s + 1):
            nodes[str(s)] = []
        
        types_pool = ["battle", "event", "shop", "elite", "rest"]
        for s in range(start_s, end_s + 1):
            s_str = str(s)
            if s in (5, 15, 23):
                nodes[s_str].append({
                    "id": f"{s}_0",
                    "type": "treasure",
                    "next": []
                })
            elif s in (10, 20, 25):
                nodes[s_str].append({
                    "id": f"{s}_0",
                    "type": "boss",
                    "next": []
                })
            else:
                width = random.randint(2, 3)
                for i in range(width):
                    ntype = random.choice(types_pool)
                    nodes[s_str].append({
                        "id": f"{s}_{i}",
                        "type": ntype,
                        "next": []
                    })
        
        for s in range(start_s, end_s):
            curr_layer = nodes[str(s)]
            next_layer = nodes[str(s+1)]
            
            if len(next_layer) == 1:
                for cn in curr_layer:
                    cn["next"] = [next_layer[0]["id"]]
            elif len(curr_layer) == 1:
                curr_layer[0]["next"] = [nn["id"] for nn in next_layer]
            else:
                for i, cn in enumerate(curr_layer):
                    allowed = []
                    for offset in (-1, 0, 1):
                        idx = i + offset
                        if 0 <= idx < len(next_layer):
                            allowed.append(next_layer[idx]["id"])
                    cn["next"] = random.sample(allowed, min(len(allowed), random.randint(1, 2)))
                
                for nn in next_layer:
                    nn_id = nn["id"]
                    has_pre = False
                    for cn in curr_layer:
                        if nn_id in cn["next"]:
                            has_pre = True
                            break
                    if not has_pre:
                        best_i = min(len(curr_layer)-1, int(nn_id.split("_")[1]))
                        curr_layer[best_i]["next"].append(nn_id)
                        curr_layer[best_i]["next"] = list(set(curr_layer[best_i]["next"]))
                        
        run.map_data["nodes"] = nodes
        run.map_data["current_node_id"] = None

    def choose_map_node(self, run: GameRun, option_idx: int) -> str:
        options = run.node_data.get("options", [])
        if option_idx < 1 or option_idx > len(options):
            return "❌ 无效的分支序号。"
        chosen = options[option_idx - 1]
        node_type = chosen["node_type"]
        node_id = chosen["node_id"]
        
        if node_type in ("battle", "elite", "boss"):
            run.node_type = "battle"
        else:
            run.node_type = node_type
        run.map_data["current_node_id"] = node_id
        run.node_data.clear()
        
        if node_type == "battle" or node_type == "boss":
            diff = "boss" if node_type == "boss" else "normal"
            self.battle_engine._init_battle_node(run, diff)
            name = run.enemies[0].name if run.enemies else "未知"
            num_enemies = len(run.enemies)
            self.save_manager.save_save(run.user_id, run)
            return self.battle_engine._append_logs_to_res(run, f"你选择前往【{chosen['desc']}】。前方出现了 {num_enemies} 个敌人，领头的是【{name}】！进入战斗。")
        elif node_type == "elite":
            self.battle_engine._init_battle_node(run, "elite")
            name = run.enemies[0].name if run.enemies else "未知"
            num_enemies = len(run.enemies)
            self.save_manager.save_save(run.user_id, run)
            return self.battle_engine._append_logs_to_res(run, f"你选择前往【{chosen['desc']}】。前方出现了 {num_enemies} 个强力精英，领头的是【{name}】！进入战斗。")
        elif node_type == "event":
            self.explore_engine._init_event_node(run)
            self.save_manager.save_save(run.user_id, run)
            return f"你选择前往【{chosen['desc']}】。你遇到了一个神秘事件..."
        elif node_type == "shop":
            self.explore_engine._init_shop_node(run)
            self.save_manager.save_save(run.user_id, run)
            return f"你选择前往【{chosen['desc']}】。你来到了奇妙商店，店主热情地向你招手。"
        elif node_type == "rest":
            self.save_manager.save_save(run.user_id, run)
            return f"你选择前往【{chosen['desc']}】。篝火在噼啪作响，你可以在此整顿休息。"
        elif node_type == "treasure":
            self.explore_engine._init_treasure_node(run)
            self.save_manager.save_save(run.user_id, run)
            return f"你选择前往【{chosen['desc']}】。你来到了古老宝箱前。"
        return "❌ 未知节点类型。"

    def _init_event_node(self, run: GameRun):
        self.explore_engine._init_event_node(run)

    def _init_shop_node(self, run: GameRun):
        self.explore_engine._init_shop_node(run)

    def _init_treasure_node(self, run: GameRun):
        self.explore_engine._init_treasure_node(run)

    def choose_option(self, run: GameRun, option_idx: int) -> str:
        if run.node_type == "battle":
            return "❌ 战斗中无法使用选择命令。"
        if run.node_type == "map_select":
            return self.choose_map_node(run, option_idx)
        return self.explore_engine.choose_option(run, option_idx)

    def remove_card_from_deck(self, run: GameRun, deck_idx: int) -> str:
        return self.explore_engine.remove_card_from_deck(run, deck_idx)

    def upgrade_card_in_deck(self, run: GameRun, deck_idx: int) -> str:
        return self.explore_engine.upgrade_card_in_deck(run, deck_idx)
