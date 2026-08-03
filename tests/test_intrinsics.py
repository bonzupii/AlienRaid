#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for eating intrinsics (Phase 4)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from components.entity import Entity
from components.fighter import Fighter
from functions.item_functions import eat_emu_egg, eat_taipan_meat, eat_vegemite


class TestIntrinsics(unittest.TestCase):
    def test_emu_egg_gives_speed(self):
        player = Entity(0, 0, 'player', (0, 0, 0), 'Player',
                        fighter=Fighter(100, 10, 10))
        results = eat_emu_egg(player, 550)
        self.assertTrue(any(r.get('consumed') for r in results))
        self.assertTrue(player.fighter.has_status('speed'))
        self.assertEqual(player.fighter.status['speed'], 10)

    def test_taipan_meat_gives_poison_resistance(self):
        player = Entity(0, 0, 'player', (0, 0, 0), 'Player',
                        fighter=Fighter(100, 10, 10))
        results = eat_taipan_meat(player, 300)
        self.assertTrue(any(r.get('consumed') for r in results))
        self.assertTrue(player.fighter.has_status('poison_resist'))

    def test_status_tick_expires(self):
        player = Entity(0, 0, 'player', (0, 0, 0), 'Player',
                        fighter=Fighter(100, 10, 10))
        player.fighter.add_status('speed', 2)
        expired1 = player.fighter.tick_statuses()
        self.assertEqual(expired1, [])
        self.assertTrue(player.fighter.has_status('speed'))
        expired2 = player.fighter.tick_statuses()
        self.assertEqual(expired2, ['speed'])
        self.assertFalse(player.fighter.has_status('speed'))

    def test_vegemite_gives_permanent_defense(self):
        player = Entity(0, 0, 'player', (0, 0, 0), 'Player',
                        fighter=Fighter(100, 10, 10))
        initial_defense = player.fighter.defense

        results = eat_vegemite(player, 150)
        self.assertTrue(any(r.get('consumed') for r in results))
        self.assertEqual(player.fighter.base_defense_bonus, 1)
        self.assertEqual(player.fighter.defense, initial_defense + 1)

        # Eating again must not stack.
        eat_vegemite(player, 150)
        self.assertEqual(player.fighter.base_defense_bonus, 1)

    def test_webbed_status_blocks_via_has_status(self):
        player = Entity(0, 0, 'player', (0, 0, 0), 'Player',
                        fighter=Fighter(100, 10, 10))
        player.fighter.add_status('webbed', 1)
        self.assertTrue(player.fighter.has_status('webbed'))


if __name__ == '__main__':
    unittest.main()
