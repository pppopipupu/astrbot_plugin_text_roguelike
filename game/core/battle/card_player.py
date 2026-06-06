import random
from typing import Optional
from ...models.state import GameRun, PlayerState, EnemyState, MinionState, Card, check_and_replace_fireball
from ...entities import ALL_CARDS, ALL_MINIONS, ALL_AMULETS, get_relic_name, get_relic_impl
from ...models.events import (
    CardPlayEvent, CardPlayedEvent, CardExhaustEvent, CardDiscardEvent,
    TurnEndEvent, TurnStartEvent, BattleWinEvent, DamageCalculateEvent
)

class CardPlayer:
    def __init__(self, engine):
        self.engine = engine

    def _handle_card_post_play(self, run, card, cid, source="played"):
        p = run.player
        is_fragile = getattr(card, "fragile", 0) > 0
        if is_fragile:
            base_cid = cid.split(":fragile:")[0]
            curr_fragile = card.fragile
            if curr_fragile <= 1:
                if base_cid in p.deck:
                    p.deck.remove(base_cid)
                self.engine._log_event(run, f"💥 【{card.name}】彻底碎裂，已从牌组中移除！")
            else:
                next_fragile = curr_fragile - 1
                next_cid = f"{base_cid}:fragile:{next_fragile}"
                if getattr(card, "fleeting", False):
                    if base_cid in p.deck:
                        p.deck.remove(base_cid)
                elif card.type in ("minion", "amulet"):
                    if card.type == "minion":
                        self.engine._log_event(run, f"✨ [消耗] 【{card.name}】进入战场。")
                    else:
                        self.engine._log_event(run, f"✨ [消耗] 【{card.name}】部署完毕。")
                    exhaust_evt = CardExhaustEvent(run, next_cid, source)
                    self.engine.event_bus.dispatch(exhaust_evt)
                elif getattr(card, "exhaust", False):
                    p.exhaust_pile.append(next_cid)
                    self.engine._log_event(run, f"✨ [消耗] 【{card.name}】已被移入消耗堆。")
                    exhaust_evt = CardExhaustEvent(run, next_cid, source)
                    self.engine.event_bus.dispatch(exhaust_evt)
                elif any(b.id == "void_exhaustion" for b in p.buffs):
                    p.exhaust_pile.append(next_cid)
                    self.engine._log_event(run, f"✨ [虚空耗竭] 【{card.name}】已被强行移入消耗堆！")
                    exhaust_evt = CardExhaustEvent(run, next_cid, source)
                    self.engine.event_bus.dispatch(exhaust_evt)
                else:
                    p.discard_pile.append(next_cid)
                    self.engine._log_event(run, f"🧩 【{card.name}】磨损，变更为【{ALL_CARDS.get(next_cid).name}】并移入弃牌堆。")
        else:
            if getattr(card, "fleeting", False):
                if cid in p.deck:
                    p.deck.remove(cid)
            elif any(b.id == "void_exhaustion" for b in p.buffs):
                p.exhaust_pile.append(cid)
                self.engine._log_event(run, f"✨ [虚空耗竭] 【{card.name}】已被强行移入消耗堆！")
                exhaust_evt = CardExhaustEvent(run, cid, source)
                self.engine.event_bus.dispatch(exhaust_evt)
            elif card.type in ("minion", "amulet"):
                if card.type == "minion":
                    self.engine._log_event(run, f"✨ [消耗] 【{card.name}】进入战场。")
                else:
                    self.engine._log_event(run, f"✨ [消耗] 【{card.name}】部署完毕。")
                exhaust_evt = CardExhaustEvent(run, cid, source)
                self.engine.event_bus.dispatch(exhaust_evt)
            elif getattr(card, "exhaust", False):
                p.exhaust_pile.append(cid)
                self.engine._log_event(run, f"✨ [消耗] 【{card.name}】已被移入消耗堆。")
                exhaust_evt = CardExhaustEvent(run, cid, source)
                self.engine.event_bus.dispatch(exhaust_evt)
            else:
                p.discard_pile.append(cid)

    def draw_cards(self, p: PlayerState, count: int, run: Optional[GameRun] = None, ignore_focus: bool = False):
        if not ignore_focus and any(b.id == "tactical_focus" for b in p.buffs):
            if run is not None:
                self.engine._log_event(run, "⚠️ [无法抽牌] 本回合无法再抽牌。")
            return
        max_hand = 9 if "mask_of_void" in p.relics else 12
        drawn_cards = []
        reshuffled = False
        hand_full_logged = False
        for _ in range(count):
            if not p.draw_pile:
                if p.discard_pile:
                    p.draw_pile = p.discard_pile.copy()
                    random.shuffle(p.draw_pile)
                    p.discard_pile.clear()
                    reshuffled = True
            if p.draw_pile:
                if len(p.hand) < max_hand:
                    cid = p.draw_pile.pop()
                    p.hand.append(cid)
                    drawn_cards.append(cid)
                else:
                    if not hand_full_logged and run is not None:
                        self.engine._log_event(run, "⚠️ 提示：手牌已达上限，无法抽取更多卡牌。")
                        hand_full_logged = True
        if run is not None:
            if reshuffled:
                self.engine._log_event(run, "🔄 弃牌堆已重新洗入抽牌堆。")

    def discard_card(self, run: GameRun, cid: str) -> str:
        p = run.player
        card = ALL_CARDS.get(cid)
        discard_evt = CardDiscardEvent(run, cid, "manual")
        self.engine.event_bus.dispatch(discard_evt)
        if not card:
            p.discard_pile.append(cid)
            return self.engine._append_logs_to_res(run, "")
        if getattr(card, "agile", False):
            target = None
            if card.type == "spell":
                p0_spells = {"first_aid", "get_ready", "adrenaline", "mana_potion", "mass_healing_word", "refresh_spirit", "shield", "misty_step", "arcane_intellect", "calculated_gamble", "time_warp", "time_stop", "archmage_wish"}
                if card.id.replace("+", "") in p0_spells:
                    target = "p0"
                else:
                    target = self.engine._get_first_alive_enemy(run)
                if target == "0" or target == "e0":
                    target = "e1"
            res = self.engine._execute_card_effect(run, card, target)
            replay_val = getattr(card, "replay", 0)
            if replay_val > 0:
                for _ in range(replay_val):
                    if self.engine.is_battle_won(run):
                        break
                    extra_res = self.engine._execute_card_effect(run, card, target)
                    res += f" 🔁 [重放触发] {extra_res}"
            played_evt = CardPlayedEvent(run, card, target, res)
            self.engine.event_bus.dispatch(played_evt)
            res = played_evt.feedback
            self._handle_card_post_play(run, card, cid, source="agile")
            self._reindex_minions(p)
            return self.engine._append_logs_to_res(run, f"✨ 触发[灵巧]：丢弃【{card.name}】时自动打出！效果：{res}")
        else:
            p.discard_pile.append(cid)
            self._reindex_minions(p)
            return self.engine._append_logs_to_res(run, "")

    def play_card(self, run: GameRun, hand_idx: int, target: Optional[str] = None) -> str:
        initial_status = [(e.hp, e.shield) for e in run.enemies]
        p = run.player
        if run.node_type != "battle":
            return "❌ 只有在战斗中才能使用卡牌。"
        if hand_idx < 1 or hand_idx > len(p.hand):
            return "❌ 无效的手牌序号。"
        cid = p.hand[hand_idx - 1]
        card = ALL_CARDS.get(cid)
        if not card:
            return "❌ 卡牌不存在。"
        if getattr(card, "unplayable", False):
            return "❌ 该卡牌不能被打出。"
        if target is None:
            if card.type == "spell":
                p0_spells = {"first_aid", "get_ready", "adrenaline", "mana_potion", "mass_healing_word", "refresh_spirit", "shield", "misty_step", "arcane_intellect", "calculated_gamble", "time_warp", "time_stop", "archmage_wish"}
                if card.id.replace("+", "") in p0_spells:
                    target = "p0"
                else:
                    target = self.engine._get_first_alive_enemy(run)

        if target is not None:
            if isinstance(target, str) and target.isdigit():
                target = f"e{target}"
            if target == "0" or target == "e0":
                target = "e1"
            elif target == "p":
                target = "p0"
            if target.startswith("e"):
                try:
                    grid = int(target[1:]) - 1
                except ValueError:
                    grid = 0
                if grid < 0 or grid >= len(run.enemies):
                    return f"❌ 敌方格子 [{target}] 没有敌人。"
            elif target == "p0":
                pass
            elif target.startswith("p"):
                grid = target[1:]
                if grid not in p.minions:
                    return f"❌ 我方格子 [{grid}] 没有随从。"
            else:
                return "❌ 无效的目标选择。"
        if card.type in ("minion", "amulet") and self.engine._get_free_grid(p) is None:
            return "❌ 你的战场格子已满，无法召唤随从或部署护符。"
        
        req_a = card.cost_a
        req_ba = card.cost_ba
        real_x_a = 0
        real_x_ba = 0
        if req_a == -1:
            real_x_a = p.actions
            req_a = p.actions
        if req_ba == -1:
            real_x_ba = p.bonus_actions
            req_ba = p.bonus_actions

        if "chemical_x" in p.relics:
            if card.cost_a == -1:
                real_x_a += 2
            if card.cost_ba == -1:
                real_x_ba += 2

        run.node_data["last_x_cost_a"] = real_x_a
        run.node_data["last_x_cost_ba"] = real_x_ba

        play_evt = CardPlayEvent(run, card, target, req_a, req_ba)
        self.engine.event_bus.dispatch(play_evt)
        req_a = play_evt.cost_a
        req_ba = play_evt.cost_ba
        if p.actions < req_a or p.bonus_actions < req_ba:
            return f"❌ 你的动作资源不足（需要 {req_a}A {req_ba}BA，当前 {p.actions}A {p.bonus_actions}BA）。"
        p.actions -= req_a
        p.bonus_actions -= req_ba
        p.hand.pop(hand_idx - 1)
        self._handle_card_post_play(run, card, cid, source="played")
        run.node_data["current_playing_card_id"] = card.id
        try:
            res = self.engine._execute_card_effect(run, card, target)
            replay_val = getattr(card, "replay", 0)
            if replay_val > 0:
                for _ in range(replay_val):
                    if self.engine.is_battle_won(run):
                        break
                    extra_res = self.engine._execute_card_effect(run, card, target)
                    res += f" 🔁 [重放触发] {extra_res}"
        finally:
            run.node_data["current_playing_card_id"] = ""
        played_count = run.node_data.get("cards_played_this_turn", 0)
        played_evt = CardPlayedEvent(run, card, target, res)
        self.engine.event_bus.dispatch(played_evt)
        res = played_evt.feedback
        run.node_data["cards_played_this_turn"] = played_count + 1
        self.engine.save_manager.save_save(run.user_id, run)
        has_damaged = False
        for idx, e in enumerate(run.enemies):
            if idx < len(initial_status):
                old_hp, old_shield = initial_status[idx]
                if e.hp < old_hp or e.shield < old_shield:
                    has_damaged = True
                    break
        if has_damaged and run.node_data.get("extra_turns_left", 0) > 0:
            end_turn_res = self.end_turn(run)
            res += f"\n⏳ [时间停止] 额外回合中对敌人造成了伤害，当前额外回合提前结束！\n{end_turn_res}"
        for enemy in run.enemies:
            self.engine._sync_enemy_intents(enemy)
        self._reindex_minions(p)
        return self.engine._append_logs_to_res(run, res)

    def play_special_action(self, run: GameRun, hand_idx: int, target: Optional[str] = None) -> str:
        initial_status = [(e.hp, e.shield) for e in run.enemies]
        p = run.player
        if run.node_type != "battle":
            return "❌ 只有在战斗中才能使用卡牌的特殊行动。"
        if hand_idx < 1 or hand_idx > len(p.hand):
            return "❌ 无效的手牌序号。"
        cid = p.hand[hand_idx - 1]
        card = ALL_CARDS.get(cid)
        if not card:
            return "❌ 卡牌不存在。"
        if getattr(card, "unplayable", False):
            return "❌ 该卡牌不能被打出。"
        
        req_a = card.cost_a
        req_ba = card.cost_ba
        real_x_a = 0
        real_x_ba = 0
        if req_a == -1:
            real_x_a = p.actions
            req_a = p.actions
        if req_ba == -1:
            real_x_ba = p.bonus_actions
            req_ba = p.bonus_actions

        if "chemical_x" in p.relics:
            if card.cost_a == -1:
                real_x_a += 2
            if card.cost_ba == -1:
                real_x_ba += 2

        run.node_data["last_x_cost_a"] = real_x_a
        run.node_data["last_x_cost_ba"] = real_x_ba

        if p.actions < req_a or p.bonus_actions < req_ba:
            return f"❌ 你的动作资源不足（需要 {req_a}A {req_ba}BA，当前 {p.actions}A {p.bonus_actions}BA）。"
        if target is None:
            p0_spells = {"first_aid", "get_ready", "adrenaline", "mana_potion", "mass_healing_word", "refresh_spirit", "shield", "misty_step", "arcane_intellect", "calculated_gamble", "time_warp", "time_stop", "archmage_wish"}
            if card.id.replace("+", "") in p0_spells:
                target = "p0"
            else:
                target = self.engine._get_first_alive_enemy(run)
        if target == "0" or target == "e0":
            target = "e1"
        elif target == "p":
            target = "p0"
        p.actions -= req_a
        p.bonus_actions -= req_ba
        p.hand.pop(hand_idx - 1)
        is_fragile = getattr(card, "fragile", 0) > 0
        if is_fragile:
            base_cid = cid.split(":fragile:")[0]
            curr_fragile = card.fragile
            if curr_fragile <= 1:
                if base_cid in p.deck:
                    p.deck.remove(base_cid)
                self.engine._log_event(run, f"💥 【{card.name}】彻底碎裂，已从牌组中移除！")
            else:
                next_fragile = curr_fragile - 1
                next_cid = f"{base_cid}:fragile:{next_fragile}"
                if getattr(card, "fleeting", False):
                    if base_cid in p.deck:
                        p.deck.remove(base_cid)
                elif any(b.id == "void_exhaustion" for b in p.buffs):
                    p.exhaust_pile.append(next_cid)
                    self.engine._log_event(run, f"✨ [虚空耗竭] 【{card.name}】已被强行移入消耗堆！")
                    exhaust_evt = CardExhaustEvent(run, next_cid, "played")
                    self.engine.event_bus.dispatch(exhaust_evt)
                else:
                    p.discard_pile.append(next_cid)
                    self.engine._log_event(run, f"🧩 【{card.name}】磨损，变更为【{ALL_CARDS.get(next_cid).name}】并移入弃牌堆。")
        else:
            if getattr(card, "fleeting", False):
                if cid in p.deck:
                    p.deck.remove(cid)
            elif any(b.id == "void_exhaustion" for b in p.buffs):
                p.exhaust_pile.append(cid)
                self.engine._log_event(run, f"✨ [虚空耗竭] 【{card.name}】已被强行移入消耗堆！")
                exhaust_evt = CardExhaustEvent(run, cid, "played")
                self.engine.event_bus.dispatch(exhaust_evt)
            else:
                p.discard_pile.append(cid)
        run.node_data["current_playing_card_id"] = card.id
        try:
            res = card.special_action(run, target)
        finally:
            run.node_data["current_playing_card_id"] = ""
        self.engine.save_manager.save_save(run.user_id, run)
        has_damaged = False
        for idx, e in enumerate(run.enemies):
            if idx < len(initial_status):
                old_hp, old_shield = initial_status[idx]
                if e.hp < old_hp or e.shield < old_shield:
                    has_damaged = True
                    break
        if has_damaged and run.node_data.get("extra_turns_left", 0) > 0:
            end_turn_res = self.end_turn(run)
            res += f"\n⏳ [时间停止] 额外回合中对敌人造成了伤害，当前额外回合提前结束！\n{end_turn_res}"
        for enemy in run.enemies:
            self.engine._sync_enemy_intents(enemy)
        self._reindex_minions(p)
        return self.engine._append_logs_to_res(run, res)

    def minion_attack(self, run: GameRun, my_grid: str, opp_grid: Optional[str] = None) -> str:
        initial_status = [(e.hp, e.shield) for e in run.enemies]
        p = run.player
        if run.node_type != "battle":
            return "❌ 只有在战斗中才能控制随从攻击。"
        if my_grid not in p.minions:
            return f"❌ 我方格子 [{my_grid}] 没有随从。"
        m = p.minions[my_grid]
        if m.attack_actions < 1:
            return "❌ 该随从本回合已经没有可用的攻击动作（AA）点。"
        if opp_grid is None:
            opp_grid = self.engine._get_first_alive_enemy(run)
        m.attack_actions -= 1
        try:
            opp_idx = int(opp_grid.replace("e", "")) - 1
            if opp_idx < 0:
                opp_idx = 0
        except ValueError:
            opp_idx = 0
        if opp_idx < 0 or opp_idx >= len(run.enemies):
            return f"❌ 敌方格子 [{opp_grid}] 没有合法的敌人目标。"
        enemy = run.enemies[opp_idx]
        opp_grid = f"e{opp_idx+1}"
        self.engine._damage_target(run, opp_grid, m.atk, source=f"p{my_grid}", damage_type="attack")
        res = f"我方随从【{m.name}】攻击了敌人【{enemy.name}】。"
        self.engine.save_manager.save_save(run.user_id, run)
        has_damaged = False
        for idx, e in enumerate(run.enemies):
            if idx < len(initial_status):
                old_hp, old_shield = initial_status[idx]
                if e.hp < old_hp or e.shield < old_shield:
                    has_damaged = True
                    break
        if has_damaged and run.node_data.get("extra_turns_left", 0) > 0:
            end_turn_res = self.end_turn(run)
            res += f"\n⏳ [时间停止] 额外回合中对敌人造成了伤害，当前额外回合提前结束！\n{end_turn_res}"
        for enemy in run.enemies:
            self.engine._sync_enemy_intents(enemy)
        self._reindex_minions(p)
        return self.engine._append_logs_to_res(run, res)

    def minion_skill(self, run: GameRun, my_grid: str, skill_idx: int = 1, target: Optional[str] = None) -> str:
        initial_status = [(e.hp, e.shield) for e in run.enemies]
        p = run.player
        if run.node_type != "battle":
            return "❌ 只有在战斗中才能发动随从技能。"
        if my_grid not in p.minions:
            return f"❌ 我方格子 [{my_grid}] 没有随从。"
        m = p.minions[my_grid]
        if m.id not in ALL_MINIONS:
            return f"❌ 随从【{m.name}】没有任何可用技能。"
        template = ALL_MINIONS[m.id]
        skills_list = template.skills
        if skill_idx < 1 or skill_idx > len(skills_list):
            skills_desc = "\n".join([f" [{idx}] {s.name}: {s.desc}" for idx, s in enumerate(skills_list, 1)])
            return f"❌ 无效的技能序号。随从【{m.name}】的可用技能有：\n{skills_desc}"
        skill = skills_list[skill_idx - 1]
        cost_a = skill.cost_a
        cost_ba = skill.cost_ba
        if m.actions < cost_a or m.bonus_actions < cost_ba:
            return f"❌ 随从资源不足（需要 {cost_a}A {cost_ba}BA，当前 {m.actions}A {m.bonus_actions}BA）。"
        needs_target = False
        base_id = m.id.rstrip("+")
        if base_id == "mercenary" and skill_idx == 1:
            needs_target = True
        elif base_id == "shield_guard" and skill_idx == 2:
            needs_target = True
        elif base_id == "water_elemental" and skill_idx == 2:
            needs_target = True
        if needs_target:
            if target is None:
                target = self.engine._get_first_alive_enemy(run)
            if isinstance(target, str) and target.isdigit():
                target = f"e{target}"
            if target == "0" or target == "e0":
                target = "e1"
            if target.startswith("e"):
                try:
                    idx = int(target[1:]) - 1
                except ValueError:
                    idx = 0
                if idx < 0 or idx >= len(run.enemies):
                    return f"❌ 敌方目标 [{target}] 不存在。"
            else:
                return "❌ 无效的目标。该技能只能对敌方目标释放。"
        m.actions -= cost_a
        m.bonus_actions -= cost_ba
        msg = f"随从【{m.name}】发动了技能【{skill.name}】！"
        effect_msg = skill.execute(run, my_grid, target, self.engine)
        msg += effect_msg
        self.engine.save_manager.save_save(run.user_id, run)
        has_damaged = False
        for idx, e in enumerate(run.enemies):
            if idx < len(initial_status):
                old_hp, old_shield = initial_status[idx]
                if e.hp < old_hp or e.shield < old_shield:
                    has_damaged = True
                    break
        if has_damaged and run.node_data.get("extra_turns_left", 0) > 0:
            end_turn_res = self.end_turn(run)
            msg += f"\n⏳ [时间停止] 额外回合中对敌人造成了伤害，当前额外回合提前结束！\n{end_turn_res}"
        for enemy in run.enemies:
            self.engine._sync_enemy_intents(enemy)
        self._reindex_minions(p)
        return self.engine._append_logs_to_res(run, msg)

    def end_turn(self, run: GameRun) -> str:
        if run.node_type != "battle":
            return "❌ 只有在战斗中才能结束回合。"
        p = run.player
        evt_end = TurnEndEvent(run, is_player=True)
        self.engine.event_bus.dispatch(evt_end)
        retained = []
        temp_retains = list(run.node_data.get("temp_retain_cards", []))
        for cid in p.hand:
            card = ALL_CARDS.get(cid)
            if card and getattr(card, "retain", False):
                retained.append(cid)
            elif cid in temp_retains:
                retained.append(cid)
                temp_retains.remove(cid)
            elif card and (card.id == "curse_dimensional_tear" or card.id == "curse_dimensional_tear+"):
                p.exhaust_pile.append(cid)
                self.engine._log_event(run, f"💥 [空间撕裂] 手牌中的【{card.name}】在回合结束时发生坍缩，被消耗并对玩家造成 3 点真实伤害！")
                self.engine.combat_resolver.damage_target(run, "p0", 3, source="curse", damage_type="true")
                exhaust_evt = CardExhaustEvent(run, cid, "curse_dimensional_tear")
                self.engine.event_bus.dispatch(exhaust_evt)
            elif card and getattr(card, "ethereal", False):
                p.exhaust_pile.append(cid)
                self.engine._log_event(run, f"✨ [虚无] 【{card.name}】在回合结束时被消耗。")
                exhaust_evt = CardExhaustEvent(run, cid, "ethereal")
                self.engine.event_bus.dispatch(exhaust_evt)
            else:
                p.discard_pile.append(cid)
        p.hand = retained
        run.node_data["temp_retain_cards"] = []
        for ak, av in list(p.amulets.items()):
            base_id = av.id[:-1] if av.id.endswith("+") else av.id
            template = ALL_AMULETS.get(base_id)
            if template:
                template.on_end_turn(run, ak, self.engine)
            av.countdown -= 1
            if av.countdown <= 0:
                del p.amulets[ak]
                p.minion_graveyard.append(av.id)
                lw_msg = ""
                if template:
                    is_upgraded = av.id.endswith("+")
                    lw_msg = template.on_death(run, ak, is_upgraded, self.engine)
                if lw_msg:
                    self.engine._log_event(run, f"🔔 [谢幕曲] 我方【{av.name}】吟唱结束进入墓地：{lw_msg}")
                else:
                    self.engine._log_event(run, f"🔔 我方【{av.name}】吟唱结束进入墓地。")
        if self.engine.is_battle_won(run):
            self.handle_battle_win(run)
            self._reindex_minions(p)
            return self.engine._append_logs_to_res(run, "战斗胜利！敌方单位已被全部击败。")
        extra_turns = run.node_data.get("extra_turns_left", 0)
        if extra_turns > 0:
            run.node_data["extra_turns_left"] = extra_turns - 1
            enemy_actions = f"⏳ [时间停止] 额外回合进行中（剩余 {extra_turns - 1} 个额外回合），敌人全部陷入静止。"
        else:
            enemy_actions = self.engine._enemy_turn(run)
        if p.hp <= 0:
            settle_msg = self.engine.save_manager.settle_game_and_delete(run.user_id, run, is_victory=False)
            return f"{enemy_actions}\n💀 冒险结束。你被击败了！存档已被清除。\n{settle_msg}"
        decay_msgs = []
        has_barricade = any(b.id.startswith("barricade") for b in p.buffs)
        if p.shield > 0 and not has_barricade:
            lost = p.shield - (p.shield // 2)
            p.shield = p.shield // 2
            if lost > 0:
                decay_msgs.append(f"玩家失去 {lost} 点护盾")
                from ...models.events import ShieldDecayEvent
                self.engine.event_bus.dispatch(ShieldDecayEvent(run, "p0", lost))
        elif p.shield > 0 and has_barricade:
            pass
        else:
            p.shield = 0
        decay_info = ""
        if decay_msgs:
            decay_info = "🛡️ 护盾流失：" + "，".join(decay_msgs) + "\n"
        p.actions = 2
        p.bonus_actions = 1
        if run.node_data.get("drain_ba"):
            p.bonus_actions = max(0, p.bonus_actions - 1)
            run.node_data.pop("drain_ba", None)
        if run.node_data.get("drain_a"):
            p.actions = max(0, p.actions - 1)
            run.node_data.pop("drain_a", None)
        evt_start = TurnStartEvent(run, is_player=True)
        self.engine.event_bus.dispatch(evt_start)
        if getattr(p, "subclass", "") == "时序法师":
            if random.random() < 0.25:
                p.bonus_actions += 1
                self.engine._log_event(run, "⏳ [时序被动] 触发时间跳跃，本回合额外获得 1 个附赠动作（BA）！")
        for mk, mv in p.minions.items():
            mv.actions += 1
            mv.bonus_actions += 1 if mv.id.startswith("arcane_golem") else 0
            mv.attack_actions = 1
            if mv.id == "mercenary":
                mv.atk = 4
            elif mv.id == "mercenary+":
                mv.atk = 5
            elif mv.id == "arcane_golem":
                mv.atk = 6
            elif mv.id == "arcane_golem+":
                mv.atk = 8
        if run.enemies and any(e.name == "腐化之心" for e in run.enemies):
            run.node_data["heart_turn"] = run.node_data.get("heart_turn", 1) + 1
        if run.enemies and any(e.name == "Icerainboww" for e in run.enemies):
            run.node_data["icerainboww_turn"] = run.node_data.get("icerainboww_turn", 1) + 1
        if run.enemies and any(e.name == "雷霆领主" for e in run.enemies):
            run.node_data["thunder_lord_turn"] = run.node_data.get("thunder_lord_turn", 1) + 1
        draw_count = 6
        if run.node_data.get("draw_penalty_next_turn"):
            draw_count = max(0, draw_count - run.node_data["draw_penalty_next_turn"])
            run.node_data.pop("draw_penalty_next_turn", None)
        self.draw_cards(p, draw_count, run, ignore_focus=True)
        self.engine._roll_enemy_intent(run)
        run.node_data["cards_played_this_turn"] = 0
        self._reindex_minions(p)
        self.engine.save_manager.save_save(run.user_id, run)
        return self.engine._append_logs_to_res(run, f"{enemy_actions}\n{decay_info}进入玩家回合。已重置动作并抽取手牌。")

    def handle_battle_win(self, run: GameRun):
        p = run.player
        p.buffs.clear()
        p.hp = min(p.max_hp, p.hp)
        evt_win = BattleWinEvent(run)
        self.engine.event_bus.dispatch(evt_win)
        difficulty = run.node_data.get("difficulty", "normal")
        quest = run.node_data.get("quest")
        quest_bonus = ""
        if quest == "knight_cave":
            p.deck.append("shield_guard")
            p.relics.append("heavy_armor")
            quest_bonus = "\n🗡️ 任务完成！你帮奥术骑士夺回了长剑。作为谢礼，【盾卫】加入了你的卡组，你还获得了一个遗物【重装甲片】！"
        elif quest == "maze_fight":
            got_relic = random.choice(["whetstone", "ready_pack", "arcane_rune"])
            p.relics.append(got_relic)
            quest_bonus = f"\n🔥 任务完成！你击败了火元素守卫，在石门后获得稀有遗物【{get_relic_name(got_relic)}】！"
        if difficulty == "elite":
            reward_gold = 25 + random.randint(10, 20)
        else:
            reward_gold = 10 + random.randint(5, 15)
        p.gold += reward_gold
        stats = self.engine.save_manager.load_stats(run.user_id)
        has_gatekey = getattr(stats, "unlocked_gatekey", False)
        if p.stage == 25:
            run.node_type = "victory"
            stats.killed_yog_sothoth = True
            self.engine.save_manager.save_stats(run.user_id, stats)
        elif p.stage == 20 and not has_gatekey:
            run.node_type = "victory"
            if run.node_data.get("boss_name") == "Icerainboww":
                stats.killed_icerainboww = True
                self.engine.save_manager.save_stats(run.user_id, stats)
        else:
            run.node_type = "reward"
            card_pool = list(ALL_CARDS.keys())
            p_class = getattr(stats, "selected_class", "法师")
            target_color = "warrior" if p_class == "战士" else "wizard"
            normal_cards = [cid for cid in card_pool if ALL_CARDS[cid].rarity not in ("legendary", "mythic", "artifact") and not cid.startswith("curse_") and ALL_CARDS[cid].color in (target_color, "neutral")]
            reward_cards = random.sample(normal_cards, 3)
            final_reward_cards = []
            for cid in reward_cards:
                cid = check_and_replace_fireball(run, cid)
                if p.subclass == "秘钥学者" and ALL_CARDS.get(cid) and ALL_CARDS[cid].color == "wizard" and ALL_CARDS[cid].rarity not in ("legendary", "mythic", "artifact"):
                    if random.random() < 0.35:
                        cid = "key_resonance"
                final_reward_cards.append(cid)
            run.node_data = {"cards": final_reward_cards, "quest_bonus": quest_bonus}
            self.engine.save_manager.save_save(run.user_id, run)

    def _reindex_minions(self, p: PlayerState):
        new_minions = {}
        sorted_keys = sorted(list(p.minions.keys()), key=lambda x: int(x))
        for idx, k in enumerate(sorted_keys, 1):
            new_minions[str(idx)] = p.minions[k]
        p.minions = new_minions
