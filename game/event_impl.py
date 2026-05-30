from typing import Optional, List
from .data.event_data import EVENT_CONFIG

class EventOption:
    def __init__(self, text: str, action: str):
        self.text = text
        self.action = action

    def execute(self, run, engine) -> str:
        return ""

class DrinkFountainOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        p.hp = min(p.max_hp, p.hp + 10)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你喝下了泉水，生命值回复了 10 点。已前往下一关。"

class CoinFountainOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        if p.gold < 10:
            return "❌ 你的金币不足 10。"
        p.gold -= 10
        import random
        from .card_impl import ALL_CARDS
        wizards = [cid for cid, c in ALL_CARDS.items() if c.color == "wizard" and c.rarity != "legendary"]
        reward_cards = random.sample(wizards, 3) if len(wizards) >= 3 else wizards
        run.node_type = "card_select"
        run.node_data = {
            "title": "许愿泉水：请选择你的回馈",
            "desc": "你在泉水中投入了 10 金币，泉水散发出耀眼的奥术涟漪，升起三张卡牌：",
            "cards": reward_cards
        }
        engine.save_manager.save_save(run.user_id, run)
        return "你在泉水中投入了 10 金币，开始选择泉水的回赠。"

class ObserveFountainOption(EventOption):
    def execute(self, run, engine) -> str:
        cfg = EVENT_CONFIG["fountain_observe"]
        run.node_data["event_id"] = "fountain_observe"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你凑近池塘向下观察..."

class TakeNecklaceOption(EventOption):
    def execute(self, run, engine) -> str:
        import random
        p = run.player
        if random.random() < 0.5:
            p.relics.append("arcane_rune")
            res = "🍀 运气不错！你安全地解除了符文陷阱，成功捞出了【奥术项链】，获得遗物【奥术符文】！"
        else:
            p.deck.append("curse_dazed")
            res = "⚡ 糟糕！捞取项链时触发了爆裂电弧陷阱，你感到一阵晕眩（1张【晕眩】卡牌已加入卡组），且项链在电弧中化为了灰烬！"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return res

class HelpKnightOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        has_aid = False
        for idx, cid in enumerate(p.deck):
            if cid == "first_aid":
                p.deck.pop(idx)
                has_aid = True
                break
        if not has_aid:
            return "❌ 你的卡组中没有【绷带包扎】卡牌！"
        p.deck.append("shield_guard")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你将绷带给予骑士治疗。为了答谢，【盾卫】加入了你的卡组。已前往下一关。"

class RobKnightOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        p.gold += 25
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你不顾骑士的反抗夺走了他的财物，获得 25 金币。已前往下一关。"

class AskKnightOption(EventOption):
    def execute(self, run, engine) -> str:
        cfg = EVENT_CONFIG["knight_story"]
        run.node_data["event_id"] = "knight_story"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你向受伤的骑士询问缘由..."

class CaveQuestOption(EventOption):
    def execute(self, run, engine) -> str:
        cfg = EVENT_CONFIG["knight_cave"]
        run.node_data["event_id"] = "knight_cave"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你答应帮他去取回佩剑，顺着他的指引来到了山洞深处。"

class CaveFightOption(EventOption):
    def execute(self, run, engine) -> str:
        run.node_data["quest"] = "knight_cave"
        engine.battle_engine._init_battle_node(run, "normal")
        run.node_type = "battle"
        if run.enemies:
            run.enemies[0].name = "狂暴魔仆"
            run.enemies[0].hp = 15
            run.enemies[0].max_hp = 15
            run.enemies[0].shield = 0
            run.enemies[0].actions = 1
            run.enemies[0].bonus_actions = 0
            run.enemies[0].max_actions = 1
            run.enemies[0].max_bonus_actions = 0
        engine.save_manager.save_save(run.user_id, run)
        return "你跨入洞穴，一只面目狰狞的【狂暴魔仆】冲了过来！进入战斗。"

class AbsorbAltarOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        p.deck.append("arcane_charge")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你吸收了奥术波动的力量，将【奥术充能】加入卡组。已前往下一关。"

class BreakAltarOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        p.gold += 20
        p.hp = max(1, p.hp - 4)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你用法杖敲碎了祭坛上的水晶并收集了碎片（获得 20 金币），但被震荡的爆风伤及（失去 4 点生命值）。已前往下一关。"

class MeditateAltarOption(EventOption):
    def execute(self, run, engine) -> str:
        cfg = EVENT_CONFIG["altar_portal"]
        run.node_data["event_id"] = "altar_portal"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你在祭坛前盘膝坐下，闭目静思..."

class EnterPortalOption(EventOption):
    def execute(self, run, engine) -> str:
        import random
        if random.random() < 0.5:
            run.node_type = "shop"
            engine._init_shop_node(run)
            if "items" in run.node_data:
                for item in run.node_data["items"]:
                    item["price"] = max(0, int(item["price"] * 0.5))
            engine.save_manager.save_save(run.user_id, run)
            return "🌀 传送门闪烁！你被一股平稳的引力吸入，竟然直接降落在了一个神秘的流浪旅商营地，且这次流浪旅商给予了你 5 折全店优惠！"
        else:
            run.node_type = "battle"
            engine.battle_engine._init_battle_node(run, "elite")
            if run.enemies:
                from .data.enemy_data import ENEMY_CONFIG
                cfg = ENEMY_CONFIG.get("传送门守卫者", {})
                import re
                hp_str = cfg.get("hp", "45")
                base_hp = 45
                match = re.match(r"^(\d+)", hp_str)
                if match:
                    base_hp = int(match.group(1))
                hp_final = base_hp + run.player.stage * 3
                run.enemies[0].name = "传送门守卫者"
                run.enemies[0].hp = hp_final
                run.enemies[0].max_hp = hp_final
                run.enemies[0].shield = 0
                run.enemies[0].actions = 1
                run.enemies[0].bonus_actions = 1
                run.enemies[0].max_actions = 1
                run.enemies[0].max_bonus_actions = 1
            engine.save_manager.save_save(run.user_id, run)
            return "⚠️ 空间发生强烈扭曲！传送门能量崩溃，你被卷入一处荒野废墟，前方出现了一只凶猛的【传送门守卫者】！进入战斗。"

class ShatterPortalOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        p.gold += 40
        p.deck.append("curse_agony")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "💥 你用法术强行轰碎了虚空传送门！空间之门产生了剧烈爆炸，巨大的余波让你心神苦恼（1张【苦恼】卡牌已加入卡组），但破碎的裂隙中获得 40 金币。"

class MazeFireOption(EventOption):
    def execute(self, run, engine) -> str:
        cfg = EVENT_CONFIG["maze_guard"]
        run.node_data["event_id"] = "maze_guard"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你跟着红色的火光，在湿润的石壁甬道中穿行..."

class MazeWaterOption(EventOption):
    def execute(self, run, engine) -> str:
        cfg = EVENT_CONFIG["maze_pool"]
        run.node_data["event_id"] = "maze_pool"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你顺着潺潺的水流声，在布满青苔的石墙中摸行..."

class MazeMarkOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        p.gold += 10
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "🧭 你在每个路口用小刀刻下记号。虽然多花了一些时间，但你安稳地走出了迷宫，且在出口处捡到了前人遗留的 10 金币。"

class BribeGuardOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        if p.gold < 20:
            return "❌ 你的金币不足 20 点，火元素守卫拒绝放行，并发出愤怒的嘶吼！"
        p.gold -= 20
        relics_pool = ["lucky_coin", "red_bottle", "leather_armor", "whetstone", "ready_pack", "arcane_rune"]
        available_relics = [r for r in relics_pool if r not in p.relics]
        got_relic = ""
        if available_relics:
            import random
            got_relic = random.choice(available_relics)
            p.relics.append(got_relic)
            if got_relic == "red_bottle":
                p.max_hp += 5
                p.hp += 5
        from .relic_impl import get_relic_name
        relic_msg = f"，并在宝座后的石盒中获得遗物【{get_relic_name(got_relic)}】" if got_relic else ""
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return f"🪙 你向火元素守卫进献了 20 金币。它满意地让开道路{relic_msg}。已离开迷宫。"

