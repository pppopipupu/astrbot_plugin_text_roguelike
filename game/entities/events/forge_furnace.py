import random
from .base import EventOption
from ...data.card_upgrade_data import CARD_UPGRADE_CONFIG
from ..cards import ALL_CARDS
from ..relics import get_relic_name
from ...models.state import BuffState

class ForgeFireOption(EventOption, action="forge_fire", text="使用常规重铸"):
    def _run_effect(self, run, engine) -> str:
        run.node_data["upgrade_source"] = "event"
        return "UPGRADE_FLOW"

class OverloadForgeOption(EventOption, action="overload_forge", text="过载重铸"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        if random.random() < 0.8:
            counts = {}
            for c_id in p.deck:
                if not c_id.endswith("+") and c_id in CARD_UPGRADE_CONFIG:
                    counts[c_id] = counts.get(c_id, 0) + 1
            upgradable = list(counts.keys())
            if not upgradable:
                res = "熔炉隆隆作响，但你的卡组中没有可以升级的卡牌！你并没有受到任何效果。"
            else:
                upgraded_names = []
                to_upgrade = random.sample(upgradable, min(2, len(upgradable)))
                for cid in to_upgrade:
                    p.deck.remove(cid)
                    p.deck.append(cid + "+")
                    upgraded_names.append(ALL_CARDS[cid].name)
                res = f"🔥 熔炉光芒大盛！你成功将卡组中的【{'】和【'.join(upgraded_names)}】随机升级为了它们的强力变体！"
        else:
            p.hp -= 8
            p.deck.append("curse_pain")
            res = "💥 糟糕！熔炉突然发生能量逆流！熔炉的狂暴能量反噬了你（受到 8 点伤害，且1张【苦恼】卡牌已加入卡组）。"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return res

class ForgeBackfireOption(EventOption, action="forge_backfire", text="汲取熔炉余温"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.max_hp += 5
        p.hp = min(p.max_hp, p.hp + 10)
        found = False
        for b in p.buffs:
            if b.id == "forge_backfire":
                b.stacks += 2
                found = True
                break
        if not found:
            p.buffs.append(BuffState("forge_backfire", "炉温反噬", 2, "造成的法术伤害-1"))
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "🍀 你坐在熔炉旁，缓缓引导并吸取其余温。你感到肉体在温暖的奥能下得到了升华（生命上限+5，生命回复了 10 点），但同时体内充斥着紊乱的余温热量，法术释放受到了干扰（获得了 2 层【炉温反噬】buff）。已前往下一关。"

class ShatterForgeOption(EventOption, action="shatter_forge", text="强行破坏熔炉"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.gold += 50
        p.hp -= 6
        p.deck.append("curse_dazed")
        relics_pool = ["lucky_coin", "red_bottle", "leather_armor", "whetstone", "ready_pack", "arcane_rune", "ancient_eye", "gold_compass", "dragon_blood", "energy_core", "heavy_armor"]
        available_relics = [r for r in relics_pool if r not in p.relics]
        got_relic = ""
        if available_relics:
            got_relic = random.choice(available_relics)
            p.relics.append(got_relic)
            if got_relic == "red_bottle":
                p.max_hp += 5
                p.hp += 5
        relic_msg = f"与遗物【{get_relic_name(got_relic)}】" if got_relic else ""
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return f"💥 你用法术强行破坏了熔炉！炉体瞬间发生剧烈爆炸，碎片四射！你受到了 6 点爆炸伤害，1张【晕眩】卡牌已加入卡组。但你在废墟中搜刮到了 50 金币{relic_msg}。已前往下一关。"
