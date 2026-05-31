from .base import EventOption

class LeaveEventOption(EventOption, action="leave_event", text="离开事件"):
    def __init__(self, text: str = None, action: str = None, event_id: str = "fountain"):
        super().__init__(text, action)
        self.event_id = event_id

    def _run_effect(self, run, engine) -> str:
        engine.enter_next_stage(run)
        engine.save_manager.save_save(run.user_id, run)
        return "你决定不节外生枝，继续赶路。已前往下一关。"