class FightGuardOption(EventOption):
    def execute(self, run, engine) -> str:
        run.node_data["quest"] = "maze_fight"
        engine.battle_engine._init_battle_node(run, "elite")
        run.node_type = "battle"
        if run.enemies:
            run.enemies[0].name = "火元素守卫"
            run.enemies[0].hp = 30 + run.player.stage * 2
            run.enemies[0].max_hp = run.enemies[0].hp
            run.enemies[0].shield = 0
            run.enemies[0].actions = 1
            run.enemies[0].bonus_actions = 1
            run.enemies[0].max_actions = 1
            run.enemies[0].max_bonus_actions = 1
        engine.save_manager.save_save(run.user_id, run)
        return "🔥 谈和破裂！火元素守卫扬起法杖，滚滚热浪席卷而来！进入战斗。"

class BathePoolOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        p.max_hp += 3
        if "wither_seed" not in p.relics:
            p.hp = min(p.max_hp, p.hp + 15)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "💚 泉水温热且充盈着生命气息。你在池中休整，最大生命值永久增加了 3 点，且生命值回复了 15 点（若有枯萎之种则只加生命上限不回血）。"

class FishPoolOption(EventOption):
    def execute(self, run, engine) -> str:
        import random
        p = run.player
        if random.random() < 0.5:
            relics_pool = ["lucky_coin", "red_bottle", "leather_armor", "whetstone", "ready_pack", "arcane_rune"]
            available_relics = [r for r in relics_pool if r not in p.relics]
            got_relic = ""
            if available_relics:
                got_relic = random.choice(available_relics)
                p.relics.append(got_relic)
                if got_relic == "red_bottle":
                    p.max_hp += 5
                    p.hp += 5
            from .relic_impl import get_relic_name
            res = f"🍀 运气不错！池水没有反应，你安全地摸出了一个发光的神明宝物，获得遗物【{get_relic_name(got_relic)}】！" if got_relic else "池底空无一物。"
        else:
            p.max_hp = max(5, p.max_hp - 5)
            p.hp = min(p.hp, p.max_hp)
            res = "👹 突然水流旋动！一只守护水蛇从池底窜出，咬住了你的手臂并释放毒液！你的最大生命上限减少了 5 点！"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return res

class RideCartOption(EventOption):
    def execute(self, run, engine) -> str:
        cfg = EVENT_CONFIG["mine_cart_crash"]
        run.node_data["event_id"] = "mine_cart_crash"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你纵身跳上停在轨道上的生锈矿车，松开了手刹，矿车顺着轨道稳冲而下..."

class ClimbLadderOption(EventOption):
    def execute(self, run, engine) -> str:
        cfg = EVENT_CONFIG["mine_ladder_body"]
        run.node_data["event_id"] = "mine_ladder_body"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你顺着吱呀作响的木质旋转扶梯，一步步向矿坑深处摸去..."

class JumpCartOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        p.gold += 40
        p.deck.append("curse_dazed")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "🤕 在矿车冲入深渊的前一瞬间，你狼狈地跳车。你重重摔在坚硬的矿石上并感到一阵晕眩（1张【晕眩】卡牌已加入卡组），但在碎石堆中获得了 40 金币。"

class StopCartSpellOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        has_key_card = any(cid in p.deck for cid in ["shield_guard", "fireball", "thunderwave"])
        if has_key_card:
            relics_pool = ["lucky_coin", "red_bottle", "leather_armor", "whetstone", "ready_pack", "arcane_rune"]
            available_relics = [r for r in relics_pool if r not in p.relics]
            got_relic = ""
            if available_relics:
                import random
                got_relic = random.choice(available_relics)
                p.relics.append(got_relic)
                if got_relic == "red_bottle":
                    p.max_hp += 5
                    p.hp += 5
            from .relic_impl import get_relic_name
            relic_msg = f"，并从脱落的铸铁轨道环上取下了一个精密的遗物【{get_relic_name(got_relic)}】" if got_relic else ""
            res = f"🛡️ 你利用卡组中强大的法术/随从力量顶住了矿车底盘，伴随着令人牙酸的摩擦火花，矿车在悬崖前奇迹般停下。你安然无恙{relic_msg}！"
        else:
            p.hp = max(1, p.hp - 10)
            p.gold += 10
            res = "💀 你无法有效控制疯狂疾驰的矿车！矿车飞出了断裂轨道跌落崖底。伴随着金属扭曲的巨响，你受到重创（失去 10 生命值），只勉强在残骸中搜集到了 10 金币。"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return res

class LootBodyOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        p.gold += 25
        p.deck.append("curse_agony")
        heal_msg = ""
        if "wither_seed" not in p.relics:
            p.hp = min(p.max_hp, p.hp + 4)
            heal_msg = "，但你顺便饮下了干尸腰包中残留的一小瓶古代药水（生命值回复了 4 点）"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return f"🕷️ 你撬开了干尸怀里的盒子，在里面收获了 25 金币。虽然触碰干尸使你沾染了古老诅咒，感到心神苦恼（1张【苦恼】卡牌已加入卡组）{heal_msg}。"

class DigOreOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        has_fire_or_thunder = any(cid in p.deck for cid in ["fireball", "thunderwave"])
        if has_fire_or_thunder:
            p.gold += 50
            res = "💥 你用卡组中的强力法术【火球术】或【雷鸣波】直接轰向闪着微光的矿石层！一阵爆破声后矿墙坍塌，大片露天晶矿被炸落，你收集到了 50 金币！"
        else:
            p.gold += 15
            res = "⛏️ 由于卡组里缺乏强大的重火力爆破手段，你只能用小刀和双手吃力地在矿石墙上挖掘，费了半天劲只挖出了价值 15 金币的晶石碎屑。"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return res

class ReadScrollOption(EventOption):
    def execute(self, run, engine) -> str:
        import random
        p = run.player
        if random.random() < 0.5:
            p.deck.append("spell_surge")
            res = "🍀 你成功解读了残卷！你对奥术的领悟更深了，将卡牌【奥术涌动】加入了你的卡组。"
        else:
            p.deck.append("curse_dazed")
            res = "⚡ 残卷上狂暴的奥术能量瞬间反噬了你！你感到一阵【晕眩】（1张【晕眩】卡牌已加入卡组）。"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return res

class ResonateScrollOption(EventOption):
    def execute(self, run, engine) -> str:
        import random
        p = run.player
        if p.gold < 15:
            return "❌ 你的金币不足 15 点。"
        p.gold -= 15
        from .card_impl import ALL_CARDS
        spells = [cid for cid, c in ALL_CARDS.items() if c.type == "spell" and c.rarity != "legendary" and not cid.startswith("curse_")]
        got_card = random.choice(spells) if spells else "dagger_throw"
        p.deck.append(got_card)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return f"🪙 你消耗了 15 金币。魔网与残卷共鸣，凭空凝聚出一张卡牌【{ALL_CARDS[got_card].name}】并加入了你的卡组。"

class DispelPhantomOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        heal = 15
        if "wither_seed" not in p.relics:
            p.hp = min(p.max_hp, p.hp + heal)
            res = "✨ 你用魔力驱散了法师的残影。残影破碎为纯净的奥术微光，治愈了你的伤势，生命值回复了 15 点。"
        else:
            res = "✨ 你用魔力驱散了法师的残影。残影化为奥术微光散去（因为有枯萎之种，你无法获得治疗）。"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return res

