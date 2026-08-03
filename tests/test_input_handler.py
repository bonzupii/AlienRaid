#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for components/input_handler.py: every key must be interpreted
relative to the current game state (the same 'a' key means different things
in PLAYERS_TURN vs SHOW_INVENTORY vs ITEM_CONTEXT), so an action can never
leak across states."""
import os
import sys
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

import pygame

pygame.init()

from components.game_states import GameStates
from components.input_handler import (handle_keys, handle_mouse,
                                      handle_main_menu)


def key(key, ch='', mod=0):
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=ch, mod=mod)


def mouse(button, tile):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=button, pos=(0, 0))


class TestStateGating(unittest.TestCase):
    def test_same_key_differs_by_state(self):
        """The same 'a' key: nothing in play, inventory index 0 in the
        inventory menu, 'use' in the item context menu."""
        self.assertEqual(handle_keys(key(pygame.K_a, 'a'), GameStates.PLAYERS_TURN), {})
        self.assertEqual(handle_keys(key(pygame.K_a, 'a'), GameStates.SHOW_INVENTORY),
                         {'inventory_index': 0})
        self.assertEqual(handle_keys(key(pygame.K_a, 'a'), GameStates.ITEM_CONTEXT),
                         {'context_choice': 'use'})

    def test_inventory_letters_map_to_indices(self):
        for state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
            self.assertEqual(handle_keys(key(pygame.K_b, 'b'), state),
                             {'inventory_index': 1})
            self.assertEqual(handle_keys(key(pygame.K_z, 'z'), state),
                             {'inventory_index': 25})

    def test_player_turn_moves_and_actions(self):
        self.assertEqual(handle_keys(key(pygame.K_h, 'h'), GameStates.PLAYERS_TURN),
                         {'move': (-1, 0)})
        self.assertEqual(handle_keys(key(pygame.K_j, 'j'), GameStates.PLAYERS_TURN),
                         {'move': (0, 1)})
        self.assertEqual(handle_keys(key(pygame.K_y, 'y'), GameStates.PLAYERS_TURN),
                         {'move': (-1, -1)})
        self.assertEqual(handle_keys(key(pygame.K_z, 'z'), GameStates.PLAYERS_TURN),
                         {'wait': True})
        self.assertEqual(handle_keys(key(pygame.K_g, 'g'), GameStates.PLAYERS_TURN),
                         {'pickup': True})
        self.assertEqual(handle_keys(key(pygame.K_i, 'i'), GameStates.PLAYERS_TURN),
                         {'show_inventory': True})
        self.assertEqual(handle_keys(key(pygame.K_d, 'd'), GameStates.PLAYERS_TURN),
                         {'drop_inventory': True})

    def test_crafting_entry_from_play_and_inventory(self):
        self.assertEqual(handle_keys(key(pygame.K_F5), GameStates.PLAYERS_TURN),
                         {'show_crafting': True})
        self.assertEqual(handle_keys(key(pygame.K_r, 'r'), GameStates.PLAYERS_TURN),
                         {'show_crafting': True})
        self.assertEqual(handle_keys(key(pygame.K_F5), GameStates.SHOW_INVENTORY),
                         {'show_crafting': True})

    def test_dialogue_and_crafting_letters(self):
        self.assertEqual(handle_keys(key(pygame.K_b, 'b'), GameStates.DIALOGUE),
                         {'dialogue_index': 1})
        self.assertEqual(handle_keys(key(pygame.K_c, 'c'), GameStates.CRAFTING),
                         {'craft_index': 2})

    def test_context_menu_keys(self):
        self.assertEqual(handle_keys(key(pygame.K_b, 'b'), GameStates.ITEM_CONTEXT),
                         {'context_choice': 'equip'})
        self.assertEqual(handle_keys(key(pygame.K_c, 'c'), GameStates.ITEM_CONTEXT),
                         {'context_choice': 'drop'})

    def test_endgame_keys(self):
        self.assertEqual(handle_keys(key(pygame.K_a, 'a'), GameStates.VICTORY),
                         {'new_game': True})
        self.assertEqual(handle_keys(key(pygame.K_b, 'b'), GameStates.PLAYER_DEAD),
                         {'exit': True})

    def test_esc_closes_menus_and_targeting(self):
        for state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY,
                      GameStates.CRAFTING, GameStates.DIALOGUE,
                      GameStates.ITEM_CONTEXT, GameStates.POPUP,
                      GameStates.CHARACTER_SCREEN, GameStates.TARGETING):
            self.assertEqual(handle_keys(key(pygame.K_ESCAPE), state),
                             {'exit': True}, state)

    def test_level_up_menu(self):
        self.assertEqual(handle_keys(key(pygame.K_a, 'a'), GameStates.LEVEL_UP),
                         {'level_up': 'hp'})
        self.assertEqual(handle_keys(key(pygame.K_c, 'c'), GameStates.LEVEL_UP),
                         {'level_up': 'def'})


class TestMouse(unittest.TestCase):
    def test_left_and_right_clicks_carry_the_tile(self):
        self.assertEqual(handle_mouse(mouse(1, (3, 4)), (3, 4)),
                         {'left_click': (3, 4)})
        self.assertEqual(handle_mouse(mouse(3, (3, 4)), (3, 4)),
                         {'right_click': (3, 4)})

    def test_non_click_events_are_ignored(self):
        self.assertEqual(handle_mouse(pygame.event.Event(pygame.MOUSEMOTION, pos=(0, 0)), None), {})


class TestMainMenu(unittest.TestCase):
    def test_main_menu_keys(self):
        self.assertEqual(handle_main_menu(key(pygame.K_a, 'a')), {'new_game': True})
        self.assertEqual(handle_main_menu(key(pygame.K_b, 'b')), {'load_game': True})
        self.assertEqual(handle_main_menu(key(pygame.K_c, 'c')), {'exit': True})
        self.assertEqual(handle_main_menu(key(pygame.K_ESCAPE)), {'exit': True})


if __name__ == '__main__':
    unittest.main()
