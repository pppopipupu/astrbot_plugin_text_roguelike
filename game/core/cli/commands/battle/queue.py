from typing import Generator
from ...base import CommandHandler
from .....renderer import GameRenderer

class QueueCommand(CommandHandler, names=["队列", "q", "queue", "qi", "queue_interrupt", "中断队列"]):
    def execute(self, router, user_id: str, parts: list[str]) -> Generator[str, None, None]:
        if len(parts) < 2:
            yield "❌ 请提供队列操作，例如：/rogue 队列 [使用 1, 随从 1 技能 2, 结束]"
            return
        is_qi = parts[0].lower() in ("qi", "queue_interrupt", "中断队列")
        full_arg = " ".join(parts[1:]).strip()
        run = router.save_manager.load_save(user_id)
        if run:
            results = []
            router._execute_queue(user_id, run, full_arg, results, interrupt_on_fail=is_qi)
            run = router.save_manager.load_save(user_id)
            if not run or run.player.hp <= 0:
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
                first_sub = parts_sub[0].lower()
                cmd_handler = router._command_handlers.get(first_sub)
                if cmd_handler:
                    curr_state = "menu"
                    stats = router.save_manager.load_stats(user_id)
                    if stats and stats.in_town:
                        curr_state = "town"
                    if curr_state in getattr(cmd_handler, "allowed_states", []):
                        gen = cmd_handler.execute(router, user_id, parts_sub)
                        res_list = []
                        success = True
                        try:
                            while True:
                                res_list.append(next(gen))
                        except StopIteration as e:
                            success = e.value if e.value is not None else True
                        res = "\n".join(res_list)
                    else:
                        res = f"❌ 指令【{first_sub}】在当前状态下不可用。"
                        success = False
                else:
                    res = f"❌ 未知指令：{first_sub}"
                    success = False
                results.append(res)
                if is_qi and not success:
                    break
            if results:
                yield "\n\n".join(results)
            else:
                yield "💬 队列未执行任何有效指令。"
