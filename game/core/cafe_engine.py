import random
from typing import Tuple
from ..models.state import GameRun, PlayerState
from ..cards import ALL_CARDS
from ..entities import get_relic_name, get_relic_desc
from ..data.relic_data import RELIC_CONFIG
from ..data.gem_data import GEM_CONFIG

class CafeEngine:
    def __init__(self, save_manager, map_engine):
        self.save_manager = save_manager
        self.map_engine = map_engine

    def init_cafe(self, run: GameRun):
        p = run.player
        guests = ["Guide_Elder", "Bartender_Jack", "Blacksmith_Ironclad", "pppopipupu"]
        normals = ["杰斯", "艾琳", "雷恩", "露娜", "莫里", "凯尔", "咪咪", "萨拉", "辛普森", "斯莱克", "编号7", "绯红"]
        
        num_guests = random.randint(1, 2)
        selected_guests = random.sample(guests, num_guests)
        selected_normals = random.sample(normals, 4 - num_guests)
        selected_npcs = selected_guests + selected_normals
        random.shuffle(selected_npcs)

        cafe_data = {
            "npcs": selected_npcs,
            "active_npc": None,
            "dialog_state": None,
            "talked_npcs": [],
            "card_master_stock": [],
            "gemcutter_stock": [],
            "hunter_stock": None
        }

        stats = self.save_manager.load_stats(run.user_id)
        p_class = getattr(stats, "selected_class", "法师")
        
        if "杰斯" in selected_npcs:
            if p_class == "战士":
                from ..data.wizard_card_data import WIZARD_CARD_CONFIG
                pool = [k for k, v in WIZARD_CARD_CONFIG.items() if v.get("rarity") not in ("legendary", "mythic", "artifact")]
            else:
                from ..data.warrior_card_data import WARRIOR_CARD_CONFIG
                pool = [k for k, v in WARRIOR_CARD_CONFIG.items() if v.get("rarity") not in ("legendary", "mythic", "artifact")]
            cafe_data["card_master_stock"] = random.sample(pool, min(len(pool), 3))

        if "艾琳" in selected_npcs:
            rare_gems = [k for k, v in GEM_CONFIG.items() if v.get("rarity") == "rare"]
            if rare_gems:
                cafe_data["gemcutter_stock"] = random.sample(rare_gems, min(len(rare_gems), 2))

        if "凯尔" in selected_npcs:
            relic_keys = [k for k, v in RELIC_CONFIG.items() if v.get("rarity") == "epic" and k not in p.relics]
            if not relic_keys:
                relic_keys = [k for k in RELIC_CONFIG.keys() if k not in p.relics]
            if relic_keys:
                cafe_data["hunter_stock"] = random.choice(relic_keys)

        run.node_type = "cafe"
        run.node_data["cafe_data"] = cafe_data
        self.save_manager.save_save(run.user_id, run)

    def render_cafe(self, run: GameRun) -> str:
        p = run.player
        cafe_data = run.node_data.get("cafe_data", {})
        active_npc = cafe_data.get("active_npc")
        
        npc_show_names = {
            "Guide_Elder": "👴 向导长老",
            "Bartender_Jack": "🍺 酒保杰克",
            "Blacksmith_Ironclad": "🔨 铁匠艾恩克拉德",
            "pppopipupu": "🐟 pppopipupu",
            "杰斯": "🃏 卡牌大师 · 杰斯",
            "艾琳": "💎 宝石琢磨师 · 艾琳",
            "雷恩": "🛡️ 退役角斗士 · 雷恩",
            "露娜": "🔮 迷路占星师 · 露娜",
            "莫里": "🍳 流浪厨师 · 莫里",
            "凯尔": "🎒 遗迹猎人 · 凯尔",
            "咪咪": "🐱 会说话的猫 · 咪咪",
            "萨拉": "🧵 虚空缝纫师 · 萨拉",
            "辛普森": "🎵 狂热诗人 · 辛普森",
            "斯莱克": "🪙 黑市宝石商 · 斯莱克",
            "编号7": "🤖 沉睡 of 古老守卫 · 编号7",
            "绯红": "🌹 神秘红衣女士 · 绯红"
        }

        if active_npc is None:
            npcs_str = ""
            for npc in cafe_data.get("npcs", []):
                status = " (已交互)" if npc in cafe_data.get("talked_npcs", []) else ""
                npcs_str += f"\n  - {npc_show_names.get(npc, npc)}{status}"
            
            lines = [
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "✨ 旅途的绿洲 ── 先古咖啡厅 ✨",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"当前层数: 第 {p.stage} 层 | 冒险者: {run.player.name}",
                f"❤️ HP: {p.hp}/{p.max_hp} | 🪙 金币: {p.gold} GP",
                "" if not p.relics else "🎒 拥有遗物: " + " ".join(f"【{get_relic_name(r)}】" for r in p.relics),
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "环境：空气中弥漫着淡淡的摩卡香气与虚空余温。这里是两个危险区域之间的夹缝港湾，几位行色各异的旅客正聚在炉火旁休息。西面的走廊通向更深处的先古赐福之地。",
                "在本店休息的旅客有：" + npcs_str,
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "💡 交互指令：/rogue talk <NPC名字> (如：/rogue talk 铁匠)",
                "💡 离开咖啡厅：/rogue 离开",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ]
            return "\n".join(lines)

        else:
            dialog_state = cafe_data.get("dialog_state")
            npc_name = npc_show_names.get(active_npc, active_npc)
            
            lines = [
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"💬 正在与 【{npc_name}】 对话中...",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ]
            
            talked = active_npc in cafe_data.get("talked_npcs", [])
            dialog_text, options = self._get_dialog_content(run, active_npc, dialog_state, talked)
            
            lines.append(dialog_text)
            lines.append("")
            
            for idx, opt in enumerate(options, 1):
                lines.append(f"  [{idx}] {opt}")
                
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("💡 交互选择：输入 /rogue c <选项序号> (可直接输入数字序号)")
            lines.append("💡 退出对话：/rogue 离开")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            return "\n".join(lines)

    def talk_npc(self, run: GameRun, target: str) -> str:
        cafe_data = run.node_data.setdefault("cafe_data", {})
        npcs = cafe_data.get("npcs", [])
        
        target_lower = target.lower().strip()
        found = None
        
        npc_mapping = {
            "guide_elder": "Guide_Elder", "向导长老": "Guide_Elder", "向导": "Guide_Elder", "长老": "Guide_Elder",
            "bartender_jack": "Bartender_Jack", "酒保杰克": "Bartender_Jack", "酒保": "Bartender_Jack", "杰克": "Bartender_Jack",
            "blacksmith_ironclad": "Blacksmith_Ironclad", "铁匠艾恩克拉德": "Blacksmith_Ironclad", "铁匠": "Blacksmith_Ironclad", "艾恩": "Blacksmith_Ironclad",
            "pppopipupu": "pppopipupu", "神秘高手": "pppopipupu", "高手": "pppopipupu",
            "杰斯": "杰斯", "卡牌大师": "杰斯",
            "艾琳": "艾琳", "宝石琢磨师": "艾琳", "宝石师": "艾琳",
            "雷恩": "雷恩", "角斗士": "雷恩",
            "露娜": "露娜", "占星师": "露娜",
            "莫里": "莫里", "厨师": "莫里",
            "凯尔": "凯尔", "遗迹猎人": "凯尔", "猎人": "凯尔",
            "咪咪": "咪咪", "猫咪": "咪咪", "猫": "咪咪",
            "萨拉": "萨拉", "缝纫师": "萨拉",
            "辛普森": "辛普森", "诗人": "辛普森",
            "斯莱克": "斯莱克", "宝石商": "斯莱克", "黑市": "斯莱克",
            "编号7": "编号7", "守卫": "编号7", "古老守卫": "编号7",
            "绯红": "绯红", "红衣女士": "绯红", "女士": "绯红"
        }

        mapped = npc_mapping.get(target_lower)
        if mapped and mapped in npcs:
            found = mapped

        if not found:
            def clean_text(text: str) -> str:
                res_chars = []
                for char in text.lower():
                    if char.isalnum() or (ord(char) >= 0x4e00 and ord(char) <= 0x9fff):
                        res_chars.append(char)
                return "".join(res_chars)

            cleaned_target = clean_text(target_lower)
            if cleaned_target:
                for npc in npcs:
                    if cleaned_target in clean_text(npc):
                        found = npc
                        break
                    show_name = npc_show_names.get(npc, "")
                    if show_name and cleaned_target in clean_text(show_name):
                        found = npc
                        break

        if not found:
            return f"❌ 咖啡厅里似乎没有名为【{target}】的旅客。请输入 /rogue 查看旅客名单。"

        cafe_data["active_npc"] = found
        cafe_data["dialog_state"] = "start"
        self.save_manager.save_save(run.user_id, run)
        
        return self.render_cafe(run)

    def leave_npc(self, run: GameRun) -> str:
        cafe_data = run.node_data.setdefault("cafe_data", {})
        active_npc = cafe_data.get("active_npc")
        if active_npc is not None:
            talked_npcs = cafe_data.setdefault("talked_npcs", [])
            if active_npc not in talked_npcs:
                talked_npcs.append(active_npc)
            cafe_data["active_npc"] = None
            cafe_data["dialog_state"] = None
            self.save_manager.save_save(run.user_id, run)
            return "你告别了交谈的旅客，回到了大堂。\n\n" + self.render_cafe(run)
        return "❌ 你当前已在大堂。"

    def leave_cafe(self, run: GameRun) -> str:
        run.node_type = "ancient"
        self.map_engine._init_ancient_node(run)
        self.save_manager.save_save(run.user_id, run)
        return "👋 你背上行囊，推开咖啡厅的木门，重新踏上了充满奥术微光的先古赐福地带。"

    def choose_option(self, run: GameRun, idx: int) -> str:
        cafe_data = run.node_data.setdefault("cafe_data", {})
        active_npc = cafe_data.get("active_npc")
        dialog_state = cafe_data.get("dialog_state")
        talked = active_npc in cafe_data.get("talked_npcs", [])

        if active_npc is None:
            return "❌ 当前不在与 NPC 对话中。请使用 talk <NPC名字> 指令进行对话。"

        _, options = self._get_dialog_content(run, active_npc, dialog_state, talked)
        if idx < 1 or idx > len(options):
            return "❌ 无效的选择序号。"

        res_msg = self._execute_dialog_logic(run, active_npc, dialog_state, idx, talked)
        self.save_manager.save_save(run.user_id, run)
        
        return res_msg

    def _get_dialog_content(self, run: GameRun, npc: str, state: str, talked: bool) -> Tuple[str, list[str]]:
        p = run.player
        cafe_data = run.node_data.get("cafe_data", {})
        
        if talked:
            if npc == "Guide_Elder":
                return "👴 向导长老拍了拍你的肩膀：'路在脚下，多想无益。去面对你该面对的难关吧。'", ["离开交谈"]
            elif npc == "Bartender_Jack":
                return "🍺 酒保杰克：'哎呀，老顾客，我的酒劲可是很大的。祝你在关卡里一切顺利！'", ["离开交谈"]
            elif npc == "Blacksmith_Ironclad":
                return "🔨 铁匠艾恩克拉德：'风箱拉得够热了。别打扰老子休息，赶紧上路吧！'", ["离开交谈"]
            elif npc == "pppopipupu":
                return "🐟 pppopipupu静静地盯着池塘：'缘起缘灭，宁静已归于水底。祝你武运昌隆。'", ["离开交谈"]
            else:
                return "此人看起来有些疲惫，不想再多说什么了。", ["离开交谈"]

        if npc == "Guide_Elder":
            if state == "start":
                return (
                    "👴 向导长老：“选了一条充满荆棘的道路啊，孩子。看到你疲惫的样子，是想退缩了吗？还是依然觉得虚空不过如此？”",
                    ["诚实诉苦：是的长老，外面的怪物简直是疯子，尤格索托斯甚至还在乱码嘲讽我！",
                     "逞强嘴硬：怎么可能？我一路砍瓜切菜，尤格索托斯我翻手可灭！",
                     "离开交谈"]
                )
            elif state == "branch_a":
                return (
                    "👴 向导长老哈哈大笑，赞赏你的坦率：“哈哈！诚实是美德。给你两句忠告：越混沌的地方，越要守住心神。”",
                    ["虚心求教：花费 40 金币购买长老的珍藏红茶，静气凝神",
                     "索要资助：长老手头宽裕，不如赞助我一些金币盘缠？",
                     "离开交谈"]
                )
            elif state == "branch_b":
                return (
                    "👴 向导长老冷笑一声，面露失望：“狂妄！在虚空面前如此自大，看来你还没有领教过真正的绝望。”",
                    ["强硬反驳：不信？我们可以现场比划一下！",
                     "顺从认错：额，其实我开玩笑的，请长老息怒...",
                     "离开交谈"]
                )

        elif npc == "Bartender_Jack":
            if state == "start":
                return (
                    "🍺 酒保杰克：“哟！竟然能在这鬼地方遇到老熟人。怎么，不来杯我亲手调的特制烈酒，暖暖冰冷的身子？价格公道，只要 50 金币！”",
                    ["豪爽接受：满上！正好需要烈酒来壮壮胆，什么代价都行！ (消耗 50 金币)",
                     "拒绝饮酒：在这混沌的咖啡厅，我只买杯普通的温红茶 (消耗 15 金币)",
                     "离开交谈"]
                )
            elif state == "branch_a":
                return (
                    "🍺 酒保杰克大喜，递给你一杯燃烧着幽蓝火焰的虚空伏特加：“好气魄！这杯【虚空烈焰】是你的了！来，喝了它还是用它淬炼你的卡牌？”",
                    ["一饮而尽：咕嘟咕嘟全部喝下！",
                     "浇在武器上：额外支付 30 金币，借助酒劲对卡牌进行回炉重塑",
                     "离开交谈"]
                )

        elif npc == "Blacksmith_Ironclad":
            return (
                "🔨 铁匠艾恩克拉德：“呸！这咖啡厅一股甜腻娘们味！不过这里的炉子勉强能用。喂，你身上的武器生锈了，要不要老子给你砸几锤？丑话说在前面，别跟老子磨叽！”",
                ["极限熔炼 (消耗 70 金币)：直接对随机卡牌进行合金升级",
                 "矿石重塑 (消耗 1 颗宝石 + 30 金币)：用宝石作为催化剂，100% 成功为指定卡牌增加 1 个插槽",
                 "离开交谈"]
            )

        elif npc == "pppopipupu":
            if state == "start":
                return (
                    "🐟 pppopipupu：“嘘……别出声。水波在动。在这混沌虚空的夹缝里钓鱼，能钓起很多不可思议的灵魂……你也是被钓上来的鱼吗？”",
                    ["安静陪伴：一言不发，在旁边静静坐下",
                     "粗暴打扰：喂！在咖啡厅的观赏水池里怎么可能钓得到鱼？你在装什么深沉？",
                     "离开交谈"]
                )
            elif state == "branch_a":
                return (
                    "他闭着眼，池水泛起金光：“很好，你没有像其他浮躁的冒险者一样急着索要力量。但钓鱼需要真正的静气，你还能继续保持沉默吗？”",
                    ["继续保持沉默：依然坐在一旁，闭目养神",
                     "忍不住开口询问：“大师，这水池里真有鱼吗？”",
                     "离开交谈"]
                )
            elif state == "branch_b":
                return (
                    "他眉头微皱，水面泛起寒霜：“惊扰了鱼群，可是要付出代价的。你是想试试我手里的竹竿，还是留下买鱼钱？”",
                    ["强硬对峙：“代价？我就站在这里，有本事你咬我啊！”",
                     "退缩道歉：“对不起！我不该打扰垂钓！”",
                     "离开交谈"]
                )

        elif npc == "杰斯":
            stock = cafe_data.get("card_master_stock", [])
            opts = []
            for cid in stock:
                name = ALL_CARDS[cid].name if cid in ALL_CARDS else cid
                desc = ALL_CARDS[cid].desc if cid in ALL_CARDS else ""
                opts.append(f"购买跨职业卡牌【{name}】 (售价 120 金币) - 效果：{desc}")
            opts.append("离开交谈")
            return "杰斯整理着卡牌：“想不想试试别的职业的绝学？魔法和利刃的交融，这才是真正的艺术！”", opts

        elif npc == "艾琳":
            stock = cafe_data.get("gemcutter_stock", [])
            opts = [
                "卡牌宝石槽扩充 (消耗 50 金币)：为指定卡牌强行多钻 1 个宝石槽位（不超过稀有度上限）"
            ]
            for gid in stock:
                name = GEM_CONFIG[gid]["name"] if gid in GEM_CONFIG else gid
                desc = GEM_CONFIG[gid]["desc"] if gid in GEM_CONFIG else ""
                opts.append(f"购买打折走私宝石【{name}】 (8折优惠，售价 64 金币) - 效果：{desc}")
            opts.append("离开交谈")
            return "艾琳抛玩着亮晶晶的碎晶：“每一块粗糙的石头都渴望着被雕琢，就像你的灵魂一样。来挑选两颗走私来的好货吗？”", opts

        elif npc == "雷恩":
            return (
                "雷恩正在擦拭生锈的肩甲：“小子，真正的力量不是在羊皮纸上写写画画，去磨砺你的肉体吧！”",
                ["肉体淬炼 (消耗 50 金币)：永久提升 8 点最大生命值上限",
                 "血誓洗礼 (消耗 10 生命值)：夺取退役战利品珍奇遗物【角斗士皮带】",
                 "离开交谈"]
            )

        elif npc == "露娜":
            return (
                "露娜摆弄着星盘，神情飘忽：“星空在指引着你，但也伴随着坠落的危险。你准备好面对未知的启示了吗？”",
                ["接受命运启示 (消耗 15 生命值)：获得占星禁术卡牌【星界坠击】",
                 "向星盘低语：询问关于最终BOSS尤格索托斯的弱点情报 (免费闲聊)",
                 "离开交谈"]
            )

        elif npc == "莫里":
            return (
                "莫里正在炖着一锅香气诡异的浓汤：“咖啡的苦涩能唤醒你沉睡的意志，但虚空的甜点...嘿，吃下去别吐出来就行。”",
                ["购买特制浓缩咖啡 (消耗 60 金币)：获得本阶段回合开始额外 +1A 临时遗物",
                 "购买虚空甜甜圈 (消耗 40 金币)：恢复 20 生命，但卡组随机被塞入一张【消化不良】诅咒卡",
                 "离开交谈"]
            )

        elif npc == "凯尔":
            opts = []
            if p.relics:
                opts.append(f"变卖现有遗物：将你身上的【{get_relic_name(p.relics[0])}】以 50 金币价格转卖给凯尔")
            else:
                opts.append("变卖现有遗物 (你身上没有可卖的遗物)")
            opts.append("随机淘一件古老遗物 (消耗 120 金币)")
            opts.append("离开交谈")
            return "凯尔蹲坐在包裹旁整理古董：“我在荒野里刨了一辈子土，什么宝贝没见过？只要你出得起价，没有买不到的。”", opts

        elif npc == "咪咪":
            return (
                "咪咪骄傲地舔着爪子：“愚蠢的人类，看在你有闪亮金币的份上，本喵允许你摸一下。喵呜——”",
                ["免费抚摸它 (可能被抓伤流血，或者获得金币)",
                 "喂食美味小鱼干 (消耗 15 金币)：借机抚摸耳朵，或进行卡牌净化",
                 "离开交谈"]
            )
        
        elif npc == "萨拉":
            return (
                "萨拉的指尖缠绕着虚空能量线：“虚空的丝线比黄金更坚韧，我可以用它重塑你的卡牌效果。”",
                ["编织保留织物 (免费)：为指定卡牌赋予【保留】词条，但该卡伤害/防御效果永久降低 4 点",
                 "编织裂变织物 (消耗 80 金币)：为指定卡牌成功编织【复制 1】被动词条",
                 "离开交谈"]
            )

        elif npc == "辛普森":
            return (
                "辛普森怀抱竖琴，激情满怀：“你的伟绩将被传唱！只要给点小钱，我的诗歌能让你在战场上充满斗志！”",
                ["倾听赞歌 (免费)：获得在接下来的 3 场战斗开始时获得 2 护盾的临时遗物【赞歌】",
                 "资助诗集出版 (消耗 30 金币)：获得狂热吟游诗人赠予的卡牌【英雄赞歌】",
                 "离开交谈"]
            )

        elif npc == "斯莱克":
            return (
                "斯莱克拉低兜帽，神神秘秘：“嘘——低调点。这些可是从先古矿区偷偷带出来的绝品，识货的就快下手。”",
                ["走私传奇宝石 (消耗 240 金币)：以 8 折购买一颗随机传奇宝石",
                 "接受危险试验 (免费)：白嫖一颗随机珍奇宝石，但卡组被迫塞入一张【法力逆流】诅咒卡",
                 "离开交谈"]
            )

        elif npc == "编号7":
            return (
                "编号7的装甲缝隙里漏出电火花，红光闪烁：“滴...能量水平极低...检测到有机生命体...是否注入动力源...”",
                ["注入动作点动力源 (消耗 1A)：使后续首场战斗第一回合动作点临时少 1A，完全激活并获取独特遗物【能量护盾电池】",
                 "暴力拆解机械核心 (免费)：尝试强行拆卸它，可能获得大量金币，也可能引发剧烈爆炸伤害",
                 "离开交谈"]
            )

        elif npc == "绯红":
            return (
                "绯红端着红酒，优雅迷人：“命运是一场迷人的舞会，我的朋友。你愿意为了一时的欢愉，付出什么代价呢？”",
                ["灵魂之舞契约 (消耗 25% 最大生命值上限)：获取强大物比的被动遗物【绯红之心】",
                 "命运轻吻：撕裂并彻底移除卡组中的一张卡牌，同时最大生命上限增加 6 点",
                 "离开交谈"]
            )

        return "未知旅客。", ["离开交谈"]

    def _execute_dialog_logic(self, run: GameRun, npc: str, state: str, idx: int, talked: bool) -> str:
        p = run.player
        cafe_data = run.node_data.setdefault("cafe_data", {})
        talked_npcs = cafe_data.setdefault("talked_npcs", [])

        if talked:
            cafe_data["active_npc"] = None
            cafe_data["dialog_state"] = None
            return "你已结束了与该旅客的交谈。"

        if npc == "Guide_Elder":
            if state == "start":
                if idx == 1:
                    cafe_data["dialog_state"] = "branch_a"
                    return "你向长老诉说了虚空之苦。\n\n" + self.render_cafe(run)
                elif idx == 2:
                    cafe_data["dialog_state"] = "branch_b"
                    return "你对长老吹嘘了自己的战绩。\n\n" + self.render_cafe(run)
                else:
                    return self.leave_npc(run)
            elif state == "branch_a":
                if idx == 1:
                    if p.gold < 40:
                        return "❌ 你的金币不足 40 GP。"
                    p.gold -= 40
                    p.deck.append("neutral_emperor_eye")
                    talked_npcs.append(npc)
                    cafe_data["active_npc"] = None
                    cafe_data["dialog_state"] = None
                    return "👴 向导长老递给你一杯温热的红茶：'静气凝神，孩子。这本【霸瞳天星】就交予你，助你窥视命运。'\n你获得了传奇卡牌【霸瞳天星】！"
                elif idx == 2:
                    p.max_hp = max(5, p.max_hp - 4)
                    p.hp = min(p.hp, p.max_hp)
                    p.gold += 120
                    talked_npcs.append(npc)
                    cafe_data["active_npc"] = None
                    cafe_data["dialog_state"] = None
                    return "👴 向导长老嫌弃地敲了敲你的骨头，扣除了你 4 点最大生命值上限（摸骨惩罚），但赞助了你 120 金币：'身子骨太弱了，拿着这些钱去置办点好装备吧！'"
                else:
                    return self.leave_npc(run)
            elif state == "branch_b":
                if idx == 1:
                    p.hp = max(1, p.hp - 6)
                    if p.deck:
                        cid = random.choice(p.deck)
                        if cid in ALL_CARDS:
                            upg_cid = cid + "+"
                            if upg_cid in ALL_CARDS and upg_cid not in p.deck:
                                p.deck.remove(cid)
                                p.deck.append(upg_cid)
                    talked_npcs.append(npc)
                    cafe_data["active_npc"] = None
                    cafe_data["dialog_state"] = None
                    return "👴 向导长老一拂袖打出一道惩戒训诫光芒（你流失了 6 点生命值），但强烈的能量波动淬炼了你的卡组：你卡组中随机一张卡牌获得了【升级】！"
                elif idx == 2:
                    p.gold = max(0, p.gold - 20)
                    if p.deck:
                        cid = random.choice(p.deck)
                        card_obj = ALL_CARDS.get(cid.split(":gems:")[0])
                        if card_obj:
                            max_slots = card_obj.get_gem_slots_count()
                            base_cid = cid.split(":gems:")[0]
                            old_gems = cid.split(":gems:")[1].split(",") if ":gems:" in cid else []
                            if len(old_gems) < max_slots:
                                old_gems.append("empty")
                                new_cid = f"{base_cid}:gems:{','.join(old_gems)}"
                                p.deck.remove(cid)
                                p.deck.append(new_cid)
                    talked_npcs.append(npc)
                    cafe_data["active_npc"] = None
                    cafe_data["dialog_state"] = None
                    return "👴 向导长老脸色缓和，收下了你 20 金币作为学费：'知错能改，善莫大焉。去吧。'\n他亲自动手为你卡组中随机一张卡牌扩充了 1 个宝石插槽！"
                else:
                    return self.leave_npc(run)

        elif npc == "Bartender_Jack":
            if state == "start":
                if idx == 1:
                    if p.gold < 50:
                        return "❌ 你的金币不足 50 GP。"
                    p.gold -= 50
                    cafe_data["dialog_state"] = "branch_a"
                    return "你支付了 50 金币，杰克端出了一杯燃烧着幽火的【虚空烈焰】烈酒！\n\n" + self.render_cafe(run)
                elif idx == 2:
                    if p.gold < 15:
                        return "❌ 你的金币不足 15 GP。"
                    p.gold -= 15
                    p.hp = min(p.max_hp, p.hp + 10)
                    talked_npcs.append(npc)
                    cafe_data["active_npc"] = None
                    cafe_data["dialog_state"] = None
                    return "你支付了 15 金币，喝了一杯温茶，全身暖洋洋的（回复了 10 点生命值）。酒保杰克向你报以稳健的微笑。"
                else:
                    return self.leave_npc(run)
            elif state == "branch_a":
                if idx == 1:
                    p.hp = max(1, p.hp - 8)
                    p.relics.append("espresso_relic")
                    talked_npcs.append(npc)
                    cafe_data["active_npc"] = None
                    cafe_data["dialog_state"] = None
                    return "🔥 你将烈酒一饮而尽！喉咙像被火烧一样剧痛（流失了 8 点生命值），但虚空魔力彻底唤醒了你的潜能：你获得了临时整备遗物【特制浓缩咖啡】（本阶段所有战斗回合开始额外得 1A）！"
                elif idx == 2:
                    if p.gold < 30:
                        return "❌ 你的金币不足 30 GP。"
                    p.gold -= 30
                    attacks = [cid for cid in p.deck if cid in ALL_CARDS and ALL_CARDS[cid].type == "attack"]
                    if not attacks:
                        attacks = p.deck.copy()
                    if attacks:
                        cid = random.choice(attacks)
                        base_cid = cid.split(":gems:")[0]
                        gems_part = f":gems:{cid.split(':gems:')[1]}" if ":gems:" in cid else ""
                        if not base_cid.endswith("+copy_1"):
                            p.deck.remove(cid)
                            p.deck.append(f"{base_cid}+copy_1{gems_part}")
                    talked_npcs.append(npc)
                    cafe_data["active_npc"] = None
                    cafe_data["dialog_state"] = None
                    return "🍺 你额外支付了 30 金币，酒保杰克将烈酒倒在你的卡牌上，用火焰进行了重塑：你卡组中随机一张卡牌被织入了【复制 1】词条！"
                else:
                    return self.leave_npc(run)

        elif npc == "Blacksmith_Ironclad":
            if idx == 1:
                if p.gold < 70:
                    return "❌ 你的金币不足 70 GP。"
                p.gold -= 70
                if p.deck:
                    from ..models.state import ensure_card_state
                    cid = ensure_card_state(random.choice(p.deck))
                    from ..data.card_upgrade_data import CARD_UPGRADE_CONFIG
                    import copy
                    if cid.id in CARD_UPGRADE_CONFIG and not cid.upgraded:
                        upg_cid = copy.copy(cid)
                        upg_cid.upgraded = True
                        p.deck.remove(cid)
                        p.deck.append(upg_cid)
                        cid = upg_cid
                    if random.random() < 0.5:
                        card_obj = ALL_CARDS.get(cid.id)
                        if card_obj:
                            max_slots = card_obj.get_gem_slots_count()
                            old_gems = list(cid.gems)
                            if len(old_gems) < max_slots:
                                new_gems = old_gems + ["empty"]
                                upg_gem_cid = copy.copy(cid)
                                upg_gem_cid.gems = new_gems
                                p.deck.remove(cid)
                                p.deck.append(upg_gem_cid)
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return "🔨 铁匠艾恩克拉德吐了口唾沫，大锤猛砸，直接将你的一张随机卡牌升级强化！并且在锤击的震荡下，有 50% 几率额外扩充了 1 个宝石插槽！"
            elif idx == 2:
                if p.gold < 30:
                    return "❌ 你的金币不足 30 GP。"
                p.gold -= 30
                if p.deck:
                    from ..models.state import ensure_card_state
                    cid = ensure_card_state(random.choice(p.deck))
                    card_obj = ALL_CARDS.get(cid.id)
                    if card_obj:
                        max_slots = card_obj.get_gem_slots_count()
                        old_gems = list(cid.gems)
                        if len(old_gems) < max_slots:
                            new_gems = old_gems + ["empty"]
                            import copy
                            new_cid = copy.copy(cid)
                            new_cid.gems = new_gems
                            p.deck.remove(cid)
                            p.deck.append(new_cid)
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return "🔨 铁匠铁匠艾恩克拉德爽快地收下 30 金币，熟练地拿过你卡组中的一张卡牌，用铁凿在其表面完美地扩充了 1 个宝石插槽！"
            else:
                return self.leave_npc(run)

        elif npc == "pppopipupu":
            if state == "start":
                if idx == 1:
                    cafe_data["dialog_state"] = "branch_a"
                    return "你放轻了呼吸，在钓鱼高手身旁缓缓坐下，闭上了双眼。\n\n" + self.render_cafe(run)
                elif idx == 2:
                    cafe_data["dialog_state"] = "branch_b"
                    return "你在观赏池边指手画脚，大声吵闹打扰了垂钓。\n\n" + self.render_cafe(run)
                else:
                    return self.leave_npc(run)
            elif state == "branch_a":
                if idx == 1:
                    talked_npcs.append(npc)
                    cafe_data["active_npc"] = None
                    cafe_data["dialog_state"] = None
                    run.node_data["cafe_data"] = cafe_data
                    
                    from .explore_engine import ExploreEngine
                    expl = ExploreEngine(self.save_manager, self.map_engine)
                    expl.start_gem_insert_flow(run, "gem_return_5", "cafe", run.node_data.copy())
                    return "🐟 pppopipupu转过头赞许地看着你：'你很有静气。这颗【永恒祖母绿】送给你，它是宁静的馈赠。'\n你开启了【永恒祖母绿】的强制镶嵌流程！"
                elif idx == 2:
                    p.gold = max(0, p.gold - 20)
                    from ..models.state import ensure_card_state
                    curses = [cid for cid in p.deck if ensure_card_state(cid).id.startswith("curse_")]
                    purged_msg = "（你卡组中没有诅咒卡牌，但他依然收下了 20 金币作为惊扰费）"
                    if curses:
                        cur = curses[0]
                        p.deck.remove(cur)
                        purged_msg = f"（他用细长的钓线一甩，精准地从你的卡组中把诅咒卡【{ALL_CARDS[cur].name}】钩走并化为了飞灰！）"
                    talked_npcs.append(npc)
                    cafe_data["active_npc"] = None
                    cafe_data["dialog_state"] = None
                    return f"🐟 pppopipupu叹了口气：'心浮气躁，鱼都被你吓跑了。'\n你流失了 20 金币，但得到了他的奇妙净化 {purged_msg}"
                else:
                    return self.leave_npc(run)
            elif state == "branch_b":
                if idx == 1:
                    p.hp = max(1, p.hp - 15)
                    p.relics.append("energy_core")
                    talked_npcs.append(npc)
                    cafe_data["active_npc"] = None
                    cafe_data["dialog_state"] = None
                    return "❄️ 池塘的水波瞬间化为冰霜之手拍在你的胸口（你受到了 15 点真实伤害）！但神秘高手似乎对你的硬气感到好笑，把一个发出沉闷轰鸣的【能量核心】遗物丢给了你！"
                elif idx == 2:
                    p.gold = max(0, p.gold - 30)
                    p.deck.append("neutral_hero_anthem")
                    talked_npcs.append(npc)
                    cafe_data["active_npc"] = None
                    cafe_data["dialog_state"] = None
                    return "🐟 pppopipupu摇了摇头，池水恢复温和。你赔礼道谢送出了 30 金币，他在水波中写下一页金色的赞歌交给了你：你获得了卡牌【英雄赞歌】！"
                else:
                    return self.leave_npc(run)

        elif npc == "杰斯":
            stock = cafe_data.get("card_master_stock", [])
            if idx <= len(stock):
                if p.gold < 120:
                    return "❌ 你的金币不足 120 GP。"
                p.gold -= 120
                cid = stock[idx - 1]
                p.deck.append(cid)
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return f"你付了 120 金币。杰斯大师指尖一弹，卡牌【{ALL_CARDS[cid].name}】化为一道光芒融入了你的卡组！"
            else:
                return self.leave_npc(run)

        elif npc == "艾琳":
            stock = cafe_data.get("gemcutter_stock", [])
            if idx == 1:
                if p.gold < 50:
                    return "❌ 你的金币不足 50 GP。"
                p.gold -= 50
                if p.deck:
                    cid = random.choice(p.deck)
                    card_obj = ALL_CARDS.get(cid.split(":gems:")[0])
                    if card_obj:
                        max_slots = card_obj.get_gem_slots_count()
                        base_cid = cid.split(":gems:")[0]
                        old_gems = cid.split(":gems:")[1].split(",") if ":gems:" in cid else []
                        if len(old_gems) < max_slots:
                            old_gems.append("empty")
                            new_cid = f"{base_cid}:gems:{','.join(old_gems)}"
                            p.deck.remove(cid)
                            p.deck.append(new_cid)
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return "艾琳嘻嘻一笑，拿出金刚钻在你的卡组随机一张卡牌表面精巧地打出了 1 个宝石插槽！"
            elif idx - 1 <= len(stock):
                if p.gold < 64:
                    return "❌ 你的金币不足 64 GP。"
                p.gold -= 64
                gem_id = stock[idx - 2]
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                run.node_data["cafe_data"] = cafe_data
                
                from .explore_engine import ExploreEngine
                expl = ExploreEngine(self.save_manager, self.map_engine)
                expl.start_gem_insert_flow(run, gem_id, "cafe", run.node_data.copy())
                return f"你付了 64 金币。艾琳眨了眨眼，从袖子里溜出一颗【{GEM_CONFIG[gem_id]['name']}】抛给你，进入了强制镶嵌流程！"
            else:
                return self.leave_npc(run)

        elif npc == "雷恩":
            if idx == 1:
                if p.gold < 50:
                    return "❌ 你的金币不足 50 GP。"
                p.gold -= 50
                p.max_hp += 8
                p.hp += 8
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return "🏋️ 雷恩指导你进行了一套力量训练！你的最大生命值上限永久提升了 8 点并获得了治疗！"
            elif idx == 2:
                p.hp = max(1, p.hp - 10)
                p.relics.append("gladiator_belt")
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return "🩸 你忍受剧痛在钢铁上立下契约（流失了 10 点生命值）。雷恩将他珍藏的被动遗物【角斗士皮带】赠予你！"
            else:
                return self.leave_npc(run)

        elif npc == "露娜":
            if idx == 1:
                p.hp = max(1, p.hp - 15)
                p.deck.append("neutral_astral_strike")
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return "🔮 露娜的眼眸化为纯白，撕裂了你的精神（你流失了 15 点生命值），同时卡牌【星界坠击】融入了你的卡组中！"
            elif idx == 2:
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return "🔮 露娜低语：'尤格-索托斯身负时空枷锁。当他展现出觉醒和终焉形态时，他会强行扭曲界面的时空。记住，他的第三形态拥有混沌庇护，你需要用高频的多段攻击去消磨他的虚空屏障……'"
            else:
                return self.leave_npc(run)

        elif npc == "莫里":
            if idx == 1:
                if p.gold < 60:
                    return "❌ 你的金币不足 60 GP。"
                p.gold -= 60
                p.relics.append("espresso_relic")
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return "☕ 莫里为你调配了一杯滚烫浓郁的特制咖啡！你获得了临时整备遗物【特制浓缩咖啡】（本阶段所有战斗回合开始额外得 1A）！"
            elif idx == 2:
                if p.gold < 40:
                    return "❌ 你的金币不足 40 GP。"
                p.gold -= 40
                p.hp = min(p.max_hp, p.hp + 20)
                p.deck.append("curse_indigestion")
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return "🍩 你吃下了一个散发着虚空淡紫光芒的甜甜圈（回复了 20 点生命值），但肚子里很快发出了古怪的雷鸣：一张诅咒卡【消化不良】被强行塞入了你的卡组！"
            else:
                return self.leave_npc(run)

        elif npc == "凯尔":
            if idx == 1:
                if not p.relics:
                    return "❌ 你身上没有遗物可以变卖。"
                rid = p.relics.pop(0)
                p.gold += 50
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return f"💰 你将身上的遗物【{get_relic_name(rid)}】卖给了凯尔，换取了 50 金币！"
            elif idx == 2:
                if p.gold < 120:
                    return "❌ 你的金币不足 120 GP。"
                p.gold -= 120
                rid = cafe_data.get("hunter_stock")
                if not rid:
                    rid = "heavy_armor"
                p.relics.append(rid)
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return f"🎒 你付了 120 金币，在凯尔的古玩箱里淘出了一个非常古旧的遗物：【{get_relic_name(rid)}】！"
            else:
                return self.leave_npc(run)

        elif npc == "咪咪":
            if idx == 1:
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                if random.random() < 0.3:
                    p.hp = max(1, p.hp - 3)
                    from .explore_engine import ExploreEngine
                    expl = ExploreEngine(self.save_manager, self.map_engine)
                    expl.start_gem_insert_flow(run, "gem_dmg_add_2", "cafe", run.node_data.copy())
                    return "🐱 哎呀！咪咪傲娇地给了你一爪子（流失了 3 点生命值），但爪缝里掉出了一颗普通的【增幅红宝石】！你开启了强制镶嵌流程！"
                else:
                    p.gold += 20
                    return "🐱 咪咪舒服地发出了呼噜声，它开心地赠送你 20 金币！"
            elif idx == 2:
                if p.gold < 15:
                    return "❌ 你的金币不足 15 GP。"
                p.gold -= 15
                cafe_data["dialog_state"] = "branch_a"
                return "你花了 15 金币买来一串烤鱼干，咪咪闻到味道立刻扑了上来，开心地大嚼特嚼！\n\n" + self.render_cafe(run)
            else:
                return self.leave_npc(run)
        
        elif npc == "咪咪" and state == "branch_a":
            if idx == 1:
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                if random.random() < 0.5:
                    from .explore_engine import ExploreEngine
                    expl = ExploreEngine(self.save_manager, self.map_engine)
                    expl.start_gem_insert_flow(run, "gem_shield_add_8", "cafe", run.node_data.copy())
                    return "🐱 咪咪被你揉得极为舒服，呼噜噜直叫，赠予你一颗晶莹剔透的【守护真珠】！你开启了强制镶嵌流程！"
                else:
                    p.hp = max(1, p.hp - 4)
                    return "🐱 哎呀！咪咪嫌你手重，回头咬了你一下（流失了 4 点生命值）并跳上了房梁。"
            elif idx == 2:
                curses = [cid for cid in p.deck if cid.startswith("curse_")]
                purged_msg = "（你卡组里其实没有诅咒卡牌，它只是朝你打了个饱嗝）"
                if curses:
                    cur = curses[0]
                    p.deck.remove(cur)
                    purged_msg = f"（它大口嚼吧嚼吧，把你卡组里的诅咒卡【{ALL_CARDS[cur].name}】彻底嚼碎移除，剔除了诅咒！）"
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return f"🐱 咪咪大口嚼碎了烤鱼干，发出了极其满足的叫声 {purged_msg}"
            else:
                return self.leave_npc(run)

        elif npc == "萨拉":
            if idx == 1:
                non_retained = [cid for cid in p.deck if cid in ALL_CARDS and not ALL_CARDS[cid].retain and not ":gems:" in cid]
                if not non_retained:
                    non_retained = p.deck.copy()
                if non_retained:
                    cid = random.choice(non_retained)
                    base_cid = cid.split(":gems:")[0]
                    gems_part = f":gems:{cid.split(':gems:')[1]}" if ":gems:" in cid else ""
                    if not base_cid.endswith("+retain"):
                        p.deck.remove(cid)
                        p.deck.append(f"{base_cid}+retain{gems_part}")
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return "🧵 萨拉将虚空丝线织入了你的卡组随机卡牌中，为其烙印了【保留】词条！但也因为虚空撕裂，这卡牌的魔力受损，伤害/防御效果将永久降低 4 点。"
            elif idx == 2:
                if p.gold < 80:
                    return "❌ 你的金币不足 80 GP。"
                p.gold -= 80
                attacks = [cid for cid in p.deck if cid in ALL_CARDS and ALL_CARDS[cid].type == "attack"]
                if not attacks:
                    attacks = p.deck.copy()
                if attacks:
                    cid = random.choice(attacks)
                    base_cid = cid.split(":gems:")[0]
                    gems_part = f":gems:{cid.split(':gems:')[1]}" if ":gems:" in cid else ""
                    if not base_cid.endswith("+copy_1"):
                        p.deck.remove(cid)
                        p.deck.append(f"{base_cid}+copy_1{gems_part}")
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return "🧵 萨拉微笑着收取了 80 金币，在你的随机卡牌中缝入了复制织物：你卡组中随机一张卡牌成功获得了【复制 1】被动词条！"
            else:
                return self.leave_npc(run)

        elif npc == "辛普森":
            if idx == 1:
                p.relics.append("anthem_relic_3")
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return "🎵 辛普森拨动竖琴，为你低声吟唱了一段古老史诗。你获得了临时次数遗物【赞歌】（在接下来的 3 场战斗开始时获得 2 点初始护盾）！"
            elif idx == 2:
                if p.gold < 30:
                    return "❌ 你的金币不足 30 GP。"
                p.gold -= 30
                p.deck.append("neutral_hero_anthem")
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return "🎵 辛普森非常高兴地收下 30 金币，赠予你中立稀有卡牌【英雄赞歌】！"
            else:
                return self.leave_npc(run)

        elif npc == "斯莱克":
            if idx == 1:
                if p.gold < 240:
                    return "❌ 你的金币不足 240 GP。"
                p.gold -= 240
                legendary_gems = [k for k, v in GEM_CONFIG.items() if v.get("rarity") == "legendary"]
                gem_id = random.choice(legendary_gems) if legendary_gems else "gem_dmg_mul_3"
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                run.node_data["cafe_data"] = cafe_data
                
                from .explore_engine import ExploreEngine
                expl = ExploreEngine(self.save_manager, self.map_engine)
                expl.start_gem_insert_flow(run, gem_id, "cafe", run.node_data.copy())
                return f"🪙 你付了 240 金币。斯莱克塞给你一颗传奇宝石【{GEM_CONFIG[gem_id]['name']}】，进入了强制镶嵌流程！"
            elif idx == 2:
                epic_gems = [k for k, v in GEM_CONFIG.items() if v.get("rarity") == "epic"]
                gem_id = random.choice(epic_gems) if epic_gems else "gem_copy_1"
                p.deck.append("curse_mana_backflow")
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                run.node_data["cafe_data"] = cafe_data
                
                from .explore_engine import ExploreEngine
                expl = ExploreEngine(self.save_manager, self.map_engine)
                expl.start_gem_insert_flow(run, gem_id, "cafe", run.node_data.copy())
                return f"🧪 试验开始！你卡组里被塞入了一张诅咒卡【法力逆流】。斯莱克将一颗珍奇宝石【{GEM_CONFIG[gem_id]['name']}】送给了你，开启了强制镶嵌流程！"
            else:
                return self.leave_npc(run)

        elif npc == "编号7":
            if idx == 1:
                run.node_data["temp_minus_1a"] = True
                p.relics.append("shield_battery")
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return "🔋 编号7将充能线扎入你的体内，大肆吸取你的能量（你感到一阵虚弱，下场战斗首回合将少 1A）。你获得了被动遗物【能量护盾电池】！"
            elif idx == 2:
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                if random.random() < 0.5:
                    p.gold += 150
                    return "💰 撬开成功！编号7报废，你获得了 150 金币！"
                else:
                    p.hp = max(1, p.hp - 15)
                    return "💥 警报大作！你粗暴的行为引发了强烈爆炸（你受到了 15 点真实伤害）！"
            else:
                return self.leave_npc(run)

        elif npc == "绯红":
            if idx == 1:
                loss = int(p.max_hp * 0.25)
                p.max_hp = max(5, p.max_hp - loss)
                p.hp = min(p.hp, p.max_hp)
                p.relics.append("crimson_heart")
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return f"🍷 绯红抽取了你的生命精华（最大生命值上限永久减少了 {loss} 点），赠予你珍奇遗物【绯红之心】！"
            elif idx == 2:
                removed_name = "无"
                if p.deck:
                    cid = random.choice(p.deck)
                    from ..models.state import ensure_card_state
                    card_obj = ALL_CARDS.get(ensure_card_state(cid).id)
                    removed_name = card_obj.name if card_obj else ensure_card_state(cid).id
                    p.deck.remove(cid)
                p.max_hp += 6
                p.hp += 6
                talked_npcs.append(npc)
                cafe_data["active_npc"] = None
                cafe_data["dialog_state"] = None
                return f"💋 绯红留下一记深吻。你获得最大生命上限 +6，你卡组中的一张卡牌【{removed_name}】被彻底移除！"
            else:
                return self.leave_npc(run)

        return self.leave_npc(run)
