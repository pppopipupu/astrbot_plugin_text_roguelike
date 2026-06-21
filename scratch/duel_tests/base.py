import unittest
import os
import shutil
import tempfile
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from game.models.manager import SaveManager
from game.core.duel_router import DuelRouter
from game.models.state import GameRun, PlayerState, MinionState, AmuletState, BuffState
from game.renderer.duel_renderer import render_duel_battle_public, render_duel_battle_private

class DummyEvent:
    def __init__(self, message_str: str, sender_id: str):
        self.message_str = message_str
        self.sender_id = sender_id
        self.stopped = False
        self.bot = DummyBot()
        self.result_text = ""

    def get_sender_id(self) -> str:
        return self.sender_id

    def stop_event(self):
        self.stopped = True

    def plain_result(self, text: str):
        self.result_text = text
        return text

class DummyBot:
    def __init__(self):
        self.sent_messages = []

    async def call_api(self, api_name: str, **kwargs):
        self.sent_messages.append((api_name, kwargs))

class TestDuelSystem(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.save_manager = SaveManager(self.temp_dir)
        self.router = DuelRouter(self.save_manager)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
