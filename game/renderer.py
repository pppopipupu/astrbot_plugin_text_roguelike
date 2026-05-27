from .models import GameRun, PlayerState, EnemyState, MinionState, AmuletState
from .cards import ALL_CARDS, MINION_SKILLS

class GameRenderer:
    @staticmethod
    def render_menu() -> str:
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            "🔮 魔法肉鸽卡牌游戏 (DND 5.5E 法师篇)",
            "",
            "一款使用纯文字游玩的策略肉鸽卡牌游戏。",
            "每回合拥有 1 个动作 (A) 和 1 个附赠动作 (BA)。",
            "召唤随从和护符可帮助战斗。随从拥有独立的动作，需手动指挥！",
            "",
            "【开始游戏】",
            "👉 /rogue 开启  -- 开始一局新游戏",
            "",
            "【其他命令】",
            "👉 /rogue 总览  -- 查看全部卡牌信息",
            "👉 /rogue 状态  -- 查看当前局内状态",
            "👉 /rogue 牌组  -- 查看当前拥有的卡组",
            "👉 /rogue 放弃  -- 放弃当前局内游戏",
            "━━━━━━━━━━━━━━━━━━━━"
        ]
        return "\n".join(lines)

    @staticmethod
    def render_card_library() -> str:
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            "📜 魔法肉鸽卡牌总览",
            ""
        ]
        
        neutrals = []
        blue_spells = []
        
        for cid, card in ALL_CARDS.items():
            cost_str = ""
            if card.cost_a > 0:
                cost_str += f"{card.cost_a}A "
            if card.cost_ba > 0:
                cost_str += f"{card.cost_ba}BA "
            cost_str = cost_str.strip() or "免费"
            
            type_ch = ""
            if card.type == "spell":
                type_ch = "法术"
            elif card.type == "amulet":
                type_ch = f"护符(吟唱 {card.countdown})"
            elif card.type == "ability":
                type_ch = "能力"
            elif card.type == "minion":
                type_ch = "随从"
                
            rarity_map = {
                "common": "普通",
                "rare": "稀有",
                "epic": "珍奇",
                "legendary": "传奇",
                "mythic": "神器"
            }
            rname = rarity_map.get(getattr(card, "rarity", "common"), "普通")
            info = f"• {card.name} [{type_ch}] <{rname}> 消耗: {cost_str} - {card.desc}"
            if card.color == "neutral":
                neutrals.append(info)
            else:
                blue_spells.append(info)
                
        lines.append("【无色卡牌（中立）】")
        lines.extend(neutrals)
        lines.append("")
        lines.append("【蓝色卡牌（法师）】")
        lines.extend(blue_spells)
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    @staticmethod
    def render_deck(run: GameRun) -> str:
        if not run or not run.player:
            return "❌ 你当前没有正在进行的游戏。输入 /rogue 开启 开始新游戏。"
        
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            "📜 当前拥有的卡组 (共 %d 张)" % len(run.player.deck),
            ""
        ]
        
        counts = {}
        for cid in run.player.deck:
            counts[cid] = counts.get(cid, 0) + 1
            
        idx = 1
        for cid, count in sorted(counts.items()):
            card = ALL_CARDS.get(cid)
            if card:
                color_type = "🔵" if card.color == "wizard" else "⚪"
                rarity_map = {
                    "common": "普通",
                    "rare": "稀有",
                    "epic": "珍奇",
                    "legendary": "传奇",
                    "mythic": "神器"
                }
                rname = rarity_map.get(getattr(card, "rarity", "common"), "普通")
                lines.append(f"{idx}. {color_type} {card.name} <{rname}> x{count} ({card.desc})")
                idx += 1
                
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    @staticmethod
    def render_game(run: GameRun) -> str:
        if not run:
            return GameRenderer.render_menu()
            
        p = run.player
        
        if run.node_type == "battle":
            return GameRenderer._render_battle(run)
        elif run.node_type == "event":
            return GameRenderer._render_event(run)
        elif run.node_type == "shop":
            return GameRenderer._render_shop(run)
        elif run.node_type == "rest":
            return GameRenderer._render_rest(run)
        elif run.node_type == "reward":
            return GameRenderer._render_reward(run)
        elif run.node_type == "map_select":
            return GameRenderer._render_map_select(run)
        elif run.node_type == "start_ancient":
            return GameRenderer._render_start_ancient(run)
        elif run.node_type == "ancient":
            return GameRenderer._render_ancient(run)
        elif run.node_type == "treasure":
            return GameRenderer._render_treasure(run)
        
        return "未知关卡状态"

    @staticmethod
    def _render_battle(run: GameRun) -> str:
        p = run.player
        will_buff = next((b for b in p.buffs if b.id == "iron_will"), None)
        will_stacks = will_buff.stacks if will_buff else 0
        cur_max = p.max_hp + will_stacks * 10
        
        relics_str = ""
        if p.relics:
            from .relic_impl import get_relic_name
            relics_str = "\n🎒 遗物：" + " ".join([f"【{get_relic_name(r)}】" for r in p.relics])
            
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            f"⚔️ 【第 {p.stage} 关：战斗阶段】",
            f"玩家：❤️ HP {p.hp}/{cur_max} | 🛡️ 护盾 {p.shield} | ⚡ 动作 {p.actions}A {p.bonus_actions}BA" + relics_str
        ]
        
        if p.buffs:
            buff_strs = []
            for b in p.buffs:
                if b.stacks > 1:
                    buff_strs.append(f"{b.name} x{b.stacks}")
                else:
                    buff_strs.append(f"{b.name}")
            lines.append("玩家Buff：" + " | ".join(buff_strs))
            
        lines.append("")
        
        lines.append("【我方战场】")
        if not p.minions and not p.amulets:
            lines.append("（空无一物）")
        else:
            for i in range(1, 6):
                key = str(i)
                if key in p.minions:
                    m = p.minions[key]
                    skills_desc = ""
                    if m.id in MINION_SKILLS:
                        skills_desc = " | 技能: " + " ".join([f"({idx}){s['name']}" for idx, s in enumerate(MINION_SKILLS[m.id], 1)])
                    buff_desc = ""
                    if getattr(m, "buffs", None):
                        buff_desc = " | Buff: " + " ".join([f"{b.name} x{b.stacks}" if b.stacks > 1 else b.name for b in m.buffs])
                    atk_val = m.atk + (1 if "whetstone" in p.relics else 0)
                    lines.append(f" 格子 [{i}] 随从：{m.name} (❤️ HP {m.hp}/{m.max_hp} | ⚔️ 攻击 {atk_val} | ⚡ 动作 {m.actions}A {m.bonus_actions}BA {m.attack_actions}AA{skills_desc}{buff_desc})")
                elif key in p.amulets:
                    a = p.amulets[key]
                    lines.append(f" 格子 [{i}] 护符：{a.name} (⏳ 吟唱 {a.countdown}) - {a.desc}")
                    
        lines.append("")
        
        lines.append("【敌方战场】")
        if not run.enemies:
            lines.append("（空无一物）")
        else:
            for idx, enemy in enumerate(run.enemies, 1):
                intent_parts = []
                if enemy.intent_a_desc:
                    intent_parts.append(f"A: {enemy.intent_a_desc}")
                if enemy.intent_ba_desc:
                    ba_desc = enemy.intent_ba_desc
                    if enemy.intent_ba2_desc:
                        ba_desc += f" + {enemy.intent_ba2_desc}"
                    intent_parts.append(f"BA: {ba_desc}")
                intent_str = f"({', '.join(intent_parts)})" if intent_parts else "无意图"
                shield_str = f" | 🛡️ 护盾 {enemy.shield}" if enemy.shield > 0 else ""
                buff_desc = ""
                if getattr(enemy, "buffs", None):
                    buff_desc = " | Buff: " + " ".join([f"{b.name} x{b.stacks}" if b.stacks > 1 else b.name for b in enemy.buffs])
                lines.append(f" 格子 [{idx}] 敌人：{enemy.name} (❤️ HP {enemy.hp}/{enemy.max_hp}{shield_str}{buff_desc} | ⚔️ 意图：{intent_str})")
            
        lines.append("")
        lines.append("【你的手牌】")
        if not p.hand:
            lines.append("（空空如也）")
        else:
            for idx, cid in enumerate(p.hand, 1):
                card = ALL_CARDS.get(cid)
                if card:
                    color_ch = "🔵" if card.color == "wizard" else "⚪"
                    cost_str = ""
                    if card.cost_a > 0:
                        cost_str += f"{card.cost_a}A"
                    if card.cost_ba > 0:
                        cost_str += f"{card.cost_ba}BA"
                    cost_str = cost_str or "免费"
                    rarity_map = {
                        "common": "普通",
                        "rare": "稀有",
                        "epic": "珍奇",
                        "legendary": "传奇",
                        "mythic": "神器"
                    }
                    rname = rarity_map.get(getattr(card, "rarity", "common"), "普通")
                    lines.append(f" [{idx}] {color_ch} {card.name} <{rname}> (消耗: {cost_str}) - {card.desc}")
                    
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        if p.fold_guide:
            lines.append("💬 提示：操作指南已折叠。输入 /rogue 折叠 可展开。")
        else:
            lines.append("💬 战斗指令指南：")
            lines.append("• 使用卡牌：/rogue 使用 <手牌序号> [目标]")
            lines.append("• 指向目标：敌方 e1-eN (对应敌方格子) | 我方 p0-p5 (p0为自己，p1-p5为随从)")
            lines.append("• 队列打牌：/rogue 使用 [1, 2:e1, 3]")
            lines.append("• 随从指令：/rogue 随从 <我方格子> 攻击/技能 <目标格子/技能序号> [技能目标]")
            lines.append("• 结束回合：/rogue 结束")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(lines)

    @staticmethod
    def _render_map_select(run: GameRun) -> str:
        p = run.player
        options = run.node_data.get("options", [])
        
        relics_str = ""
        if p.relics:
            from .relic_impl import get_relic_name
            relics_str = "\n🎒 遗物：" + " ".join([f"【{get_relic_name(r)}】" for r in p.relics])
            
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            f"🗺️ 【第 {p.stage} 关：请选择前进路线】",
            f"玩家：❤️ HP {p.hp}/{p.max_hp} | 🪙 金币 {p.gold}" + relics_str,
            ""
        ]
        
        preview_lines = ["【树状路线预览】"]
        nodes_dict = {}
        nodes_by_stage = {}
        for stage_str, layer in run.map_data.get("nodes", {}).items():
            stg = int(stage_str)
            nodes_by_stage[stg] = layer
            for nd in layer:
                nodes_dict[nd["id"]] = nd
                
        curr_id = run.map_data.get("current_node_id")
        type_names = {
            "battle": "遭遇战",
            "elite": "精英战",
            "event": "神秘事件",
            "shop": "奇妙商店",
            "rest": "篝火营地",
            "treasure": "古老宝箱房",
            "boss": "首领战"
        }
        
        max_preview_stage = min(20, p.stage + 3)
        curr_layer_nodes = []
        if not curr_id:
            curr_layer_nodes = nodes_by_stage.get(p.stage, [])
        else:
            curr_node = nodes_dict.get(curr_id)
            if curr_node:
                curr_layer_nodes = [nodes_dict[nid] for nid in curr_node.get("next", []) if nid in nodes_dict]
                
        if curr_layer_nodes:
            preview_lines.append(f"  📍 当前(第 {p.stage} 层):")
            for idx, nd in enumerate(curr_layer_nodes, 1):
                next_types = []
                for nid in nd.get("next", []):
                    next_node = nodes_dict.get(nid)
                    if next_node:
                        next_types.append(type_names.get(next_node["type"], next_node["type"]))
                next_str = f" (去往第 {p.stage+1} 层: {', '.join(next_types)})" if next_types else " (终点)"
                preview_lines.append(f"    [{idx}] {type_names.get(nd['type'], nd['type'])}{next_str}")
                
        for next_s in range(p.stage + 1, max_preview_stage + 1):
            next_layer_nodes = nodes_by_stage.get(next_s, [])
            if not next_layer_nodes:
                continue
            reachable_ids = set()
            prev_layer_nodes = []
            if next_s - 1 == p.stage:
                prev_layer_nodes = curr_layer_nodes
            else:
                prev_layer_nodes = nodes_by_stage.get(next_s - 1, [])
            for pn in prev_layer_nodes:
                for nid in pn.get("next", []):
                    reachable_ids.add(nid)
            filtered_nodes = [nd for nd in next_layer_nodes if nd["id"] in reachable_ids]
            if not filtered_nodes:
                filtered_nodes = next_layer_nodes
                
            layer_title = "🔮 下一步" if next_s == p.stage + 1 else ("🔥 再下一步" if next_s == p.stage + 2 else "🎁 目标")
            preview_lines.append(f"  {layer_title}(第 {next_s} 层):")
            for idx, nd in enumerate(filtered_nodes, 1):
                next_types = []
                for nid in nd.get("next", []):
                    next_node = nodes_dict.get(nid)
                    if next_node:
                        next_types.append(type_names.get(next_node["type"], next_node["type"]))
                next_str = f" (去往第 {next_s+1} 层: {', '.join(next_types)})" if next_types else " (终点)"
                preview_lines.append(f"    [{idx}] {type_names.get(nd['type'], nd['type'])}{next_str}")
                
        lines.extend(preview_lines)
        lines.append("")
        lines.append("前方道路出现了分支，请选择你前往的下一个节点：")
        
        for idx, opt in enumerate(options, 1):
            lines.append(f" [{idx}] {opt.get('desc', '')}")
            
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        if p.fold_guide:
            lines.append("💬 提示：操作指南已折叠。输入 /rogue 折叠 可展开。")
        else:
            lines.append("💬 选择路线指令：/rogue 选择 <分支序号>")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    @staticmethod
    def _render_event(run: GameRun) -> str:
        p = run.player
        data = run.node_data
        
        relics_str = ""
        if p.relics:
            from .relic_impl import get_relic_name
            relics_str = "\n🎒 遗物：" + " ".join([f"【{get_relic_name(r)}】" for r in p.relics])
            
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            f"✨ 【第 {p.stage} 关：随机事件】",
            f"玩家：❤️ HP {p.hp}/{p.max_hp} | 🪙 金币 {p.gold}" + relics_str,
            "",
            data.get("description", "发生了一个神秘的事件。"),
            "",
            "请做出你的选择："
        ]
        
        options = data.get("options", [])
        for idx, opt in enumerate(options, 1):
            lines.append(f" [{idx}] {opt.get('text', '')}")
            
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        if p.fold_guide:
            lines.append("💬 提示：操作指南已折叠。输入 /rogue 折叠 可展开。")
        else:
            lines.append("💬 选择指令：/rogue 选择 <序号>")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    @staticmethod
    def _render_shop(run: GameRun) -> str:
        p = run.player
        data = run.node_data
        
        relics_str = ""
        if p.relics:
            from .relic_impl import get_relic_name
            relics_str = "\n🎒 遗物：" + " ".join([f"【{get_relic_name(r)}】" for r in p.relics])
            
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            f"🛒 【第 {p.stage} 关：奇妙商店】",
            f"玩家：❤️ HP {p.hp}/{p.max_hp} | 🪙 金币 {p.gold}" + relics_str,
            "",
            "一位旅商展示着他的精致收藏：",
            ""
        ]
        
        items = data.get("items", [])
        for idx, item in enumerate(items, 1):
            itype = item.get("type")
            price = item.get("price")
            sold = item.get("sold", False)
            
            if sold:
                lines.append(f" [{idx}] 【已售罄】")
                continue
                
            if itype == "card":
                card = ALL_CARDS.get(item.get("card_id"))
                if card:
                    color_ch = "🔵" if card.color == "wizard" else "⚪"
                    lines.append(f" [{idx}] {color_ch} {card.name} (卡牌) - 🪙 {price}金币 | {card.desc}")
            elif itype == "relic":
                from .relic_impl import get_relic_name, get_relic_desc
                rid = item.get("relic_id")
                lines.append(f" [{idx}] 🎒 {get_relic_name(rid)} (遗物) - 🪙 {price}金币 | {get_relic_desc(rid)}")
            elif itype == "remove":
                lines.append(f" [{idx}] 🧹 净化服务 (移除卡组中任意一张牌) - 🪙 {price}金币")
            elif itype == "leave":
                lines.append(f" [{idx}] 🚪 离开商店，继续冒险")
                
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        if p.fold_guide:
            lines.append("💬 提示：操作指南已折叠。输入 /rogue 折叠 可展开。")
        else:
            lines.append("💬 购买/选择指令：/rogue 选择 <商品序号>")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    @staticmethod
    def _render_rest(run: GameRun) -> str:
        p = run.player
        
        relics_str = ""
        if p.relics:
            from .relic_impl import get_relic_name
            relics_str = "\n🎒 遗物：" + " ".join([f"【{get_relic_name(r)}】" for r in p.relics])
            
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            f"🔥 【第 {p.stage} 关：篝火营地】",
            f"玩家：❤️ HP {p.hp}/{p.max_hp}" + relics_str,
            "",
            "温暖的篝火跳跃着，你感到有些疲惫。你可以选择：",
            " [1] 🍖 休息：恢复 50% 最大生命值",
            " [2] 🔮 冥想：获得一张随机蓝色法术牌并加入卡组",
            " [3] 🚪 离开：不做整顿直接出发",
            "━━━━━━━━━━━━━━━━━━━━"
        ]
        if p.fold_guide:
            lines.append("💬 提示：操作指南已折叠。输入 /rogue 折叠 可展开。")
        else:
            lines.append("💬 选择指令：/rogue 选择 <序号>")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    @staticmethod
    def _render_reward(run: GameRun) -> str:
        p = run.player
        data = run.node_data
        
        quest_bonus = data.get("quest_bonus", "")
        
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            "🎁 【战斗胜利！请选择你的战利品】",
            ""
        ]
        
        if quest_bonus:
            lines.append(quest_bonus)
            lines.append("")
            
        cards = data.get("cards", [])
        for idx, cid in enumerate(cards, 1):
            card = ALL_CARDS.get(cid)
            if card:
                color_ch = "🔵" if card.color == "wizard" else "⚪"
                lines.append(f" [{idx}] {color_ch} {card.name} ({card.desc})")
                
        skip_idx = len(cards) + 1
        lines.append(f" [{skip_idx}] 🪙 跳过奖励卡牌 (获得 15 金币)")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        if p.fold_guide:
            lines.append("💬 提示：操作指南已折叠。输入 /rogue 折叠 可展开。")
        else:
            lines.append("💬 选择指令：/rogue 选择 <序号>")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    @staticmethod
    def _render_start_ancient(run: GameRun) -> str:
        p = run.player
        options = run.node_data.get("options", [])
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            "🌌 【第 1 关：先古契约】",
            f"玩家：❤️ HP {p.hp}/{p.max_hp} | 🪙 金币 {p.gold}",
            "",
            "在你面前浮现出了六座石碑，每座石碑上都铭刻着不同的命运契约。选择其中的契约以获取力量，但命运总会索取它的代价：",
            ""
        ]
        from .relic_impl import get_relic_name, get_relic_desc
        from .card_impl import ALL_CARDS
        for idx, opt in enumerate(options, 1):
            rid = opt["relic"]
            rname = get_relic_name(rid)
            rdesc = get_relic_desc(rid)
            if opt["type"] == "double":
                lines.append(f" [{idx}] ⚖️ 双刃剑契约：【{rname}】\n     效果：{rdesc}")
            else:
                cid = opt["card"]
                cname = ALL_CARDS[cid].name
                cdesc = ALL_CARDS[cid].desc
                lines.append(f" [{idx}] 🕸️ 代价契约：【{rname}】 ➕ 传奇卡牌【{cname}】\n     效果：{rdesc} 同时获得该强力卡牌 ({cdesc})")
                
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("💬 选择契约指令：/rogue 选择 <契约序号>")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    @staticmethod
    def _render_ancient(run: GameRun) -> str:
        p = run.player
        options = run.node_data.get("options", [])
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            f"🌟 【第 {p.stage} 关：先古赐福】",
            f"玩家：❤️ HP {p.hp}/{p.max_hp} | 🪙 金币 {p.gold}",
            "",
            "空气中浮现出纯净的奥术光辉。先古的意志再次眷顾了你，向你降下丰厚的赐福礼包：",
            ""
        ]
        from .relic_impl import get_relic_name, get_relic_desc
        from .card_impl import ALL_CARDS
        for idx, opt in enumerate(options, 1):
            cid = opt["card"]
            rid = opt["relic"]
            cname = ALL_CARDS[cid].name
            cdesc = ALL_CARDS[cid].desc
            rname = get_relic_name(rid)
            rdesc = get_relic_desc(rid)
            lines.append(f" [{idx}] 🎁 赐福包：【{rname}】 ➕ 传奇卡牌【{cname}】\n     效果：获得被动遗物（{rdesc}）与卡牌（{cdesc}）")
            
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("💬 选择赐福指令：/rogue 选择 <赐福序号>")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    @staticmethod
    def _render_treasure(run: GameRun) -> str:
        p = run.player
        data = run.node_data
        text = data.get("text", "")
        state = data.get("state", "pending_remove")
        
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            f"🎁 【第 {p.stage} 关：古老宝箱】",
            f"玩家：❤️ HP {p.hp}/{p.max_hp} | 🪙 金币 {p.gold}",
            "",
            text,
            ""
        ]
        
        if state == "opened":
            lines.append(" [1] 🚪 离开宝箱房，继续冒险")
            
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        if state == "pending_remove":
            lines.append("💬 选择要献祭（移除）的卡牌序号指令：/rogue 选择 <卡牌序号>")
        else:
            lines.append("💬 离开指令：/rogue 选择 1")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)
