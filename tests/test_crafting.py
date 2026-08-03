#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the crafting system (Phase D)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from components.entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.crafting import (RECIPES, craftable, result_name, needs_text,
                                 craft_item)
from loader_functions.items import create_item


def make_player():
    return Entity(0, 0, 'player', (0, 0, 0), 'Player',
                  fighter=Fighter(100, 10, 10), inventory=Inventory(26))


def give(player, *choices):
    for choice in choices:
        player.inventory.add_item(create_item(choice, 1, 0, 0))


class TestCrafting(unittest.TestCase):
    def test_recipe_table_is_complete(self):
        # Every recipe has a display name and at least one ingredient, and
        # every ingredient choice is a real creatable item.
        self.assertTrue(RECIPES)
        for recipe_id, recipe in RECIPES.items():
            self.assertIn('name', recipe, recipe_id)
            self.assertTrue(recipe['ingredients'], recipe_id)
            for ing in recipe['ingredients']:
                item = create_item(ing, 1, 0, 0)
                self.assertEqual(item.item_choice, ing,
                                 'ingredient {0} of {1} not creatable'.format(ing, recipe_id))

    def test_craftable_false_without_ingredients(self):
        player = make_player()
        self.assertFalse(craftable(player)['med_kit'])

    def test_craftable_true_with_ingredients(self):
        player = make_player()
        give(player, 'lesser_med_kit', 'lesser_med_kit', 'eucalyptus_tea')
        self.assertTrue(craftable(player)['med_kit'])
        self.assertEqual(result_name('med_kit'), 'Med Kit')

    def test_needs_text_lists_missing(self):
        player = make_player()
        text = needs_text('med_kit', player)
        self.assertIn('Lesser Med Kit', text)

    def test_craft_item_consumes_and_creates(self):
        player = make_player()
        give(player, 'lesser_med_kit', 'lesser_med_kit', 'eucalyptus_tea')
        results = craft_item(player, 'med_kit', [], 1)
        self.assertTrue(any(r.get('consumed') for r in results))
        remaining = [i.item_choice for i in player.inventory.items]
        self.assertNotIn('lesser_med_kit', remaining)
        self.assertNotIn('eucalyptus_tea', remaining)
        self.assertEqual(remaining.count('med_kit'), 1)

    def test_craft_item_without_ingredients_fails_cleanly(self):
        player = make_player()
        before = list(player.inventory.items)
        results = craft_item(player, 'med_kit', [], 1)
        self.assertFalse(any(r.get('consumed') for r in results))
        self.assertEqual(player.inventory.items, before,
                         'failed craft must not consume anything')


if __name__ == '__main__':
    unittest.main()
