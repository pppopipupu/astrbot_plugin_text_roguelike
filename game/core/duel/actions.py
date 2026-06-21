from typing import Tuple, Optional
from .base import DuelActionHandler
from ...data.duel_template_data import DUEL_BROADCAST_TEMPLATES

class PlayAction(DuelActionHandler, names=["使用", "use", "u", "play", "p"]):
    def execute(self, router, run, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        current_turn_id = run.node_data.get("current_turn_id")
        p1_id = run.node_data["player1_id"]
        p2_id = run.node_data["player2_id"]
        
        if user_id != current_turn_id:
            return DUEL_BROADCAST_TEMPLATES["play_not_my_turn"], False, None, None, None, None
            
        if len(args) < 2:
            return DUEL_BROADCAST_TEMPLATES["play_no_idx"], False, None, None, None, None
            
        tgt_idx_str = args[1]
        if not tgt_idx_str.isdigit():
            return DUEL_BROADCAST_TEMPLATES["play_invalid_idx"], False, None, None, None, None
            
        idx = int(tgt_idx_str) - 1
        p = run.player
        if idx < 0 or idx >= len(p.hand):
            return DUEL_BROADCAST_TEMPLATES["play_out_of_range"], False, None, None, None, None
            
        cid = p.hand[idx]
        try:
            from ...entities.cards.duel import ALL_DUEL_CARDS
        except ImportError:
            from game.entities.cards.duel import ALL_DUEL_CARDS
        card = ALL_DUEL_CARDS.get(cid)
        if not card:
            return DUEL_BROADCAST_TEMPLATES["play_no_card_entity"], False, None, None, None, None
            
        try:
            from ...data.duel_card_data import DUEL_CARD_CONFIG
        except ImportError:
            try:
                from game.data.duel_card_data import DUEL_CARD_CONFIG
            except ImportError:
                from game.data import neutral_card_data
                DUEL_CARD_CONFIG = {}
                
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
            return DUEL_BROADCAST_TEMPLATES["play_insufficient_actions"].format(cost_a=card.cost_a, cost_ba=card.cost_ba, actions=p.actions, bonus_actions=p.bonus_actions), False, None, None, None, None
            
        target = None
        if len(args) >= 3:
            target = args[2].lower()
        else:
            if card.type == "spell":
                p0_spells = {"first_aid", "get_ready", "adrenaline", "mana_potion", "mass_healing_word", "refresh_spirit", "shield", "misty_step", "arcane_intellect", "calculated_gamble", "time_warp", "time_stop", "archmage_wish"}
                clean_id = card.id.replace("duel_", "").replace("+", "")
                if clean_id in p0_spells:
                    target = "p0"
                else:
                    target = router.engine._get_first_alive_enemy(run)
                        
        if target:
            if target == "0" or target == "e0":
                target = "e1"
            elif target == "p":
                target = "p0"
            elif target.isdigit():
                target = f"e{target}"
                
        if target and target.startswith("e"):
            is_damage = ("base_dmg" in cfg or "damage" in cfg or "damage_type" in cfg)
            if is_damage and not cfg.get("face_target", True) and not cfg.get("aoe", False) and target == "e1":
                return DUEL_BROADCAST_TEMPLATES["play_minion_only_err"], False, None, None, None, None
                
        if x_cost_a:
            run.node_data["last_x_cost_a"] = cost_a
        if x_cost_ba:
            run.node_data["last_x_cost_ba"] = cost_ba
            
        opp = run.player2
        initial_opp_hp = opp.hp
        initial_opp_shield = opp.shield
        initial_minion_status = {gid: m.hp for gid, m in opp.minions.items()}
        
        p.actions -= cost_a
        p.bonus_actions -= cost_ba
        p.hand.pop(idx)
        
        try:
            from ...models.events import CardPlayEvent, CardExhaustEvent, CardPlayedEvent
        except ImportError:
            try:
                from game.models.events import CardPlayEvent, CardExhaustEvent, CardPlayedEvent
            except ImportError:
                from game.models.events import CardPlayEvent, CardExhaustEvent, CardPlayedEvent
                
        play_evt = CardPlayEvent(run, card, target, cost_a, cost_ba)
        router.engine.event_bus.dispatch(play_evt)
        
        err_msg = router.engine._execute_card_effect(run, card, target)
        if err_msg:
            p.hand.insert(idx, cid)
            p.actions += cost_a
            p.bonus_actions += cost_ba
            return err_msg, False, None, None, None, None
            
        if card.type in ("minion", "amulet"):
            router.engine.event_bus.dispatch(CardExhaustEvent(run, cid, "played"))
        elif card.exhaust:
            p.exhaust_pile.append(cid)
            router.engine.event_bus.dispatch(CardExhaustEvent(run, cid, "played"))
        else:
            p.discard_pile.append(cid)
            
        played_count = run.node_data.get("cards_played_this_turn", 0)
        router.engine.event_bus.dispatch(CardPlayedEvent(run, card, target, ""))
        run.node_data["cards_played_this_turn"] = played_count + 1
        extra_msgs = run.node_data.pop("extra_play_msgs", [])
        if extra_msgs:
            for extra in extra_msgs:
                router.engine._log_event(run, extra)
        
        victory_res = router._check_victory(run, user_id, sender_name)
        if victory_res:
            return victory_res
            
        use_tip = DUEL_BROADCAST_TEMPLATES["play_card_tip"].format(sender_name=sender_name, card_name=card.name.replace('对决·', ''))
        
        interrupted = router._check_time_stop_interruption(run, initial_opp_hp, initial_opp_shield, initial_minion_status)
        if interrupted:
            run.node_data["extra_turns_left"] = 0
            router.engine.end_turn(run)
            victory_res = router._check_victory(run, user_id, sender_name)
            if victory_res:
                return victory_res
            msg = DUEL_BROADCAST_TEMPLATES["time_stop_damage_interrupted"]
            return router._save_and_render_state(run, user_id, use_tip + "\n" + msg)
            
        return router._save_and_render_state(run, user_id, use_tip)

class MinionAction(DuelActionHandler, names=["随从", "minion", "m", "attack", "atk", "sk", "skill"]):
    def execute(self, router, run, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        current_turn_id = run.node_data.get("current_turn_id")
        p1_id = run.node_data["player1_id"]
        
        if user_id != current_turn_id:
            return DUEL_BROADCAST_TEMPLATES["play_not_my_turn"], False, None, None, None, None
            
        if len(args) < 2:
            return DUEL_BROADCAST_TEMPLATES["minion_no_idx"], False, None, None, None, None
            
        my_grid_raw = args[1]
        p = run.player
        
        if my_grid_raw in ("all", "所有", "*"):
            grids = sorted(list(p.minions.keys()))
        else:
            grids = []
            for p_g in my_grid_raw.split(','):
                g = p_g.strip().replace("p", "")
                if g in p.minions:
                    grids.append(g)
                    
        if not grids:
            return DUEL_BROADCAST_TEMPLATES["minion_not_found"].format(grid=my_grid_raw), False, None, None, None, None
            
        action = "攻击"
        opp_grid = None
        if len(args) > 2:
            if args[2].lower() in ("攻击", "a", "attack"):
                action = "攻击"
                if len(args) > 3:
                    opp_grid = args[3].lower()
            elif args[2].lower() in ("技能", "s", "skill", "sk"):
                action = "技能"
            else:
                action = "攻击"
                opp_grid = args[2].lower()
                
        opp = run.player2
        initial_opp_hp = opp.hp
        initial_opp_shield = opp.shield
        initial_minion_status = {gid: m.hp for gid, m in opp.minions.items()}
        
        results = []
        for g in grids:
            if run.player2.hp <= 0:
                break
                
            m = p.minions[g]
            stunned = any(b.id == "stun" for b in m.buffs)
            if stunned:
                results.append(DUEL_BROADCAST_TEMPLATES["minion_stunned"].format(name=m.name))
                continue
                
            if action == "攻击":
                res = router.engine.minion_attack(run, g, opp_grid)
                if not res.startswith("❌"):
                    target_name = "未知"
                    if opp_grid == "e1" or opp_grid is None:
                        target_name = run.node_data.get("player2_name" if run.user_id == p1_id else "player1_name", "对手")
                    elif opp_grid.startswith("e") and len(opp_grid) > 1:
                        try:
                            opp_idx = int(opp_grid[1:]) - 1
                            opp_grid_clean = str(opp_idx)
                            if opp_grid_clean in run.player2.minions:
                                target_name = run.player2.minions[opp_grid_clean].name
                        except ValueError:
                            pass
                    atk_tip = DUEL_BROADCAST_TEMPLATES["minion_attack_tip"].format(sender_name=sender_name, minion_name=m.name.replace('+', '').replace('对决·', ''), target_name=target_name.replace('+', ''))
                    res = atk_tip + "\n" + res
                results.append(res)
            elif action == "技能":
                skill_idx = 1
                target = None
                if len(args) > 3:
                    try:
                        if args[2].lower() in ("技能", "s", "skill", "sk"):
                            skill_idx = int(args[3])
                            if len(args) > 4:
                                target = args[4].lower()
                        else:
                            skill_idx = int(args[2])
                            if len(args) > 3:
                                target = args[3].lower()
                    except ValueError:
                        if args[2].lower() in ("技能", "s", "skill", "sk"):
                            target = args[3].lower()
                        else:
                            target = args[2].lower()
                res = router.engine.minion_skill(run, g, skill_idx, target)
                results.append(res)
                
        victory_res = router._check_victory(run, user_id, sender_name)
        if victory_res:
            return victory_res
            
        res_combined = "\n".join(results)
        
        interrupted = router._check_time_stop_interruption(run, initial_opp_hp, initial_opp_shield, initial_minion_status)
        if interrupted:
            run.node_data["extra_turns_left"] = 0
            router.engine.end_turn(run)
            victory_res = router._check_victory(run, user_id, sender_name)
            if victory_res:
                return victory_res
            msg = DUEL_BROADCAST_TEMPLATES["time_stop_damage_interrupted"]
            return router._save_and_render_state(run, user_id, res_combined + "\n" + msg)
            
        return router._save_and_render_state(run, user_id, res_combined)

class CoinAction(DuelActionHandler, names=["幸运币", "coin", "cn"]):
    def execute(self, router, run, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        res = router.engine.use_coin(run, user_id)
        if res.startswith("❌"):
            return res, False, None, None, None, None
            
        coin_tip = DUEL_BROADCAST_TEMPLATES["coin_success_tip"].format(sender_name=sender_name)
        return router._save_and_render_state(run, user_id, coin_tip)

class EvolveAction(DuelActionHandler, names=["进化", "evolve", "ev"]):
    def execute(self, router, run, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        current_turn_id = run.node_data.get("current_turn_id")
        if user_id != current_turn_id:
            return DUEL_BROADCAST_TEMPLATES["play_not_my_turn"], False, None, None, None, None
        if len(args) < 2:
            return DUEL_BROADCAST_TEMPLATES["evolve_no_target"], False, None, None, None, None
            
        target = args[1]
        evolve_target_name = "未知"
        p = run.player
        if target.isdigit():
            idx = int(target) - 1
            if 0 <= idx < len(p.hand):
                try:
                    from ...entities.cards.duel import ALL_DUEL_CARDS
                except ImportError:
                    from game.entities.cards.duel import ALL_DUEL_CARDS
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
                
        res = router.engine.evolve_card(run, user_id, target)
        if res.startswith("❌"):
            return res, False, None, None, None, None
            
        evolve_tip = DUEL_BROADCAST_TEMPLATES["evolve_tip"].format(sender_name=sender_name, evolve_target_name=evolve_target_name.replace('+', '').replace('对决·', ''))
        return router._save_and_render_state(run, user_id, evolve_tip)

class EndAction(DuelActionHandler, names=["结束", "end", "endturn", "结束回合", "e"]):
    def execute(self, router, run, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        current_turn_id = run.node_data.get("current_turn_id")
        if user_id != current_turn_id:
            return DUEL_BROADCAST_TEMPLATES["end_turn_not_my_turn"], False, None, None, None, None
            
        router.engine.end_turn(run)
        
        victory_res = router._check_victory(run, user_id, sender_name)
        if victory_res:
            return victory_res
            
        end_tip = DUEL_BROADCAST_TEMPLATES["end_turn_tip"].format(sender_name=sender_name)
        return router._save_and_render_state(run, user_id, end_tip)

class StatusAction(DuelActionHandler, names=["状态", "status", "s", "查看"]):
    def execute(self, router, run, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        return router._save_and_render_state(run, user_id, "")

class QueryAction(DuelActionHandler, names=["查询", "query", "info", "i", "抽牌堆", "draw", "draw_pile", "弃牌堆", "discard", "discard_pile", "消耗堆", "exhaust", "exhaust_pile", "随从墓地", "minion_graveyard", "mg", "minion_grave"]):
    def execute(self, router, run, user_id: str, sender_name: str, args: list) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        return router._handle_query_cmd(user_id, sender_name, args)