class GambleSmallOption(EventOption):
    def execute(self, run, engine) -> str:
        import random
        p = run.player
        if p.gold < 15:
            return "❌ 你的金币不足 15 点。"
        p.gold -= 15
        if random.random() < 0.5:
            p.gold += 30
            res = "🪙 猜中了！哥布林商人一脸肉疼地付给你 30 金币。"
        else:
            res = "❌ 猜错了！哥布林商人得意地收走了你押下的 15 金币。"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return res

class GambleLargeOption(EventOption):
    def execute(self, run, engine) -> str:
        import random
        p = run.player
        if p.gold < 30:
            return "❌ 你的金币不足 30 点。"
        p.gold -= 30
        if random.random() < 0.4:
            p.gold += 60
            res = "🪙 运气爆棚！你猜中了！哥布林商人惨叫着付给你 60 金币。"
        else:
            res = "❌ 猜错了！哥布林商人哈哈大笑，将你的 30 金币塞进了自己的口袋。"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return res

class RobGoblinOption(EventOption):
    def execute(self, run, engine) -> str:
        import random
        p = run.player
        if random.random() < 0.7:
            p.gold += 40
            res = "⚔️ 抢劫成功！哥布林商人被你吓破了胆，丢下 40 金币狼狈逃窜。"
        else:
            p.hp = max(1, p.hp - 8)
            res = "💥 抢劫失败！哥布林商人早有防备，触发了地上的自爆机关。你被炸飞受了 8 点伤害，而哥布林已经乘机溜走。"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return res

class DrinkNectarOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        heal = 12
        if "wither_seed" not in p.relics:
            p.hp = min(p.max_hp, p.hp + heal)
            res = "🌸 你饮下了甜美的红色花蜜茶，感到浑身暖洋洋的，生命值回复了 12 点。"
        else:
            res = "🌸 你饮下了甜美的红色花蜜茶，口感很好，但因为有枯萎之种，你没有获得任何治疗效果。"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return res

class EatCookieOption(EventOption):
    def execute(self, run, engine) -> str:
        p = run.player
        p.max_hp += 4
        p.hp += 4
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "🍪 你享用了绿色坚果饼。这奇妙的茶点永久提升了你的生命力，最大生命值上限 +4 且当前生命值 +4。"

class ListenMusicOption(EventOption):
    def execute(self, run, engine) -> str:
        import random
        p = run.player
        from .card_impl import ALL_CARDS
        agile_cards = [cid for cid, c in ALL_CARDS.items() if getattr(c, "agile", False) and not cid.startswith("curse_")]
        got_card = random.choice(agile_cards) if agile_cards else "agile_strike"
        p.deck.append(got_card)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return f"🎵 你闭上双眼，静静倾听妖精的八音盒。美妙的旋律启发了你的身手，你获得了灵巧卡牌【{ALL_CARDS[got_card].name}】。"

class ContractRelicOption(EventOption):
    def execute(self, run, engine) -> str:
        import random
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
        from .relic_impl import get_relic_name
        relic_msg = f"获得了珍贵的遗物【{get_relic_name(got_relic)}】" if got_relic else "但周围已经没有可拿的遗物了"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return f"🖤 契约达成！你感到生命被抽离（失去 10 点生命值），但虚空中降下了一道宝光，你{relic_msg}。"

class ContractLegendOption(EventOption):
    def execute(self, run, engine) -> str:
        import random
        p = run.player
        p.max_hp = max(5, p.max_hp - 6)
        p.hp = min(p.hp, p.max_hp)
        from .card_impl import ALL_CARDS
        legends = [cid for cid, c in ALL_CARDS.items() if c.rarity == "legendary" and not cid.startswith("curse_")]
        got_card = random.choice(legends) if legends else "doomsday_judgment"
        p.deck.append(got_card)
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return f"🖤 契约达成！你的灵魂本源受到了虚空的侵蚀（最大生命值上限减少 6 点），同时一张强大的传奇卡牌【{ALL_CARDS[got_card].name}】悄然融入了你的卡组。"

class AbsorbVoidOption(EventOption):
    def execute(self, run, engine) -> str:
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

