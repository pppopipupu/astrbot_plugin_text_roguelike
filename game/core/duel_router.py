import random
import os
import json
import uuid
import re
from typing import Optional, Tuple
from ..models.state import GameRun, PlayerState, MinionState, AmuletState, BuffState
from .duel_engine import DuelEngine
from ..renderer.duel_renderer import render_duel_battle_public, render_duel_battle_private

from .duel.base import DuelCommandHandler, DuelActionHandler
from .duel import commands
from .duel import actions

def clean_user_id(uid) -> str:
    if uid is None:
        return ""
    uid_str = str(uid).strip().lower()
    if uid_str.startswith("@"):
        uid_str = uid_str[1:]
    return uid_str

class DuelRouter:
    def __init__(self, save_manager):
        self.save_manager = save_manager
        self.engine = DuelEngine(save_manager)
        self.pending_invites = {}

    def get_user_active_deck(self, user_id: str) -> Tuple[Optional[str], list]:
        data = self.save_manager.load_duel_decks(user_id)
        active = data.get("active_deck")
        decks = data.get("decks", {})
        if not active or active not in decks:
            if decks:
                first = list(decks.keys())[0]
                return first, decks[first]
            return None, []
        return active, decks[active]

    def check_deck_validity(self, deck_list: list) -> Tuple[bool, str]:
        if len(deck_list) < 25 or len(deck_list) > 50:
            return False, f"卡牌数量不合法（当前 {len(deck_list)} 张，应在 25~50 张之间）。"
        try:
            from ..data.duel_card_data import DUEL_CARD_CONFIG
        except ImportError:
            from game.data.duel_card_data import DUEL_CARD_CONFIG
        counts = {}
        for cid in deck_list:
            base_id = cid.rstrip("+")
            counts[base_id] = counts.get(base_id, 0) + 1
            cfg = DUEL_CARD_CONFIG.get(base_id, {})
            name = cfg.get("name", base_id)
            rarity = cfg.get("rarity", "common")
            ctype = cfg.get("type", "spell")
            
            limit = 4
            if rarity == "mythic" or rarity == "artifact" or ctype == "artifact":
                limit = 1
            elif rarity == "legendary":
                limit = 2
                
            if counts[base_id] > limit:
                if limit == 1:
                    return False, f"单卡超限：神话或神器卡【{name}】在每个牌组中限制只能携带 1 张。"
                elif limit == 2:
                    return False, f"单卡超限：传奇卡【{name}】在每个牌组中限制只能携带 2 张。"
                else:
                    return False, f"单卡超限：【{name}】超过了 4 张限制。"
        return True, "合法"

    def handle_deck_cmd(self, user_id: str, args: list) -> Tuple[str, bool]:
        data = self.save_manager.load_duel_decks(user_id)
        if "decks" not in data:
            data["decks"] = {}
        decks = data["decks"]
        
        if not args:
            lines = ["📋 【你的对决牌组列表】"]
            active = data.get("active_deck")
            if not decks:
                lines.append("（无任何牌组，请输入 /rogue 对决 牌组 创建 <名称> 进行创建）")
            else:
                for idx, (name, cards) in enumerate(decks.items(), 1):
                    valid, _ = self.check_deck_validity(cards)
                    act_tag = "⭐ [当前选中]" if name == active else ""
                    valid_tag = "🟢 合法" if valid else "❌ 不合法"
                    lines.append(f" [{idx}] {name} ({len(cards)}张卡) | {valid_tag} {act_tag}")
            return "\n".join(lines), False
            
        sub = args[0].lower()
        if sub in ("create", "c", "创建"):
            if len(args) < 2:
                return "❌ 请输入牌组名称，例如：/rogue 对决 牌组 创建 我的卡组1", False
            name = args[1].strip()
            if not name:
                return "❌ 牌组名称不能为空。", False
            if name in decks:
                return f"❌ 牌组【{name}】已存在。", False
            decks[name] = []
            data["active_deck"] = name
            self.save_manager.save_duel_decks(user_id, data)
            return f"✅ 成功创建空牌组【{name}】，已自动设为当前选中牌组。", False
            
        elif sub in ("select", "s", "选择"):
            if len(args) < 2:
                return "❌ 请指定要选择的牌组序号或名称。", False
            tgt = args[1].strip()
            if tgt.isdigit():
                idx = int(tgt) - 1
                keys = list(decks.keys())
                if 0 <= idx < len(keys):
                    name = keys[idx]
                else:
                    return "❌ 序号超出范围。", False
            else:
                name = tgt
                if name not in decks:
                    return f"❌ 牌组【{name}】不存在。", False
            data["active_deck"] = name
            self.save_manager.save_duel_decks(user_id, data)
            return f"✅ 已成功切换当前活动牌组为【{name}】。", False
            
        elif sub in ("info", "i", "详情"):
            name = data.get("active_deck")
            if len(args) >= 2:
                tgt = args[1].strip()
                if tgt.isdigit():
                    idx = int(tgt) - 1
                    keys = list(decks.keys())
                    if 0 <= idx < len(keys):
                        name = keys[idx]
                else:
                    name = tgt
            if not name or name not in decks:
                return "❌ 未找到指定牌组或当前没有选中的活动牌组。", False
                
            cards = decks[name]
            valid, reason = self.check_deck_validity(cards)
            lines = [f"📋 牌组【{name}】详情 ({len(cards)}张 | {'🟢 合法' if valid else '❌ 不合法: ' + reason})"]
            
            if not cards:
                lines.append("（空空如也，请输入 /rogue 对决 牌组 添加 <卡牌> 填充它）")
            else:
                counts = {}
                for cid in cards:
                    counts[cid] = counts.get(cid, 0) + 1
                    
                sorted_cids = sorted(list(counts.keys()))
                from ..entities.cards.duel import ALL_DUEL_CARDS
                for idx, cid in enumerate(sorted_cids, 1):
                    card = ALL_DUEL_CARDS.get(cid)
                    if card:
                        cost_a = card.cost_a
                        cost_str = f"{cost_a}A" if cost_a >= 0 else "X A"
                        lines.append(f" [{idx}] {card.name} (消耗: {cost_str}) x {counts[cid]}")
            return "\n".join(lines), False
            
        elif sub in ("add", "a", "添加"):
            active = data.get("active_deck")
            if not active or active not in decks:
                return "❌ 当前没有选中的活动牌组，请先创建或选择一个牌组。", False
            if len(args) < 2:
                return "❌ 请输入卡牌名称或拼音，例如：/rogue 对决 牌组 添加 挥砍 4", False
            
            query = args[1].strip()
            count = 1
            if len(args) >= 3 and args[2].isdigit():
                count = int(args[2])
                if count < 1 or count > 4:
                    count = 1
                    
            try:
                from ..data.duel_card_data import DUEL_CARD_CONFIG
            except ImportError:
                from game.data.duel_card_data import DUEL_CARD_CONFIG
            matched = []
            q_clean = query.lower()
            for cid, val in DUEL_CARD_CONFIG.items():
                name = val.get("name", "").replace("对决·", "").lower()
                if q_clean in name or q_clean in cid.lower():
                    matched.append(cid)
                    
            if not matched:
                return "❌ 未找到符合条件的对决卡牌。", False
            if len(matched) > 1:
                from ..entities.cards.duel import ALL_DUEL_CARDS
                matches_str = "、".join([f"【{ALL_DUEL_CARDS[cid].name.replace('对决·', '')}】" for cid in matched[:5]])
                return f"❌ 匹配到多个结果：{matches_str}，请提供更精确的名称。", False
                
            cid = matched[0]
            base_id = cid.rstrip("+")
            cards = decks[active]
            
            if len(cards) + count > 50:
                return "❌ 牌组容量已满，不可超过 50 张。", False
                
            cur_count = sum(1 for c in cards if c.rstrip("+") == base_id)
            cfg = DUEL_CARD_CONFIG.get(base_id, {})
            rarity = cfg.get("rarity", "common")
            ctype = cfg.get("type", "spell")
            
            limit = 4
            if rarity == "mythic" or rarity == "artifact" or ctype == "artifact":
                limit = 1
            elif rarity == "legendary":
                limit = 2
                
            if cur_count + count > limit:
                from ..entities.cards.duel import ALL_DUEL_CARDS
                cname = ALL_DUEL_CARDS[cid].name.replace('对决·', '')
                if limit == 1:
                    return f"❌ 单卡超限：神话或神器卡【{cname}】在每个牌组中限制只能携带 1 张（当前已有 {cur_count} 张）。", False
                elif limit == 2:
                    return f"❌ 单卡超限：传奇卡【{cname}】在每个牌组中限制只能携带 2 张（当前已有 {cur_count} 张）。", False
                else:
                    return f"❌ 单卡超限：【{cname}】在牌组里已有 {cur_count} 张，同名基础卡上限为 4 张。", False
                
            for _ in range(count):
                cards.append(cid)
            self.save_manager.save_duel_decks(user_id, data)
            from ..entities.cards.duel import ALL_DUEL_CARDS
            cname = ALL_DUEL_CARDS[cid].name.replace('对决·', '')
            return f"✅ 成功往牌组【{active}】添加了 {count} 张 【{cname}】。", False
            
        elif sub in ("remove", "r", "移除"):
            active = data.get("active_deck")
            if not active or active not in decks:
                return "❌ 当前没有选中的活动牌组。", False
            if len(args) < 2:
                return "❌ 请指定卡牌详情中的序号，例如：/rogue 对决 牌组 移除 2", False
                
            tgt = args[1].strip()
            if not tgt.isdigit():
                return "❌ 必须输入详情中的序号进行移除。", False
                
            idx = int(tgt) - 1
            cards = decks[active]
            
            counts = {}
            for cid in cards:
                counts[cid] = counts.get(cid, 0) + 1
            sorted_cids = sorted(list(counts.keys()))
            
            if idx < 0 or idx >= len(sorted_cids):
                return "❌ 序号超出范围。", False
                
            cid_to_rem = sorted_cids[idx]
            count = 1
            if len(args) >= 3 and args[2].isdigit():
                count = int(args[2])
                
            actual_rem = 0
            for _ in range(count):
                if cid_to_rem in cards:
                    cards.remove(cid_to_rem)
                    actual_rem += 1
                    
            self.save_manager.save_duel_decks(user_id, data)
            from ..entities.cards.duel import ALL_DUEL_CARDS
            cname = ALL_DUEL_CARDS[cid_to_rem].name.replace('对决·', '')
            return f"✅ 成功从牌组【{active}】移除了 {actual_rem} 张 【{cname}】。", False
            
        elif sub in ("export", "exp", "导出"):
            name = data.get("active_deck")
            if len(args) >= 2:
                tgt = args[1].strip()
                if tgt.isdigit():
                    idx = int(tgt) - 1
                    keys = list(decks.keys())
                    if 0 <= idx < len(keys):
                        name = keys[idx]
                else:
                    name = tgt
            if not name or name not in decks:
                return "❌ 未找到指定牌组或当前没有选中的活动牌组。", False
            cards = decks[name]
            import base64
            import json
            try:
                payload = {"name": name, "cards": cards}
                dumped = json.dumps(payload, ensure_ascii=False)
                code = base64.b64encode(dumped.encode("utf-8")).decode("utf-8")
                return f"✨ 牌组【{name}】导出成功！分享码如下（长按复制）：\n{code}\n\n可以使用以下指令导入：\n/rogue 对决 牌组 导入 <分享码> [新牌组名称]", False
            except Exception as e:
                return f"❌ 导出分享码失败: {str(e)}", False
            
        elif sub in ("import", "imp", "导入"):
            if len(args) < 2:
                return "❌ 请提供牌组分享码，例如：/rogue 对决 牌组 导入 <分享码> [自定义名称]", False
            code = args[1].strip()
            custom_name = args[2].strip() if len(args) >= 3 else None
            import base64
            import json
            try:
                decoded_bytes = base64.b64decode(code.encode("utf-8"))
                dumped = decoded_bytes.decode("utf-8")
                payload = json.loads(dumped)
            except Exception as e:
                return f"❌ 解析分享码失败，请检查分享码是否完整或正确: {str(e)}", False
            
            if not isinstance(payload, dict) or "name" not in payload or "cards" not in payload:
                return "❌ 分享码格式不正确：解析后的数据结构无效。", False
            
            orig_name = payload["name"]
            cards = payload["cards"]
            if not isinstance(cards, list):
                return "❌ 分享码卡牌列表数据格式错误。", False
            
            try:
                from ..data.duel_card_data import DUEL_CARD_CONFIG
            except ImportError:
                from game.data.duel_card_data import DUEL_CARD_CONFIG
                
            for cid in cards:
                if not isinstance(cid, str):
                    return f"❌ 分享码中包含非法的卡牌ID类型: {type(cid)}", False
                base_id = cid.rstrip("+")
                if base_id not in DUEL_CARD_CONFIG:
                    return f"❌ 分享码中包含未知的对决卡牌ID: {cid}，导入中止。", False
            
            target_name = custom_name if custom_name else orig_name
            target_name = target_name.strip()
            if not target_name:
                target_name = "导入牌组"
            
            final_name = target_name
            suffix = 0
            while final_name in decks:
                suffix += 1
                final_name = f"{target_name}_导入{suffix}"
            
            decks[final_name] = cards
            data["active_deck"] = final_name
            self.save_manager.save_duel_decks(user_id, data)
            
            valid, reason = self.check_deck_validity(cards)
            status_msg = "🟢 合法" if valid else f"❌ 不合法 ({reason})"
            return f"✅ 成功导入牌组【{final_name}】（共 {len(cards)} 张卡）并设为当前活动牌组。\n卡组状态：{status_msg}", False
            
        return "❌ 未知牌组管理子指令，请输入帮助指令获取教程。", False

    def render_duel_menu(self, user_id: str) -> str:
        active_name, deck_list = self.get_user_active_deck(user_id)
        deck_info = "🔴 未选择活动牌组"
        if active_name:
            valid, reason = self.check_deck_validity(deck_list)
            status_str = "✅ 合法" if valid else f"❌ 不合法 ({reason})"
            deck_info = f"🎴 当前活动牌组：{active_name} ({len(deck_list)}张) [{status_str}]"
            
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            "⚔️ 魔法肉鸽卡牌游戏 - 对决模式",
            "",
            "在双人对局中展现你的牌组构筑与即时决策！",
            deck_info,
            "",
            "【局外指令】",
            "👉 /rogue 对决 邀请 @用户 -- 邀请对方进行对局",
            "👉 /rogue 对决 接受     -- 接受收到的对局邀请",
            "👉 /rogue 对决 拒绝     -- 拒绝收到的对局邀请",
            "👉 /rogue 对决 牌组     -- 查看或选择你的牌组",
            "👉 /rogue 对决 牌组 导出 [序号/名称] -- 导出牌组为分享码",
            "👉 /rogue 对决 牌组 导入 <分享码> [新名称] -- 导入牌组",
            "",
            "【局内指令（在你的回合）】",
            "👉 序号 / 使用 序号 [目标] -- 使用指定手牌。例如：1 或 使用 1 e1",
            "👉 随从 序号 攻击/a [目标]   -- 指挥随从攻击。例如：随从 1 攻击 e1",
            "👉 随从 序号 技能/s [序号]   -- 释放随从技能。例如：随从 1 技能 1",
            "👉 进化 序号 [手牌/随从/护符] -- 消耗进化点进化目标。例如：进化 1",
            "👉 幸运币                  -- 消耗幸运币获得 1A（后手专属）",
            "👉 结束                    -- 结束当前回合",
            "👉 状态                    -- 在局内查看当前对战详细快照",
            "👉 队列 [指令1, 指令2...]  -- 批量顺序执行多个指令。例如：队列 [1, 随从 1 a, 结束]",
            "━━━━━━━━━━━━━━━━━━━━"
        ]
        return "\n".join(lines)

    def handle_duel_cmd(self, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        if not args or args[0].lower() in ("状态", "s", "status"):
            return self.render_duel_menu(user_id), False, None, None, None, None
            
        query_cmds = ("查询", "query", "info", "i", "抽牌堆", "draw", "draw_pile", "弃牌堆", "discard", "discard_pile", "消耗堆", "exhaust", "exhaust_pile", "随从墓地", "minion_graveyard", "mg", "minion_grave")
        if args[0].lower() in query_cmds or (args[0].lower() in ("对决", "duel") and len(args) > 1 and args[1].lower() in query_cmds):
            return self._handle_query_cmd(user_id, sender_name, args)

        if args[0].lower() in ("对决", "duel"):
            args = args[1:]
            if not args:
                return self.render_duel_menu(user_id), False, None, None, None, None
                
        sub = args[0]
        sub_lower = sub.lower()
        
        handler = DuelCommandHandler.registry.get(sub_lower)
        if handler:
            return handler.execute(self, user_id, sender_name, args)
            
        if sub.startswith("[At:") or sub.startswith("@"):
            inv_handler = DuelCommandHandler.registry.get("邀请")
            if inv_handler:
                return inv_handler.execute(self, user_id, sender_name, ["邀请", sub])
                
        return "❌ 未知的对决指令，请输入帮助指令获取教程。", False, None, None, None, None

    def route_in_game_action(self, run: GameRun, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        p1_id = run.node_data["player1_id"]
        p2_id = run.node_data["player2_id"]
        opp_id = p2_id if user_id == p1_id else p1_id
        
        query_cmds = ("查询", "query", "info", "i", "抽牌堆", "draw", "draw_pile", "弃牌堆", "discard", "discard_pile", "消耗堆", "exhaust", "exhaust_pile", "随从墓地", "minion_graveyard", "mg", "minion_grave")
        if args[0].lower() in query_cmds or (args[0].lower() in ("对决", "duel") and len(args) > 1 and args[1].lower() in query_cmds):
            return self._handle_query_cmd(user_id, sender_name, args)

        cmd = args[0].lower()
        if cmd in ("帮助", "help", "hp", "放弃", "abandon", "confirm", "牌组", "deck", "dk", "模式", "mode", "接受", "accept", "邀请", "invite", "iv") or cmd.startswith("[at:") or cmd.startswith("@"):
            return self.handle_duel_cmd(user_id, sender_name, args)
            
        if cmd in ("对决", "duel"):
            if len(args) >= 2:
                sub_cmd = args[1].lower()
                if sub_cmd in ("放弃", "abandon", "confirm", "帮助", "help", "hp", "牌组", "deck", "dk", "模式", "mode", "接受", "accept", "邀请", "invite", "iv") or sub_cmd.startswith("[at:") or sub_cmd.startswith("@"):
                    return self.handle_duel_cmd(user_id, sender_name, args[1:])
                args = args[1:]
                cmd = args[0].lower()
            else:
                return "❌ 对战进行中，只能使用局内对决指令（如：使用、随从、进化、结束、幸运币）或输入帮助指令查看指南。", False, None, None, None, None
            
        if cmd in ("放弃", "abandon"):
            return self.handle_duel_cmd(user_id, sender_name, ["放弃"])

        cmd = args[0].lower()
        is_queue = False
        raw_cmd = ""
        if cmd in ("队列", "q", "queue"):
            is_queue = True
            raw_cmd = " ".join(args[1:]).strip()
        else:
            raw_cmd = " ".join(args).strip()
            if "," in raw_cmd or "，" in raw_cmd:
                is_queue = True

        if is_queue:
            if raw_cmd.startswith("[") and raw_cmd.endswith("]"):
                raw_cmd = raw_cmd[1:-1].strip()
            from .duel.base import split_by_comma_with_brackets
            items = split_by_comma_with_brackets(raw_cmd)
            results = []
            term = False
            for item in items:
                if not item:
                    continue
                parts_sub = item.split()
                if not parts_sub:
                    continue
                if parts_sub[0].isdigit():
                    parts_sub = ["使用"] + parts_sub
                res_pub, should_term, _, _, _, _ = self._route_single_action(run, user_id, sender_name, parts_sub)
                results.append(res_pub)
                if should_term:
                    term = True
                    break
            
            self.save_manager.save_duel_save(run.user_id, run)
            
            public_text = render_duel_battle_public(run)
            dm2 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = user_id
            dm1 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = opp_id
            
            public_text = self.engine._append_logs_to_res(run, public_text)
            dm1 = self.engine._append_logs_to_res(run, dm1)
            dm2 = self.engine._append_logs_to_res(run, dm2)
            
            summary_pub = "\n".join(results) + "\n" + public_text
            return summary_pub, term, user_id, dm1, opp_id, dm2
            
        return self._route_single_action(run, user_id, sender_name, args)

    def _route_single_action(self, run: GameRun, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        if args[0].isdigit():
            args = ["使用"] + args
            
        cmd = args[0].lower()
        handler = DuelActionHandler.registry.get(cmd)
        if handler:
            return handler.execute(self, run, user_id, sender_name, args)
            
        return "❌ 未知动作指令。输入帮助指令可查看操作提示。", False, None, None, None, None

    def _save_and_render_state(self, run: GameRun, user_id: str, tip: str = "") -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        self.save_manager.save_duel_save(run.user_id, run)
        
        p1_id = run.node_data["player1_id"]
        p2_id = run.node_data["player2_id"]
        
        current_acting_id = run.user_id
        
        if current_acting_id == p1_id:
            dm1 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = p2_id
            dm2 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = p1_id
        else:
            dm2 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = p1_id
            dm1 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = p2_id
            
        public_text = render_duel_battle_public(run)
        public_text = self.engine._append_logs_to_res(run, public_text)
        dm1 = self.engine._append_logs_to_res(run, dm1)
        dm2 = self.engine._append_logs_to_res(run, dm2)
        
        if tip:
            public_text = tip + "\n" + public_text
            
        return public_text, False, p1_id, dm1, p2_id, dm2

    def _check_victory(self, run: GameRun, user_id: str, sender_name: str) -> Optional[Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]]:
        p1_id = run.node_data["player1_id"]
        p2_id = run.node_data["player2_id"]
        p1_name = run.node_data["player1_name"]
        p2_name = run.node_data["player2_name"]
        
        acting_id = run.user_id
        waiting_id = p2_id if acting_id == p1_id else p1_id
        
        if run.player2.hp <= 0:
            self.save_manager.delete_duel_save(user_id)
            win_stats = self.save_manager.load_stats(acting_id)
            win_stats.gp += 2000
            self.save_manager.save_stats(acting_id, win_stats)
            win_text = f"🏆 恭喜玩家【{sender_name}】获得了最终胜利！对方领主生命值已归零！获得 2000 GP！"
            return win_text, True, acting_id, win_text, waiting_id, "☠️ 你的生命值已归零，你输了。"
            
        if run.player.hp <= 0:
            self.save_manager.delete_duel_save(user_id)
            win_stats = self.save_manager.load_stats(waiting_id)
            win_stats.gp += 2000
            self.save_manager.save_stats(waiting_id, win_stats)
            win_name = p2_name if acting_id == p1_id else p1_name
            win_text = f"🏆 恭喜玩家【{win_name}】获得了最终胜利！对方领主生命值已归零！获得 2000 GP！"
            return win_text, True, waiting_id, win_text, acting_id, "☠️ 你的生命值已归零，你输了。"
            
        return None

    def _check_time_stop_interruption(self, run: GameRun, initial_opp_hp: int, initial_opp_shield: int, initial_minion_status: dict) -> bool:
        if run.node_data.get("extra_turns_left", 0) <= 0:
            return False
        opp = run.player2
        damaged = (opp.hp < initial_opp_hp) or (opp.shield < initial_opp_shield)
        if not damaged:
            for gid, ohp in initial_minion_status.items():
                if gid in opp.minions:
                    cur_m = opp.minions[gid]
                    if cur_m.hp < ohp:
                        damaged = True
                        break
                else:
                    damaged = True
                    break
        return damaged

    def _handle_query_cmd(self, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        if not args:
            return "❌ 请输入具体的查询内容。", False, None, None, None, None
            
        cmd = args[0].lower()
        if cmd in ("对决", "duel"):
            if len(args) > 1:
                args = args[1:]
                cmd = args[0].lower()
            else:
                return "❌ 请输入具体的查询内容。", False, None, None, None, None

        run = self.save_manager.load_duel_save(user_id)
        
        is_query_cmd = cmd in ("查询", "query", "info", "i")
        sub_query = None
        if is_query_cmd:
            if len(args) > 1:
                sub_query = " ".join(args[1:]).strip().lower()
            else:
                if run:
                    public_text = render_duel_battle_public(run)
                    dm1 = render_duel_battle_private(run)
                    p1_id = run.node_data["player1_id"]
                    p2_id = run.node_data["player2_id"]
                    opp_id = p2_id if user_id == p1_id else p1_id
                    
                    run.player, run.player2 = run.player2, run.player
                    run.user_id = opp_id
                    dm2 = render_duel_battle_private(run)
                    
                    run.player, run.player2 = run.player2, run.player
                    run.user_id = user_id
                    
                    public_text = self.engine._append_logs_to_res(run, public_text)
                    dm1 = self.engine._append_logs_to_res(run, dm1)
                    dm2 = self.engine._append_logs_to_res(run, dm2)
                    
                    return public_text, False, user_id, dm1, opp_id, dm2
                else:
                    return "❌ 只有在对战中才能查询详细战斗信息。请输入想要查询的卡牌、随从、Buff名称。\n💡 提示：你可以输入：对决查询 <名称>（如：对决查询 痛击）或对决查询 buff 查看相关介绍。", False, None, None, None, None
        else:
            sub_query = cmd
            
        if sub_query:
            if sub_query in ("抽牌堆", "draw", "draw_pile", "弃牌堆", "discard", "discard_pile", "消耗堆", "exhaust", "exhaust_pile", "随从墓地", "minion_graveyard", "mg", "minion_grave"):
                if not run:
                    return f"❌ 只有在对决战斗中才能查询对决{sub_query}。", False, None, None, None, None
                
                from ..renderer import GameRenderer
                if sub_query in ("抽牌堆", "draw", "draw_pile"):
                    render_res = GameRenderer.render_draw_pile(run)
                elif sub_query in ("弃牌堆", "discard", "discard_pile"):
                    render_res = GameRenderer.render_discard_pile(run)
                elif sub_query in ("消耗堆", "exhaust", "exhaust_pile"):
                    render_res = GameRenderer.render_exhaust_pile(run)
                else:
                    render_res = GameRenderer.render_minion_graveyard(run)
                    
                return f"✨ 对局当前【{sub_query}】信息已通过私聊发送给你！", False, user_id, render_res, None, None

            res_str = self.render_duel_query_info(sub_query)
            return res_str, False, None, None, None, None
            
        return "❌ 未知的查询指令。", False, None, None, None, None

    def render_duel_query_info(self, query_str: str) -> str:
        q = query_str.strip().lower()
        if not q:
            return "❌ 请输入具体的查询内容。"
            
        try:
            from ..data.duel_card_data import DUEL_CARD_CONFIG, QUEST_CONFIGS
        except ImportError:
            from game.data.duel_card_data import DUEL_CARD_CONFIG, QUEST_CONFIGS
            
        lines = ["━━━━━━━━━━━━━━━━━━━━", f"🔍 对决查询结果：{query_str}", ""]
        found = False
        
        for cid, val in DUEL_CARD_CONFIG.items():
            name = val.get("name", cid).replace("对决·", "")
            if q == cid.lower() or q == name.lower() or q in name.lower() or q in cid.lower():
                found = True
                rarity = val.get("rarity", "common")
                rarity_map = {
                    "common": "普通",
                    "rare": "稀有",
                    "epic": "珍奇",
                    "legendary": "传奇",
                    "mythic": "神话",
                    "artifact": "神器",
                    "curse": "诅咒"
                }
                rname = rarity_map.get(rarity, rarity)
                cost_a = val.get("cost_a", 0)
                cost_ba = val.get("cost_ba", 0)
                cost_str = ""
                if cost_a == -1:
                    cost_str += "X A "
                elif cost_a > 0:
                    cost_str += f"{cost_a}A "
                if cost_ba == -1:
                    cost_str += "X BA "
                elif cost_ba > 0:
                    cost_str += f"{cost_ba}BA "
                cost_str = cost_str.strip() or "0"
                
                lines.append(f"🎴 对决卡牌：【{name}】 ({rname})")
                lines.append(f"类型：{val.get('type', 'spell')} | 消耗: {cost_str}")
                lines.append(f"效果：{val.get('desc', '')}")
                lines.append("")
                
        for qid, val in QUEST_CONFIGS.items():
            name = val.get("name", qid)
            if q == qid.lower() or q == name.lower() or q in name.lower() or q in qid.lower():
                found = True
                rarity = val.get("rarity", "common")
                rname = {
                    "common": "普通", "rare": "稀有", "epic": "珍奇", 
                    "legendary": "传奇", "mythic": "神话", "artifact": "神器", "curse": "诅咒"
                }.get(rarity, rarity)
                cost_a = val.get("cost_a", 0)
                cost_ba = val.get("cost_ba", 0)
                cost_str = ""
                if cost_a > 0: cost_str += f"{cost_a}A "
                if cost_ba > 0: cost_str += f"{cost_ba}BA "
                cost_str = cost_str.strip() or "0"
                
                lines.append(f"🏆 对决任务/奖励：【{name}】 ({rname})")
                lines.append(f"类型：{val.get('type', 'spell')} | 消耗: {cost_str}")
                lines.append(f"描述：{val.get('desc', '')}")
                lines.append("")
                
        from ..renderer.query import render_query_info
        public_res = render_query_info(query_str)
        if "🔍 查询结果：" in public_res:
            parts = public_res.split("🔍 查询结果：" + query_str)[1].strip()
            if parts:
                found = True
                lines.append(parts)
                
        if not found:
            return f"❌ 未在对决模式中匹配到“{query_str}”相关的卡牌、随从、Buff、遗物或词条信息。"
            
        return "\n".join(lines).strip()
