from ..models import GameRun, UserStats
from .menu import render_menu, render_card_library, render_deck, render_stats, render_help
from .battle import render_battle, render_detailed_battle
from .map import render_map_select, render_start_ancient, render_ancient
from .explore import render_event, render_shop, render_rest, render_reward, render_treasure, render_card_select
from .query import render_query_info

class GameRenderer:
    @staticmethod
    def render_menu() -> str:
        return render_menu()

    @staticmethod
    def render_help() -> str:
        return render_help()

    @staticmethod
    def render_card_library() -> str:
        return render_card_library()

    @staticmethod
    def render_deck(run: GameRun) -> str:
        return render_deck(run)

    @staticmethod
    def render_game(run: GameRun) -> str:
        if not run:
            return render_menu()
        nt = run.node_type
        if nt == "battle":
            return render_battle(run)
        elif nt == "event":
            return render_event(run)
        elif nt == "shop":
            return render_shop(run)
        elif nt == "rest":
            return render_rest(run)
        elif nt == "reward":
            return render_reward(run)
        elif nt == "map_select":
            return render_map_select(run)
        elif nt == "start_ancient":
            return render_start_ancient(run)
        elif nt == "ancient":
            return render_ancient(run)
        elif nt == "treasure":
            return render_treasure(run)
        elif nt == "card_select":
            return render_card_select(run)
        return "未知关卡状态"

    @staticmethod
    def render_query_info(query_str: str) -> str:
        return render_query_info(query_str)

    @staticmethod
    def render_detailed_battle(run: GameRun) -> str:
        return render_detailed_battle(run)

    @staticmethod
    def render_stats(stats: UserStats) -> str:
        return render_stats(stats)
