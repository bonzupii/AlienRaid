#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for mob item drops (Phase C)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from functions.death_functions import kill_monster
from loader_functions.monsters import create_monster, DROP_TABLES
from loader_functions.items import create_item


class TestDrops(unittest.TestCase):
    def test_guaranteed_drop_species(self):
        """Emus always drop an emu egg (chance 100). The drop appears as a
        new item entity at the corpse's tile."""
        emu = create_monster('emu', 3, 10, 10)
        message, dropped = kill_monster(emu, 3)
        self.assertIsNotNone(dropped)
        self.assertEqual(dropped.item_choice, 'emu_egg')
        self.assertEqual((dropped.x, dropped.y), (10, 10))

    def test_cassowary_drops_crown(self):
        cassowary = create_monster('cassowary', 15, 5, 5)
        _, dropped = kill_monster(cassowary, 15)
        self.assertIsNotNone(dropped)
        self.assertEqual(dropped.item_choice, 'cassowary_crest_crown')

    def test_kill_still_turns_monster_into_corpse(self):
        """Drops must not replace the corpse conversion."""
        dingo = create_monster('dingo', 2, 3, 3)
        message, _dropped = kill_monster(dingo, 2)
        self.assertFalse(dingo.blocks)
        self.assertIsNone(dingo.fighter)
        self.assertEqual(dingo.sprite_id, 'corpse')

    def test_non_dropping_species_returns_none(self):
        # 'wallaby' has no entry in DROP_TABLES.
        wallaby = create_monster('wallaby', 3, 10, 10)
        _message, dropped = kill_monster(wallaby, 3)
        self.assertIsNone(dropped)

    def test_every_drop_table_references_a_real_item(self):
        """Every item_choice in a drop table must be creatable -- a typo'd
        choice would crash the game the moment that species dies."""
        self.assertTrue(DROP_TABLES)
        for species, table in DROP_TABLES.items():
            for choice in table:
                item = create_item(choice, 1, 0, 0)
                self.assertEqual(item.item_choice, choice,
                                 'bad drop for {0}: {1}'.format(species, choice))


if __name__ == '__main__':
    unittest.main()
