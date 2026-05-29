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

async def run_cmd(plugin, cmd: str):
    event = DummyEvent(cmd)
    await plugin.shortcut_rogue(event)
    if not event.results:
        generator_cmd = plugin.rogue(event)
        async for _ in generator_cmd:
            pass
    return "\n".join(event.results)

async def main():
    plugin = MyPlugin(DummyContext())
    save_manager = SaveManager()
    save_manager.delete_save("test_user")
    
    print("=== 1. 开启游戏 ===")
    res = await run_cmd(plugin, ".rogue 开启 确认")
    print(res)
    
    print("\n=== 2. 选择先古契约第 1 项 ===")
    res = await run_cmd(plugin, ".rogue 选择 1")
    print(res)
    
    print("\n=== 3. 查看当前状态 ===")
    res = await run_cmd(plugin, ".rogue 状态")
    print(res)
    
    print("\n=== 4. 查看当前卡组 ===")
    res = await run_cmd(plugin, ".rogue 牌组")
    print(res)

    print("\n=== 5. 选择地图路线第 1 分支 ===")
    res = await run_cmd(plugin, ".rogue 选择 1")
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
