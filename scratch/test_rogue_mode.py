import os
import sys
import io
import asyncio

if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import MyPlugin

class DummyContext:
    pass

class DummyEvent:
    def __init__(self, message_str: str, sender_id: str = "test_user_rogue"):
        self.message_str = message_str
        self.sender_id = sender_id
        self.results = []
        self.stopped = False

    def get_sender_id(self) -> str:
        return self.sender_id

    def plain_result(self, text: str):
        self.results.append(text)
        return text

    def stop_event(self):
        self.stopped = True

async def test_rogue_mode():
    plugin = MyPlugin(DummyContext())
    plugin.save_manager.delete_save("test_user_rogue")
    
    stats_path = plugin.save_manager.get_stats_path("test_user_rogue")
    if os.path.exists(stats_path):
        os.remove(stats_path)

    stats = plugin.save_manager.load_stats("test_user_rogue")
    assert stats.rogue_mode is False, "Default rogue mode must be False"

    event_toggle = DummyEvent(".rogue mode")
    async for _ in plugin.shortcut_rogue(event_toggle): pass
    
    stats = plugin.save_manager.load_stats("test_user_rogue")
    assert stats.rogue_mode is True, "Rogue mode must be toggled to True"
    assert "免前缀肉鸽模式已开启" in "\n".join(event_toggle.results)

    event_start = DummyEvent("开启")
    async for _ in plugin.shortcut_rogue(event_start): pass
    assert event_start.stopped is True, "Event should be stopped and intercepted"
    start_res = "\n".join(event_start.results)
    assert "先古契约" in start_res, "Game should start"

    event_chat = DummyEvent("你好吗")
    async for _ in plugin.shortcut_rogue(event_chat): pass
    assert event_chat.stopped is False, "Normal chat messages should not be intercepted"

    event_num_with_save = DummyEvent("1")
    async for _ in plugin.shortcut_rogue(event_num_with_save): pass
    assert event_num_with_save.stopped is True, "Digit should be intercepted if save exists"

    event_alias_deck = DummyEvent("deck")
    async for _ in plugin.shortcut_rogue(event_alias_deck): pass
    assert event_alias_deck.stopped is True
    assert "当前拥有的卡组" in "\n".join(event_alias_deck.results)

    event_alias_overview = DummyEvent("overview")
    async for _ in plugin.shortcut_rogue(event_alias_overview): pass
    assert event_alias_overview.stopped is True
    assert "魔法肉鸽卡牌总览" in "\n".join(event_alias_overview.results)

    event_alias_abandon = DummyEvent("abandon confirm")
    async for _ in plugin.shortcut_rogue(event_alias_abandon): pass
    assert event_alias_abandon.stopped is True
    assert "已放弃当前局内游戏" in "\n".join(event_alias_abandon.results)

    event_num_no_save = DummyEvent("1")
    async for _ in plugin.shortcut_rogue(event_num_no_save): pass
    assert event_num_no_save.stopped is False, "Digit should NOT be intercepted if no save exists"

    event_toggle_off = DummyEvent("模式")
    async for _ in plugin.shortcut_rogue(event_toggle_off): pass
    stats = plugin.save_manager.load_stats("test_user_rogue")
    assert stats.rogue_mode is False, "Rogue mode must be toggled to False"

    event_start_disabled = DummyEvent("开启")
    async for _ in plugin.shortcut_rogue(event_start_disabled): pass
    assert event_start_disabled.stopped is False, "No-prefix start should not intercept when rogue mode is False"

    print("ROGUE MODE TEST PASSED!")

if __name__ == "__main__":
    asyncio.run(test_rogue_mode())
