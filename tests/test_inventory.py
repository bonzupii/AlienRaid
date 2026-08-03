#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Phase E drop UX (components/inventory.py).

Dropping on a tile blocked by another creature should place the item on the
nearest adjacent free tile instead of under the blocker, and dropping an
equipped item must unequip it first.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from components.entity import Entity
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from loader_functions.items import create_item
from map_objects.game_map import GameMap


def make_player():
    # The game's player invariant: always has inventory AND equipment (the
    # drop path checks equipment slots to unequip on drop).
    return Entity(5, 5, 'player', (0, 0, 0), 'P', blocks=True,
                  fighter=Fighter(100, 10, 10), inventory=Inventory(26),
                  equipment=Equipment())


def open_map(w=20, h=20):
    gm = GameMap(w, h)
    gm.blocked = bytearray(w * h)
    gm.block_sight = bytearray(w * h)
    return gm


class TestDropUX(unittest.TestCase):
    def test_drop_on_open_tile_stays_put(self):
        player = make_player()
        item = create_item('lesser_med_kit', 1, 5, 5)
        player.inventory.add_item(item)
        gm = open_map()
        results = player.inventory.drop_item(item, gm, [player])
        self.assertEqual((item.x, item.y), (5, 5))
        self.assertNotIn(item, player.inventory.items)
        self.assertTrue(any(r.get('item_dropped') for r in results))

    def test_drop_lands_on_adjacent_tile_when_blocked(self):
        """The player's tile is occupied by a blocker; the only free neighbor
        is (6,5) -- the item must land there, not on the blocker."""
        player = make_player()
        blocker = Entity(5, 5, 'kanga', (0, 0, 0), 'Kanga', blocks=True)
        item = create_item('lesser_med_kit', 1, 5, 5)
        player.inventory.add_item(item)
        gm = open_map()
        # Wall off every neighbor of (5,5) except (6,5).
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = 5 + dx, 5 + dy
                if (nx, ny) != (6, 5) and 0 <= nx < 20 and 0 <= ny < 20:
                    gm.blocked[ny * 20 + nx] = 1
                    gm.block_sight[ny * 20 + nx] = 1
        results = player.inventory.drop_item(item, gm, [player, blocker])
        self.assertEqual((item.x, item.y), (6, 5))
        self.assertNotIn(item, player.inventory.items)
        self.assertTrue(any(r.get('item_dropped') for r in results))

    def test_dropping_equipped_item_unequips(self):
        player = make_player()
        item = create_item('whippy_willow_twig', 1, 5, 5)
        player.inventory.add_item(item)
        player.equipment.toggle_equip(item)
        gm = open_map()
        player.inventory.drop_item(item, gm, [player])
        eq = player.equipment
        slots = (eq.top_right_tentacle, eq.top_left_tentacle,
                 eq.bottom_right_tentacle, eq.bottom_left_tentacle,
                 eq.chest_plate, eq.helmet, eq.neck)
        self.assertTrue(all(slot is not item for slot in slots),
                        'dropped item is still equipped')
        self.assertNotIn(item, player.inventory.items)


if __name__ == '__main__':
    unittest.main()
