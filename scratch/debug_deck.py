import sys
from game.models.state import GameRun, PlayerState
from game.renderer import GameRenderer

player = PlayerState(
    hp=80,
    max_hp=80,
    shield=0,
    gold=20,
    stage=1,
    deck=["warrior_strike", "warrior_strike", "arcane_spark"],
    draw_pile=[],
    discard_pile=[],
    hand=[],
    actions=1,
    bonus_actions=1,
    minions={},
    amulets={},
    abilities=[],
    subclass="",
    selected_class="战士"
)
run = GameRun(
    user_id="test_user",
    node_type="map_select",
    player=player,
    enemies=[],
    node_data={}
)

output = GameRenderer.render_deck(run)
print("=== DECK OUTPUT ===")
print(output)
print("===================")
