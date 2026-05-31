import random
from .base import EventOption
from ...data.event_data import EVENT_CONFIG
from ..relics import get_relic_name

class RideCartOption(EventOption, action="ride_cart", text="坐上生锈矿车滑入矿坑"):
    def _run_effect(self, run, engine) -> str:
        cfg = EVENT_CONFIG["mine_cart_crash"]
        run.node_data["event_id"] = "mine_cart_crash"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你纵身跳上停在轨道上的生锈矿车，松开了手刹，矿车顺着轨道稳冲而下..."

class ClimbLadderOption(EventOption, action="climb_ladder", text="沿着破旧梯子慢慢爬下去"):
    def _run_effect(self, run, engine) -> str:
        cfg = EVENT_CONFIG["mine_ladder_body"]
        run.node_data["event_id"] = "mine_ladder_body"
        run.node_data["description"] = cfg["description"]
        run.node_data["options"] = [{"text": o["text"], "action": o["action"]} for o in cfg["options"]]
        engine.save_manager.save_save(run.user_id, run)
        return "你顺着吱呀作响的木质旋转扶梯，一步步向矿坑深处摸去..."

class JumpCartOption(EventOption, action="jump_cart", text="果断跳车"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.gold += 40
        p.deck.append("curse_dazed")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "🤕 在矿车冲入深渊的前一瞬间，你狼狈地跳车。你重重摔在坚硬的矿石上并感到一阵晕眩（1张【晕眩】卡牌已加入卡组），但在碎石堆中获得了 40 金币。"

class StopCartSpellOption(EventOption, action="stop_cart_spell", text="使用法术或盾牌强行刹车"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        has_key_card = any(cid in p.deck for cid in ["shield_guard", "fireball", "thunderwave"])
        if has_key_card:
            relics_pool = ["lucky_coin", "red_bottle", "leather_armor", "whetstone", "ready_pack", "arcane_rune"]
            available_relics = [r for r in relics_pool if r not in p.relics]
            got_relic = ""
            if available_relics:
                got_relic = random.choice(available_relics)
                p.relics.append(got_relic)
                if got_relic == "red_bottle":
                    p.max_hp += 5
                    p.hp += 5
            relic_msg = f"，并从脱落的铸铁轨道环上取下了一个精密的遗物【{get_relic_name(got_relic)}】" if got_relic else ""
            res = f"🛡️ 你利用卡组中强大的法术/随从力量顶住了矿车底盘，伴随着令人牙酸的摩擦火花，矿车在悬崖前奇迹般停下。你安然无恙{relic_msg}！"
        else:
            p.hp = max(1, p.hp - 10)
            p.gold += 10
            res = "💀 你无法有效控制疯狂疾驰的矿车！矿车飞出了断裂轨道跌落崖底。伴随着金属扭曲的巨响，你受到重创（失去 10 生命值），只勉强在残骸中搜集到了 10 金币。"
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return res

class LootBodyOption(EventOption, action="loot_body", text="搜刮干尸"):
    def _run_effect(self, run, engine) -> str:
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

class DigOreOption(EventOption, action="dig_ore", text="用重火力法术轰开矿坑底部的矿墙"):
    def _run_effect(self, run, engine) -> str:
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
