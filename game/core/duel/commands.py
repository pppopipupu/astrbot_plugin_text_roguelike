import uuid
import re
from typing import Tuple, Optional
from .base import DuelCommandHandler
from ...models.state import PlayerState, GameRun
from ...renderer.duel_renderer import render_duel_battle_public, render_duel_battle_private
from ...data.duel_template_data import DUEL_BROADCAST_TEMPLATES

def clean_user_id(uid) -> str:
    if uid is None:
        return ""
    uid_str = str(uid).strip().lower()
    if uid_str.startswith("@"):
        uid_str = uid_str[1:]
    return uid_str

class AcceptCommand(DuelCommandHandler, names=["接受", "accept"]):
    def execute(self, router, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        invite_sender_clean = None
        cur_user_clean = clean_user_id(user_id)
        for sender_clean, target_clean in list(router.pending_invites.items()):
            if sender_clean.endswith("_name") or sender_clean.endswith("_raw_target") or sender_clean.endswith("_raw_sender"):
                continue
            tc_part = target_clean.split(":")[0]
            cc_part = cur_user_clean.split(":")[0]
            if target_clean == cur_user_clean or tc_part == cc_part:
                invite_sender_clean = sender_clean
                break
        if not invite_sender_clean:
            return DUEL_BROADCAST_TEMPLATES["accept_no_invite"], False, None, None, None, None
            
        opp_id = router.pending_invites[invite_sender_clean + "_raw_sender"]
        raw_target_id = router.pending_invites[invite_sender_clean + "_raw_target"]
        p1_name = router.pending_invites.get(invite_sender_clean + "_name", "玩家一")
        
        del router.pending_invites[invite_sender_clean]
        del router.pending_invites[invite_sender_clean + "_name"]
        del router.pending_invites[invite_sender_clean + "_raw_sender"]
        del router.pending_invites[invite_sender_clean + "_raw_target"]
        
        p1_active, p1_deck = router.get_user_active_deck(opp_id)
        p2_active, p2_deck = router.get_user_active_deck(raw_target_id)
        
        p1_valid, p1_err = router.check_deck_validity(p1_deck)
        p2_valid, p2_err = router.check_deck_validity(p2_deck)
        
        if not p1_valid:
            return DUEL_BROADCAST_TEMPLATES["accept_sender_deck_invalid"].format(err=p1_err), False, None, None, None, None
        if not p2_valid:
            return DUEL_BROADCAST_TEMPLATES["accept_receiver_deck_invalid"].format(err=p2_err), False, None, None, None, None
            
        game_id = str(uuid.uuid4())[:8]
        
        p1_state = PlayerState(hp=200, max_hp=200, shield=0, gold=0, stage=1, deck=p1_deck, name=p1_name)
        p2_state = PlayerState(hp=200, max_hp=200, shield=0, gold=0, stage=1, deck=p2_deck, name=sender_name)
        
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
        
        router.engine.init_duel(run)
        router.save_manager.bind_duel_game(opp_id, raw_target_id, game_id)
        router.save_manager.save_duel_save(opp_id, run)
        
        public_text = render_duel_battle_public(run)
        dm1 = render_duel_battle_private(run)
        
        run.player, run.player2 = run.player2, run.player
        run.user_id = raw_target_id
        dm2 = render_duel_battle_private(run)
        
        run.player, run.player2 = run.player2, run.player
        run.user_id = opp_id
        
        return public_text, False, opp_id, dm1, raw_target_id, dm2

class AbandonCommand(DuelCommandHandler, names=["放弃", "abandon", "confirm"]):
    def execute(self, router, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        game_id = router.save_manager.get_duel_game_id(user_id)
        if not game_id:
            return DUEL_BROADCAST_TEMPLATES["abandon_not_in_game"], False, None, None, None, None
            
        run = router.save_manager.load_duel_save(user_id)
        if not run:
            return DUEL_BROADCAST_TEMPLATES["abandon_no_save"], False, None, None, None, None
            
        p1_id = run.node_data["player1_id"]
        p2_id = run.node_data["player2_id"]
        p1_name = run.node_data["player1_name"]
        p2_name = run.node_data["player2_name"]
        
        opp_id = p2_id if user_id == p1_id else p1_id
        opp_name = p2_name if user_id == p1_id else p1_name
        my_name = p1_name if user_id == p1_id else p2_name
        
        router.save_manager.delete_duel_save(user_id)
        
        opp_stats = router.save_manager.load_stats(opp_id)
        opp_stats.gp += 2000
        router.save_manager.save_stats(opp_id, opp_stats)
        
        res_text = DUEL_BROADCAST_TEMPLATES["abandon_win_announcement"].format(my_name=my_name, opp_name=opp_name)
        return res_text, True, opp_id, res_text, user_id, DUEL_BROADCAST_TEMPLATES["abandon_self_tip"]

class ModeCommand(DuelCommandHandler, names=["模式", "mode"]):
    def execute(self, router, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        stats = router.save_manager.load_stats(user_id)
        stats.duel_mode = not stats.duel_mode
        if stats.duel_mode:
            stats.rogue_mode = False
        router.save_manager.save_stats(user_id, stats)
        status_str = "开启" if stats.duel_mode else "关闭"
        return DUEL_BROADCAST_TEMPLATES["mode_toggle_tip"].format(status_str=status_str), False, None, None, None, None

class InviteCommand(DuelCommandHandler, names=["邀请", "invite", "iv"]):
    def execute(self, router, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        if len(args) < 2:
            return DUEL_BROADCAST_TEMPLATES["invite_no_target"], False, None, None, None, None
        target = args[1]
        
        opp_id = target.strip()
        opp_id_match = re.search(r"qq=([^\s\]]+)", opp_id)
        if opp_id_match:
            opp_id = opp_id_match.group(1)
        if opp_id.startswith("@"):
            opp_id = opp_id[1:]
            
        if not opp_id:
            return DUEL_BROADCAST_TEMPLATES["invite_no_match"], False, None, None, None, None
            
        opp_id_clean = clean_user_id(opp_id)
        user_id_clean = clean_user_id(user_id)
        if opp_id_clean == user_id_clean or opp_id_clean.split(":")[0] == user_id_clean.split(":")[0]:
            return DUEL_BROADCAST_TEMPLATES["invite_self"], False, None, None, None, None
            
        _, my_deck = router.get_user_active_deck(user_id)
        my_valid, my_err = router.check_deck_validity(my_deck)
        if not my_valid:
            return DUEL_BROADCAST_TEMPLATES["invite_deck_invalid"].format(err=my_err), False, None, None, None, None
            
        router.pending_invites[user_id_clean] = opp_id_clean
        router.pending_invites[user_id_clean + "_name"] = sender_name
        router.pending_invites[user_id_clean + "_raw_target"] = opp_id
        router.pending_invites[user_id_clean + "_raw_sender"] = user_id
        
        pub = DUEL_BROADCAST_TEMPLATES["invite_public_tip"].format(sender_name=sender_name)
        pri = DUEL_BROADCAST_TEMPLATES["invite_private_tip"].format(sender_name=sender_name)
        return pub, False, opp_id, pri, None, None

class HelpCommand(DuelCommandHandler, names=["帮助", "help", "hp"]):
    def execute(self, router, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        return DUEL_BROADCAST_TEMPLATES["help_text"], False, None, None, None, None

class DeckCommand(DuelCommandHandler, names=["牌组", "deck", "dk"]):
    def execute(self, router, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        res, term = router.handle_deck_cmd(user_id, args[1:])
        return res, term, None, None, None, None

class OverviewCommand(DuelCommandHandler, names=["总览", "overview"]):
    def execute(self, router, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        stats = router.save_manager.load_stats(user_id)
        from game.renderer.menu import get_duel_card_library_items
        items = get_duel_card_library_items()
        stats.reader_title = "⚔️ 对决卡牌总览"
        stats.reader_items = items
        stats.reader_page = 1
        stats.reader_active = True
        stats.reader_mode = "duel"
        router.save_manager.save_stats(user_id, stats)
        from game.renderer.menu import render_reader_page
        res = render_reader_page(stats)
        return res, False, None, None, None, None