class LeaveEventOption(EventOption):
    def __init__(self, text: str, action: str, event_id: str = "fountain"):
        super().__init__(text, action)
        self.event_id = event_id

    def execute(self, run, engine) -> str:
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你决定不节外生枝，继续赶路。已前往下一关。"

class EventTemplate:
    def __init__(self, id: str, description: str, options: List[EventOption], min_stage: int = 2, max_stage: int = 19):
        self.id = id
        self.description = description
        self.options = options
        self.min_stage = min_stage
        self.max_stage = max_stage

ALL_EVENTS = [
    EventTemplate(
        "fountain",
        EVENT_CONFIG["fountain"]["description"],
        [
            DrinkFountainOption("饮用泉水", "drink_fountain"),
            CoinFountainOption("投入金币", "coin_fountain"),
            ObserveFountainOption("仔细观察泉底", "observe_fountain"),
            LeaveEventOption("悄悄离开", "leave_event", "fountain")
        ]
    ),
    EventTemplate(
        "knight",
        EVENT_CONFIG["knight"]["description"],
        [
            HelpKnightOption("施以援手", "help_knight"),
            RobKnightOption("趁火打劫", "rob_knight"),
            AskKnightOption("询问他的来历", "ask_knight"),
            LeaveEventOption("置之不理", "leave_event", "knight")
        ]
    ),
    EventTemplate(
        "altar",
        EVENT_CONFIG["altar"]["description"],
        [
            AbsorbAltarOption("汲取奥术", "absorb_altar"),
            BreakAltarOption("摧毁水晶", "break_altar"),
            MeditateAltarOption("在祭坛前冥想", "meditate_altar"),
            LeaveEventOption("绕道而行", "leave_event", "altar")
        ]
    ),
    EventTemplate(
        "lost_maze",
        EVENT_CONFIG["lost_maze"]["description"],
        [
            MazeFireOption("循着远处的微弱火光走", "maze_fire"),
            MazeWaterOption("沿着潺潺的水流声走", "maze_water"),
            MazeMarkOption("在墙壁做标记，小心翼翼前行", "maze_mark")
        ]
    ),
    EventTemplate(
        "abandoned_mine",
        EVENT_CONFIG["abandoned_mine"]["description"],
        [
            RideCartOption("坐上生锈矿车滑入矿坑", "ride_cart"),
            ClimbLadderOption("沿着破旧梯子慢慢爬下去", "climb_ladder")
        ]
    ),
    EventTemplate(
        "phantom_mage",
        EVENT_CONFIG["phantom_mage"]["description"],
        [
            ReadScrollOption("解读残卷", "read_scroll"),
            ResonateScrollOption("用魔网产生共鸣", "resonate_scroll"),
            DispelPhantomOption("驱散残影", "dispel_phantom"),
            LeaveEventOption("悄悄离开", "leave_event", "phantom_mage")
        ]
    ),
    EventTemplate(
        "goblin_gamble",
        EVENT_CONFIG["goblin_gamble"]["description"],
        [
            GambleSmallOption("小赌一把", "gamble_small"),
            GambleLargeOption("豪赌一把", "gamble_large"),
            RobGoblinOption("强行抢劫", "rob_goblin"),
            LeaveEventOption("拒绝并离开", "leave_event", "goblin_gamble")
        ]
    ),
    EventTemplate(
        "fairy_tea",
        EVENT_CONFIG["fairy_tea"]["description"],
        [
            DrinkNectarOption("饮用红色花蜜茶", "drink_nectar"),
            EatCookieOption("享用绿色坚果饼", "eat_cookie"),
            ListenMusicOption("倾听妖精的八音盒", "listen_music"),
            LeaveEventOption("婉言谢绝并离开", "leave_event", "fairy_tea")
        ],
        min_stage=2,
        max_stage=9
    ),
    EventTemplate(
        "void_contract",
        EVENT_CONFIG["void_contract"]["description"],
        [
            ContractRelicOption("献祭生命换取遗物", "contract_relic"),
            ContractLegendOption("以血肉之躯汲取奥法", "contract_legend"),
            AbsorbVoidOption("将虚空吞噬", "absorb_void"),
            LeaveEventOption("拒绝契约并离开", "leave_event", "void_contract")
        ],
        min_stage=12,
        max_stage=19
    )
]

