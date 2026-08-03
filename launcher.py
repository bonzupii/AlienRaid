#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AlienRaid launcher (pygame).

Run inside the nix dev shell::

    nix develop
    .venv/bin/python launcher.py
"""

from random import randint

import pygame

from functions.death_functions import kill_monster, kill_player
from functions.senses import NoiseMap
from components.ai import HeuristicMonster, HUNT, FLEE
from components.entity import get_blocking_entities_at_location
from algorithms.fov import compute_fov
from components.game_messages import Message
from components.game_states import GameStates
from components.input_handler import handle_keys, handle_mouse, handle_main_menu
from loader_functions.initialize_new_game import get_constants, get_game_variables
from loader_functions.data_loaders import load_game, save_game
from components import menus
from components.menus import main_menu, popup_box, action_at, set_mouse
from components.crafting import craft_item, RECIPES as CRAFT_RECIPES
from functions.dialogue import get_dialogue, process_dialogue_choice
from functions.render_functions import get_names_under_mouse
from renderer.renderer import Renderer
from renderer.menu_background import generate_menu_background
from renderer import palette as C
from functions.systems import passive_regen, wait_action, process_player_turn_results

print("AlienRaid Copyright (C) 2019-2026  Bonzupii <bonzupii@protonmail.com>\n"
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


def _start_dialogue(target, player):
    """Open dialogue with an NPC. Returns (npc, dialogue_data) or (None, None)."""
    if not getattr(target, 'npc_id', None):
        return None, None
    return target, get_dialogue(target, player)


def _apply_level_up(player, level_up):
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


def play_game(player, entities, game_map, message_log, game_state, renderer, constants):
    """Main game loop. Returns 'new_game', 'main_menu', or None (quit)."""
    fov_recompute = True
    fov_map = _recompute_fov(game_map, player, constants)

    game_state = GameStates.PLAYERS_TURN
    previous_game_state = game_state

    targeting_item = None
    context_item = None
    active_npc = None
    dialogue_data = None
    popup_text = None
    wait_timer = 0
    mouse_tile = None
    noise_map = NoiseMap(game_map.width, game_map.height)
    clock = pygame.time.Clock()

    while True:
        # Fresh ears each player turn: noise from the previous turn is wiped
        # before the player acts, so events this turn are heard the same turn.
        if game_state == GameStates.PLAYERS_TURN:
            noise_map.clear()

        # Feed the frame-space cursor to the menus (hover highlight + clicks).
        frame_pos = renderer.screen_to_frame(pygame.mouse.get_pos())
        menus.set_mouse(frame_pos if frame_pos is not None else (0, 0))

        action = {}
        mouse_action = {}
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game(player, entities, game_map, message_log, game_state)
                return None
            elif event.type == pygame.KEYDOWN:
                candidate = handle_keys(event, game_state)
                if candidate:
                    action = candidate
            elif event.type == pygame.MOUSEBUTTONDOWN:
                frame = renderer.screen_to_frame(event.pos)
                tile = renderer.screen_to_tile(event.pos)
                if frame is not None:
                    menus.set_mouse(frame)
                    menu_action = action_at(frame)
                    if menu_action:
                        action.update(menu_action)
                if event.button in (1, 3):
                    candidate = handle_mouse(event, tile)
                    if candidate:
                        mouse_action = candidate
            elif event.type == pygame.MOUSEMOTION:
                frame = renderer.screen_to_frame(event.pos)
                if frame is not None:
                    menus.set_mouse(frame)
                tile = renderer.screen_to_tile(event.pos)
                if tile is not None:
                    mouse_tile = tile
            elif event.type == pygame.VIDEORESIZE:
                renderer.resize(event.w, event.h)

        if fov_recompute:
            fov_map = _recompute_fov(game_map, player, constants)
            fov_recompute = False

        context_index = None
        if context_item is not None:
            try:
                context_index = player.inventory.items.index(context_item)
            except ValueError:
                context_item = None

        render_dialogue = None
        if dialogue_data is not None:
            render_dialogue = (dialogue_data[0], [opt[0] for opt in dialogue_data[1]])

        renderer.render(game_map, fov_map, entities, player, message_log,
                        game_state, mouse_tile, dialogue=render_dialogue,
                        popup=popup_text, context_index=context_index)
        pygame.display.flip()
        clock.tick(30)

        if player.fighter.max_hp < player.fighter.hp:
            player.fighter.hp = player.fighter.max_hp

        left_click = mouse_action.get('left_click')
        right_click = mouse_action.get('right_click')

        move = action.get('move')
        wait = action.get('wait')
        pickup = action.get('pickup')
        show_inventory = action.get('show_inventory')
        drop_inventory = action.get('drop_inventory')
        show_crafting = action.get('show_crafting')
        inventory_index = action.get('inventory_index')
        craft_index = action.get('craft_index')
        dialogue_index = action.get('dialogue_index')
        dialogue_choice = action.get('dialogue_choice')
        context_choice = action.get('context_choice')
        context_use = action.get('context_use')
        context_equip = action.get('context_equip')
        context_drop = action.get('context_drop')
        crafting = action.get('crafting')
        take_trail = action.get('take_trail')
        level_up = action.get('level_up')
        show_character_screen = action.get('show_character_screen')
        checkpoint = action.get('checkpoint')
        exit_game = action.get('exit')
        fullscreen = action.get('fullscreen')
        new_game = action.get('new_game')

        player_turn_results = []

        # ------------------------------------------------------- map clicks
        if left_click and game_state == GameStates.PLAYERS_TURN:
            tx, ty = left_click
            target = get_blocking_entities_at_location(entities, tx, ty)
            if target is not None and target is not player:
                if getattr(target, 'npc_id', None):
                    active_npc, dialogue_data = _start_dialogue(target, player)
                    previous_game_state = game_state
                    game_state = GameStates.DIALOGUE
                elif target.fighter:
                    player_turn_results.extend(player.fighter.attack(target))
                    game_state = GameStates.ENEMY_TURN
            elif target is None:
                player.move_towards(tx, ty, game_map, entities)
                _collect_ship_part(player, entities, message_log)
                fov_recompute = True
                game_state = GameStates.ENEMY_TURN

        if right_click and game_state == GameStates.PLAYERS_TURN:
            names = get_names_under_mouse(right_click, entities, fov_map, game_map)
            if names:
                popup_text = names
                previous_game_state = game_state
                game_state = GameStates.POPUP

        # -------------------------------------------------- menu states
        if game_state == GameStates.SHOW_INVENTORY:
            if right_click is not None and inventory_index is not None \
                    and inventory_index < len(player.inventory.items):
                context_item = player.inventory.items[inventory_index]
                previous_game_state = game_state
                game_state = GameStates.ITEM_CONTEXT
            elif inventory_index is not None \
                    and inventory_index < len(player.inventory.items):
                item = player.inventory.items[inventory_index]
                player_turn_results.extend(player.inventory.use(
                    item, entities=entities, fov_map=fov_map, game_map=game_map,
                    noise_map=noise_map))
                game_state = GameStates.ENEMY_TURN
            elif crafting:
                previous_game_state = game_state
                game_state = GameStates.CRAFTING

        elif game_state == GameStates.DROP_INVENTORY:
            if inventory_index is not None \
                    and inventory_index < len(player.inventory.items):
                item = player.inventory.items[inventory_index]
                player_turn_results.extend(
                    player.inventory.drop_item(item, game_map, entities))
                game_state = GameStates.ENEMY_TURN

        elif game_state == GameStates.CRAFTING:
            if craft_index is not None and craft_index < len(CRAFT_RECIPES):
                recipe_key = list(CRAFT_RECIPES)[craft_index]
                player_turn_results.extend(craft_item(
                    player, recipe_key, entities, game_map.dungeon_level))
                game_state = GameStates.ENEMY_TURN

        elif game_state == GameStates.DIALOGUE and dialogue_data:
            index = dialogue_choice if dialogue_choice is not None else dialogue_index
            if index is not None and index < len(dialogue_data[1]):
                choice_key = dialogue_data[1][index][1]
                if choice_key == 'exit':
                    game_state = previous_game_state
                else:
                    process_dialogue_choice(active_npc, choice_key, player,
                                            game_map.dungeon_level, message_log)
                    game_state = GameStates.ENEMY_TURN
                active_npc = None
                dialogue_data = None

        elif game_state == GameStates.ITEM_CONTEXT:
            if context_item is not None:
                if context_use or context_equip:
                    player_turn_results.extend(player.inventory.use(
                        context_item, entities=entities, fov_map=fov_map,
                        game_map=game_map, noise_map=noise_map))
                    game_state = GameStates.ENEMY_TURN
                elif context_drop:
                    player_turn_results.extend(player.inventory.drop_item(
                        context_item, game_map, entities))
                    game_state = GameStates.ENEMY_TURN
                context_item = None

        elif game_state == GameStates.POPUP:
            if exit_game:
                game_state = previous_game_state
                popup_text = None

        elif game_state in (GameStates.VICTORY, GameStates.PLAYER_DEAD):
            if new_game:
                return 'new_game'
            if exit_game:
                return 'main_menu'

        # -------------------------------------------------- player turn
        if move and game_state == GameStates.PLAYERS_TURN:
            if player.fighter.has_status('webbed'):
                message_log.add_message(Message('You are tangled in sticky spider web!', C.GREEN))
                game_state = GameStates.ENEMY_TURN
            else:
                dx, dy = move
                destination_x = player.x + dx
                destination_y = player.y + dy

                if wait_timer > 0:
                    if randint(0, 7) == 7:
                        wait_timer -= 5

                passive_regen(player, message_log)

                if not game_map.is_blocked(destination_x, destination_y):
                    target = get_blocking_entities_at_location(
                        entities, destination_x, destination_y)
                    if target is not None and target is not player:
                        if getattr(target, 'npc_id', None):
                            active_npc, dialogue_data = _start_dialogue(target, player)
                            previous_game_state = game_state
                            game_state = GameStates.DIALOGUE
                        elif target.fighter:
                            player_turn_results.extend(player.fighter.attack(target))
                            game_state = GameStates.ENEMY_TURN
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
                    player_turn_results.extend(player.inventory.add_item(entity))
                    break
            else:
                message_log.add_message(Message('There is nothing here to pick up.', C.YELLOW))

        if show_inventory and game_state == GameStates.PLAYERS_TURN:
            previous_game_state = game_state
            game_state = GameStates.SHOW_INVENTORY

        if drop_inventory and game_state == GameStates.PLAYERS_TURN:
            previous_game_state = game_state
            game_state = GameStates.DROP_INVENTORY

        if show_crafting and game_state in (GameStates.PLAYERS_TURN,
                                            GameStates.SHOW_INVENTORY):
            previous_game_state = game_state
            game_state = GameStates.CRAFTING

        if take_trail and game_state == GameStates.PLAYERS_TURN:
            entities = _handle_take(player, entities, game_map, message_log, constants)
            if player.quest.complete:
                game_state = GameStates.VICTORY
            fov_map = _recompute_fov(game_map, player, constants)
            fov_recompute = True

        if level_up and game_state == GameStates.LEVEL_UP:
            _apply_level_up(player, level_up)
            game_state = previous_game_state

        if show_character_screen and game_state == GameStates.PLAYERS_TURN:
            previous_game_state = game_state
            game_state = GameStates.CHARACTER_SCREEN

        if game_state == GameStates.TARGETING:
            if left_click:
                target_x, target_y = left_click
                player_turn_results.extend(player.inventory.use(
                    targeting_item, entities=entities, fov_map=fov_map,
                    game_map=game_map, target_x=target_x, target_y=target_y,
                    noise_map=noise_map))
            elif right_click:
                player_turn_results.append({'targeting_cancelled': True})

        if checkpoint:
            save_game(player, entities, game_map, message_log, game_state)
            message_log.add_message(Message('Your game has been saved.', C.GREEN))

        if exit_game:
            if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY,
                              GameStates.CRAFTING, GameStates.DIALOGUE,
                              GameStates.ITEM_CONTEXT, GameStates.CHARACTER_SCREEN,
                              GameStates.POPUP):
                game_state = previous_game_state
                context_item = None
                active_npc = None
                dialogue_data = None
                popup_text = None
            elif game_state == GameStates.TARGETING:
                player_turn_results.append({'targeting_cancelled': True})
            elif game_state in (GameStates.VICTORY, GameStates.PLAYER_DEAD):
                return 'main_menu'
            else:
                save_game(player, entities, game_map, message_log, game_state)
                return None

        if fullscreen:
            renderer.toggle_fullscreen()

        game_state, targeting_item = process_player_turn_results(
            player_turn_results, player, entities, game_map, message_log,
            game_state, previous_game_state)

        # ------------------------------------------------------- enemy turn
        if game_state == GameStates.ENEMY_TURN:
            expired = player.fighter.tick_statuses()
            for status in expired:
                if status == 'speed':
                    message_log.add_message(Message('Your speed boost wears off.', C.YELLOW))
                elif status == 'poison_resist':
                    message_log.add_message(Message('Your poison resistance fades.', C.YELLOW))
                elif status == 'invisible':
                    message_log.add_message(Message('You are no longer invisible.', C.YELLOW))
                elif status == 'webbed':
                    message_log.add_message(Message('You tear free of the sticky web.', C.LIGHT_GRAY))

            for entity in entities:
                if entity.ai:
                    enemy_turn_results = entity.ai.take_turn(
                        player, fov_map, game_map, entities, noise_map)

                    for enemy_turn_result in enemy_turn_results:
                        message = enemy_turn_result.get('message')
                        dead_entity = enemy_turn_result.get('dead')
                        hurt_entity = enemy_turn_result.get('hurt')
                        webbed = enemy_turn_result.get('webbed')

                        if message:
                            message_log.add_message(message)

                        if webbed and webbed.fighter:
                            webbed.fighter.add_status('webbed',
                                                      enemy_turn_result.get('turns', 1))
                            message_log.add_message(Message(
                                'You are caught in sticky spider web!', C.GREEN))

                        if hurt_entity:
                            # Group morale: nearby pack-mates react to a hurt
                            # ally (timid scatter, dingoes hesitate, brutes enrage).
                            for other in entities:
                                if other is hurt_entity or not other.ai or not other.fighter:
                                    continue
                                if not isinstance(other.ai, HeuristicMonster) \
                                        or not isinstance(hurt_entity.ai, HeuristicMonster):
                                    continue
                                if type(other.ai) is not type(hurt_entity.ai):
                                    continue
                                if other.distance_to(hurt_entity) > 6:
                                    continue
                                roll = randint(0, 100)
                                if other.ai.FLEE_HP > 0.3 and roll < 30:
                                    other.ai.state = FLEE
                                    other.ai.state_turns = 0
                                elif other.ai.PACK > 0 and roll < 40:
                                    other.ai.slow_tick += 1  # hesitate a turn
                                elif other.ai.CAUTION == 0 and roll < 50:
                                    other.ai.state = HUNT
                                    other.ai.state_turns = 0

                        if dead_entity:
                            if dead_entity == player:
                                message, game_state = kill_player(dead_entity)
                            else:
                                # Capture name/AI before kill_monster nuls them.
                                dead_name = dead_entity.name
                                dead_ai = dead_entity.ai
                                message, dropped = kill_monster(
                                    dead_entity, game_map.dungeon_level)
                                if dropped:
                                    entities.append(dropped)
                                    message_log.add_message(Message(
                                        'The {0} dropped a {1}!'.format(
                                            dead_name, dropped.name),
                                        C.LIGHT_GREEN))

                            message_log.add_message(message)

                            if dead_entity is not player:
                                # Morale on death: nearby allies react.
                                for other in entities:
                                    if other is dead_entity or not other.ai or not other.fighter:
                                        continue
                                    if not isinstance(other.ai, HeuristicMonster):
                                        continue
                                    if type(other.ai) is not type(dead_ai):
                                        continue
                                    if other.distance_to(dead_entity) > 6:
                                        continue
                                    if other.ai.FLEE_HP > 0.3:
                                        other.ai.state = FLEE
                                    elif other.ai.PACK > 0:
                                        other.ai.slow_tick += 1  # hesitate
                                    elif other.ai.CAUTION == 0:
                                        other.ai.state = HUNT

                            if game_state == GameStates.PLAYER_DEAD:
                                break

                    if game_state == GameStates.PLAYER_DEAD:
                        break
            else:
                game_state = GameStates.PLAYERS_TURN


def main():
    constants = get_constants()

    renderer = Renderer(constants)
    bg = generate_menu_background(renderer.screen_w, renderer.screen_h)

    show_main_menu = True
    show_load_error_message = False
    clock = pygame.time.Clock()

    while True:
        if show_main_menu:
            frame_pos = renderer.screen_to_frame(pygame.mouse.get_pos())
            menus.set_mouse(frame_pos if frame_pos is not None else (0, 0))

            action = {}
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
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

            main_menu(renderer.frame, renderer.font, bg,
                      constants['screen_width'], constants['screen_height'])

            if show_load_error_message:
                popup_box(renderer.frame, renderer.font, 'No saved game to load',
                          constants['screen_width'], constants['screen_height'])

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
            result = play_game(player, entities, game_map, message_log, game_state,
                               renderer, constants)
            if result == 'new_game':
                player, entities, game_map, message_log, game_state = get_game_variables(constants)
                game_state = GameStates.PLAYERS_TURN
                show_main_menu = False
            elif result == 'main_menu':
                show_main_menu = True
            else:
                return


if __name__ == '__main__':
    main()
