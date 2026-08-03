#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Renderer: the pygame drawing pipeline.

* The static *explored* terrain is pre-rendered onto a cached surface once;
  each frame we blit that cache, then overlay only the FOV-lit tiles and the
  visible dynamic entities.
* ``build_render_model`` returns a flat list of tuples
  ``(x, y, type, sprite_id_or_char, color, layer)`` — no dicts per entity.
* The font is used exclusively for the interface (panel/menus); every map
  entity is a procedural sprite.
"""

import pygame

from components.game_states import GameStates
from components import menus
from functions.render_order import RenderOrder  # noqa: F401
from functions.render_functions import get_names_under_mouse
from renderer.font_renderer import FontRenderer
from renderer.sprites import SpriteLoader
from renderer import palette as C

TILE = 12


def build_render_model(entities, fov, game_map):
    """Flat list of (x, y, type, sprite_id_or_char, color, layer) tuples."""
    model = []
    width = game_map.width
    for entity in entities:
        if not (0 <= entity.x < width and 0 <= entity.y < game_map.height):
            continue
        in_fov = fov[entity.y * width + entity.x] != 0
        on_explored = entity.trail or entity.ship or entity.part_id
        if not in_fov and not (on_explored and game_map.explored[entity.y * width + entity.x]):
            continue
        model.append((entity.x, entity.y, 'sprite', entity.sprite_id,
                      entity.color, entity.render_order.value))
    return model


class Renderer:
    def __init__(self, constants):
        self.constants = constants
        self.tile = TILE
        self.screen_w = constants['screen_width'] * TILE
        self.screen_h = constants['screen_height'] * TILE
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption(constants['window_title'])
        self.font = FontRenderer()
        self.sprites = SpriteLoader()

        self.terrain_cache = None
        self.map_surface = pygame.Surface(
            (constants['map_width'] * TILE, constants['map_height'] * TILE))
        self._dark_wall = None
        self._dark_floor = None
        self._light_wall = None
        self._light_floor = None
        self._cached_level = None
        self.fullscreen = False

    # ------------------------------------------------------------- tiles
    @staticmethod
    def _make_wall_tile(base):
        s = pygame.Surface((TILE, TILE))
        s.fill(base)
        dark = C.shade(base, 0.7)
        bright = C.shade(base, 1.3)
        # brick mortar
        pygame.draw.rect(s, dark, (0, 0, TILE, 1))
        pygame.draw.rect(s, dark, (0, 0, 1, TILE))
        pygame.draw.rect(s, dark, (6, 0, 1, TILE))
        pygame.draw.rect(s, dark, (0, 6, TILE, 1))
        pygame.draw.rect(s, dark, (3, 6, 1, TILE))
        # highlights
        pygame.draw.rect(s, bright, (1, 1, 2, 2))
        pygame.draw.rect(s, bright, (7, 7, 2, 1))
        return s

    @staticmethod
    def _make_floor_tile(base):
        s = pygame.Surface((TILE, TILE))
        s.fill(base)
        dark = C.shade(base, 0.85)
        bright = C.shade(base, 1.2)
        pygame.draw.rect(s, dark, (2, 2, 1, 1))
        pygame.draw.rect(s, dark, (8, 5, 1, 1))
        pygame.draw.rect(s, dark, (5, 9, 1, 1))
        pygame.draw.rect(s, bright, (6, 2, 1, 1))
        pygame.draw.rect(s, bright, (9, 8, 1, 1))
        return s

    # ------------------------------------------------------------- terrain
    def rebuild_terrain(self, game_map):
        colors = self.constants['colors']
        self.terrain_cache = pygame.Surface(
            (game_map.width * TILE, game_map.height * TILE))
        self.terrain_cache.fill((0, 0, 0))
        self._dark_wall = self._make_wall_tile(colors['dark_wall'])
        self._dark_floor = self._make_floor_tile(colors['dark_ground'])
        self._light_wall = self._make_wall_tile(colors['light_wall'])
        self._light_floor = self._make_floor_tile(colors['light_ground'])
        self._cached_level = game_map.dungeon_level
        # Stamp already-explored tiles (e.g. after loading a save).
        width, height = game_map.width, game_map.height
        for y in range(height):
            base = y * width
            for x in range(width):
                if game_map.explored[base + x]:
                    self._stamp_dark(game_map, x, y)

    def _stamp_dark(self, game_map, x, y):
        tile = self._dark_wall if game_map.is_wall(x, y) else self._dark_floor
        self.terrain_cache.blit(tile, (x * TILE, y * TILE))

    def _sync_level(self, game_map):
        if self.terrain_cache is None or self._cached_level != game_map.dungeon_level:
            self.rebuild_terrain(game_map)

    # ------------------------------------------------------------- frame
    def render(self, game_map, fov, entities, player, message_log, game_state, mouse_tile):
        self._sync_level(game_map)
        width, height = game_map.width, game_map.height
        map_surf = self.map_surface

        map_surf.blit(self.terrain_cache, (0, 0))

        # FOV-lit tiles: mark explored, stamp dark into the cache for later,
        # and overlay the light version right now.
        for y in range(height):
            base = y * width
            for x in range(width):
                if fov[base + x]:
                    if not game_map.explored[base + x]:
                        game_map.explored[base + x] = 1
                        self._stamp_dark(game_map, x, y)
                    light = self._light_wall if game_map.is_wall(x, y) else self._light_floor
                    map_surf.blit(light, (x * TILE, y * TILE))

        # Dynamic entities through the flat render model.
        model = build_render_model(entities, fov, game_map)
        model.sort(key=lambda item: item[5])
        for (x, y, kind, sprite_id, color, _layer) in model:
            if kind == 'text':
                self.font.draw_char(map_surf, sprite_id, x, y, color)
            else:
                map_surf.blit(self.sprites.get(sprite_id, color),
                              (x * TILE, y * TILE))

        self.screen.blit(map_surf, (0, 0))
        self._draw_panel(game_map, entities, player, message_log, fov, mouse_tile)

        if game_state == GameStates.SHOW_INVENTORY:
            menus.inventory_menu(self.screen, self.font,
                                 'Press the key next to an item to use it, or Esc to cancel.\n',
                                 player, 50, self.constants['screen_width'], self.constants['screen_height'])
        elif game_state == GameStates.DROP_INVENTORY:
            menus.inventory_menu(self.screen, self.font,
                                 'Press the key next to an item to drop it, or Esc to cancel.\n',
                                 player, 50, self.constants['screen_width'], self.constants['screen_height'])
        elif game_state == GameStates.LEVEL_UP:
            menus.level_up_menu(self.screen, self.font, 'Level up! Choose a stat to raise:',
                                player, 40, self.constants['screen_width'], self.constants['screen_height'])
        elif game_state == GameStates.CHARACTER_SCREEN:
            menus.character_screen(self.screen, self.font, player, 30, 12,
                                   self.constants['screen_width'], self.constants['screen_height'])
        elif game_state == GameStates.VICTORY:
            menus.victory_screen(self.screen, self.font, player, game_map,
                                 self.constants['screen_width'], self.constants['screen_height'])
        elif game_state == GameStates.PLAYER_DEAD:
            menus.death_overlay(self.screen, self.font,
                                self.constants['screen_width'], self.constants['screen_height'])

    # ------------------------------------------------------------- panel
    def _draw_panel(self, game_map, entities, player, message_log, fov, mouse_tile):
        sw = self.screen_w
        panel_y = self.constants['panel_y']          # in tiles
        screen = self.screen

        pygame.draw.rect(screen, (0, 0, 0), (0, panel_y * TILE, sw, self.screen_h - panel_y * TILE))

        # Mouse-over names
        names = get_names_under_mouse(mouse_tile, entities, fov, game_map)
        self.font.draw_text(screen, names, 1, panel_y, C.LIGHT_GRAY)

        # HP bar
        hp = player.fighter.hp
        max_hp = max(1, player.fighter.max_hp)
        bar_width = self.constants['bar_width']
        fill = int(bar_width * hp / max_hp)
        pygame.draw.rect(screen, C.DARKER_RED, (1 * TILE, (panel_y + 1) * TILE, bar_width * TILE, TILE))
        if fill > 0:
            pygame.draw.rect(screen, C.LIGHT_RED, (1 * TILE, (panel_y + 1) * TILE, fill * TILE, TILE))
        self.font.draw_text(screen, 'HP: {0}/{1}'.format(hp, max_hp), 2, panel_y + 1, C.WHITE)

        # Dungeon level + quest status
        self.font.draw_text(screen, 'Dungeon level: {0}'.format(game_map.dungeon_level),
                            1, panel_y + 3, C.LIGHT_GRAY)
        self.font.draw_text(screen, 'Ship parts: {0}/{1}'.format(
            player.quest.found_count, player.quest.parts_total), 1, panel_y + 4, C.GOLD)

        # Messages
        y = panel_y + 1
        for message in message_log.message:
            self.font.draw_text(screen, message.text, message_log.x, y, message.color)
            y += 1

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h), flags)
