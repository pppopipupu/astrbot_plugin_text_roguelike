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
    generator = plugin.shortcut_rogue(event)
    async for _ in generator:
        pass
    if not event.results:
        generator_cmd = plugin.rogue(event)
        async for _ in generator_cmd:
            pass
    return "\n".join(event.results)

async def main():
    plugin = MyPlugin(DummyContext())
    
    print("=== 1. 测试总览（无参数，默认卡牌） ===")
    res_default = await run_cmd(plugin, ".rogue 总览")
    assert "魔法肉鸽卡牌总览" in res_default, "无参数时应该展示卡牌总览"
    assert "魔法肉鸽遗物总览" not in res_default, "无参数时不能展示遗物总览"
    print("测试通过！")
    
    print("=== 2. 测试总览 卡牌 ===")
    res_cards = await run_cmd(plugin, ".rogue 总览 卡牌")
    assert "魔法肉鸽卡牌总览" in res_cards, "指定卡牌时应该展示卡牌总览"
    assert "魔法肉鸽遗物总览" not in res_cards, "指定卡牌时不能展示遗物总览"
    print("测试通过！")
    
    print("=== 3. 测试总览 遗物 ===")
    res_relics = await run_cmd(plugin, ".rogue 总览 遗物")
    assert "魔法肉鸽遗物总览" in res_relics, "指定遗物时应该展示遗物总览"
    assert "魔法肉鸽卡牌总览" not in res_relics, "指定遗物时不能展示卡牌总览"
    assert "先古之眼" in res_relics, "遗物总览中应该包含遗物详情，如先古之眼"
    print("测试通过！")
    
    print("=== 4. 测试总览 relic ===")
    res_relics_en = await run_cmd(plugin, ".rogue 总览 relic")
    assert "魔法肉鸽遗物总览" in res_relics_en, "指定relic时应该展示遗物总览"
    print("测试通过！")
    
    print("=== 5. 测试帮助命令中总览的说明 ===")
    res_help = await run_cmd(plugin, ".rogue 帮助")
    assert "总览 [卡牌/遗物]" in res_help, "帮助信息中应该有总览 [卡牌/遗物] 提示"
    print("测试通过！所有总览指令测试全部成功！")

if __name__ == "__main__":
    asyncio.run(main())
