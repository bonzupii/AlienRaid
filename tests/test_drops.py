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
        self.assertTrue(dropped)
        self.assertEqual(dropped[0].item_choice, 'emu_egg')
        self.assertEqual((dropped[0].x, dropped[0].y), (10, 10))

    def test_cassowary_drops_crown(self):
        """The cassowary crest crown is the species-relevant tier (tier 2):
        it sits in the table and does drop, but the meat roll (tier 1)
        comes first in the dict order."""
        self.assertIn('cassowary_crest_crown', DROP_TABLES['cassowary'])
        for _ in range(60):
            cassowary = create_monster('cassowary', 15, 5, 5)
            _, dropped = kill_monster(cassowary, 15)
            if any(d.item_choice == 'cassowary_crest_crown' for d in dropped):
                return
        self.fail('cassowary never dropped its crown in 60 kills (40% per kill)')

    def test_kill_still_turns_monster_into_corpse(self):
        """Drops must not replace the corpse conversion."""
        dingo = create_monster('dingo', 2, 3, 3)
        message, _dropped = kill_monster(dingo, 2)
        self.assertFalse(dingo.blocks)
        self.assertIsNone(dingo.fighter)
        self.assertEqual(dingo.sprite_id, 'corpse')

    def test_every_species_has_a_drop_table(self):
        """The economy fix: no species drops nothing any more -- every one
        has at least its own meat."""
        self.assertTrue(DROP_TABLES)
        for species in DROP_TABLES:
            self.assertTrue(DROP_TABLES[species],
                            '{0} has an empty drop table'.format(species))

    def test_wallaby_drops_its_own_meat(self):
        """Wallabies used to drop nothing; now every kill can feed you.
        The meat lands at the corpse's tile."""
        for _ in range(50):
            wallaby = create_monster('wallaby', 3, 10, 10)
            _message, dropped = kill_monster(wallaby, 3)
            meat = next((d for d in dropped if d.item_choice == 'wallaby_meat'),
                        None)
            if meat is not None:
                self.assertEqual((meat.x, meat.y), (10, 10))
                return
        self.fail('wallaby never dropped its meat in 50 kills (80% per kill)')

    def test_croc_can_drop_the_esky(self):
        """The Esky of Holding is a croc drop (alongside the hide)."""
        self.assertIn('esky_of_holding', DROP_TABLES['crocodile'])
        self.assertIn('croc_hide_cuirass', DROP_TABLES['crocodile'])

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
