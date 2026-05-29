from typing import Optional, List
from ...models.state import Card
from ...data.card_data import CARD_CONFIG
from .registry import register_card

@register_card("time_warp")
class TimeWarpCard(Card):
    def execute(self, run, target, engine) -> str:
        p = run.player
        max_hand = 9 if "mask_of_void" in p.relics else 12
        p.draw_pile.extend(p.discard_pile)
        p.draw_pile.extend(p.hand)
        p.discard_pile.clear()
        p.hand.clear()
        import random
        random.shuffle(p.draw_pile)
        before = len(p.hand)
        engine._draw_cards(p, max_hand, run)
        after = len(p.hand)
        draw_count = after - before
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(draw_count=draw_count)
        return f"时光倒流！已将所有卡牌重新洗回抽牌堆，并重新抽取了 {draw_count} 张牌。"

@register_card("meteor_swarm")
class MeteorSwarmCard(Card):
    def __init__(self, id, name, color, type, cost_a, cost_ba, base_dmg, desc=""):
        super().__init__(id, name, color, type, cost_a, cost_ba, desc=desc)
        self.base_dmg = base_dmg

    def execute(self, run, target, engine) -> str:
        import random
        dmg = sum(random.randint(1, 12) for _ in range(8))
        if self.damage_type == "fire":
            has_ring = any(av.id == "ring_of_elements" for av in run.player.amulets.values())
            if has_ring:
                dmg += 2
        if "arcane_rune" in run.player.relics:
            dmg += 1
        if "mark_of_fury" in run.player.relics:
            dmg += 2
        if "unstable_crystal" in run.player.relics:
            dmg += 1
        dmg = engine.get_modified_spell_damage(run, self, dmg)
        for idx in range(len(run.enemies) - 1, -1, -1):
            engine._damage_target(run, f"e{idx+1}", dmg, damage_type="fire", card=self)
        cfg = CARD_CONFIG.get(self.id, {})
        feedback_tmpl = cfg.get("feedback")
        if feedback_tmpl:
            return feedback_tmpl.format(dmg=dmg)
        return f"释放流星爆！对所有敌人造成了 {dmg} 点火焰伤害。"

@register_card("archmage_wish")
class ArchmageWishCard(Card):
    def execute(self, run, target, engine) -> str:
        run.player.shield += 10
        engine._add_buff_to(run.player, "wish_power", "祈愿奥术", "本场战斗法术伤害 +4")
        engine._draw_cards(run.player, 2, run)
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "完成了大法师的祈愿！获得了 10 点护盾，【祈愿奥术】法术伤害 +4，并抽了 2 张牌。")

@register_card("time_stop")
class TimeStopCard(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["extra_turns_left"] = 3
        cfg = CARD_CONFIG.get(self.id, {})
        return cfg.get("feedback", "施展了时间停止！你获得了 3 个额外回合。")
