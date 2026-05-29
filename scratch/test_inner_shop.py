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
    def __init__(self, message_str: str, sender_id: str = "test_inner_shop_user"):
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

async def run_command(plugin, cmd_str: str, sender_id: str = "test_inner_shop_user") -> str:
    event = DummyEvent(cmd_str, sender_id)
    await plugin.shortcut_rogue(event)
    if not event.results:
        generator = plugin.rogue(event)
        async for _ in generator:
            pass
    return "\n".join(event.results)

async def test_inner_shop():
    plugin = MyPlugin(DummyContext())
    user_id = "test_inner_shop_user"
    plugin.save_manager.delete_save(user_id)
    
    await run_command(plugin, ".rogue 开启")
    await run_command(plugin, ".rogue 选择 1")
    
    run = plugin.save_manager.load_save(user_id)
    assert run is not None
    
    run.node_type = "shop"
    plugin.engine.map_engine.explore_engine._init_shop_node(run)
    plugin.save_manager.save_save(user_id, run)
    
    status_output = await run_command(plugin, ".rogue 状态")
    print("--- SHOP INITIAL DISPLAY ---")
    print(status_output)
    assert "奇妙商店" in status_output
    assert "净化服务" in status_output
    assert "离开商店" in status_output
    
    run = plugin.save_manager.load_save(user_id)
    run.player.gold = 500
    plugin.save_manager.save_save(user_id, run)
    initial_gold = 500
    initial_deck_len = len(run.player.deck)
    
    items = run.node_data.get("items", [])
    card_idx = -1
    for idx, item in enumerate(items):
        if item.get("type") == "card":
            card_idx = idx + 1
            break
            
    assert card_idx != -1
    buy_res = await run_command(plugin, f".rogue 选择 {card_idx}")
    print("--- BUY CARD RESULT ---")
    print(buy_res)
    assert "购买成功" in buy_res
    
    run = plugin.save_manager.load_save(user_id)
    assert len(run.player.deck) == initial_deck_len + 1
    assert run.player.gold < initial_gold
    
    relic_idx = -1
    for idx, item in enumerate(items):
        if item.get("type") == "relic":
            relic_idx = idx + 1
            break
            
    if relic_idx != -1:
        run = plugin.save_manager.load_save(user_id)
        run.player.gold = 500
        plugin.save_manager.save_save(user_id, run)
        
        buy_relic_res = await run_command(plugin, f".rogue 选择 {relic_idx}")
        print("--- BUY RELIC RESULT ---")
        print(buy_relic_res)
        assert "购买成功" in buy_relic_res
        
        run = plugin.save_manager.load_save(user_id)
        relic_id = items[relic_idx - 1].get("relic_id")
        assert relic_id in run.player.relics
        
    leave_idx = -1
    for idx, item in enumerate(items):
        if item.get("type") == "leave":
            leave_idx = idx + 1
            break
            
    assert leave_idx != -1
    leave_res = await run_command(plugin, f".rogue 选择 {leave_idx}")
    print("--- LEAVE SHOP RESULT ---")
    print(leave_res)
    assert "你离开了商店" in leave_res
    
    run = plugin.save_manager.load_save(user_id)
    assert run.node_type != "shop"
    
    print("INNER SHOP TEST PASSED!")

if __name__ == "__main__":
    asyncio.run(test_inner_shop())
