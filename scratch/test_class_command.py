import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game.core.cli_router import CLIRouter
from game.models.manager import SaveManager
from game.models.state import UserStats

class DummySaveManager:
    def __init__(self):
        self.stats = UserStats()
        self.stats.unlocked_subclasses = ["时序法师", "塑能法师"]
    def load_stats(self, user_id):
        return self.stats
    def save_stats(self, user_id, stats):
        self.stats = stats
        return True
    def load_save(self, user_id):
        return None

def run_tests():
    mgr = DummySaveManager()
    router = CLIRouter(mgr, None)

    res = list(router.handle_command("test_user", ["class"]))
    assert "魔法肉鸽卡牌子职业系统" in res[0]

    list(router.handle_command("test_user", ["class", "c", "1"]))
    assert mgr.stats.selected_subclass == "时序法师"

    list(router.handle_command("test_user", ["class", "c", "2"]))
    assert mgr.stats.selected_subclass == "塑能法师"

    list(router.handle_command("test_user", ["class", "2"]))
    assert mgr.stats.selected_subclass == "塑能法师"

    list(router.handle_command("test_user", ["class", "0"]))
    assert mgr.stats.selected_subclass == ""

    list(router.handle_command("test_user", ["class", "c", "0"]))
    assert mgr.stats.selected_subclass == ""

    res = list(router.handle_command("test_user", ["class", "c", "3"]))
    assert "无效的子职业" in res[0]

    list(router.handle_command("test_user", ["class", "c", "时序法师"]))
    assert mgr.stats.selected_subclass == "时序法师"

    list(router.handle_command("test_user", ["class", "无"]))
    assert mgr.stats.selected_subclass == ""

    print("Class Command Alias and Index Tests passed successfully!")

if __name__ == "__main__":
    run_tests()
