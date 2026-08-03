#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the v4 organic map generator (Phase 1).

The rooms-and-corridors dungeon is gone; the new generator produces
cellular-automata cave terrain. These tests assert the NEW design's actual
promises: one connected walkable region reaching every gameplay entity,
nothing spawning inside terrain, solid borders, and a substantial open
area -- not the old dungeon's structure (rooms, corridors, brick).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from components.entity import Entity
from components.fighter import Fighter
from map_objects.game_map import (GameMap, MIB_FLOOR, AECD_FLOOR,
                                  ROADHOUSE_FLOORS)


def make_player():
    return Entity(0, 0, 'player', (15, 77, 0), 'P', blocks=True,
                  fighter=Fighter(1250, 10, 40))


class TestOrganicMap(unittest.TestCase):
    def _make(self, level):
        player = make_player()
        entities = [player]
        gm = GameMap(100, 48, dungeon_level=level)
        gm.make_map(100, 48, player, entities)
        return gm, player, entities

    @staticmethod
    def _flood(gm, sx, sy):
        """Independent 8-directional flood fill (not GameMap._flood) so the
        connectivity check cannot agree with the code under test. 8-dir
        because the game's movement allows diagonals (move_towards, astar),
        so diagonal pinches are walkable in play."""
        w, h = gm.width, gm.height
        seen = bytearray(w * h)
        if gm.blocked[sy * w + sx]:
            return seen
        seen[sy * w + sx] = 1
        stack = [(sx, sy)]
        while stack:
            x, y = stack.pop()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] \
                            and not gm.blocked[ny * w + nx]:
                        seen[ny * w + nx] = 1
                        stack.append((nx, ny))
        return seen

    def test_every_entity_on_walkable_tile(self):
        """No entity may spawn inside terrain or landmark walls -- the
        generator promises entities only ever sit on open ground."""
        for level in (1, 5, 6, 11, 20):
            gm, player, entities = self._make(level)
            for e in entities:
                self.assertTrue(gm.in_bounds(e.x, e.y), e.name + ' out of bounds')
                self.assertFalse(gm.is_blocked(e.x, e.y),
                                 '{0} inside terrain at ({1},{2})'.format(
                                     e.name, e.x, e.y))

    def test_one_connected_region_reaches_all_critical_entities(self):
        """The walkable region is a single connected component reaching
        every trail/ship/part/NPC -- the core promise of the new design."""
        for level in (1, 6, 11, 20):
            gm, player, entities = self._make(level)
            seen = self._flood(gm, player.x, player.y)
            critical = [e for e in entities
                        if e.trail or e.ship or e.part_id or e.npc_id]
            self.assertTrue(critical, 'no critical entities on floor {0}'.format(level))
            for e in critical:
                self.assertTrue(seen[gm.idx(e.x, e.y)],
                                'disconnected on floor {0}: {1}'.format(level, e.name))

    def test_borders_are_solid_wall(self):
        gm, player, entities = self._make(1)
        for x in range(gm.width):
            self.assertTrue(gm.is_wall(x, 0))
            self.assertTrue(gm.is_wall(x, gm.height - 1))
        for y in range(gm.height):
            self.assertTrue(gm.is_wall(0, y))
            self.assertTrue(gm.is_wall(gm.width - 1, y))

    def test_open_terrain_is_substantial_and_not_full(self):
        """CA caves at 44% random fill smoothed 5x leave a substantial
        contiguous open region -- neither a nearly-empty map nor a nearly-
        full one (a broken generator that produced a single open rectangle
        would still satisfy this only if it also passed connectivity, which
        it can't by itself prove irregularity -- the ratio is a sanity
        bound on the smoothing, not a claim of organic-ness)."""
        for level in (1, 10, 20):
            gm, player, entities = self._make(level)
            open_count = sum(1 for v in gm.blocked if v == 0)
            ratio = open_count / (gm.width * gm.height)
            self.assertGreater(ratio, 0.25, 'map too walled up on floor {0}'.format(level))
            self.assertLess(ratio, 0.85, 'map too open on floor {0}'.format(level))

    def test_npc_camps(self):
        # npc_id values are 'mib'/'aecd'/'swaggie' (dialogue looks them up
        # by npc_id; the MIB agent renders as the 'agent_j_cameo' sprite).
        for level, npc_id in ((MIB_FLOOR, 'mib'),
                              (AECD_FLOOR, 'aecd'),
                              (ROADHOUSE_FLOORS[0], 'swaggie'),
                              (ROADHOUSE_FLOORS[1], 'swaggie')):
            gm, player, entities = self._make(level)
            npcs = [e for e in entities if e.npc_id == npc_id]
            self.assertEqual(len(npcs), 1,
                             'floor {0} should host {1}'.format(level, npc_id))


if __name__ == '__main__':
    unittest.main()
