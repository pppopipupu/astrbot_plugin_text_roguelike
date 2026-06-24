from typing import Generator
from ...base import CommandHandler
from .....renderer import GameRenderer

class QueueCommand(CommandHandler, names=["队列", "q", "queue"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        if len(parts) < 2:
            yield "❌ 请提供队列操作，例如：/rogue 队列 [使用 1, 随从 1 技能 2, 结束]"
            return
        full_arg = " ".join(parts[1:]).strip()
        run = router.save_manager.load_save(user_id)
        if run:
            results = []
            router._execute_queue(user_id, run, full_arg, results)
            if run.player.hp <= 0:
                yield "\n".join(results)
            else:
                yield "\n".join(results) + "\n" + GameRenderer.render_game(run)
        else:
            content = full_arg
            if content.startswith("[") and content.endswith("]"):
                content = content[1:-1].strip()
            from ...base import split_by_comma_with_brackets
            items = split_by_comma_with_brackets(content)
            results = []
            for item in items:
                if not item:
                    continue
                parts_sub = item.split()
                if not parts_sub:
                    continue
                sub_res_list = list(router.handle_command(user_id, parts_sub))
                if sub_res_list:
                    results.append("\n".join(sub_res_list))
            if results:
                yield "\n\n".join(results)
            else:
                yield "💬 队列未执行任何有效指令。"
