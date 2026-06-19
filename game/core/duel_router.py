import random
import os
import json
import uuid
from typing import Optional, Tuple
from ..models.state import GameRun, PlayerState, MinionState, AmuletState, BuffState
from .duel_engine import DuelEngine
from ..renderer.duel_renderer import render_duel_battle_public, render_duel_battle_private

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
        counts = {}
        for cid in deck_list:
            base_id = cid.rstrip("+")
            counts[base_id] = counts.get(base_id, 0) + 1
            if counts[base_id] > 4:
                try:
                    from ..data.duel_card_data import DUEL_CARD_CONFIG
                except ImportError:
                    from game.data.duel_card_data import DUEL_CARD_CONFIG
                cfg = DUEL_CARD_CONFIG.get(base_id, {})
                name = cfg.get("name", base_id).replace("对决·", "")
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
            if cur_count + count > 4:
                from ..entities.cards.duel import ALL_DUEL_CARDS
                cname = ALL_DUEL_CARDS[cid].name.replace('对决·', '')
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
            
        return "❌ 未知牌组管理子指令，请输入帮助指令获取教程。", False

    def perform_invite(self, user_id: str, sender_name: str, target: str) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        import re
        opp_id = target.strip()
        opp_id_match = re.search(r"qq=([^\s\]]+)", opp_id)
        if opp_id_match:
            opp_id = opp_id_match.group(1)
        if opp_id.startswith("@"):
            opp_id = opp_id[1:]
            
        if not opp_id:
            return "❌ 未匹配到被邀请的对方用户 ID。", False, None, None, None, None
            
        opp_id_clean = clean_user_id(opp_id)
        user_id_clean = clean_user_id(user_id)
        if opp_id_clean == user_id_clean or opp_id_clean.split(":")[0] == user_id_clean.split(":")[0]:
            return "❌ 不能与自己进行对决。", False, None, None, None, None
            
        _, my_deck = self.get_user_active_deck(user_id)
        my_valid, my_err = self.check_deck_validity(my_deck)
        if not my_valid:
            return f"❌ 无法发起邀请：你的活动牌组不合法（{my_err}）。请先进行构筑并保证 25~50 张牌。", False, None, None, None, None
            
        self.pending_invites[user_id_clean] = opp_id_clean
        self.pending_invites[user_id_clean + "_name"] = sender_name
        self.pending_invites[user_id_clean + "_raw_target"] = opp_id
        self.pending_invites[user_id_clean + "_raw_sender"] = user_id
        
        return f"⚔️ 玩家【{sender_name}】向你发起了 TCG 卡牌对决！请输入 /rogue 对决 接受 (或 accept) 以开始对战！", False, opp_id, f"⚔️ 【{sender_name}】向你发起了 TCG 卡牌对决！输入 /rogue 对决 接受 开始对局！", None, None

    def handle_duel_cmd(self, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        if not args:
            return "❌ 请提供对决子指令或 At 目标进行对决邀请。", False, None, None, None, None
            
        if args[0].lower() in ("对决", "duel"):
            args = args[1:]
            if not args:
                return "❌ 请提供对决子指令或 At 目标进行对决邀请。", False, None, None, None, None
                
        sub = args[0]
        sub_lower = sub.lower()
        
        if sub_lower in ("帮助", "help", "hp"):
            help_text = (
                "━━━━━━━━━━━━━━━━━━━━\n"
                "⚔️ 【对决模式 (Duel) 指令帮助手册】\n"
                "对决模式是完全独立于肉鸽模式的双人 TCG 卡牌对决系统。\n\n"
                "💡 [局外/系统指令] (前缀支持 .duel 或 /duel)：\n"
                "• 发起对决：.duel @对方 或者是 .duel 邀请 <目标ID/At> (或 invite/iv)\n"
                "• 接受对决：.duel 接受 (或 accept)\n"
                "• 开启/关闭个人免前缀对决模式：.duel 模式 (或 mode)\n"
                "• 直接认输：.duel 放弃 (或 abandon)\n"
                "• 牌组管理：.duel 牌组 (或 deck/dk) <子指令>\n"
                "  - 创建牌组：创建 <名称> (或 create)\n"
                "  - 选择牌组：选择 <序号/名称> (或 select)\n"
                "  - 牌组详情：详情 (或 info)\n"
                "  - 添加卡牌：添加 <卡牌名> [数量] (或 add)\n"
                "  - 移除卡牌：移除 <详情序号> [数量] (或 remove)\n\n"
                "⚔️ [局内对局动作] (仅在你的回合生效，可用简写)：\n"
                "• 查看状态：.duel 状态 (或 status/s/查看/overview)\n"
                "• 使用卡牌：.duel 使用 <手牌序号> [目标格子] (或 play/use/p)\n"
                "  (注：物理或法术伤害牌默认只能以敌方随从格子 e2-e7 为目标，有 face_target 词条 of 直伤卡方可打领主 e1)\n"
                "• 随从攻击：.duel 随从 <我方格子> [攻击] [敌方格子] (或 minion/atk/m)\n"
                "  (注：进场首回合随从召唤失调，突进/冲锋词条除外，未指定目标默认打敌方第一个存活随从/领主)\n"
                "• 进化卡牌：.duel 进化 <我方格子/手牌序号> (或 evolve/ev)\n"
                "  (注：第 3 回合起解禁，每回合可进化一次，随从生命补满且攻血+2，护符进化不减吟唱)\n"
                "• 使用幸运币：.duel 幸运币 (或 coin/cn)\n"
                "  (注：仅后手机会获得 2 个幸运币，使用不占手牌，本回合动作点 A+1)\n"
                "• 结束回合：.duel 结束 (或 end/结束回合/e)\n"
                "━━━━━━━━━━━━━━━━━━━━"
            )
            return help_text, False, None, None, None, None
            
        elif sub_lower in ("牌组", "deck", "dk"):
            res, term = self.handle_deck_cmd(user_id, args[1:])
            return res, term, None, None, None, None
            
        elif sub_lower in ("接受", "accept"):
            invite_sender_clean = None
            cur_user_clean = clean_user_id(user_id)
            for sender_clean, target_clean in list(self.pending_invites.items()):
                if sender_clean.endswith("_name") or sender_clean.endswith("_raw_target") or sender_clean.endswith("_raw_sender"):
                    continue
                tc_part = target_clean.split(":")[0]
                cc_part = cur_user_clean.split(":")[0]
                if target_clean == cur_user_clean or tc_part == cc_part:
                    invite_sender_clean = sender_clean
                    break
            if not invite_sender_clean:
                return "❌ 你当前没有收到任何未处理的对决邀请。", False, None, None, None, None
                
            opp_id = self.pending_invites[invite_sender_clean + "_raw_sender"]
            raw_target_id = self.pending_invites[invite_sender_clean + "_raw_target"]
            p1_name = self.pending_invites.get(invite_sender_clean + "_name", "玩家一")
            
            del self.pending_invites[invite_sender_clean]
            del self.pending_invites[invite_sender_clean + "_name"]
            del self.pending_invites[invite_sender_clean + "_raw_sender"]
            del self.pending_invites[invite_sender_clean + "_raw_target"]
            
            p1_active, p1_deck = self.get_user_active_deck(opp_id)
            p2_active, p2_deck = self.get_user_active_deck(raw_target_id)
            
            p1_valid, p1_err = self.check_deck_validity(p1_deck)
            p2_valid, p2_err = self.check_deck_validity(p2_deck)
            
            if not p1_valid:
                return f"❌ 无法开始：发起方牌组不合法（{p1_err}）。", False, None, None, None, None
            if not p2_valid:
                return f"❌ 无法开始：你的活动牌组不合法（{p2_err}）。请进行构筑并保持 25~50 张牌。", False, None, None, None, None
                
            game_id = str(uuid.uuid4())[:8]
            
            p1_state = PlayerState(hp=200, max_hp=200, shield=0, gold=0, stage=1, deck=p1_deck)
            p2_state = PlayerState(hp=200, max_hp=200, shield=0, gold=0, stage=1, deck=p2_deck)
            
            run = GameRun(
                user_id=opp_id,
                node_type="duel",
                player=p1_state,
                player2=p2_state,
                node_data={
                    "player1_id": opp_id,
                    "player2_id": raw_target_id,
                    "player1_name": p1_name,
                    "player2_name": sender_name
                }
            )
            
            self.engine.init_duel(run)
            self.save_manager.bind_duel_game(opp_id, raw_target_id, game_id)
            self.save_manager.save_duel_save(opp_id, run)
            
            public_text = render_duel_battle_public(run)
            dm1 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = raw_target_id
            dm2 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = opp_id
            
            return public_text, False, opp_id, dm1, raw_target_id, dm2
            
        elif sub_lower in ("放弃", "abandon", "confirm"):
            game_id = self.save_manager.get_duel_game_id(user_id)
            if not game_id:
                return "❌ 你当前不在任何对局中。", False, None, None, None, None
                
            run = self.save_manager.load_duel_save(user_id)
            if not run:
                return "❌ 未找到对应对战存档。", False, None, None, None, None
                
            p1_id = run.node_data["player1_id"]
            p2_id = run.node_data["player2_id"]
            p1_name = run.node_data["player1_name"]
            p2_name = run.node_data["player2_name"]
            
            opp_id = p2_id if user_id == p1_id else p1_id
            opp_name = p2_name if user_id == p1_id else p1_name
            my_name = p1_name if user_id == p1_id else p2_name
            
            self.save_manager.delete_duel_save(user_id)
            
            opp_stats = self.save_manager.load_stats(opp_id)
            opp_stats.gp += 2000
            self.save_manager.save_stats(opp_id, opp_stats)
            
            res_text = f"🏳️ 玩家【{my_name}】直接认输了！对决结束，玩家【{opp_name}】获得了最终胜利！获得 2000 GP！"
            return res_text, True, opp_id, res_text, user_id, "🏳️ 你已认输，本局对战结束。"
            
        elif sub_lower in ("模式", "mode"):
            stats = self.save_manager.load_stats(user_id)
            stats.duel_mode = not stats.duel_mode
            if stats.duel_mode:
                stats.rogue_mode = False
            self.save_manager.save_stats(user_id, stats)
            status_str = "开启" if stats.duel_mode else "关闭"
            return f"✨ 免前缀对决模式已{status_str}！此设置仅对你个人生效。", False, None, None, None, None
            
        elif sub_lower in ("邀请", "invite", "iv"):
            if len(args) < 2:
                return "❌ 请指定要邀请的对方用户 ID，例如：/rogue 对决 邀请 @玩家", False, None, None, None, None
            target = args[1]
            return self.perform_invite(user_id, sender_name, target)
            
        else:
            if sub.startswith("[At:") or sub.startswith("@"):
                return self.perform_invite(user_id, sender_name, sub)
            return "❌ 未知的对决指令，请输入帮助指令获取教程。", False, None, None, None, None

    def route_in_game_action(self, run: GameRun, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        current_turn_id = run.node_data.get("current_turn_id")
        p1_id = run.node_data["player1_id"]
        p2_id = run.node_data["player2_id"]
        
        opp_id = p2_id if user_id == p1_id else p1_id
        
        cmd = args[0].lower()
        
        if cmd in ("帮助", "help", "hp", "放弃", "abandon", "confirm", "牌组", "deck", "dk", "模式", "mode"):
            return self.handle_duel_cmd(user_id, sender_name, args)
            
        if cmd in ("对决", "duel"):
            if len(args) >= 2:
                sub_cmd = args[1].lower()
                if sub_cmd in ("放弃", "abandon", "confirm", "帮助", "help", "hp", "牌组", "deck", "dk", "模式", "mode"):
                    return self.handle_duel_cmd(user_id, sender_name, args[1:])
                args = args[1:]
                cmd = args[0].lower()
            else:
                return "❌ 对战进行中，只能使用局内对决指令（如：使用、随从、进化、结束、幸运币）或输入帮助指令查看指南。", False, None, None, None, None
            
        if cmd in ("放弃", "abandon"):
            return self.handle_duel_cmd(user_id, sender_name, ["放弃"])
            
        if cmd in ("使用", "use", "u", "play", "p"):
            if user_id != current_turn_id:
                return "❌ 当前是对方的回合，请耐心等待。", False, None, None, None, None
            if len(args) < 2:
                return "❌ 请输入要使用的手牌序号，例如：/rogue 使用 1", False, None, None, None, None
                
            tgt_idx_str = args[1]
            if not tgt_idx_str.isdigit():
                return "❌ 请提供合法的数字序号。", False, None, None, None, None
                
            idx = int(tgt_idx_str) - 1
            p = run.player
            if idx < 0 or idx >= len(p.hand):
                return "❌ 手牌序号超出范围。", False, None, None, None, None
                
            cid = p.hand[idx]
            from ..entities.cards.duel import ALL_DUEL_CARDS
            card = ALL_DUEL_CARDS.get(cid)
            if not card:
                return "❌ 未找到对应卡牌实体。", False, None, None, None, None
                
            try:
                from ..data.duel_card_data import DUEL_CARD_CONFIG
            except ImportError:
                from game.data.duel_card_data import DUEL_CARD_CONFIG
            cfg = DUEL_CARD_CONFIG.get(card.id, {})
            cost_a = card.cost_a
            cost_ba = card.cost_ba
            
            x_cost_a = False
            x_cost_ba = False
            
            if cost_a == -1:
                cost_a = p.actions
                x_cost_a = True
            if cost_ba == -1:
                cost_ba = p.bonus_actions
                x_cost_ba = True
                
            if p.actions < cost_a or p.bonus_actions < cost_ba:
                return f"❌ 动作点不足，该牌需要 {card.cost_a}A {card.cost_ba}BA，你当前有 {p.actions}A {p.bonus_actions}BA。", False, None, None, None, None
                
            target = None
            if len(args) >= 3:
                target = args[2].lower()
            else:
                is_damage = ("base_dmg" in cfg or "damage" in cfg or "damage_type" in cfg)
                if is_damage and card.type == "spell":
                    for i in range(1, 7):
                        if str(i) in run.player2.minions:
                            target = f"e{i+1}"
                            break
                    if not target:
                        if cfg.get("face_target", True):
                            target = "e1"
                        else:
                            return "❌ 敌方无随从，且该卡牌无法以领主为目标！", False, None, None, None, None
                            
            if target and target.startswith("e"):
                is_damage = ("base_dmg" in cfg or "damage" in cfg or "damage_type" in cfg)
                if is_damage and not cfg.get("face_target", True) and target == "e1":
                    return "❌ 该卡牌只能以随从为目标，无法以敌方领主为目标。", False, None, None, None, None
                    
            if x_cost_a:
                run.node_data["last_x_cost_a"] = cost_a
            if x_cost_ba:
                run.node_data["last_x_cost_ba"] = cost_ba
                
            p.actions -= cost_a
            p.bonus_actions -= cost_ba
            
            p.hand.pop(idx)
            
            err_msg = card.execute(run, target, self.engine)
            if err_msg:
                p.hand.insert(idx, cid)
                p.actions += cost_a
                p.bonus_actions += cost_ba
                return err_msg, False, None, None, None, None
                
            if not card.exhaust:
                if card.type not in ("minion", "amulet"):
                    p.discard_pile.append(cid)
            
            from ..models.events import CardPlayedEvent
            self.engine.event_bus.dispatch(CardPlayedEvent(run, card, "p0", target))
            
            if run.player2.hp <= 0:
                self.save_manager.delete_duel_save(user_id)
                my_stats = self.save_manager.load_stats(user_id)
                my_stats.gp += 2000
                self.save_manager.save_stats(user_id, my_stats)
                win_text = f"🏆 恭喜玩家【{sender_name}】获得了最终胜利！对方领主生命值已归零！获得 2000 GP！"
                return win_text, True, opp_id, win_text, user_id, "☠️ 你的生命值已归零，你输了。"
                
            self.save_manager.save_duel_save(user_id, run)
            
            public_text = render_duel_battle_public(run)
            dm1 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = opp_id
            dm2 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = user_id
            
            public_text = self.engine._append_logs_to_res(run, public_text)
            dm1 = self.engine._append_logs_to_res(run, dm1)
            dm2 = self.engine._append_logs_to_res(run, dm2)
            
            use_tip = f"📢 玩家【{sender_name}】打出了卡牌【{card.name.replace('对决·', '')}】！"
            public_text = use_tip + "\n" + public_text
            
            return public_text, False, user_id, dm1, opp_id, dm2
            
        elif cmd in ("随从", "minion", "m", "attack", "atk", "sk", "skill"):
            if user_id != current_turn_id:
                return "❌ 当前是对方的回合，请耐心等待。", False, None, None, None, None
            if len(args) < 2:
                return "❌ 请输入我方随从格子序号，例如：/rogue 随从 1 攻击 e1", False, None, None, None, None
                
            grid = args[1]
            p = run.player
            if grid not in p.minions:
                return f"❌ 你的战场格子 [{grid}] 没有部署随从。", False, None, None, None, None
                
            m = p.minions[grid]
            
            stunned = any(b.id == "stun" for b in m.buffs)
            sickness = any(b.id == "summon_sickness" for b in m.buffs)
            
            if stunned:
                return f"❌ 随从【{m.name}】处于眩晕状态，无法行动。", False, None, None, None, None
            if sickness:
                return f"❌ 随从【{m.name}】处于召唤失调状态，本回合无法攻击。", False, None, None, None, None
            if m.attack_actions < 1:
                return f"❌ 随从【{m.name}】本回合攻击次数已用尽。", False, None, None, None, None
                
            target = None
            if len(args) >= 4:
                target = args[3].lower()
            elif len(args) >= 3 and args[2].lower() not in ("攻击", "attack", "atk", "a"):
                target = args[2].lower()
                
            if not target:
                for i in range(1, 7):
                    if str(i) in run.player2.minions:
                        target = f"e{i+1}"
                        break
                if not target:
                    target = "e1"
                    
            if target == "e1":
                has_rush = any(b.id == "rush_buff" for b in m.buffs)
                if has_rush:
                    return f"❌ 随从【{m.name}】本回合处于突进状态，只能攻击敌方随从，无法直接攻击领主。", False, None, None, None, None
                    
            p2 = run.player2
            target_name = "未知"
            if target == "e1":
                target_name = run.node_data.get("player2_name" if run.user_id == p1_id else "player1_name", "对手")
                self.engine._damage_target(run, "e1", m.atk, source=f"p{grid}", damage_type="attack")
            elif target.startswith("e") and len(target) > 1:
                opp_grid = str(int(target[1:]) - 1)
                if opp_grid not in p2.minions:
                    return f"❌ 敌方战场对应格子 [{opp_grid}] 没有随从存在。", False, None, None, None, None
                enemy_m = p2.minions[opp_grid]
                target_name = enemy_m.name
                
                self.engine._damage_target(run, target, m.atk, source=f"p{grid}", damage_type="attack")
                
                if opp_grid in p2.minions:
                    enemy_m = p2.minions[opp_grid]
                    self.engine._damage_target(run, f"p{grid}", enemy_m.atk, source=target, damage_type="attack")
            else:
                return "❌ 攻击目标非法，随从只能攻击 e1-e7。", False, None, None, None, None
                
            m_name = m.name
            m.attack_actions -= 1
            m.actions -= 1
            
            if run.player2.hp <= 0:
                self.save_manager.delete_duel_save(user_id)
                my_stats = self.save_manager.load_stats(user_id)
                my_stats.gp += 2000
                self.save_manager.save_stats(user_id, my_stats)
                win_text = f"🏆 恭喜玩家【{sender_name}】获得了最终胜利！对方领主生命值已归零！获得 2000 GP！"
                return win_text, True, opp_id, win_text, user_id, "☠️ 你的生命值已归零，你输了。"
            if run.player.hp <= 0:
                self.save_manager.delete_duel_save(user_id)
                opp_stats = self.save_manager.load_stats(opp_id)
                opp_stats.gp += 2000
                self.save_manager.save_stats(opp_id, opp_stats)
                win_text = f"🏆 恭喜玩家【{run.node_data['player2_name' if run.user_id == p1_id else 'player1_name']}】获得了最终胜利！对方领主生命值已归零！获得 2000 GP！"
                return win_text, True, opp_id, win_text, user_id, "☠️ 你的生命值已归零，你输了。"
                
            self.save_manager.save_duel_save(user_id, run)
            
            public_text = render_duel_battle_public(run)
            dm1 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = opp_id
            dm2 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = user_id
            
            public_text = self.engine._append_logs_to_res(run, public_text)
            dm1 = self.engine._append_logs_to_res(run, dm1)
            dm2 = self.engine._append_logs_to_res(run, dm2)
            
            atk_tip = f"📢 玩家【{sender_name}】指挥随从【{m_name.replace('+', '')}】攻击了【{target_name.replace('+', '')}】！"
            public_text = atk_tip + "\n" + public_text
            
            return public_text, False, user_id, dm1, opp_id, dm2
            
        elif cmd in ("幸运币", "coin", "cn"):
            res = self.engine.use_coin(run, user_id)
            if res.startswith("❌"):
                return res, False, None, None, None, None
                
            self.save_manager.save_duel_save(user_id, run)
            
            public_text = render_duel_battle_public(run)
            dm1 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = opp_id
            dm2 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = user_id
            
            public_text = self.engine._append_logs_to_res(run, public_text)
            dm1 = self.engine._append_logs_to_res(run, dm1)
            dm2 = self.engine._append_logs_to_res(run, dm2)
            
            coin_tip = f"📢 玩家【{sender_name}】使用了幸运币，获得了 1 点动作点！"
            public_text = coin_tip + "\n" + public_text
            
            return public_text, False, user_id, dm1, opp_id, dm2
            
        elif cmd in ("进化", "evolve", "ev"):
            if user_id != current_turn_id:
                return "❌ 当前是对方的回合，请耐心等待。", False, None, None, None, None
            if len(args) < 2:
                return "❌ 请输入进化目标手牌序号或格子，例如：/rogue 进化 1 或 /rogue 进化 p1", False, None, None, None, None
                
            target = args[1]
            evolve_target_name = "未知"
            p = run.player
            if target.isdigit():
                idx = int(target) - 1
                if 0 <= idx < len(p.hand):
                    from ..entities.cards.duel import ALL_DUEL_CARDS
                    cid = p.hand[idx]
                    card = ALL_DUEL_CARDS.get(cid)
                    if card:
                        evolve_target_name = f"手牌【{card.name.replace('对决·', '')}】"
            elif target.startswith("p") and len(target) > 1:
                grid = target[1:]
                if grid in p.minions:
                    evolve_target_name = f"随从【{p.minions[grid].name}】"
                elif grid in p.amulets:
                    evolve_target_name = f"护符【{p.amulets[grid].name}】"
                    
            res = self.engine.evolve_card(run, user_id, target)
            if res.startswith("❌"):
                return res, False, None, None, None, None
                
            self.save_manager.save_duel_save(user_id, run)
            
            public_text = render_duel_battle_public(run)
            dm1 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = opp_id
            dm2 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = user_id
            
            public_text = self.engine._append_logs_to_res(run, public_text)
            dm1 = self.engine._append_logs_to_res(run, dm1)
            dm2 = self.engine._append_logs_to_res(run, dm2)
            
            evolve_tip = f"📢 玩家【{sender_name}】将{evolve_target_name.replace('+', '')}进化了！"
            public_text = evolve_tip + "\n" + public_text
            
            return public_text, False, user_id, dm1, opp_id, dm2
            
        elif cmd in ("结束", "end", "endturn", "结束回合", "e"):
            if user_id != current_turn_id:
                return "❌ 现在不是你的回合，无法结束回合。", False, None, None, None, None
                
            self.engine.end_turn(run)
            if run.player2.hp <= 0:
                self.save_manager.delete_duel_save(user_id)
                my_stats = self.save_manager.load_stats(user_id)
                my_stats.gp += 2000
                self.save_manager.save_stats(user_id, my_stats)
                win_text = f"🏆 恭喜玩家【{sender_name}】获得了最终胜利！对方领主生命值已归零！获得 2000 GP！"
                return win_text, True, opp_id, win_text, user_id, "☠️ 你的生命值已归零，你输了。"
            if run.player.hp <= 0:
                self.save_manager.delete_duel_save(user_id)
                opp_stats = self.save_manager.load_stats(opp_id)
                opp_stats.gp += 2000
                self.save_manager.save_stats(opp_id, opp_stats)
                win_text = f"🏆 恭喜玩家【{run.node_data['player2_name' if run.user_id == p1_id else 'player1_name']}】获得了最终胜利！对方领主生命值已归零！获得 2000 GP！"
                return win_text, True, opp_id, win_text, user_id, "☠️ 你的生命值已归零，你输了。"
            self.save_manager.save_duel_save(run.user_id, run)
            
            public_text = render_duel_battle_public(run)
            dm1 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = opp_id
            dm2 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = user_id
            
            public_text = self.engine._append_logs_to_res(run, public_text)
            dm1 = self.engine._append_logs_to_res(run, dm1)
            dm2 = self.engine._append_logs_to_res(run, dm2)
            
            end_tip = f"📢 玩家【{sender_name}】结束了回合！"
            public_text = end_tip + "\n" + public_text
            
            return public_text, False, user_id, dm1, opp_id, dm2
            
        elif cmd in ("状态", "status", "s", "查看", "overview"):
            public_text = render_duel_battle_public(run)
            dm1 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = opp_id
            dm2 = render_duel_battle_private(run)
            
            run.player, run.player2 = run.player2, run.player
            run.user_id = user_id
            
            public_text = self.engine._append_logs_to_res(run, public_text)
            dm1 = self.engine._append_logs_to_res(run, dm1)
            dm2 = self.engine._append_logs_to_res(run, dm2)
            
            return public_text, False, user_id, dm1, opp_id, dm2
            
        return "❌ 未知动作指令。输入帮助指令可查看操作提示。", False, None, None, None, None
