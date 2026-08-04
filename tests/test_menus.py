#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Phase B menu click registry (components/menus.py).

The menus register per-option hit-rects plus the action each option fires,
so a MOUSEBUTTONDOWN is equivalent to the letter keys. These tests pin the
registry down -- and the stale-registry guard: when no menu is on screen
(plain play state), every clickable rect must be dropped so a leftover
death/victory menu can never swallow a click during play.
"""
import os
import sys
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

import pygame

pygame.init()

from algorithms.fov import compute_fov
from components import menus
from components.entity import Entity
from components.equipment import Equipment
from components.fighter import Fighter
from components.game_states import GameStates
from components.inventory import Inventory
from loader_functions.initialize_new_game import get_constants, get_game_variables
from loader_functions.items import create_item
from renderer.font_renderer import FontRenderer
from renderer.renderer import Renderer


def fresh_game():
    constants = get_constants()
    player, entities, game_map, message_log, game_state = get_game_variables(constants)
    return constants, player, entities, game_map, message_log, game_state


def make_player():
    # The game's player invariant: inventory + equipment (the inventory
    # menu labels equipped items via the equipment slots).
    player = Entity(0, 0, 'player', (0, 0, 0), 'P',
                    fighter=Fighter(100, 10, 10), inventory=Inventory(26),
                    equipment=Equipment())
    player.inventory.add_item(create_item('lesser_med_kit', 1, 0, 0))
    player.inventory.add_item(create_item('med_kit', 1, 0, 0))
    return player


class TestClickRegistry(unittest.TestCase):
    def test_inventory_menu_registers_clickable_options(self):
        surface = pygame.Surface((1600, 852))
        font = FontRenderer()
        player = make_player()
        menus.inventory_menu(surface, font, 'header\n', player, 50, 100, 55)
        rects = menus._ACTIVE['rects']
        actions = menus._ACTIVE['actions']
        self.assertTrue(rects)
        self.assertEqual(len(rects), len(actions))
        # Clicking the first option resolves to that item's index.
        action = menus.action_at(rects[0].center)
        self.assertIsNotNone(action)
        self.assertEqual(action['inventory_index'], 0)
        # A click far outside any rect resolves to nothing.
        self.assertIsNone(menus.action_at((2, 2)))

    def test_context_menu_actions(self):
        surface = pygame.Surface((1600, 852))
        font = FontRenderer()
        item = create_item('lesser_med_kit', 1, 0, 0)
        menus.context_menu(surface, font, item, 100, 55)
        rects = menus._ACTIVE['rects']
        actions = menus._ACTIVE['actions']
        self.assertEqual(len(rects), 3)
        for i, rect in enumerate(rects):
            self.assertIsNotNone(menus.action_at(rect.center))
        self.assertEqual(actions[0], {'context_use': True})
        self.assertEqual(actions[1], {'context_equip': True})
        self.assertEqual(actions[2], {'context_drop': True})

    def test_no_menu_means_no_clicks(self):
        """Stale-registry guard: after a menu frame the registry has rects;
        after a plain play-state frame it must be empty again."""
        constants, player, entities, game_map, message_log, game_state = fresh_game()
        renderer = Renderer(constants)
        fov = compute_fov(game_map.block_sight, game_map.width, game_map.height,
                          player.x, player.y, constants['fov_radius'])
        renderer.render(game_map, fov, entities, player, message_log,
                        GameStates.SHOW_INVENTORY, None)
        self.assertTrue(menus._ACTIVE['rects'])
        renderer.render(game_map, fov, entities, player, message_log,
                        GameStates.PLAYERS_TURN, None)
        self.assertEqual(menus._ACTIVE['rects'], [])
        self.assertIsNone(menus.action_at((500, 500)))


class TestMenuSizingAndGroupedHotkeys(unittest.TestCase):
    def test_menu_box_sizes_to_content_never_truncates(self):
        """The box must grow to hold the longest option -- options are
        never wrapped and never elided with '...'."""
        surface = pygame.Surface((1600, 852))
        font = FontRenderer()
        long_option = ('Craft Med Kit (needs: 2 x Lesser Med Kit, 1 x '
                       'Eucalyptus Tea) - shown in full')
        m = menus.Menu('Crafting.', [long_option], width=5)
        _x, _y, w, h = m.draw(surface, font)
        full = '(a) ' + long_option
        # The box widened itself far past the caller's requested width so
        # the whole option fits on one line -- no truncation, no wrapping.
        self.assertGreaterEqual(w, len(full) + 3)
        self.assertEqual(h, 1 + 1 + 2)  # header row + 1 option + box padding
        self.assertNotIn('...', full)

    def test_grouped_hotkeys_collapse_stacks(self):
        """Stacks collapse to ONE hotkey and the letter resolves to the
        top item of its stack -- never a raw list position behind a stack
        (the bug where stacked items ate multiple hotkeys)."""
        player = Entity(0, 0, 'player', (0, 0, 0), 'P',
                        fighter=Fighter(100, 10, 10),
                        inventory=Inventory(26), equipment=Equipment())
        player.inventory.add_item(create_item('lesser_med_kit', 1, 0, 0))
        player.inventory.add_item(create_item('lesser_med_kit', 1, 0, 0))
        player.inventory.add_item(create_item('med_kit', 1, 0, 0))
        # Raw list: [lesser(0), lesser(1), med(2)] -> groups: lesser(a,
        # rep 0), med(b, rep 2). 'b' must hit the med kit at RAW index 2,
        # not the second lesser kit at raw index 1.
        groups = menus.inventory_groups(player.inventory.items)
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0][1], 0)   # lesser stack reps index 0
        self.assertEqual(groups[1][1], 2)   # med kit reps index 2
        self.assertIs(menus.inventory_item_at(player, 0),
                      player.inventory.items[0])
        self.assertIs(menus.inventory_item_at(player, 1),
                      player.inventory.items[2])
        self.assertIsNone(menus.inventory_item_at(player, 99))


if __name__ == '__main__':
    unittest.main()
