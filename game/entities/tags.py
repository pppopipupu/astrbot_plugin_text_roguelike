import copy
from typing import Optional
from ..models.state import CardTag, Card, GameRun
from ..models.events import CardPlayedEvent, CardExhaustEvent

class ReplayTag(CardTag):
    def execute(self, card: Card, run: GameRun, target: Optional[str], engine) -> Optional[str]:
        if self.value > 0:
            for _ in range(self.value):
                if engine.is_battle_won(run):
                    break
                extra_res = engine._execute_card_effect(run, card, target)
                played_evt_rep = CardPlayedEvent(run, card, target, extra_res, is_extra=True)
                engine.event_bus.dispatch(played_evt_rep)
                run.node_data.setdefault("extra_play_msgs", []).append(f" 🔁 [重放触发] {played_evt_rep.feedback}")
        return None

class FragileTag(CardTag):
    def handle_post_play(self, card: Card, run: GameRun, cid: str, source: str, engine) -> bool:
        p = run.player
        from ..models.state import ensure_card_state
        cid = ensure_card_state(cid)
        base_cid = cid.id
        curr_fragile = cid.fragile
        if curr_fragile <= 0:
            curr_fragile = self.value

        match_state = copy.copy(cid)
        match_state.replay = 0
        match_state.fragile = 0

        found = None
        for dc in p.deck:
            if (dc.id == match_state.id and 
                dc.upgraded == match_state.upgraded and 
                dc.gems == match_state.gems):
                found = dc
                break

        if curr_fragile <= 1:
            if found:
                p.deck.remove(found)
            engine._log_event(run, f"💥 【{card.name}】彻底碎裂，已从牌组中移除！")
        else:
            next_fragile = curr_fragile - 1
            next_cid = copy.copy(cid)
            next_cid.fragile = next_fragile

            from ..entities.cards import ALL_CARDS
            if getattr(card, "fleeting", False):
                if found:
                    p.deck.remove(found)
            elif any(b.id == "void_exhaustion" for b in p.buffs):
                p.exhaust_pile.append(next_cid)
                engine._log_event(run, f"✨ [虚空耗竭] 【{card.name}】已被强行移入消耗堆！")
                exhaust_evt = CardExhaustEvent(run, next_cid, "played")
                engine.event_bus.dispatch(exhaust_evt)
            else:
                p.discard_pile.append(next_cid)
                next_card = ALL_CARDS.get(next_cid)
                next_name = next_card.name if next_card else card.name
                engine._log_event(run, f"🧩 【{card.name}】磨损，变更为【{next_name}】并移入弃牌堆。")
        return True
