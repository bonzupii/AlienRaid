#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Phase F MIB storyline: dialogue choices, the neuralyzer,
and the victory epilogue derived from faction standings."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from components.ai import DingoAI, KangaAI, FLEE
from components.entity import Entity
from components.fighter import Fighter
from components.game_messages import MessageLog
from components.inventory import Inventory
from components.reputation import Reputation
from functions.dialogue import get_dialogue, process_dialogue_choice
from functions.item_functions import use_neuralyzer
from map_objects.game_map import GameMap


def make_player():
    return Entity(0, 0, 'player', (0, 0, 0), 'Player',
                  fighter=Fighter(100, 10, 10), inventory=Inventory(26),
                  reputation=Reputation())


def empty_map(w=20, h=20):
    gm = GameMap(w, h)
    gm.blocked = bytearray(w * h)
    gm.block_sight = bytearray(w * h)
    return gm


class TestMIB(unittest.TestCase):
    def test_dialogue_choice_moves_reputation(self):
        player = make_player()
        npc = Entity(5, 5, 'npc_mib', (20, 20, 20), 'Agent J', npc_id='mib')
        header, options = get_dialogue(npc, player)
        self.assertEqual(player.reputation.mib, 0)
        choice_key = next(key for _text, key in options if key == 'mib_lost')
        process_dialogue_choice(npc, choice_key, player, 6, MessageLog(32, 66, 6))
        self.assertEqual(player.reputation.mib, 10)
        self.assertEqual(player.reputation.mib_quest_state, 'given')

    def test_neuralyzer_clears_dingo_memory_and_scatters(self):
        player = make_player()
        gm = empty_map()
        fov = bytearray(20 * 20)
        dingo = Entity(3, 3, 'dingo', (0, 0, 0), 'Dingo', fighter=Fighter(100, 10, 10),
                       ai=DingoAI())
        dingo.ai.owner = dingo
        dingo.ai.last_seen = (0, 0)
        fov[3 * 20 + 3] = 1
        kanga = Entity(4, 4, 'kanga', (0, 0, 0), 'Kanga', fighter=Fighter(100, 10, 10),
                       ai=KangaAI())
        kanga.ai.owner = kanga
        fov[4 * 20 + 4] = 1

        results = use_neuralyzer(player, entities=[player, dingo, kanga],
                                 fov_map=fov, game_map=gm)
        self.assertTrue(any(r.get('consumed') for r in results))
        self.assertIsNone(dingo.ai.last_seen)
        self.assertEqual(dingo.ai.state, FLEE)
        # A kanga is untouched: its AI is intact and the item did not consume.
        self.assertIsNotNone(kanga.ai)

    def test_neuralyzer_fails_without_dingoes(self):
        player = make_player()
        gm = empty_map()
        fov = bytearray(20 * 20)
        kanga = Entity(4, 4, 'kanga', (0, 0, 0), 'Kanga', fighter=Fighter(100, 10, 10),
                       ai=KangaAI())
        kanga.ai.owner = kanga
        fov[4 * 20 + 4] = 1
        results = use_neuralyzer(player, entities=[player, kanga],
                                 fov_map=fov, game_map=gm)
        self.assertFalse(any(r.get('consumed') for r in results))
        self.assertIsNotNone(kanga.ai)

    def test_epilogue_selection(self):
        player = make_player()
        self.assertEqual(player.reputation.epilogue(), 'solo')
        player.reputation.update('mib', 15)
        self.assertEqual(player.reputation.epilogue(), 'mib')
        player.reputation.update('aecd', 15)
        self.assertEqual(player.reputation.epilogue(), 'betrayal')

        aecd_player = make_player()
        aecd_player.reputation.update('aecd', 15)
        self.assertEqual(aecd_player.reputation.epilogue(), 'aecd')


if __name__ == '__main__':
    unittest.main()
