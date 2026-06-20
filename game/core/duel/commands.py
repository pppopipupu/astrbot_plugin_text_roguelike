import uuid
import re
from typing import Tuple, Optional
from .base import DuelCommandHandler
from ...models.state import PlayerState, GameRun
from ...renderer.duel_renderer import render_duel_battle_public, render_duel_battle_private

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
            return "❌ 你当前没有收到 any 未处理的对决邀请。", False, None, None, None, None
            
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
            return f"❌ 无法开始：发起方牌组不合法（{p1_err}）。", False, None, None, None, None
        if not p2_valid:
            return f"❌ 无法开始：你的活动牌组不合法（{p2_err}）。请进行构筑并保证 25~50 张牌。", False, None, None, None, None
            
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
            return "❌ 你当前不在任何对局中。", False, None, None, None, None
            
        run = router.save_manager.load_duel_save(user_id)
        if not run:
            return "❌ 未找到对应对战存档。", False, None, None, None, None
            
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
        
        res_text = f"🏳️ 玩家【{my_name}】直接认输了！对决结束，玩家【{opp_name}】获得了最终胜利！获得 2000 GP！"
        return res_text, True, opp_id, res_text, user_id, "🏳️ 你已认输，本局对战结束。"

class ModeCommand(DuelCommandHandler, names=["模式", "mode"]):
    def execute(self, router, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        stats = router.save_manager.load_stats(user_id)
        stats.duel_mode = not stats.duel_mode
        if stats.duel_mode:
            stats.rogue_mode = False
        router.save_manager.save_stats(user_id, stats)
        status_str = "开启" if stats.duel_mode else "关闭"
        return f"✨ 免前缀对决模式已{status_str}！此设置仅对你个人生效。", False, None, None, None, None

class InviteCommand(DuelCommandHandler, names=["邀请", "invite", "iv"]):
    def execute(self, router, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        if len(args) < 2:
            return "❌ 请指定要邀请的对方用户 ID，例如：/rogue 对决 邀请 @玩家", False, None, None, None, None
        target = args[1]
        
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
            
        _, my_deck = router.get_user_active_deck(user_id)
        my_valid, my_err = router.check_deck_validity(my_deck)
        if not my_valid:
            return f"❌ 无法发起邀请：你的活动牌组不合法（{my_err}）。请先进行构筑并保证 25~50 张牌。", False, None, None, None, None
            
        router.pending_invites[user_id_clean] = opp_id_clean
        router.pending_invites[user_id_clean + "_name"] = sender_name
        router.pending_invites[user_id_clean + "_raw_target"] = opp_id
        router.pending_invites[user_id_clean + "_raw_sender"] = user_id
        
        return f"⚔️ 玩家【{sender_name}】向你发起了 TCG 卡牌对决！请输入 /rogue 对决 接受 (或 accept) 以开始对战！", False, opp_id, f"⚔️ 【{sender_name}】向你发起了 TCG 卡牌对决！输入 /rogue 对决 接受 开始对局！", None, None

class HelpCommand(DuelCommandHandler, names=["帮助", "help", "hp"]):
    def execute(self, router, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
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
            "  (注：进场首回合随从无法立即攻击，突进/冲锋词条除外，未指定目标默认打敌方第一个存活随从/领主)\n"
            "• 进化卡牌：.duel 进化 <我方格子/手牌序号> (或 evolve/ev)\n"
            "  (注：第 3 回合起解禁，每回合可进化一次，随从生命补满且攻血+2，护符进化不减吟唱)\n"
            "• 使用幸运币：.duel 幸运币 (或 coin/cn)\n"
            "  (注：仅后手机会获得 2 个幸运币，使用不占手牌，本回合动作点 A+1)\n"
            "• 结束回合：.duel 结束 (或 end/结束回合/e)\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        return help_text, False, None, None, None, None

class DeckCommand(DuelCommandHandler, names=["牌组", "deck", "dk"]):
    def execute(self, router, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        res, term = router.handle_deck_cmd(user_id, args[1:])
        return res, term, None, None, None, None
