#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for landmarks and biome gradients (Phase 5)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from components.entity import Entity
from components.fighter import Fighter
from loader_functions.initialize_new_game import biome_for_level
from map_objects.game_map import GameMap, MIB_FLOOR, AECD_FLOOR, ROADHOUSE_FLOORS


def _find_fence(gm):
    """Return True if some row is a long blocked line containing a passable
    gap (the dingo-fence signature: >= 50 blocked tiles in x 5..94 with a
    run of >= 3 open tiles inside it)."""
    for y in range(gm.height):
        run = [gm.blocked[gm.idx(x, y)] for x in range(5, gm.width - 5)]
        if run.count(1) > 50:
            zeros = 0
            for v in run:
                if v == 0:
                    zeros += 1
                    if zeros >= 3:
                        return True
                else:
                    zeros = 0
    return False


class TestBiomes(unittest.TestCase):
    def test_biome_colors(self):
        # Red dirt scrub (1-5)
        colors1 = biome_for_level(3)
        self.assertEqual(colors1['dark_ground'], (170, 90, 10))
        self.assertIn('dark_brush', colors1)
        self.assertIn('light_brush', colors1)

        # Creek country (6-10)
        colors6 = biome_for_level(8)
        self.assertEqual(colors6['dark_ground'], (140, 110, 70))

        # Limestone caves (11-15)
        colors12 = biome_for_level(13)
        self.assertEqual(colors12['dark_ground'], (60, 60, 60))

        # The hollow (16-20)
        colors18 = biome_for_level(18)
        self.assertEqual(colors18['dark_ground'], (40, 30, 60))

    def test_brush_bytearray(self):
        player = Entity(0, 0, 'player', (15, 77, 0), 'P',
                        blocks=True, fighter=Fighter(100, 10, 10))
        gm = GameMap(100, 48)
        self.assertIsInstance(gm.brush, bytearray)
        self.assertEqual(len(gm.brush), 100 * 48)
        gm.make_map(100, 48, player, [player])
        # Brush only ever lands on walkable tiles, and always blocks sight.
        for y in range(gm.height):
            for x in range(gm.width):
                idx = gm.idx(x, y)
                if gm.brush[idx]:
                    self.assertEqual(gm.blocked[idx], 0,
                                     'brush on a blocked tile at ({0},{1})'.format(x, y))
                    self.assertEqual(gm.block_sight[idx], 1,
                                     'brush should block sight at ({0},{1})'.format(x, y))

    def test_fence_floor_has_fence_with_gap(self):
        """Fence floors (3, 7, 11, 15, 19) contain a long blocked line with
        a passable gap — a signature chokepoint feature."""
        for floor in (3, 7, 11, 15, 19):
            player = Entity(0, 0, 'player', (15, 77, 0), 'P',
                            blocks=True, fighter=Fighter(100, 10, 10))
            gm = GameMap(100, 48, dungeon_level=floor)
            gm.make_map(100, 48, player, [player])
            self.assertTrue(_find_fence(gm),
                            'floor {0} should have a fenced line with a gap'.format(floor))

    def test_npc_camps_spawn(self):
        """Phase F: MIB camp on floor 12, AECD checkpoint on floor 11,
        roadhouse on floors 7 and 14. Each NPC spawns on a walkable tile.
        (npc_id is 'mib'/'aecd'/'swaggie'; the MIB agent renders as the
        'agent_j_cameo' sprite.)"""
        expected = [(MIB_FLOOR, 'mib'), (AECD_FLOOR, 'aecd'),
                    (ROADHOUSE_FLOORS[0], 'swaggie'),
                    (ROADHOUSE_FLOORS[1], 'swaggie')]
        for floor, npc_id in expected:
            player = Entity(0, 0, 'player', (15, 77, 0), 'P',
                            blocks=True, fighter=Fighter(100, 10, 10))
            entities = [player]
            gm = GameMap(100, 48, dungeon_level=floor)
            gm.make_map(100, 48, player, entities)
            npcs = [e for e in entities if e.npc_id == npc_id]
            self.assertEqual(len(npcs), 1,
                             'floor {0} should host {1}'.format(floor, npc_id))
            self.assertFalse(gm.is_blocked(npcs[0].x, npcs[0].y))

    def test_aecd_holds_the_neuralyzer(self):
        """The AECD officer holds the confiscated neuralyzer -- it must not
        be lying free in the camp for the taking (it is granted via the
        bribe dialogue choice instead)."""
        player = Entity(0, 0, 'player', (15, 77, 0), 'P',
                        blocks=True, fighter=Fighter(100, 10, 10))
        entities = [player]
        gm = GameMap(100, 48, dungeon_level=AECD_FLOOR)
        gm.make_map(100, 48, player, entities)
        free = [e for e in entities
                if getattr(e, 'item_choice', None) == 'neuralyzer']
        self.assertEqual(len(free), 0,
                         'the neuralyzer must be held, not left on the ground')

if __name__ == '__main__':
    unittest.main()
