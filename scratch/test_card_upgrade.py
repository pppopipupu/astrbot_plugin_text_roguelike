import os
import sys
import io
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from game.models.manager import SaveManager
from main import MyPlugin
from game.renderer.query import render_query_info
from game.cards import ALL_CARDS
from game.engine import GameEngine
from game.core.map_engine import MapEngine
from game.models.state import GameRun, PlayerState

class DummyContext:
    pass

class DummyEvent:
    def __init__(self, message_str: str, sender_id: str = "test_user_upg"):
        self.message_str = message_str
        self.sender_id = sender_id
        self.results = []

    def get_sender_id(self) -> str:
        return self.sender_id

    def plain_result(self, text: str):
        self.results.append(text)
        return text

    def stop_event(self):
        pass

async def run_cmd(plugin, cmd: str):
    event = DummyEvent(cmd)
    await plugin.shortcut_rogue(event)
    if not event.results:
        generator_cmd = plugin.rogue(event)
        async for _ in generator_cmd:
            pass
    return "\n".join(event.results)

async def test_all():
    fb = ALL_CARDS.get("fireball")
    fb_plus = ALL_CARDS.get("fireball+")
    assert fb is not None
    assert fb_plus is not None
    assert fb_plus.upgraded is True
    assert fb_plus.base_dmg == 22

    q_res_normal = render_query_info("fireball")
    assert "升级变体" in q_res_normal
    assert "22" in q_res_normal

    q_res_plus = render_query_info("fireball+")
    assert "升级变体" in q_res_plus
    assert "22" in q_res_plus

    plugin = MyPlugin(DummyContext())
    save_manager = SaveManager()
    save_manager.delete_save("test_user_upg")

    await run_cmd(plugin, ".rogue 开启 确认")
    await run_cmd(plugin, ".rogue 选择 1")
    
    run = save_manager.load_save("test_user_upg")
    run.node_type = "rest"
    run.node_data = {}
    save_manager.save_save("test_user_upg", run)

    res = await run_cmd(plugin, ".rogue 选择 4")
    assert "卡牌升级强化已启动" in res

    run = save_manager.load_save("test_user_upg")
    assert run.node_data.get("pending_upgrade") is True

    res_upg = await run_cmd(plugin, ".rogue 选择 1")
    assert "升级成功" in res_upg

    run = save_manager.load_save("test_user_upg")
    assert any(card.endswith("+") for card in run.player.deck)

    run.node_type = "event"
    run.node_data = {
        "event_id": "forge_furnace",
        "description": "奥术符文熔炉描述",
        "options": [
            {"text": "使用常规重铸", "action": "forge_fire"},
            {"text": "过载重铸", "action": "overload_forge"},
            {"text": "汲取熔炉余温", "action": "forge_backfire"},
            {"text": "强行破坏熔炉", "action": "shatter_forge"},
            {"text": "安全离开", "action": "leave_event"}
        ]
    }
    save_manager.save_save("test_user_upg", run)

    res_event_fire = await run_cmd(plugin, ".rogue 选择 1")
    print("res_event_fire is:", repr(res_event_fire))
    assert "卡牌升级强化已启动" in res_event_fire

    run = save_manager.load_save("test_user_upg")
    run.node_type = "event"
    run.node_data = {
        "event_id": "forge_furnace",
        "description": "奥术符文熔炉描述",
        "options": [
            {"text": "使用常规重铸", "action": "forge_fire"},
            {"text": "过载重铸", "action": "overload_forge"},
            {"text": "汲取熔炉余温", "action": "forge_backfire"},
            {"text": "强行破坏熔炉", "action": "shatter_forge"},
            {"text": "安全离开", "action": "leave_event"}
        ]
    }
    save_manager.save_save("test_user_upg", run)
    
    res_backfire = await run_cmd(plugin, ".rogue 选择 3")
    print("res_backfire is:", repr(res_backfire))
    assert "炉温反噬" in res_backfire
    
    run = save_manager.load_save("test_user_upg")
    assert any(b.id == "forge_backfire" for b in run.player.buffs)

    save_manager.delete_save("test_user_upg")
    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_all())
