#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the bytearray GameMap (no pygame needed)."""
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
    'max_rooms': 80, 'room_min_size': 3, 'room_max_size': 12,
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
        self.game_map.make_map(CONSTANTS['max_rooms'], CONSTANTS['room_min_size'],
                               CONSTANTS['room_max_size'], CONSTANTS['map_width'],
                               CONSTANTS['map_height'], self.player, self.entities)

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

    def test_part_floors_have_parts(self):
        for floor in (5, 10, 15, 20):
            player = make_player()
            entities = [player]
            gm = GameMap(100, 48, dungeon_level=floor)
            gm.make_map(60, 3, 10, 100, 48, player, entities)
            parts = [e for e in entities if e.part_id]
            self.assertEqual(len(parts), 1, 'floor {0}'.format(floor))
            expected_id = next(pid for pid, (_, f) in SHIP_PARTS.items() if f == floor)
            self.assertEqual(parts[0].part_id, expected_id)

    def test_last_floor_has_no_down_trail(self):
        player = make_player()
        entities = [player]
        gm = GameMap(100, 48, dungeon_level=LAST_FLOOR)
        gm.make_map(60, 3, 10, 100, 48, player, entities)
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
