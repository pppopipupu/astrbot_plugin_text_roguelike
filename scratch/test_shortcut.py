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
    def __init__(self, message_str: str, sender_id: str = "test_user"):
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

async def test_shortcut():
    plugin = MyPlugin(DummyContext(), config={"enable_shortcut": True, "shortcut_prefix": [".rogue", ".rg", "xr"]})
    plugin.save_manager.delete_save("test_user")
    
    event_start = DummyEvent("xr 开启")
    async for _ in plugin.shortcut_rogue(event_start): pass
    
    event_choose = DummyEvent(".rg 1")
    async for _ in plugin.shortcut_rogue(event_choose): pass
    
    res = "\n".join(event_choose.results)
    print("OUTPUT FROM .rg 1:")
    print(res)
    assert "契约达成" in res or "选择" in res, "Failed shortcut list config redirect"
    
    plugin2 = MyPlugin(DummyContext(), config={"enable_shortcut": True, "shortcut_prefix": [".rg", ".rogue"]})
    plugin2.save_manager.delete_save("test_user")
    
    event_start2 = DummyEvent(".rogue 开启")
    async for _ in plugin2.shortcut_rogue(event_start2): pass
    
    res2 = "\n".join(event_start2.results)
    print("OUTPUT FROM .rogue 开启 with shorter prefix first:")
    print(res2)
    assert "未知子命令" not in res2, "Failed to resolve correct prefix when shorter prefix matches part of it"
    assert "契约达成" in res2 or "选择" in res2 or "冒险" in res2, "Failed to start game"
    
    print("SHORTCUT TEST PASSED!")

if __name__ == "__main__":
    asyncio.run(test_shortcut())
