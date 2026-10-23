#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for eating intrinsics (Phase 4)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from components.entity import Entity
from components.fighter import Fighter
from functions.item_functions import eat_emu_egg, eat_vegemite
from loader_functions.items import create_item


class TestIntrinsics(unittest.TestCase):
    def test_emu_egg_gives_speed(self):
        player = Entity(0, 0, 'player', (0, 0, 0), 'Player',
                        fighter=Fighter(100, 10, 10))
        results = eat_emu_egg(player, 550)
        self.assertTrue(any(r.get('consumed') for r in results))
        self.assertTrue(player.fighter.has_status('speed'))
        self.assertEqual(player.fighter.status['speed'], 10)

    def test_raw_taipan_meat_is_poison_but_food(self):
        """Raw taipan meat bites back: it feeds but damages, and grants NO
        poison resistance -- the good end comes from the crafted
        antivenin (see components/crafting.py)."""
        player = Entity(0, 0, 'player', (0, 0, 0), 'Player',
                        fighter=Fighter(100, 10, 10))
        player.fighter.hunger = 300
        meat = create_item('taipan_meat', 1, 0, 0)
        results = meat.item.use_function(player, **meat.item.function_kwargs)
        self.assertTrue(any(r.get('consumed') for r in results))
        self.assertEqual(player.fighter.hp, 60, 'raw taipan venom deals 40')
        self.assertEqual(player.fighter.hunger, 480, 'it still feeds')
        self.assertFalse(player.fighter.has_status('poison_resist'))

    def test_taipan_antivenin_grants_poison_resistance(self):
        player = Entity(0, 0, 'player', (0, 0, 0), 'Player',
                        fighter=Fighter(100, 10, 10))
        antivenin = create_item('taipan_antivenin', 1, 0, 0)
        results = antivenin.item.use_function(
            player, **antivenin.item.function_kwargs)
        self.assertTrue(any(r.get('consumed') for r in results))
        self.assertTrue(player.fighter.has_status('poison_resist'))
        self.assertEqual(player.fighter.status['poison_resist'], 30)

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
