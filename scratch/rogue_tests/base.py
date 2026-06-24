import os
import sys
import io
import unittest
import asyncio


if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from game.models.manager import SaveManager
from game.models.state import GameRun, PlayerState, EnemyState, MinionState, BuffState
from game.core.battle_engine import BattleEngine
from game.core.map_engine import MapEngine
from game.entities.cards.base import ALL_CARDS
from game.renderer.query import render_query_info
from game.core.cli_router import CLIRouter
from game.models.state import UserStats
from game.engine import GameEngine
from main import MyPlugin

class DummyContext:
    pass

class DummyEvent:
    def __init__(self, message_str: str, sender_id: str = "test_user"):
        self.message_str = message_str
        self.sender_id = sender_id
        self.results = []
        self.stopped = False

    def get_sender_id(self) -> str:
        return self.sender_id

    def plain_result(self, text: str):
        self.results.append(text)
        return text

    def stop_event(self):
        self.stopped = True

async def run_command(plugin, cmd_str: str, sender_id: str = "test_user") -> str:
    event = DummyEvent(cmd_str, sender_id)
    await plugin.shortcut_rogue(event)
    if not event.results:
        generator = plugin.rogue(event)
        async for _ in generator:
            pass
    return "\n".join(event.results)
