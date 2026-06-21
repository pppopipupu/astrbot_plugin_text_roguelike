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
from .duel.deck_manager import DeckManager
from .duel.query_manager import QueryManager
from ..data.duel_template_data import DUEL_BROADCAST_TEMPLATES

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
        self.deck_manager = DeckManager(save_manager)
        self.query_manager = QueryManager(save_manager)

    def get_user_active_deck(self, user_id: str) -> Tuple[Optional[str], list]:
        return self.deck_manager.get_user_active_deck(user_id)

    def check_deck_validity(self, deck_list: list) -> Tuple[bool, str]:
        return self.deck_manager.check_deck_validity(deck_list)

    def handle_deck_cmd(self, user_id: str, args: list) -> Tuple[str, bool]:
        return self.deck_manager.handle_deck_cmd(user_id, args)

    def render_duel_menu(self, user_id: str) -> str:
        active_name, deck_list = self.get_user_active_deck(user_id)
        deck_info = "消除未选中对决牌组"
        if active_name:
            valid, reason = self.check_deck_validity(deck_list)
            status_str = "✅ 合法" if valid else f"❌ 不合法 ({reason})"
            deck_info = f"🎴 当前活动牌组：{active_name} ({len(deck_list)}张) [{status_str}]"
        else:
            deck_info = "🔴 未选择活动牌组"
            
        lines = [
            "━━━━━━━━━━━━━━━━━━━━",
            "⚔️ 魔法肉鸽卡牌游戏 - 对决模式 (Duel Mode)",
            "",
            "双人联机策略卡牌 (TCG) 对决。支持玩家之间构筑牌组（25-50张卡，同名上限4张）、召唤随从，合理规划能量与动作（A/BA），消耗进化点强化单位以击败对手！",
            deck_info,
            "",
            "【局外指令】",
            "👉 /rogue duel invite @用户 -- 邀请对方进行对局",
            "👉 /rogue duel accept      -- 接受收到的对局邀请",
            "👉 /rogue duel deck        -- 查看或选择你的牌组",
            "👉 /rogue duel deck export [序号/名称] -- 导出牌组为分享码",
            "👉 /rogue duel deck import <分享码> [新名称] -- 导入牌组",
            "",
            "【局内指令（在你的回合）】",
            "👉 序号 / p 序号 [目标]   -- 使用指定手牌。例如：1 或 p 1 e1",
            "👉 m 序号 a [目标]         -- 指挥随从攻击。例如：m 1 a e1",
            "👉 m 序号 s [序号]         -- 释放随从技能。例如：m 1 s 1",
            "👉 ev 序号 [手牌/随从/护符] -- 消耗进化点进化目标。例如：ev 1",
            "👉 coin                    -- 消耗幸运币获得 1A（后手专属）",
            "👉 e                       -- 结束当前回合",
            "👉 s                       -- 在局内查看当前对战详细快照",
            "👉 q [指令1, 指令2...]     -- 批量顺序执行多个指令。例如：q [1, m 1 a, e]",
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
                
        return DUEL_BROADCAST_TEMPLATES["duel_cmd_unknown"], False, None, None, None, None

    def route_in_game_action(self, run: GameRun, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        p1_id = run.node_data["player1_id"]
        p2_id = run.node_data["player2_id"]
        
        query_cmds = ("查询", "query", "info", "i", "抽牌堆", "draw", "draw_pile", "弃牌堆", "discard", "discard_pile", "消耗堆", "exhaust", "exhaust_pile", "随从墓地", "minion_graveyard", "mg", "minion_grave")
        if args[0].lower() in query_cmds or (args[0].lower() in ("对决", "duel") and len(args) > 1 and args[1].lower() in query_cmds):
            return self._handle_query_cmd(user_id, sender_name, args)

        cmd = args[0].lower()
        if cmd in ("帮助", "help", "hp", "放弃", "abandon", "confirm", "牌组", "deck", "dk", "模式", "mode", "接受", "accept", "邀请", "invite", "iv", "总览", "overview") or cmd.startswith("[at:") or cmd.startswith("@"):
            return self.handle_duel_cmd(user_id, sender_name, args)
            
        if cmd in ("对决", "duel"):
            if len(args) >= 2:
                sub_cmd = args[1].lower()
                if sub_cmd in ("放弃", "abandon", "confirm", "帮助", "help", "hp", "牌组", "deck", "dk", "模式", "mode", "接受", "accept", "邀请", "invite", "iv", "总览", "overview") or sub_cmd.startswith("[at:") or sub_cmd.startswith("@"):
                    return self.handle_duel_cmd(user_id, sender_name, args[1:])
                args = args[1:]
                cmd = args[0].lower()
            else:
                return DUEL_BROADCAST_TEMPLATES["duel_action_in_battle_only"], False, None, None, None, None
            
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
            
            summary_pub = "\n".join(results) + "\n" + public_text
            return summary_pub, term, p1_id, dm1, p2_id, dm2
            
        return self._route_single_action(run, user_id, sender_name, args)

    def _route_single_action(self, run: GameRun, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        if args[0].isdigit():
            args = ["使用"] + args
            
        cmd = args[0].lower()
        handler = DuelActionHandler.registry.get(cmd)
        if handler:
            return handler.execute(self, run, user_id, sender_name, args)
            
        return DUEL_BROADCAST_TEMPLATES["duel_action_unknown"], False, None, None, None, None

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
            win_text = DUEL_BROADCAST_TEMPLATES["victory_announcement"].format(winner_name=sender_name)
            lose_text = DUEL_BROADCAST_TEMPLATES["defeat_private_tip"]
            return win_text, True, acting_id, win_text, waiting_id, lose_text
            
        if run.player.hp <= 0:
            self.save_manager.delete_duel_save(user_id)
            win_stats = self.save_manager.load_stats(waiting_id)
            win_stats.gp += 2000
            self.save_manager.save_stats(waiting_id, win_stats)
            win_name = p2_name if acting_id == p1_id else p1_name
            win_text = DUEL_BROADCAST_TEMPLATES["victory_announcement"].format(winner_name=win_name)
            lose_text = DUEL_BROADCAST_TEMPLATES["defeat_private_tip"]
            return win_text, True, waiting_id, win_text, acting_id, lose_text
            
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
        return self.query_manager.handle_query_cmd(self, user_id, sender_name, args)

    def render_duel_query_info(self, query_str: str) -> str:
        return self.query_manager.render_duel_query_info(query_str)
