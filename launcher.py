#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AlienRaid launcher (pygame).

Run inside the nix dev shell::

    nix develop
    .venv/bin/python launcher.py
"""

import os

import pygame

from random import randint

from functions.death_functions import kill_monster, kill_player
from components.entity import get_blocking_entities_at_location
from algorithms.fov import compute_fov
from components.game_messages import Message
from components.game_states import GameStates
from components.input_handler import handle_keys, handle_mouse, handle_main_menu
from loader_functions.initialize_new_game import get_constants, get_game_variables
from loader_functions.data_loaders import load_game, save_game
from components.menus import main_menu, message_box
from renderer.renderer import Renderer
from renderer import palette as C
from functions.systems import passive_regen, wait_action, process_player_turn_results

print("AlienRaid Copyright (C) 2019  Bonzu <bonzupii@protonmail.com>\n"
      "This program comes with ABSOLUTELY NO WARRANTY.\n"
      "This is free software, and you are welcome to redistribute it under\n"
      "certain conditions.\n"
      "See enclosed LICENSE.md for details.\n")


def _recompute_fov(game_map, player, constants):
    return compute_fov(game_map.block_sight, game_map.width, game_map.height,
                       player.x, player.y, constants['fov_radius'])


def _collect_ship_part(player, entities, message_log):
    for entity in entities:
        if entity.part_id and entity.x == player.x and entity.y == player.y:
            player.quest.find_part(entity.part_id)
            message_log.add_message(Message(
                'You salvage the {0}! ({1}/{2} ship parts found.)'.format(
                    entity.name, player.quest.found_count, player.quest.parts_total),
                C.GOLD))
            entities.remove(entity)
            return True
    return False


def _handle_take(player, entities, game_map, message_log, constants):
    """Trail (up/down) or the ship (install parts / escape)."""
    for entity in entities:
        if entity.trail and entity.x == player.x and entity.y == player.y:
            if entity.trail.direction == 'down':
                return game_map.go_down(player, message_log, constants)
            return game_map.go_up(player, message_log, constants)
        elif entity.ship and entity.x == player.x and entity.y == player.y:
            if player.quest.found_count == 0:
                message_log.add_message(Message(
                    'The ship is gutted. You need to salvage its missing parts from deeper in the Outback.',
                    C.YELLOW))
            elif player.quest.complete:
                message_log.add_message(Message(
                    'Every part is installed. The engine hums to life!', C.LIGHT_GREEN))
            else:
                missing = player.quest.parts_total - player.quest.found_count
                message_log.add_message(Message(
                    'You install the salvaged parts. {0} more part{1} to find.'.format(
                        missing, '' if missing == 1 else 's'), C.GOLD))
            return entities
    message_log.add_message(Message('There is nothing here to use.', C.YELLOW))
    return entities


def play_game(player, entities, game_map, message_log, game_state, renderer, constants):
    fov_recompute = True
    fov_map = _recompute_fov(game_map, player, constants)

    game_state = GameStates.PLAYERS_TURN
    previous_game_state = game_state

    targeting_item = None
    wait_timer = 0
    mouse_tile = (0, 0)
    clock = pygame.time.Clock()

    while True:
        action = {}
        mouse_action = {}
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game(player, entities, game_map, message_log, game_state)
                return True
            elif event.type == pygame.KEYDOWN:
                candidate = handle_keys(event, game_state)
                if candidate:
                    action = candidate
            elif event.type == pygame.MOUSEBUTTONDOWN:
                tile = renderer.screen_to_tile(event.pos)
                if tile is not None:
                    mouse_tile = tile
                    candidate = handle_mouse(event, tile)
                    if candidate:
                        mouse_action = candidate
            elif event.type == pygame.MOUSEMOTION:
                tile = renderer.screen_to_tile(event.pos)
                if tile is not None:
                    mouse_tile = tile
            elif event.type == pygame.VIDEORESIZE:
                renderer.resize(event.w, event.h)

        if fov_recompute:
            fov_map = _recompute_fov(game_map, player, constants)
            fov_recompute = False

        renderer.render(game_map, fov_map, entities, player, message_log,
                        game_state, mouse_tile)
        pygame.display.flip()
        clock.tick(30)

        if player.fighter.max_hp < player.fighter.hp:
            player.fighter.hp = player.fighter.max_hp

        move = action.get('move')
        wait = action.get('wait')
        pickup = action.get('pickup')
        show_inventory = action.get('show_inventory')
        drop_inventory = action.get('drop_inventory')
        inventory_index = action.get('inventory_index')
        take_trail = action.get('take_trail')
        level_up = action.get('level_up')
        show_character_screen = action.get('show_character_screen')
        checkpoint = action.get('checkpoint')
        exit_game = action.get('exit')
        fullscreen = action.get('fullscreen')

        left_click = mouse_action.get('left_click')
        right_click = mouse_action.get('right_click')

        player_turn_results = []

        if move and game_state == GameStates.PLAYERS_TURN:
            dx, dy = move
            destination_x = player.x + dx
            destination_y = player.y + dy

            if wait_timer > 0:
                if randint(0, 7) == 7:
                    wait_timer -= 5

            passive_regen(player, message_log)

            if not game_map.is_blocked(destination_x, destination_y):
                target = get_blocking_entities_at_location(entities, destination_x, destination_y)
                if target:
                    player_turn_results.extend(player.fighter.attack(target))
                else:
                    player.move(dx, dy)
                    _collect_ship_part(player, entities, message_log)
                    fov_recompute = True
                game_state = GameStates.ENEMY_TURN

        elif wait and game_state == GameStates.PLAYERS_TURN:
            wait_timer, game_state = wait_action(player, message_log, wait_timer)

        elif pickup and game_state == GameStates.PLAYERS_TURN:
            for entity in entities:
                if entity.item and entity.x == player.x and entity.y == player.y:
                    pickup_results = player.inventory.add_item(entity)
                    player_turn_results.extend(pickup_results)
                    break
            else:
                message_log.add_message(Message('There is nothing here to pick up.', C.YELLOW))

        if show_inventory:
            previous_game_state = game_state
            game_state = GameStates.SHOW_INVENTORY

        if drop_inventory:
            previous_game_state = game_state
            game_state = GameStates.DROP_INVENTORY

        if inventory_index is not None and previous_game_state != GameStates.PLAYER_DEAD \
                and inventory_index < len(player.inventory.items):
            item = player.inventory.items[inventory_index]

            if game_state == GameStates.SHOW_INVENTORY:
                player_turn_results.extend(player.inventory.use(
                    item, entities=entities, fov_map=fov_map, game_map=game_map))
                game_state = GameStates.ENEMY_TURN
            elif game_state == GameStates.DROP_INVENTORY:
                player_turn_results.extend(player.inventory.drop_item(item))

        if take_trail and game_state == GameStates.PLAYERS_TURN:
            entities = _handle_take(player, entities, game_map, message_log, constants)
            if player.quest.complete:
                game_state = GameStates.VICTORY
            fov_map = _recompute_fov(game_map, player, constants)
            fov_recompute = True

        if level_up:
            if player.fighter.hp <= player.fighter.max_hp - round((player.fighter.max_hp / 7)):
                player.fighter.hp += round((player.fighter.max_hp / 7))
            else:
                player.fighter.hp = player.fighter.max_hp
            if level_up == 'hp':
                player.fighter.base_max_hp += 250
                player.fighter.hp += 250
            elif level_up == 'str':
                player.fighter.base_power += 12
            elif level_up == 'def':
                player.fighter.base_defense += 12
            game_state = previous_game_state

        if show_character_screen:
            previous_game_state = game_state
            game_state = GameStates.CHARACTER_SCREEN

        if game_state == GameStates.TARGETING:
            if left_click:
                target_x, target_y = left_click
                player_turn_results.extend(player.inventory.use(
                    targeting_item, entities=entities, fov_map=fov_map,
                    game_map=game_map, target_x=target_x, target_y=target_y))
            elif right_click:
                player_turn_results.append({'targeting_cancelled': True})

        if checkpoint:
            save_game(player, entities, game_map, message_log, game_state)
            message_log.add_message(Message('Your game has been saved.', C.GREEN))

        if exit_game:
            if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY,
                              GameStates.CHARACTER_SCREEN):
                game_state = previous_game_state
            elif game_state == GameStates.TARGETING:
                player_turn_results.append({'targeting_cancelled': True})
            elif game_state == GameStates.VICTORY or game_state == GameStates.PLAYER_DEAD:
                return True
            else:
                save_game(player, entities, game_map, message_log, game_state)
                return True

        if fullscreen:
            renderer.toggle_fullscreen()

        game_state, targeting_item = process_player_turn_results(
            player_turn_results, player, entities, game_map, message_log,
            game_state, previous_game_state)

        if game_state == GameStates.ENEMY_TURN:
            for entity in entities:
                if entity.ai:
                    enemy_turn_results = entity.ai.take_turn(player, fov_map, game_map, entities)

                    for enemy_turn_result in enemy_turn_results:
                        message = enemy_turn_result.get('message')
                        dead_entity = enemy_turn_result.get('dead')

                        if message:
                            message_log.add_message(message)

                        if dead_entity:
                            if dead_entity == player:
                                message, game_state = kill_player(dead_entity)
                            else:
                                message = kill_monster(dead_entity)

                            message_log.add_message(message)

                            if game_state == GameStates.PLAYER_DEAD:
                                break

                    if game_state == GameStates.PLAYER_DEAD:
                        break
            else:
                game_state = GameStates.PLAYERS_TURN


def main():
    constants = get_constants()

    renderer = Renderer(constants)

    try:
        background_image = pygame.image.load('menu_background.png')
    except pygame.error:
        background_image = None

    show_main_menu = True
    show_load_error_message = False
    clock = pygame.time.Clock()

    while True:
        if show_main_menu:
            action = {}
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    candidate = handle_main_menu(event)
                    if candidate:
                        action = candidate
                elif event.type == pygame.VIDEORESIZE:
                    renderer.resize(event.w, event.h)

            main_menu(renderer.frame, renderer.font, background_image,
                      constants['screen_width'], constants['screen_height'])

            if show_load_error_message:
                message_box(renderer.frame, renderer.font, 'No saved game to load',
                            50, constants['screen_width'], constants['screen_height'])

            renderer.present()
            pygame.display.flip()
            clock.tick(30)

            new_game = action.get('new_game')
            load_saved_game = action.get('load_game')
            exit_game = action.get('exit')

            if show_load_error_message and (new_game or load_saved_game or exit_game):
                show_load_error_message = False
            elif new_game:
                player, entities, game_map, message_log, game_state = get_game_variables(constants)
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
            play_game(player, entities, game_map, message_log, game_state,
                      renderer, constants)
            show_main_menu = True


if __name__ == '__main__':
    main()
