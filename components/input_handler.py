#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Input handling: map pygame events to the action-dict format the main
loop consumes (e.g. ``{'move': (0, -1)}``, ``{'left_click': (x, y)}``)."""

import pygame

from components.game_states import GameStates

TILE = 12


def handle_keys(event, game_state):
    if event.type != pygame.KEYDOWN:
        return {}

    if game_state == GameStates.PLAYERS_TURN:
        return handle_player_turn_keys(event)
    elif game_state == GameStates.PLAYER_DEAD:
        return handle_player_dead_keys(event)
    elif game_state == GameStates.TARGETING:
        return handle_targeting_keys(event)
    elif game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
        return handle_inventory_keys(event)
    elif game_state == GameStates.LEVEL_UP:
        return handle_level_up_menu(event)
    elif game_state == GameStates.CHARACTER_SCREEN:
        return handle_character_screen(event)
    elif game_state == GameStates.VICTORY:
        return handle_victory_keys(event)

    return {}


def _char(event):
    if event.unicode and event.unicode.isprintable():
        return event.unicode.lower()
    return ''


def _is_alt_enter(event):
    return (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER) and \
        (event.mod & pygame.KMOD_ALT)


def handle_player_turn_keys(event):
    ch = _char(event)

    if event.key == pygame.K_UP or ch == 'k':
        return {'move': (0, -1)}
    elif event.key == pygame.K_DOWN or ch == 'j':
        return {'move': (0, 1)}
    elif event.key == pygame.K_LEFT or ch == 'h':
        return {'move': (-1, 0)}
    elif event.key == pygame.K_RIGHT or ch == 'l':
        return {'move': (1, 0)}
    elif ch == 'y':
        return {'move': (-1, -1)}
    elif ch == 'u':
        return {'move': (1, -1)}
    elif ch == 'b':
        return {'move': (-1, 1)}
    elif ch == 'n':
        return {'move': (1, 1)}
    elif ch == 'z':
        return {'wait': True}
    elif ch == 'g':
        return {'pickup': True}
    elif ch == 'i':
        return {'show_inventory': True}
    elif ch == 'd':
        return {'drop_inventory': True}
    elif ch == '.':
        return {'take_trail': True}
    elif ch == 'c':
        return {'show_character_screen': True}
    elif ch == 's':
        return {'checkpoint': True}

    if _is_alt_enter(event):
        return {'fullscreen': True}
    elif event.key == pygame.K_ESCAPE:
        return {'exit': True}

    return {}


def handle_targeting_keys(event):
    if event.key == pygame.K_ESCAPE:
        return {'exit': True}
    return {}


def handle_player_dead_keys(event):
    if _char(event) == 'i':
        return {'show_inventory': True}
    if _is_alt_enter(event):
        return {'fullscreen': True}
    elif event.key == pygame.K_ESCAPE:
        return {'exit': True}
    return {}


def handle_victory_keys(event):
    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
        return {'exit': True}
    return {}


def handle_mouse(event):
    if event.type != pygame.MOUSEBUTTONDOWN:
        return {}
    x = event.pos[0] // TILE
    y = event.pos[1] // TILE
    if event.button == 1:
        return {'left_click': (x, y)}
    elif event.button == 3:
        return {'right_click': (x, y)}
    return {}


def handle_inventory_keys(event):
    ch = _char(event)
    if ch and 'a' <= ch <= 'z':
        return {'inventory_index': ord(ch) - ord('a')}

    if _is_alt_enter(event):
        return {'fullscreen': True}
    elif event.key == pygame.K_ESCAPE:
        return {'exit': True}
    return {}


def handle_main_menu(event):
    if event.type != pygame.KEYDOWN:
        return {}
    ch = _char(event)
    if ch == 'a':
        return {'new_game': True}
    elif ch == 'b':
        return {'load_game': True}
    elif ch == 'c' or event.key == pygame.K_ESCAPE:
        return {'exit': True}
    return {}


def handle_level_up_menu(event):
    ch = _char(event)
    if ch == 'a':
        return {'level_up': 'hp'}
    elif ch == 'b':
        return {'level_up': 'str'}
    elif ch == 'c':
        return {'level_up': 'def'}
    return {}


def handle_character_screen(event):
    ch = _char(event)
    if event.key == pygame.K_ESCAPE or ch == 'c':
        return {'exit': True}
    return {}
