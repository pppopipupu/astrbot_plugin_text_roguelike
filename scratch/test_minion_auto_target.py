import os
import sys
import io
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from game.models.manager import SaveManager
from game.models.state import GameRun, PlayerState, EnemyState, MinionState
from game.core.battle_engine import BattleEngine

async def run_test():
    sm = SaveManager()
    engine = BattleEngine(sm)
    run = GameRun(
        user_id="test_user",
        node_type="battle",
        node_data={"cards_played_this_turn": 0},
        player=PlayerState(
            hp=30,
            max_hp=30,
            shield=0,
            actions=2,
            bonus_actions=1,
            deck=[],
            hand=[],
            draw_pile=[],
            discard_pile=[],
            exhaust_pile=[],
            graveyard=[],
            amulets={},
            minions={
                "1": MinionState(
                    id="mercenary",
                    name="雇佣兵",
                    hp=10,
                    max_hp=10,
                    atk=4,
                    actions=1,
                    bonus_actions=0,
                    attack_actions=1,
                    buffs=[]
                )
            },
            buffs=[],
            gold=100,
            stage=1
        ),
        enemies=[
            EnemyState(
                name="地精突袭者",
                hp=12,
                max_hp=12,
                shield=0,
                actions=1,
                bonus_actions=0,
                max_actions=1,
                max_bonus_actions=0,
                intent_a_type="attack",
                intent_a_val=0,
                intent_a_desc=""
            )
        ]
    )

    print("Initial enemy HP:", run.enemies[0].hp)
    res = engine.minion_attack(run, "1")
    print(res)
    print("Enemy HP after attack without target:", run.enemies[0].hp)

    assert run.enemies[0].hp == 8
    print("Test passed successfully!")

if __name__ == "__main__":
    asyncio.run(run_test())
