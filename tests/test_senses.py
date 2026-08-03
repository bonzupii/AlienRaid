#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the noise/hearing system (Phase 2)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from components.ai import DropbearAI, DingoAI
from components.entity import Entity
from components.fighter import Fighter
from functions.senses import NoiseMap
from map_objects.game_map import GameMap


class TestNoiseMap(unittest.TestCase):
    def setUp(self):
        self.w, self.h = 20, 20
        self.game_map = GameMap(self.w, self.h)
        self.game_map.blocked = bytearray(self.w * self.h)
        self.game_map.block_sight = bytearray(self.w * self.h)
        self.player = Entity(5, 5, 'player', (15, 77, 0), 'Player',
                             fighter=Fighter(100, 10, 10))

    def test_emit_and_query_radius(self):
        nm = NoiseMap(self.w, self.h)
        nm.emit(10, 10, 3, 'test')
        # Inside the radius: intensity decays with Manhattan distance.
        self.assertGreater(nm.get_noise_at(10, 10), 0)
        self.assertGreater(nm.get_noise_at(11, 10), 0)
        self.assertGreater(nm.get_noise_at(10, 13), 0)   # dist 3 == radius
        self.assertEqual(nm.get_noise_at(10, 14), 0)     # dist 4 > radius
        self.assertEqual(nm.get_noise_at(0, 0), 0)
        # Out-of-bounds query is safe.
        self.assertEqual(nm.get_noise_at(-1, 5), 0)

    def test_find_strongest_noise(self):
        nm = NoiseMap(self.w, self.h)
        nm.emit(5, 5, 2, 'a')
        nm.emit(12, 12, 4, 'b')
        best = nm.find_strongest_noise()
        self.assertIsNotNone(best)
        # The louder (larger radius) source wins.
        self.assertEqual((best[0], best[1]), (12, 12))

    def test_clear(self):
        nm = NoiseMap(self.w, self.h)
        nm.emit(10, 10, 3, 'test')
        nm.clear()
        self.assertEqual(nm.get_noise_at(10, 10), 0)
        self.assertEqual(nm.find_strongest_noise(), None)

    def test_monster_hears_noise_outside_fov(self):
        """A dropbear outside FOV hears an explosion and paths to it."""
        ai = DropbearAI()
        monster = Entity(10, 10, 'dropbear', (0, 0, 0), 'Dropbear',
                         blocks=True, fighter=Fighter(100, 10, 10), ai=ai)
        ai.owner = monster

        # Only the player's tile is lit; the monster is in the dark.
        fov_map = bytearray(self.w * self.h)
        fov_map[5 * self.w + 5] = 1

        nm = NoiseMap(self.w, self.h)
        nm.emit(12, 10, 3, 'explosion')  # within hearing of the monster

        entities = [self.player, monster]
        ai.take_turn(self.player, fov_map, self.game_map, entities, nm)

        self.assertEqual(monster.x, 11, 'dropbear did not path toward the noise')

    def test_dingo_smells_player_out_of_fov(self):
        """Dingoes (SMELL=8) track the player even without line of sight."""
        ai = DingoAI()
        monster = Entity(12, 12, 'dingo', (0, 0, 0), 'Dingo',
                         blocks=True, fighter=Fighter(100, 10, 10), ai=ai)
        ai.owner = monster
        self.player.x, self.player.y = 10, 10

        # Monster at (12,12), player at (10,10): dist ~2.8 <= 8 -> smell.
        fov_map = bytearray(self.w * self.h)
        fov_map[10 * self.w + 10] = 1  # only the player is lit

        entities = [self.player, monster]
        ai.take_turn(self.player, fov_map, self.game_map, entities)

        # Smelling counts as "seen": it sets last_seen and acts.
        self.assertEqual(ai.last_seen, (10, 10))
        # It should have closed in on the player.
        self.assertLess(monster.distance_to(self.player), 3)


if __name__ == '__main__':
    unittest.main()
