#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AlienRaid launcher (pygame).

Run inside the nix dev shell::

    nix develop
    .venv/bin/python launcher.py

This module owns only the launch concern: the boot banner (GPL + parody
fair-use notice), the main-menu shell, and wiring the chosen outcome (new
game / load / play / quit) into ``functions.game_loop.play_game``. All
in-game turn and menu-state logic lives in ``functions/game_loop``.
"""

import pygame

from components.game_states import GameStates
from components.input_handler import handle_main_menu
from components import menus
from components.menus import main_menu, popup_box, action_at, set_mouse
from loader_functions.initialize_new_game import get_constants, get_game_variables
from loader_functions.data_loaders import load_game
from renderer.renderer import Renderer
from renderer.menu_background import MenuBackdrop
import functions.death_functions as death_mod
from functions.game_loop import play_game

# The old codes still work out here: Up Up Down Down Left Right Left
# Right B A grants cosmetic sunglasses on the player sprite.
KONAMI_SEQUENCE = [pygame.K_UP, pygame.K_UP, pygame.K_DOWN, pygame.K_DOWN,
                   pygame.K_LEFT, pygame.K_RIGHT, pygame.K_LEFT,
                   pygame.K_RIGHT, pygame.K_b, pygame.K_a]

print("AlienRaid Copyright (C) 2019-2026  Bonzupii <bonzupii@protonmail.com>\n"
      "This program comes with ABSOLUTELY NO WARRANTY.\n"
      "This is free software, and you are welcome to redistribute it under\n"
      "certain conditions.\n"
      "See enclosed LICENSE.md for details.\n")
print("AlienRaid is an unofficial Men in Black parody; see README.md "
      "for the full fair-use notice. No affiliation with or claim to "
      "any Sony/Columbia/Marvel property is made.\n")


def main():
    constants = get_constants()

    renderer = Renderer(constants)
    backdrop = MenuBackdrop(renderer.screen_w, renderer.screen_h)

    show_main_menu = True
    show_load_error_message = False
    outback_remembers = False
    konami_buffer = []
    konami_active = False
    clock = pygame.time.Clock()

    while True:
        dt = clock.tick(30) / 1000.0
        if show_main_menu:
            frame_pos = renderer.screen_to_frame(pygame.mouse.get_pos())
            menus.set_mouse(frame_pos if frame_pos is not None else (0, 0))

            events = pygame.event.get()
            # Menu idle blink: any input keeps the face awake; untouched for
            # ~3 minutes it blinks once, then the timer restarts.
            backdrop.update(dt, events)

            action = {}
            for event in events:
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    # Konami code: the final B + A must not also fire the
                    # menu's load/new-game actions, so the completing key
                    # press is swallowed.
                    if not konami_active:
                        konami_buffer.append(event.key)
                        if len(konami_buffer) > len(KONAMI_SEQUENCE):
                            konami_buffer = konami_buffer[-len(KONAMI_SEQUENCE):]
                        if konami_buffer == KONAMI_SEQUENCE:
                            konami_active = True
                            konami_buffer = []
                            continue
                    candidate = handle_main_menu(event)
                    if candidate:
                        action = candidate
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    frame = renderer.screen_to_frame(event.pos)
                    if frame is not None:
                        menus.set_mouse(frame)
                        menu_action = action_at(frame)
                        if menu_action:
                            action.update(menu_action)
                elif event.type == pygame.VIDEORESIZE:
                    renderer.resize(event.w, event.h)

            main_menu(renderer.frame, renderer.font, backdrop.surface,
                      constants['screen_width'], constants['screen_height'],
                      remember_line='The Outback remembers you.' if outback_remembers else None,
                      konami_footer='The old codes still work out here.' if konami_active else None)

            if show_load_error_message:
                popup_box(renderer.frame, renderer.font, 'No saved game to load',
                          constants['screen_width'], constants['screen_height'])

            renderer.present()
            pygame.display.flip()

            new_game = action.get('new_game')
            load_saved_game = action.get('load_game')
            exit_game = action.get('exit')

            if show_load_error_message and (new_game or load_saved_game or exit_game):
                show_load_error_message = False
            elif new_game:
                player, entities, game_map, message_log, game_state = get_game_variables(constants)
                if konami_active:
                    player.sprite_id = 'player_sunglasses'
                game_state = GameStates.PLAYERS_TURN
                show_main_menu = False
            elif load_saved_game:
                try:
                    player, entities, game_map, message_log, game_state = load_game()
                    show_main_menu = False
                except FileNotFoundError:
                    show_load_error_message = True
            elif exit_game:
                return
        else:
            result = play_game(player, entities, game_map, message_log, game_state,
                               renderer, constants)
            if result == 'new_game':
                player, entities, game_map, message_log, game_state = get_game_variables(constants)
                if konami_active:
                    player.sprite_id = 'player_sunglasses'
                game_state = GameStates.PLAYERS_TURN
                show_main_menu = False
            elif result == 'main_menu':
                # The Outback remembers you: after any death, the menu
                # footer changes for the rest of the session.
                if death_mod.PLAYER_DIED_FLAG:
                    outback_remembers = True
                show_main_menu = True
            else:
                return


if __name__ == '__main__':
    main()
