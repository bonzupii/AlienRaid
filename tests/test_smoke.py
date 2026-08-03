#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Headless smoke test of the whole game pipeline (run with: nix develop).

These tests assert *content*, not just "not a black screen": the player
sprite must be painted at the player's tile, the HP bar must be drawn, the
message log must render text, and the rendered picture must change as the
game runs.
"""
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
from components import menus
from components.entity import Entity, get_blocking_entities_at_location
from components.fighter import Fighter
from components.game_messages import MessageLog
from components.game_states import GameStates
from components.quest import Quest, SHIP_PARTS
from functions.death_functions import kill_monster, kill_player
from functions.systems import wait_action
from launcher import _handle_take, _collect_ship_part
from loader_functions.initialize_new_game import get_constants, get_game_variables
from loader_functions.items import create_item
from loader_functions.monsters import create_monster
from map_objects.game_map import GameMap
from renderer import palette as C
from renderer.renderer import Renderer, build_render_model, TILE


def fresh_game():
    constants = get_constants()
    player, entities, game_map, message_log, game_state = get_game_variables(constants)
    return constants, player, entities, game_map, message_log, game_state


def _player_tuple(player):
    """The exact render-model tuple the renderer must produce for the player."""
    return (player.x, player.y, 'sprite', player.sprite_id,
            player.color, player.render_order.value)


def _region_ink(surf, rect, step=2):
    x0, y0, w, h = rect
    count = 0
    for yy in range(y0, y0 + h, step):
        for xx in range(x0, x0 + w, step):
            r, g, b, *_ = surf.get_at((xx, yy))
            if r + g + b > 24:
                count += 1
    return count


def _region_has_color(surf, rect, color, tol=70):
    x0, y0, w, h = rect
    for yy in range(y0, y0 + h):
        for xx in range(x0, x0 + w):
            r, g, b, *_ = surf.get_at((xx, yy))
            if (abs(r - color[0]) <= tol and abs(g - color[1]) <= tol
                    and abs(b - color[2]) <= tol):
                return True
    return False


def _frame_sig(surf, step=12, max_y=None):
    """A cheap deterministic fingerprint of a rendered frame.

    Pass ``max_y`` (e.g. the map region only) to exclude the panel, so the
    fingerprint changes only when the map itself changes.
    """
    w, h = surf.get_size()
    if max_y is not None:
        h = min(h, max_y)
    data = bytearray()
    for yy in range(0, h, step):
        for xx in range(0, w, step):
            r, g, b, *_ = surf.get_at((xx, yy))
            data += bytes((r, g, b))
    return hash(bytes(data))


class TestBoot(unittest.TestCase):
    def test_main_menu_renders(self):
        """Regression guard: the main menu must render with the real
        menu_background.png. A paletted (8-bit) background used to crash
        smoothscale with 'Only 24-bit or 32-bit surfaces can be smoothly
        scaled'."""
        constants, player, entities, game_map, message_log, game_state = fresh_game()
        renderer = Renderer(constants)
        if not os.path.isfile('menu_background.png'):
            self.skipTest('menu_background.png missing')
        bg = pygame.image.load('menu_background.png')
        self.assertGreaterEqual(
            bg.get_bitsize(), 24,
            'menu background must be a 24/32-bit surface (paletted 8-bit crashes smoothscale)')
        menus.main_menu(renderer.frame, renderer.font, bg,
                        constants['screen_width'], constants['screen_height'])
        renderer.present()
        pygame.display.flip()
        w, h = renderer.frame.get_size()
        self.assertGreater(_region_ink(renderer.frame, (0, 0, w, h), step=6), 100,
                           'main menu rendered nothing')

    def test_render_every_state(self):
        constants, player, entities, game_map, message_log, game_state = fresh_game()
        renderer = Renderer(constants)
        fov = compute_fov(game_map.block_sight, game_map.width, game_map.height,
                          player.x, player.y, constants['fov_radius'])

        renderer.render(game_map, fov, entities, player, message_log,
                        GameStates.PLAYERS_TURN, (10, 10))
        pygame.display.flip()

        # Content assertion: the player sprite is in the render model at the
        # player's tile, and is actually painted on the frame.
        self.assertIn(_player_tuple(player), build_render_model(entities, fov, game_map))
        self.assertTrue(
            _region_has_color(renderer.frame,
                              (player.x * TILE, player.y * TILE, TILE, TILE),
                              player.color),
            'player sprite not painted at its tile')

        # Content assertion: the HP bar is drawn (the player starts with hp).
        panel_y = constants['panel_y']
        self.assertTrue(
            _region_has_color(renderer.frame,
                              (TILE, (panel_y + 1) * TILE,
                               constants['bar_width'] * TILE, TILE),
                              C.LIGHT_RED),
            'HP bar not painted in the panel')

        # Content assertion: the welcome message renders as text in the log.
        log_x = constants['message_x'] * TILE
        log_y = (panel_y + 1) * TILE
        self.assertGreater(
            _region_ink(renderer.frame, (log_x, log_y, 40 * TILE, TILE)),
            10, 'message log text not rendered')

        # Every other state must render without crashing.
        for state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY,
                      GameStates.LEVEL_UP, GameStates.CHARACTER_SCREEN,
                      GameStates.VICTORY, GameStates.PLAYER_DEAD):
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
        # Sanity check on the scaled window surface: not entirely black.
        w, h = renderer.screen.get_size()
        self.assertGreater(_region_ink(renderer.screen, (0, 0, w, h), step=6), 200)

    def test_simulated_turns(self):
        constants, player, entities, game_map, message_log, game_state = fresh_game()
        renderer = Renderer(constants)
        fov = compute_fov(game_map.block_sight, game_map.width, game_map.height,
                          player.x, player.y, constants['fov_radius'])
        start_pos = (player.x, player.y)
        kills = 0
        player_dead = False
        frame_signatures = set()

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
            frame_signatures.add(_frame_sig(renderer.frame,
                                            max_y=game_map.height * TILE))

        # Content assertion: the *map* changed as the world ran — the game
        # is drawing moving entities and changing FOV, not a static (or
        # black) map. Only the map region is fingerprinted, so a shrinking
        # HP bar in the panel cannot satisfy this on its own.
        self.assertGreaterEqual(len(frame_signatures), 2,
                                'map never changed across 150 turns')

        # Something real must have happened: the player moved, fought, or died.
        self.assertTrue(
            (player.x, player.y) != start_pos or kills > 0 or player_dead,
            'no movement, no combat and no death over 150 turns')

        # If the player is still alive, it is still drawn at its tile.
        if not player_dead:
            fov = compute_fov(game_map.block_sight, game_map.width, game_map.height,
                              player.x, player.y, constants['fov_radius'])
            self.assertIn(_player_tuple(player),
                          build_render_model(entities, fov, game_map))

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

    def test_deterministic_combat(self):
        constants, player, entities, game_map, message_log, game_state = fresh_game()
        monster = create_monster('joey', 1, player.x + 1, player.y)
        entities.append(monster)
        hp_before = monster.fighter.hp

        # Player power (40 base + 40 from starting tentacle gear) always
        # exceeds a level-1 joey's defense, so this attack must deal damage.
        results = player.fighter.attack(monster)
        self.assertLess(monster.fighter.hp, hp_before, 'attack dealt no damage')
        self.assertTrue(any('message' in r for r in results),
                        'attack produced no message')

        # Beat it to death; the monster must become a non-blocking corpse.
        while monster.fighter.hp > 0:
            player.fighter.attack(monster)
        kill_monster(monster)
        self.assertFalse(monster.blocks)
        self.assertIsNone(monster.fighter)
        self.assertEqual(monster.sprite_id, 'corpse')

    def test_use_heal_item(self):
        """Regression: using a med kit through the inventory (exactly as the
        launcher calls it, with entities/fov_map/game_map kwargs) must heal,
        not crash with 'heal() got an unexpected keyword argument
        entities'."""
        constants, player, entities, game_map, message_log, game_state = fresh_game()
        player.fighter.hp = player.fighter.max_hp // 2
        hp_before = player.fighter.hp
        medkit = create_item('lesser_med_kit', 1, player.x, player.y)
        player.inventory.add_item(medkit)
        fov_map = compute_fov(game_map.block_sight, game_map.width, game_map.height,
                              player.x, player.y, constants['fov_radius'])
        results = player.inventory.use(medkit, entities=entities,
                                       fov_map=fov_map, game_map=game_map)
        self.assertGreater(player.fighter.hp, hp_before, 'med kit did not heal')
        self.assertTrue(any(r.get('consumed') for r in results),
                        'med kit was not consumed')
        self.assertNotIn(medkit, player.inventory.items,
                         'consumed med kit still in inventory')

    def test_echidna_thorns(self):
        """Hitting an echidna pricks the attacker (quill counter-damage)."""
        constants, player, entities, game_map, message_log, game_state = fresh_game()
        echidna = create_monster('echidna', 6, player.x + 1, player.y)
        entities.append(echidna)
        thorns = echidna.fighter.thorns
        self.assertGreater(thorns, 0, 'echidna should have quill thorns')
        player.fighter.base_power = 500  # guaranteed to hurt it, immune to starter-gear changes
        hp_before = player.fighter.hp
        player.fighter.attack(echidna)
        self.assertLess(player.fighter.hp, hp_before,
                        'echidna quills did not prick the attacker')
        self.assertEqual(player.fighter.hp, hp_before - thorns)

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
