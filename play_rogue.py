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

from game.models.manager import SaveManager
from game.renderer import GameRenderer
from main import MyPlugin

class DummyContext:
    pass

class DummyEvent:
    def __init__(self, message_str: str, sender_id: str = "console_player"):
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
    print("================━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━====================")
    print("  ✨ 欢迎来到魔法肉鸽卡牌游戏控制台版！")
    print("  💬 本控制台版不需要前缀即可游玩，比如输入：开启 / 使用 1 / 结束")
    print("  🚪 输入 exit 退出控制台")
    print("================━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━====================")
    
    run = plugin.save_manager.load_save("console_player")
    if run:
        print(GameRenderer.render_game(run))
    else:
        print(GameRenderer.render_menu())
        
    while True:
        try:
            line = input("RogueConsole> ").strip()
            if not line:
                continue
            if line.lower() in ("exit", "quit"):
                break
            if not line.startswith(".") and not line.startswith("/"):
                line = ".rogue " + line
            res = await run_command(plugin, line)
            print(res)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