def get_option_by_action(action: str) -> Optional[EventOption]:
    mapping = {
        "drink_fountain": DrinkFountainOption("饮用泉水", "drink_fountain"),
        "coin_fountain": CoinFountainOption("投入金币", "coin_fountain"),
        "observe_fountain": ObserveFountainOption("仔细观察泉底", "observe_fountain"),
        "take_necklace": TakeNecklaceOption("冒险捞取项链", "take_necklace"),
        "help_knight": HelpKnightOption("施以援手", "help_knight"),
        "rob_knight": RobKnightOption("趁火打劫", "rob_knight"),
        "ask_knight": AskKnightOption("询问他的来历", "ask_knight"),
        "cave_quest": CaveQuestOption("帮他去洞穴取回长剑", "cave_quest"),
        "cave_fight": CaveFightOption("进入战斗", "cave_fight"),
        "absorb_altar": AbsorbAltarOption("汲取奥术", "absorb_altar"),
        "break_altar": BreakAltarOption("摧毁水晶", "break_altar"),
        "meditate_altar": MeditateAltarOption("在祭坛前冥想", "meditate_altar"),
        "enter_portal": EnterPortalOption("跨入传送门", "enter_portal"),
        "shatter_portal": ShatterPortalOption("摧毁传送门", "shatter_portal"),
        "maze_fire": MazeFireOption("循着远处的微弱火光走", "maze_fire"),
        "maze_water": MazeWaterOption("沿着潺潺的水流声走", "maze_water"),
        "maze_mark": MazeMarkOption("在墙壁做标记，小心翼翼前行", "maze_mark"),
        "bribe_guard": BribeGuardOption("贿赂守卫", "bribe_guard"),
        "fight_guard": FightGuardOption("与守卫战斗", "fight_guard"),
        "bathe_pool": BathePoolOption("在泉水中沐浴", "bathe_pool"),
        "fish_pool": FishPoolOption("捞取水底的遗物", "fish_pool"),
        "ride_cart": RideCartOption("坐上生锈矿车滑入矿坑", "ride_cart"),
        "climb_ladder": ClimbLadderOption("沿着破旧梯子慢慢爬下去", "climb_ladder"),
        "jump_cart": JumpCartOption("果断跳车", "jump_cart"),
        "stop_cart_spell": StopCartSpellOption("使用法术或盾牌强行刹车", "stop_cart_spell"),
        "loot_body": LootBodyOption("搜刮干尸", "loot_body"),
        "dig_ore": DigOreOption("用重火力法术轰开矿坑底部的矿墙", "dig_ore"),
        "leave_event": LeaveEventOption("离开事件", "leave_event"),
        "read_scroll": ReadScrollOption("解读残卷", "read_scroll"),
        "resonate_scroll": ResonateScrollOption("用魔网产生共鸣", "resonate_scroll"),
        "dispel_phantom": DispelPhantomOption("驱散残影", "dispel_phantom"),
        "gamble_small": GambleSmallOption("小赌一把", "gamble_small"),
        "gamble_large": GambleLargeOption("豪赌一把", "gamble_large"),
        "rob_goblin": RobGoblinOption("强行抢劫", "rob_goblin"),
        "drink_nectar": DrinkNectarOption("饮用红色花蜜茶", "drink_nectar"),
        "eat_cookie": EatCookieOption("享用绿色坚果饼", "eat_cookie"),
        "listen_music": ListenMusicOption("倾听妖精的八音盒", "listen_music"),
        "contract_relic": ContractRelicOption("献祭生命换取遗物", "contract_relic"),
        "contract_legend": ContractLegendOption("以血肉之躯汲取奥法", "contract_legend"),
        "absorb_void": AbsorbVoidOption("将虚空吞噬", "absorb_void")
    }
    return mapping.get(action)
