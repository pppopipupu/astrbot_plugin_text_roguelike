import random
from typing import Optional
from ...models.state import GameRun, PlayerState, Card
from ...models.events import CardDiscardEvent, CardPlayedEvent

class DuelCardPlayer:
    def __init__(self, engine):
        self.engine = engine

    def draw_cards(self, p: PlayerState, count: int, run: Optional[GameRun] = None, ignore_focus: bool = False):
        if not ignore_focus and any(b.id == "tactical_focus" for b in p.buffs):
            if run is not None:
                self.engine._log_event(run, "⚠️ [无法抽牌] 本回合无法再抽牌。")
            return
        max_hand = 12
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
        try:
            from ...entities.cards.duel import ALL_DUEL_CARDS
        except ImportError:
            from ...entities.cards.duel import ALL_DUEL_CARDS
        card = ALL_DUEL_CARDS.get(cid)
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
            run.node_data["extra_play_msgs"] = []
            res = self.engine._execute_card_effect(run, card, target)
            if hasattr(card, "execute_tags"):
                card.execute_tags(run, target, self.engine)
            played_evt = CardPlayedEvent(run, card, target, res)
            self.engine.event_bus.dispatch(played_evt)
            res = played_evt.feedback
            extra_msgs = run.node_data.pop("extra_play_msgs", [])
            if len(extra_msgs) > 10:
                res += f"x {len(extra_msgs)}次"
            else:
                res += "".join(extra_msgs)
            self._handle_card_post_play(run, card, cid, source="agile")
            return self.engine._append_logs_to_res(run, f"✨ 触发[灵巧]：丢弃【{card.name}】时自动打出！效果：{res}")
        else:
            p.discard_pile.append(cid)
            return self.engine._append_logs_to_res(run, "")

    def _handle_card_post_play(self, run: GameRun, card: Card, card_id: str, source: str):
        p = run.player
        if hasattr(card, "handle_post_play") and card.handle_post_play(run, card_id, source, self.engine):
            return
        if card.exhaust or source == "agile":
            from ...models.events import CardExhaustEvent
            p.exhaust_pile.append(card_id)
            self.engine.event_bus.dispatch(CardExhaustEvent(run, card))
        else:
            p.discard_pile.append(card_id)
