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
    plugin = MyPlugin(DummyContext())
    plugin.save_manager.delete_save("test_user")
    
    event_start = DummyEvent(".rogue 开启")
    async for _ in plugin.shortcut_rogue(event_start): pass
    
    event_choose = DummyEvent(".rogue 1")
    async for _ in plugin.shortcut_rogue(event_choose): pass
    
    res = "\n".join(event_choose.results)
    print("OUTPUT FROM .rogue 1:")
    print(res)
    assert "契约达成" in res or "选择" in res, "Failed shortcut redirect"
    print("SHORTCUT TEST PASSED!")

if __name__ == "__main__":
    asyncio.run(test_shortcut())
