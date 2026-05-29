import os
import sys
import io
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

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
    
    print("=== 1. Test Query Red Dragon ===")
    res = await run_cmd(plugin, ".rogue 查询 远古红龙")
    print(res)
    assert "远古红龙" in res
    assert "领主" in res
    assert "60" in res
    assert "1A 2BA" in res
    assert "魔仆" in res
    print("Passed 1!")

    print("=== 2. Test Query Corrupted Heart ===")
    res = await run_cmd(plugin, ".rogue 查询 腐化之心")
    print(res)
    assert "腐化之心" in res
    assert "领主" in res
    assert "120" in res
    assert "死亡律动" in res
    assert "第一回合" in res
    print("Passed 2!")

    print("=== 3. Test Query Goblin Centurion ===")
    res = await run_cmd(plugin, ".rogue 查询 地精百夫长")
    print(res)
    assert "地精百夫长" in res
    assert "精英" in res
    assert "30 (+ 3 * 关卡数)" in res
    assert "重击" in res
    print("Passed 3!")

    print("=== 4. Test Query Goblin Raider ===")
    res = await run_cmd(plugin, ".rogue 查询 地精突袭者")
    print(res)
    assert "地精突袭者" in res
    assert "普通" in res
    assert "12 (+ 2 * 关卡数)" in res
    print("Passed 4!")

    print("=== 5. Test Query Summon Hound ===")
    res = await run_cmd(plugin, ".rogue 查询 狂暴猎犬")
    print(res)
    assert "狂暴猎犬" in res
    assert "召唤物" in res
    assert "扑咬" in res
    print("Passed 5!")

    print("=== 6. Test Help Description ===")
    res = await run_cmd(plugin, ".rogue 帮助")
    assert "Buff/怪物信息" in res
    print("Passed 6!")

    print("All query tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
