import random
from typing import Optional, List, Dict
from .models.state import GameRun, PlayerState, EnemyState, MinionState, AmuletState, Card
from .entities import ALL_CARDS
from .models.manager import SaveManager
from .core.battle_engine import BattleEngine
from .core.map_engine import MapEngine

class GameEngine:
    def __init__(self, save_manager: SaveManager):
        self.save_manager = save_manager
        self.battle_engine = BattleEngine(save_manager)
        self.map_engine = MapEngine(save_manager, self.battle_engine)

    def start_new_game(self, user_id: str) -> GameRun:
        stats = self.save_manager.load_stats(user_id)
        selected_subclass = getattr(stats, "selected_subclass", "")
        commons = [cid for cid, c in ALL_CARDS.items() if getattr(c, "rarity", "common") == "common" and not cid.startswith("curse_") and cid != "time_stop"]
        rares = [cid for cid, c in ALL_CARDS.items() if getattr(c, "rarity", "common") == "rare" and not cid.startswith("curse_") and cid != "time_stop"]
        epics = [cid for cid, c in ALL_CARDS.items() if getattr(c, "rarity", "common") == "epic" and not cid.startswith("curse_") and cid != "time_stop"]
        initial_deck = []
        for _ in range(5):
            initial_deck.append(random.choice(commons))
        for _ in range(2):
            initial_deck.append(random.choice(rares))
        for _ in range(1):
            initial_deck.append(random.choice(epics))
        if selected_subclass == "时序法师":
            initial_deck.append("time_stop")
        player = PlayerState(
            hp=45,
            max_hp=45,
            shield=0,
            gold=20,
            stage=0,
            deck=initial_deck,
            draw_pile=[],
            discard_pile=[],
            hand=[],
            actions=1,
            bonus_actions=1,
            minions={},
            amulets={},
            abilities=[],
            subclass=selected_subclass
        )
        run = GameRun(
            user_id=user_id,
            node_type="start",
            player=player,
            enemies=[],
            node_data={}
        )
        self.enter_next_stage(run)
        self.save_manager.save_save(user_id, run)
        return run

    def enter_next_stage(self, run: GameRun):
        self.map_engine.enter_next_stage(run)

    def is_battle_won(self, run: GameRun) -> bool:
        return self.battle_engine.is_battle_won(run)

    def play_card(self, run: GameRun, hand_idx: int, target: Optional[str] = None) -> str:
        return self.battle_engine.play_card(run, hand_idx, target)

    def play_special_action(self, run: GameRun, hand_idx: int, target: Optional[str] = None) -> str:
        return self.battle_engine.play_special_action(run, hand_idx, target)

    def minion_attack(self, run: GameRun, my_grid: str, opp_grid: Optional[str] = None) -> str:
        return self.battle_engine.minion_attack(run, my_grid, opp_grid)

    def minion_skill(self, run: GameRun, my_grid: str, skill_idx: int = 1, target: Optional[str] = None) -> str:
        return self.battle_engine.minion_skill(run, my_grid, skill_idx, target)

    def end_turn(self, run: GameRun) -> str:
        return self.battle_engine.end_turn(run)

    def choose_option(self, run: GameRun, option_idx: int) -> str:
        return self.map_engine.choose_option(run, option_idx)

    def choose_map_node(self, run: GameRun, option_idx: int) -> str:
        return self.map_engine.choose_map_node(run, option_idx)

    def remove_card_from_deck(self, run: GameRun, deck_idx: int) -> str:
        return self.map_engine.remove_card_from_deck(run, deck_idx)

    def _handle_battle_win(self, run: GameRun):
        self.battle_engine._handle_battle_win(run)

    def _discard_card(self, run: GameRun, cid: str) -> str:
        return self.battle_engine._discard_card(run, cid)
