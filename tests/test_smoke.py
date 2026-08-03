#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Headless smoke test of the whole game pipeline (run with nix develop)."""
import os
import sys
import unittest
from random import randint

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

import pygame

pygame.init()

from algorithms.fov import compute_fov
from components.entity import Entity, get_blocking_entities_at_location
from components.fighter import Fighter
from components.game_messages import MessageLog
from components.game_states import GameStates
from components.quest import Quest, SHIP_PARTS
from functions.death_functions import kill_monster, kill_player
from functions.systems import wait_action
from launcher import _handle_take, _collect_ship_part
from loader_functions.initialize_new_game import get_constants, get_game_variables
from map_objects.game_map import GameMap
from renderer.renderer import Renderer


def fresh_game():
    constants = get_constants()
    player, entities, game_map, message_log, game_state = get_game_variables(constants)
    return constants, player, entities, game_map, message_log, game_state


class TestBoot(unittest.TestCase):
    def test_render_every_state(self):
        constants, player, entities, game_map, message_log, game_state = fresh_game()
        renderer = Renderer(constants)
        fov = compute_fov(game_map.block_sight, game_map.width, game_map.height,
                          player.x, player.y, constants['fov_radius'])
        for state in (GameStates.PLAYERS_TURN, GameStates.SHOW_INVENTORY,
                      GameStates.DROP_INVENTORY, GameStates.LEVEL_UP,
                      GameStates.CHARACTER_SCREEN, GameStates.VICTORY,
                      GameStates.PLAYER_DEAD):
            renderer.render(game_map, fov, entities, player, message_log, state, (10, 10))
            pygame.display.flip()
        # Resize the window (as a tiling WM would) and re-render.
        renderer.resize(900, 700)
        renderer.render(game_map, fov, entities, player, message_log,
                        GameStates.PLAYERS_TURN, (10, 10))
        pygame.display.flip()
        tile = renderer.screen_to_tile((450, 350))
        self.assertIsNotNone(tile)
        self.assertGreaterEqual(tile[0], 0)
        renderer.resize(renderer.screen_w, renderer.screen_h)
        renderer.render(game_map, fov, entities, player, message_log,
                        GameStates.PLAYERS_TURN, (10, 10))
        pygame.display.flip()

        pygame.image.save(renderer.screen, '/tmp/alienraid_frame.png')
        # The screen should not be entirely black.
        w, h = renderer.screen.get_size()
        inked = 0
        for yy in range(0, h, 6):
            for xx in range(0, w, 6):
                r, g, b, *_ = renderer.screen.get_at((xx, yy))
                if r + g + b > 24:
                    inked += 1
        self.assertGreater(inked, 200)

    def test_simulated_turns(self):
        constants, player, entities, game_map, message_log, game_state = fresh_game()
        renderer = Renderer(constants)
        fov = compute_fov(game_map.block_sight, game_map.width, game_map.height,
                          player.x, player.y, constants['fov_radius'])
        kills = 0
        player_dead = False

        for _ in range(150):
            dx, dy = randint(-1, 1), randint(-1, 1)
            if dx == 0 and dy == 0:
                continue
            nx, ny = player.x + dx, player.y + dy
            if not game_map.is_blocked(nx, ny):
                target = get_blocking_entities_at_location(entities, nx, ny)
                if target:
                    for r in player.fighter.attack(target):
                        if r.get('dead'):
                            kill_monster(r['dead'])
                            kills += 1
                else:
                    player.move(dx, dy)
                    _collect_ship_part(player, entities, message_log)

            for entity in list(entities):
                if entity.ai:
                    for r in entity.ai.take_turn(player, fov, game_map, entities):
                        dead = r.get('dead')
                        if dead is player:
                            kill_player(player)
                            player_dead = True
                            break
                        elif dead:
                            kill_monster(dead)
                            kills += 1
                    if player_dead:
                        break
            if player_dead:
                break

            fov = compute_fov(game_map.block_sight, game_map.width, game_map.height,
                              player.x, player.y, constants['fov_radius'])
            renderer.render(game_map, fov, entities, player, message_log,
                            GameStates.PLAYERS_TURN, (5, 5))
            pygame.display.flip()

        self.assertTrue(player_dead or kills > 0 or len(entities) > 1)

    def test_wait_action(self):
        constants, player, entities, game_map, message_log, game_state = fresh_game()
        log = MessageLog(32, 66, 6)
        timer = 0
        for _ in range(11):  # up to 55
            timer, state = wait_action(player, log, timer)
            self.assertEqual(state, GameStates.ENEMY_TURN)
        # One more rest reaches 60: now the Dropbear ambushes.
        timer, state = wait_action(player, log, timer)
        self.assertEqual(timer, 60)
        player.fighter.hp = 600
        timer, state = wait_action(player, log, timer)
        self.assertEqual(state, GameStates.ENEMY_TURN)
        self.assertEqual(player.fighter.hp, 100)
        player.fighter.hp = 400
        timer, state = wait_action(player, log, timer)
        self.assertEqual(state, GameStates.PLAYER_DEAD)

    def test_floor_transitions_and_ship(self):
        constants, player, entities, game_map, message_log, game_state = fresh_game()
        down = next(e for e in entities if e.trail and e.trail.direction == 'down')
        player.x, player.y = down.x, down.y
        entities = _handle_take(player, entities, game_map, message_log, constants)
        self.assertEqual(game_map.dungeon_level, 2)

        up = next(e for e in entities if e.trail and e.trail.direction == 'up')
        player.x, player.y = up.x, up.y
        entities = _handle_take(player, entities, game_map, message_log, constants)
        self.assertEqual(game_map.dungeon_level, 1)

        ship = next(e for e in entities if e.ship)
        player.x, player.y = ship.x, ship.y
        entities = _handle_take(player, entities, game_map, message_log, constants)
        self.assertFalse(player.quest.complete)
        for part_id in SHIP_PARTS:
            player.quest.find_part(part_id)
        entities = _handle_take(player, entities, game_map, message_log, constants)
        self.assertTrue(player.quest.complete)

    def test_part_collection(self):
        p = Entity(0, 0, 'player', (15, 77, 0), 'P', blocks=True,
                   fighter=Fighter(1250, 10, 40), quest=Quest())
        entities = [p]
        gm = GameMap(100, 48, dungeon_level=5)
        gm.make_map(60, 3, 10, 100, 48, p, entities)
        log = MessageLog(32, 66, 6)
        part = next(e for e in entities if e.part_id)
        p.x, p.y = part.x, part.y
        _collect_ship_part(p, entities, log)
        self.assertTrue(p.quest.has_part(part.part_id))
        self.assertNotIn(part, entities)


if __name__ == '__main__':
    unittest.main()
