import random
from .base import EventOption

class GambleSmallOption(EventOption, action="gamble_small", text="小赌一把"):
    def _run_effect(self, run, engine) -> str:
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

class GambleLargeOption(EventOption, action="gamble_large", text="豪赌一把"):
    def _run_effect(self, run, engine) -> str:
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

class RobGoblinOption(EventOption, action="rob_goblin", text="强行抢劫"):
    def _run_effect(self, run, engine) -> str:
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
