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
from loader_functions.items import create_item
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
        npc = Entity(5, 5, 'agent_j_cameo', (20, 20, 20), 'Agent J', npc_id='mib')
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
        # Flashing nothing flashes YOURSELF: the rest timer reset marker is
        # emitted (and the canine-brain joke line now accompanies it).
        self.assertTrue(any(r.get('wait_timer_reset') for r in results))
        self.assertTrue(any('canine brains' in r.get('message', '').text
                            for r in results if 'message' in r))

    def test_neuralyzer_blocked_by_the_cameo(self):
        """Flashing Agent J (the cameo) is a unique non-consumed failure:
        he shields his eyes."""
        player = make_player()
        gm = empty_map()
        fov = bytearray(20 * 20)
        cameo = Entity(5, 5, 'agent_j_cameo', (20, 20, 20), 'Agent J', npc_id='mib')
        fov[5 * 20 + 5] = 1
        dingo = Entity(3, 3, 'dingo', (0, 0, 0), 'Dingo', fighter=Fighter(100, 10, 10),
                       ai=DingoAI())
        dingo.ai.owner = dingo
        fov[3 * 20 + 3] = 1
        results = use_neuralyzer(player, entities=[player, cameo, dingo],
                                 fov_map=fov, game_map=gm)
        self.assertFalse(any(r.get('consumed') for r in results))
        self.assertTrue(any('seen this bit before' in r.get('message', '').text
                            for r in results if 'message' in r))

    def test_aecd_bribe_hands_over_the_neuralyzer(self):
        """The AECD officer holds the confiscated neuralyzer; bribing them
        with a vegemite ration grants it (with the standard inventory
        feedback message)."""
        player = make_player()
        vegemite = create_item('vegemite_ration', 1, 0, 0)
        player.inventory.add_item(vegemite)
        npc = Entity(5, 5, 'npc_aecd', (140, 120, 80), 'AECD Officer', npc_id='aecd')
        _header, options = get_dialogue(npc, player)
        key = next(k for _t, k in options if k == 'aecd_bribe')
        log = MessageLog(32, 66, 6)
        process_dialogue_choice(npc, key, player, 11, log)
        self.assertTrue(any(getattr(i, 'item_choice', None) == 'neuralyzer'
                            for i in player.inventory.items),
                        'bribe did not grant the neuralyzer')
        self.assertFalse(any(getattr(i, 'item_choice', None) == 'vegemite_ration'
                             for i in player.inventory.items),
                         'vegemite ration not consumed by the bribe')

    def test_mib_npc_uses_the_agent_j_cameo_sprite(self):
        """The in-game Agent J is the parody cameo sprite, and the recipe
        exists in the sprite registry (no magenta fallback)."""
        from renderer.sprites import SpriteLoader, RECIPES
        self.assertIn('agent_j_cameo', RECIPES)
        surf = SpriteLoader().get('agent_j_cameo', (20, 20, 20))
        # Black suit on a dark body: the adaptive palette rim-lights it, so
        # it must have visible ink (not the magenta unknown fallback).
        magenta = (255, 0, 255)
        any_ink = any(surf.get_at((x, y))[:3] != magenta
                      for y in range(surf.get_height())
                      for x in range(surf.get_width()))
        self.assertTrue(any_ink, 'cameo sprite fell back to magenta unknown')

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
