import random
from .base import EventOption
from ...data.card_upgrade_data import CARD_UPGRADE_CONFIG
from ..cards import ALL_CARDS

class ReadVoidTomeOption(EventOption, action="read_void_tome", text="强行阅读虚空秘典"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.hp = max(1, p.hp - 10)
        p.deck.append("curse_dimensional_tear")
        legends = [cid for cid, c in ALL_CARDS.items() if c.rarity in ("legendary", "mythic", "artifact") and not cid.startswith("curse_")]
        got_card = random.choice(legends) if legends else "doomsday_judgment"
        p.deck.append(got_card)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        card_name = ALL_CARDS[got_card].name if got_card in ALL_CARDS else got_card
        return f"📖 你强行翻开了虚空秘典，狂暴的禁忌低语几乎将你的精神撕碎（失去 10 点生命值），一张【空间撕裂】诅咒悄然融入你的卡组。但同时，你领悟了【{card_name}】的奥秘！"

class BurnVoidBooksOption(EventOption, action="burn_void_books", text="点燃禁忌书架"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.max_hp = max(5, p.max_hp - 15)
        p.hp = min(p.hp, p.max_hp)
        if "doomsday_core" not in p.relics:
            p.relics.append("doomsday_core")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "🔥 你放火点燃了飞舞的书卷，烈火将虚空的倒影焚烧殆尽。虽然你被火焰中倒映的末日幻象重创了灵魂本源（最大生命上限减少 15 点），但你在灰烬中找到了一块【末日核心】（遗物）。"

class SacrificeMindOption(EventOption, action="sacrifice_mind", text="献祭部分心智"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.hp = max(1, p.hp - 8)
        removed_names = []
        if len(p.deck) > 2:
            removed = random.sample(p.deck, 2)
            for r in removed:
                p.deck.remove(r)
                from ...models.state import ensure_card_state
                base_cid = ensure_card_state(r).id
                if base_cid in ALL_CARDS:
                    removed_names.append(ALL_CARDS[base_cid].name)
        else:
            for r in list(p.deck):
                p.deck.remove(r)
                from ...models.state import ensure_card_state
                base_cid = ensure_card_state(r).id
                if base_cid in ALL_CARDS:
                    removed_names.append(ALL_CARDS[base_cid].name)
        p.deck.append("curse_dazed")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        rem_msg = f"失去了卡牌【{'】和【'.join(removed_names)}】" if removed_names else "没有卡牌可以失去"
        return f"🧠 你斩断了自己的一部分精神，虚空迷雾随之散去。你感到一阵剧烈的头痛，同时一张【晕眩】卡牌加入卡组，你的生命值减少了 8 点。你脑海中某些记忆变得模糊，你{rem_msg}。"

class BuyBlackmarketRelicOption(EventOption, action="buy_blackmarket_relic", text="强行买下神秘包裹"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        cost_msg = ""
        if p.gold >= 50:
            p.gold -= 50
            cost_msg = "支付了 50 金币"
        else:
            p.hp = max(1, p.hp - 15)
            cost_msg = "由于金币不足，你被地精警卫狠狠教训了一顿，失去了 15 点生命值作为抵偿"
        from ...data.relic_data import RELIC_CONFIG
        pool = [rid for rid, r in RELIC_CONFIG.items() if r.get("rarity") != "curse" and rid != "time_sand_blessing"]
        available = [rid for rid in pool if rid not in p.relics]
        got_relic = random.choice(available) if available else "lucky_coin"
        if got_relic not in p.relics:
            p.relics.append(got_relic)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        relic_name = RELIC_CONFIG.get(got_relic, {}).get("name", got_relic)
        return f"📦 你{cost_msg}，强行买下了地精的神秘包裹。打开包裹，你获得了遗物【{relic_name}】。"

class RobBlackmarketOption(EventOption, action="rob_blackmarket", text="强行抢劫黑市"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        if random.random() < 0.7:
            p.gold += 100
            from ...data.gem_data import GEM_CONFIG
            gem_pool = list(GEM_CONFIG.keys())
            gem_id = random.choice(gem_pool)
            engine.enter_next_stage(run)
            next_type = run.node_type
            next_data = run.node_data.copy() if isinstance(run.node_data, dict) else {}
            msg = engine.explore_engine.start_gem_insert_flow(run, gem_id, next_type, next_data)
            engine.save_manager.save_save(run.user_id, run)
            return f"💰 抢劫成功！你悄无声息地打晕了地精黑市商贩，夺走了他的钱袋（获得 100 金币）和一颗宝石。{msg}"
        else:
            engine.battle_engine._init_battle_node(run, "elite")
            run.node_type = "battle"
            engine.save_manager.save_save(run.user_id, run)
            return engine.battle_engine._append_logs_to_res(run, "🚨 抢劫失败！你的小动作被地精警卫发现了，尖锐的警报声响起，大批守卫将你包围！进入战斗。")

class SellFleshOption(EventOption, action="sell_flesh", text="出售血肉"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.max_hp = max(5, p.max_hp - 10)
        p.hp = min(p.hp, p.max_hp)
        p.gold += 80
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "🩸 你与邪异的黑市商人完成了血肉契约，将自身的生命力出售（最大生命上限减少 10 点）。随之，80 金币落入了你的行囊。"

class DrinkTimeSandOption(EventOption, action="drink_time_sand", text="吞食时间光沙"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.max_hp = max(2, p.max_hp // 2)
        p.hp = max(1, p.hp // 2)
        if "time_sand_blessing" not in p.relics:
            p.relics.append("time_sand_blessing")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "⏳ 你吞下了金色的时间光沙。时间法则在你体内生根，你的生命本源被撕裂削弱（最大生命上限与当前生命值减半），但时间沙之赐福（遗物）让你在战斗中行动更加敏捷！"

class AccelerateCinderOption(EventOption, action="accelerate_cinder", text="加速自身薪火"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.hp = max(1, p.hp - 12)
        p.deck.append("warrior_source_of_cinder")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "🔥 你引导古泉的温度加速了自身薪火的燃烧（失去了 12 点生命值），同时卡牌【薪火之源】加入了你的卡组。"

class TouchTimeRiftOption(EventOption, action="touch_time_rift", text="触碰时间裂隙"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.hp = max(1, p.hp - 6)
        p.deck.append("curse_dimensional_tear")
        upgraded_names = []
        counts = {}
        for c_id in p.deck:
            base_cid = c_id.split(":gems:")[0]
            if not base_cid.endswith("+") and base_cid in CARD_UPGRADE_CONFIG:
                counts[c_id] = counts.get(c_id, 0) + 1
        upgradable = list(counts.keys())
        if upgradable:
            to_upgrade = random.sample(upgradable, min(3, len(upgradable)))
            for cid in to_upgrade:
                p.deck.remove(cid)
                if ":gems:" in cid:
                    parts = cid.split(":gems:", 1)
                    new_cid = parts[0] + "+" + ":gems:" + parts[1]
                else:
                    new_cid = cid + "+"
                p.deck.append(new_cid)
                base_cid = cid.split(":gems:")[0]
                if base_cid in ALL_CARDS:
                    upgraded_names.append(ALL_CARDS[base_cid].name)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        up_msg = f"卡组中的【{'】、【'.join(upgraded_names)}】获得了时间加速并永久升级" if upgraded_names else "没有卡牌可以升级"
        return f"🌀 你将手伸入了闪隙的时间裂隙。你的生命被紊乱的时间波动击伤（失去 6 点生命值），一张【空间撕裂】诅咒卡加入卡组。但你的{up_msg}！"

class LootWreckageOption(EventOption, action="loot_wreckage", text="强行搜刮飞船残骸"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.gold += 120
        p.hp = max(1, p.hp - 12)
        p.deck.append("curse_dazed")
        p.deck.append("curse_dazed")
        from ...data.gem_data import GEM_CONFIG
        gem_pool = list(GEM_CONFIG.keys())
        gem_id = random.choice(gem_pool)
        engine.enter_next_stage(run)
        next_type = run.node_type
        next_data = run.node_data.copy() if isinstance(run.node_data, dict) else {}
        msg = engine.explore_engine.start_gem_insert_flow(run, gem_id, next_type, next_data)
        engine.save_manager.save_save(run.user_id, run)
        return f"🚀 你强行剥离了商船残骸的货仓，获得了 120 金币，但强烈的虚空辐射灼伤了你（失去 12 点生命值），你的精神极度涣散（2张【晕眩】加入卡组）。同时你搜刮到了一颗宝石。{msg}"

class RepairEngineOption(EventOption, action="repair_engine", text="修复动力源并带走"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.gold = max(0, p.gold - 30)
        p.max_hp = max(5, p.max_hp - 10)
        p.hp = min(p.hp, p.max_hp)
        got_relic = random.choice(["doomsday_core", "energy_core"])
        if got_relic not in p.relics:
            p.relics.append(got_relic)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        from ...data.relic_data import RELIC_CONFIG
        relic_name = RELIC_CONFIG.get(got_relic, {}).get("name", got_relic)
        return f"🔧 你使用工具修复了商船的动力源，并将其强行拆卸融合到了自己的装备中（消耗 30 金币，最大生命上限减少 10 点），你获得了遗物【{relic_name}】。"

class BraveStormOption(EventOption, action="brave_storm", text="穿越虚空风暴逃跑"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        loss = int(p.hp * 0.4)
        p.hp = max(1, p.hp - loss)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return f"⚡ 你咬紧牙关，迎着呼啸的虚空风暴强行突围！狂暴的奥能风暴疯狂撕扯着你的躯壳，你失去了 {loss} 点生命值（当前生命的 40%），终于艰难地逃出了风暴圈。"

class DigGraveOption(EventOption, action="dig_grave", text="掘开墓穴底下的陪葬品"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.deck.append("curse_dimensional_tear")
        p.deck.append("curse_dimensional_tear")
        if "necromancer_skull" not in p.relics:
            p.relics.append("necromancer_skull")
        from ...data.gem_data import GEM_CONFIG
        gem_pool = list(GEM_CONFIG.keys())
        gem_id = random.choice(gem_pool)
        engine.enter_next_stage(run)
        next_type = run.node_type
        next_data = run.node_data.copy() if isinstance(run.node_data, dict) else {}
        msg = engine.explore_engine.start_gem_insert_flow(run, gem_id, next_type, next_data)
        engine.save_manager.save_save(run.user_id, run)
        return f"🪦 你粗暴地掘开了古老的墓穴。墓碑上的邪神低语瞬间在虚空中爆发，化为诅咒缠绕你的灵魂（2张【空间撕裂】加入卡组），但你成功夺取了陪葬遗物【巫师颅骨】和一颗闪烁的宝石。{msg}"

class ReadEpitaphOption(EventOption, action="read_epitaph", text="强行解读墓碑碑文"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.max_hp += 20
        if "wither_seed" not in p.relics:
            p.hp = min(p.max_hp, p.hp + 20)
        p.gold = 0
        p.deck.append("curse_agony")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "🪱 你凝视着墓碑上邪异晦涩的符文强行解读。疯狂的启示涌入你的脑海，你的体魄得到了诡异的强化（最大生命上限增加 20 并恢复 20 生命值），但你精神恍惚导致身上所有的金币都在迷雾中流失了（失去全部金币），且 1张【苦恼】卡牌加入卡组。"

class CarveOwnNameOption(EventOption, action="carve_own_name", text="在碑文刻上自己的名字避邪"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.hp = max(1, p.hp - 15)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "✍️ 你用利刃在墓碑上刻下了自己的名字。古老的诅咒被名字吸引，瞬间抽干了你的部分气血（失去 15 点生命值），但缠绕周围的黑雾终于消散，你得以继续前行。"
