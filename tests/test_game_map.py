#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the bytearray GameMap (no pygame needed).

v4: the generator is organic (cellular-automata caves + winding tunnels),
so the rooms-and-corridors parameters are gone. The invariants stay -- flat
bytearray fields, the player starts on a walkable tile, floor 1 has a
down-trail + ship and no up-trail, part floors hold a part, the deepest
floor has no down-trail, and go_down/go_up work -- and the connectivity
test asserts the new generator's real promise: ONE connected walkable
region reaching every critical entity (verified with an independent
flood fill, not the map's own).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from components.entity import Entity
from components.fighter import Fighter
from components.game_messages import MessageLog
from components.quest import SHIP_PARTS
from functions.render_order import RenderOrder
from map_objects.game_map import GameMap, LAST_FLOOR
from loader_functions.monsters import create_monster
from loader_functions.items import create_item

CONSTANTS = {
    'map_width': 100, 'map_height': 48,
}


def make_player():
    fighter = Fighter(hp=1250, defense=10, power=40)
    return Entity(0, 0, 'player', (15, 77, 0), 'Wrpgnyth', blocks=True,
                  render_order=RenderOrder.ACTOR, fighter=fighter)


class TestGameMap(unittest.TestCase):
    def setUp(self):
        self.player = make_player()
        self.entities = [self.player]
        self.game_map = GameMap(CONSTANTS['map_width'], CONSTANTS['map_height'])
        self.game_map.make_map(CONSTANTS['map_width'], CONSTANTS['map_height'],
                               self.player, self.entities)

    @staticmethod
    def _flood(gm, sx, sy):
        """Independent 8-directional flood fill over open tiles -- written
        in the test, NOT GameMap._flood, so the connectivity check cannot
        simply agree with the code under test. 8-directional because the
        game's movement is: Entity.move_towards and astar both allow
        diagonals, so a diagonal pinch is walkable in play."""
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

    def test_bytearray_fields(self):
        w, h = CONSTANTS['map_width'], CONSTANTS['map_height']
        self.assertIsInstance(self.game_map.blocked, bytearray)
        self.assertIsInstance(self.game_map.block_sight, bytearray)
        self.assertIsInstance(self.game_map.explored, bytearray)
        self.assertEqual(len(self.game_map.blocked), w * h)
        self.assertEqual(len(self.game_map.block_sight), w * h)
        self.assertEqual(len(self.game_map.explored), w * h)

    def test_player_on_open_tile(self):
        self.assertFalse(self.game_map.is_blocked(self.player.x, self.player.y))

    def test_floor1_has_down_trail_and_ship_no_up_trail(self):
        down = [e for e in self.entities if e.trail and e.trail.direction == 'down']
        up = [e for e in self.entities if e.trail and e.trail.direction == 'up']
        ships = [e for e in self.entities if e.ship]
        self.assertEqual(len(down), 1)
        self.assertEqual(len(up), 0)
        self.assertEqual(len(ships), 1)

    def test_connected_region_reaches_critical_entities(self):
        """The organic generator's core promise: the walkable region is ONE
        connected component, so the player can walk to the down-trail, the
        ship and (on part floors) the part without any impassable seam."""
        seen = self._flood(self.game_map, self.player.x, self.player.y)
        critical = [e for e in self.entities if e.trail or e.ship or e.part_id]
        self.assertTrue(critical, 'no critical entities were placed')
        for e in critical:
            self.assertTrue(seen[self.game_map.idx(e.x, e.y)],
                            'critical entity disconnected: ' + e.name)

    def test_part_floors_have_parts(self):
        for floor in (5, 10, 15, 20):
            player = make_player()
            entities = [player]
            gm = GameMap(100, 48, dungeon_level=floor)
            gm.make_map(100, 48, player, entities)
            parts = [e for e in entities if e.part_id]
            self.assertEqual(len(parts), 1, 'floor {0}'.format(floor))
            expected_id = next(pid for pid, (_, f) in SHIP_PARTS.items() if f == floor)
            self.assertEqual(parts[0].part_id, expected_id)
            # The part sits on a walkable tile in the connected region.
            self.assertFalse(gm.is_blocked(parts[0].x, parts[0].y))
            self.assertTrue(self._flood(gm, player.x, player.y)[gm.idx(parts[0].x, parts[0].y)])

    def test_last_floor_has_no_down_trail(self):
        player = make_player()
        entities = [player]
        gm = GameMap(100, 48, dungeon_level=LAST_FLOOR)
        gm.make_map(100, 48, player, entities)
        down = [e for e in entities if e.trail and e.trail.direction == 'down']
        self.assertEqual(len(down), 0)

    def test_go_down_and_up(self):
        log = MessageLog(32, 66, 6)
        self.entities = self.game_map.go_down(self.player, log, CONSTANTS)
        self.assertEqual(self.game_map.dungeon_level, 2)
        self.assertTrue(self.player.fighter.hp > 0)
        ups = [e for e in self.entities if e.trail and e.trail.direction == 'up']
        self.assertEqual(len(ups), 1)
        # back up
        self.entities = self.game_map.go_up(self.player, log, CONSTANTS)
        self.assertEqual(self.game_map.dungeon_level, 1)
        downs = [e for e in self.entities if e.trail and e.trail.direction == 'down']
        self.assertEqual(len(downs), 1)

    def test_monster_and_item_factories(self):
        kanga = create_monster('kanga', 5, 10, 10)
        self.assertEqual(kanga.sprite_id, 'kanga')
        self.assertGreater(kanga.fighter.hp, 0)
        self.assertGreater(kanga.fighter.power, 0)
        self.assertTrue(kanga.ai is not None)

        medkit = create_item('med_kit', 5, 20, 20)
        self.assertEqual(medkit.sprite_id, 'icon_cross')
        self.assertTrue(medkit.item is not None)
        self.assertIsNotNone(medkit.item.use_function)

        vest = create_item('wombat_hide_cuirass', 10, 30, 30)
        self.assertTrue(vest.equippable is not None)
        self.assertEqual(vest.equippable.defense_bonus, 40)


if __name__ == '__main__':
    unittest.main()
