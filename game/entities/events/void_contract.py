import random
from .base import EventOption
from ..relics import get_relic_name
from ..cards import ALL_CARDS

class ContractRelicOption(EventOption, action="contract_relic", text="献祭生命换取遗物"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.hp = max(1, p.hp - 10)
        relics_pool = ["lucky_coin", "red_bottle", "leather_armor", "whetstone", "ready_pack", "arcane_rune", "ancient_eye", "gold_compass", "dragon_blood", "energy_core", "heavy_armor"]
        available_relics = [r for r in relics_pool if r not in p.relics]
        got_relic = ""
        if available_relics:
            got_relic = random.choice(available_relics)
            p.relics.append(got_relic)
            if got_relic == "red_bottle":
                p.max_hp += 5
                p.hp += 5
        relic_msg = f"获得了珍贵的遗物【{get_relic_name(got_relic)}】" if got_relic else "but there are no relics available to take"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return f"🖤 契约达成！你感到生命被抽离（失去 10 点生命值），但虚空中降下了一道宝光，你{relic_msg}。"

class ContractLegendOption(EventOption, action="contract_legend", text="以血肉之躯汲取奥法"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.max_hp = max(5, p.max_hp - 6)
        p.hp = min(p.hp, p.max_hp)
        legends = [cid for cid, c in ALL_CARDS.items() if c.rarity == "legendary" and not cid.startswith("curse_")]
        got_card = random.choice(legends) if legends else "doomsday_judgment"
        p.deck.append(got_card)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return f"🖤 契约达成！你的灵魂本源受到了虚空的侵蚀（最大生命值上限减少 6 点），同时一张强大的传奇卡牌【{ALL_CARDS[got_card].name}】悄然融入了你的卡组。"

class AbsorbVoidOption(EventOption, action="absorb_void", text="将虚空吞噬"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.gold += 35
        p.deck.append("curse_agony")
        heal_msg = ""
        if "wither_seed" not in p.relics:
            p.hp = min(p.max_hp, p.hp + 6)
            heal_msg = "，但其精纯的暗影魔力却在你的血管中奔流，反而治愈了你身上的伤势（生命值回复了 6 点）"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return f"🌌 你张开双臂疯狂吸收周围的虚空能量，虚空结晶化为了 35 金币落入你的行囊。虽然狂暴的虚空能量给你的心灵留下了难以磨灭的【苦恼】（1张【苦恼】卡牌已加入卡组）{heal_msg}。"
