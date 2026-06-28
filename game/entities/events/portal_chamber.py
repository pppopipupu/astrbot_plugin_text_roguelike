import math
from .base import EventOption

class ContractPortalOption(EventOption, action="contract_portal", text="献祭最大生命换取遗物"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        cost_hp = math.ceil(p.max_hp * 0.05)
        p.max_hp = max(5, p.max_hp - cost_hp)
        p.hp = min(p.hp, p.max_hp)
        if "portal_fragment" not in p.relics:
            p.relics.append("portal_fragment")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return f"🖤 契约达成！你感到自己的虚空感知被极大地增强，但灵魂本源受到了永久的削弱（最大生命值上限减少 {cost_hp} 点）。你获得了遗物【门扉碎片】。"

class ArcanePortalOption(EventOption, action="arcane_portal", text="获得万能钥匙和空间撕裂"):
    def _run_effect(self, run, engine) -> str:
        p = run.player
        p.deck.append("master_key")
        p.deck.append("curse_dimensional_tear")
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "🌌 奥术之门开启！你获得了泛着星光的法术卡牌【万能钥匙】。然而，空间通道的不稳定导致你的灵魂沾染了异次元的尘埃（一张【空间撕裂】诅咒卡被塞入了你的卡组）。"
