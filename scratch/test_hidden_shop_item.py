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
from main import MyPlugin

class DummyContext:
    pass

class DummyEvent:
    def __init__(self, message_str: str, sender_id: str = "test_hidden_shop_user"):
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

async def run_command(plugin, cmd_str: str, sender_id: str = "test_hidden_shop_user") -> str:
    event = DummyEvent(cmd_str, sender_id)
    await plugin.shortcut_rogue(event)
    if not event.results:
        generator = plugin.rogue(event)
        async for _ in generator:
            pass
    return "\n".join(event.results)

async def test_hidden_shop():
    plugin = MyPlugin(DummyContext())
    user_id = "test_hidden_shop_user"
    
    plugin.save_manager.delete_save(user_id)
    stats_path = plugin.save_manager.get_stats_path(user_id)
    if os.path.exists(stats_path):
        os.remove(stats_path)

    stats = plugin.save_manager.load_stats(user_id)
    stats.killed_icerainboww = False
    plugin.save_manager.save_stats(user_id, stats)

    shop_output_false = await run_command(plugin, "/rogue 商店")
    print("--- SHOP DISPLAY (killed_icerainboww = False) ---")
    print(shop_output_false)
    assert "[4] ？？？ - 状态：未解锁" in shop_output_false
    assert "击败未知的最终BOSS解锁。" in shop_output_false
    assert "Icerainboww" not in shop_output_false

    buy_4_false = await run_command(plugin, "/rogue 商店 购买 4")
    print("--- BUY 4 RESULT (False) ---")
    print(buy_4_false)
    assert "❌ 无法购买未知的隐藏商品。" in buy_4_false

    buy_name_false = await run_command(plugin, "/rogue 商店 购买 Icerainboww")
    print("--- BUY BY NAME RESULT (False) ---")
    print(buy_name_false)
    assert "❌ 无法购买未知的隐藏商品。" in buy_name_false

    buy_5_false = await run_command(plugin, "/rogue 商店 购买 5")
    print("--- BUY 5 RESULT (False) ---")
    print(buy_5_false)
    assert "❌ 无效的商品。可选商品序号：1、2、3。" in buy_5_false

    stats = plugin.save_manager.load_stats(user_id)
    stats.killed_icerainboww = True
    plugin.save_manager.save_stats(user_id, stats)

    shop_output_true = await run_command(plugin, "/rogue 商店")
    print("--- SHOP DISPLAY (killed_icerainboww = True) ---")
    print(shop_output_true)
    assert "[4] Icerainboww - 状态：已解锁" in shop_output_true
    assert "击败最终BOSS Icerainboww解锁。" in shop_output_true

    buy_4_true = await run_command(plugin, "/rogue 商店 购买 4")
    print("--- BUY 4 RESULT (True) ---")
    print(buy_4_true)
    assert "❌ 该商品已自动解锁，无需购买。" in buy_4_true

    buy_name_true = await run_command(plugin, "/rogue 商店 购买 Icerainboww")
    print("--- BUY BY NAME RESULT (True) ---")
    print(buy_name_true)
    assert "❌ 该商品已自动解锁，无需购买。" in buy_name_true

    buy_5_true = await run_command(plugin, "/rogue 商店 购买 5")
    print("--- BUY 5 RESULT (True) ---")
    print(buy_5_true)
    assert "❌ 无效的商品。可选商品序号：1、2、3、4。" in buy_5_true

    if os.path.exists(stats_path):
        os.remove(stats_path)
    print("HIDDEN SHOP ITEM TEST PASSED!")

if __name__ == "__main__":
    asyncio.run(test_hidden_shop())
