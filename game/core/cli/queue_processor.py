from ..cli.base import split_by_comma_with_brackets

class QueueProcessor:
    def __init__(self, save_manager, engine):
        self.save_manager = save_manager
        self.engine = engine

    def execute_queue(self, router, user_id: str, run, queue_content: str, results: list[str]) -> bool:
        content = queue_content.strip()
        if content.startswith("[") and content.endswith("]"):
            content = content[1:-1].strip()
        items = split_by_comma_with_brackets(content)
        for item in items:
            if not item:
                continue
            parts_sub = item.split()
            if not parts_sub:
                continue
            first_sub = parts_sub[0].lower()
            if first_sub in ("队列", "q", "queue"):
                sub_content = item[len(parts_sub[0]):].strip()
                term = self.execute_queue(router, user_id, run, sub_content, results)
                if term:
                    return True
            else:
                cmd_handler = router.command_router._command_handlers.get(first_sub)
                if cmd_handler:
                    curr_state = run.node_type if run else "menu"
                    if curr_state in getattr(cmd_handler, "allowed_states", []):
                        res_list = list(cmd_handler.execute(router, user_id, parts_sub))
                        res = "\n".join(res_list)
                    else:
                        res = f"❌ 指令【{first_sub}】在当前状态下不可用。"
                    term = False
                else:
                    res, term = router.action_router.execute_action(router, user_id, run, parts_sub)
                results.append(res)
                if term:
                    return True
        return False
