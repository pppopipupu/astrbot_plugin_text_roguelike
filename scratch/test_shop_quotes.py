import os
import sys
import io
import asyncio

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models.state import UserStats
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

async def run_command(plugin, cmd_str: str) -> str:
    event = DummyEvent(cmd_str)
    await plugin.shortcut_rogue(event)
    if not event.results:
        generator_cmd = plugin.rogue(event)
        async for _ in generator_cmd:
            pass
    return "\n".join(event.results)

async def test_shop_quotes():
    plugin = MyPlugin(DummyContext())
    
    stats = plugin.save_manager.load_stats("test_user")
    stats.gp = 100
    stats.unlocked_subclasses = []
    plugin.save_manager.save_stats("test_user", stats)
    
    output = await run_command(plugin, ".rogue 商店")
    print("--- OUTPUT ---")
    print(output)
    
    welcome_quotes = [
        "“...嘘，悄悄看，我这儿可都是从无尽时空深处淘来的宝贝。”",
        "“又是你，旅者？只要GP足够，我这里的东西随时都可以归你。”",
        "“想要掌控时间，还是驾驭元素？或者……你对那件‘神秘物品’感兴趣？”",
        "“奥术的轨迹是有限的，但金钱和力量的秘密是无限的。”",
        "“有些东西并不存在于当下的时空，但在这里，一切皆有可能。”",
        "“外面的风暴越来越近了，或许你该准备点真正强力的武器？”"
    ]
    found_welcome = any(quote in output for quote in welcome_quotes)
    assert found_welcome, f"Expected one of welcome quotes in: {output}"
    
    output_fail = await run_command(plugin, ".rogue 商店 购买 1")
    print("--- OUTPUT FAIL ---")
    print(output_fail)
    
    fail_quotes = [
        "“呵呵，我的宝贝可概不赊账。多去地下城闯一闯，赚够了GP再来吧。”",
        "“看来你的钱包和你的雄心壮志并不相符，旅者。”",
        "“钱不够？那可不行。等你有了足够的GP，我随时在这儿等你。”",
        "“GP不够可是买不到虚空造物的，去多打败一些强大的怪兽吧。”",
        "“哦？想要空手套白狼？这可不是一个合格法师该有的行为。”",
        "“即使是至高法皇，没钱也得从我这里老老实实地退出去，懂吗？”"
    ]
    found_fail = any(quote in output_fail for quote in fail_quotes)
    assert "GP" in output_fail
    assert "不足" in output_fail
    assert found_fail, f"Expected one of fail quotes in: {output_fail}"
    
    stats.gp = 10000
    plugin.save_manager.save_stats("test_user", stats)
    
    output_success = await run_command(plugin, ".rogue 商店 购买 1")
    print("--- OUTPUT SUCCESS ---")
    print(output_success)
    
    success_quotes = [
        "“明智的选择，它现在属于你了。”",
        "“收您对应GP，拿好它，祝您好运，勇敢的旅者。”",
        "“呵呵，这股力量已经在虚空中沉睡了太久，希望你能配得上它。”",
        "“拿去吧，它会指引你在接下来的地下城里改写宿命。”",
        "“噢……它离去时，连虚空的波动都微微震颤了一下。”",
        "“成交。记住，有些契约一经签订，便无法回头。”"
    ]
    found_success = any(quote in output_success for quote in success_quotes)
    assert "购买成功" in output_success
    assert found_success, f"Expected one of success quotes in: {output_success}"
    
    assert "**" not in output
    assert "**" not in output_fail
    assert "**" not in output_success
    
    print("Shop quotes and purchase behavior tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_shop_quotes())
