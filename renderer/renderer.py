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
* The window is adaptive: everything is drawn to an internal fixed-resolution
  frame which is then letterbox-scaled onto the actual window, so a tiling
  window manager resizing the window can never break the game's aspect ratio.
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
        self.frame = pygame.Surface((self.screen_w, self.screen_h))
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h),
                                              pygame.RESIZABLE)
        pygame.display.set_caption(constants['window_title'])
        self.font = FontRenderer()
        self.sprites = SpriteLoader()

        self.terrain_cache = None
        self._dark_wall = None
        self._dark_floor = None
        self._light_wall = None
        self._light_floor = None
        self._cached_level = None
        self.fullscreen = False
        self._scale = 1.0
        self._offset = (0, 0)

    # ------------------------------------------------------------- tiles
    @staticmethod
    def _make_wall_tile(base):
        s = pygame.Surface((TILE, TILE))
        s.fill(base)
        dark = C.shade(base, 0.7)
        bright = C.shade(base, 1.3)
        pygame.draw.rect(s, dark, (0, 0, TILE, 1))
        pygame.draw.rect(s, dark, (0, 0, 1, TILE))
        pygame.draw.rect(s, dark, (6, 0, 1, TILE))
        pygame.draw.rect(s, dark, (0, 6, TILE, 1))
        pygame.draw.rect(s, dark, (3, 6, 1, TILE))
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

    # ------------------------------------------------------------- window
    def present(self):
        """Letterbox-scale the internal frame onto the actual window."""
        fw, fh = self.frame.get_size()
        sw, sh = self.screen.get_size()
        scale = min(sw / fw, sh / fh)
        tw = max(1, int(fw * scale))
        th = max(1, int(fh * scale))
        if (tw, th) == (fw, fh):
            self.screen.blit(self.frame, (0, 0))
            self._offset = (0, 0)
        else:
            scaled = pygame.transform.smoothscale(self.frame, (tw, th))
            self.screen.fill((0, 0, 0))
            self._offset = ((sw - tw) // 2, (sh - th) // 2)
            self.screen.blit(scaled, self._offset)
        self._scale = tw / fw

    def resize(self, width, height):
        self.screen = pygame.display.set_mode((max(1, width), max(1, height)),
                                              pygame.RESIZABLE)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = (pygame.FULLSCREEN | pygame.RESIZABLE) if self.fullscreen else pygame.RESIZABLE
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h), flags)

    def screen_to_tile(self, pos):
        """Map a window pixel position to map tile coords, or None if outside
        the game frame (e.g. on a letterbox bar)."""
        mx, my = pos
        ox, oy = self._offset
        ix = (mx - ox) / self._scale
        iy = (my - oy) / self._scale
        tx = int(ix // TILE)
        ty = int(iy // TILE)
        if 0 <= tx < self.constants['map_width'] and 0 <= ty < self.constants['map_height']:
            return (tx, ty)
        return None

    # ------------------------------------------------------------- frame
    def render(self, game_map, fov, entities, player, message_log, game_state, mouse_tile):
        self._sync_level(game_map)
        width, height = game_map.width, game_map.height
        map_surf = pygame.Surface((width * TILE, height * TILE))

        map_surf.blit(self.terrain_cache, (0, 0))

        for y in range(height):
            base = y * width
            for x in range(width):
                if fov[base + x]:
                    if not game_map.explored[base + x]:
                        game_map.explored[base + x] = 1
                        self._stamp_dark(game_map, x, y)
                    light = self._light_wall if game_map.is_wall(x, y) else self._light_floor
                    map_surf.blit(light, (x * TILE, y * TILE))

        model = build_render_model(entities, fov, game_map)
        model.sort(key=lambda item: item[5])
        for (x, y, kind, sprite_id, color, _layer) in model:
            if kind == 'text':
                self.font.draw_char(map_surf, sprite_id, x, y, color)
            else:
                map_surf.blit(self.sprites.get(sprite_id, color),
                              (x * TILE, y * TILE))

        self.frame.blit(map_surf, (0, 0))
        self._draw_panel(game_map, entities, player, message_log, fov, mouse_tile)

        sw = self.constants['screen_width']
        sh = self.constants['screen_height']
        if game_state == GameStates.SHOW_INVENTORY:
            menus.inventory_menu(self.frame, self.font,
                                 'Press the key next to an item to use it, or Esc to cancel.\n',
                                 player, 50, sw, sh)
        elif game_state == GameStates.DROP_INVENTORY:
            menus.inventory_menu(self.frame, self.font,
                                 'Press the key next to an item to drop it, or Esc to cancel.\n',
                                 player, 50, sw, sh)
        elif game_state == GameStates.LEVEL_UP:
            menus.level_up_menu(self.frame, self.font, 'Level up! Choose a stat to raise:',
                                player, 40, sw, sh)
        elif game_state == GameStates.CHARACTER_SCREEN:
            menus.character_screen(self.frame, self.font, player, 30, 12, sw, sh)
        elif game_state == GameStates.VICTORY:
            menus.victory_screen(self.frame, self.font, player, game_map, sw, sh)
        elif game_state == GameStates.PLAYER_DEAD:
            menus.death_overlay(self.frame, self.font, sw, sh)

        self.present()

    # ------------------------------------------------------------- panel
    def _draw_panel(self, game_map, entities, player, message_log, fov, mouse_tile):
        panel_y = self.constants['panel_y']          # in tiles
        frame = self.frame

        pygame.draw.rect(frame, (0, 0, 0),
                         (0, panel_y * TILE, self.screen_w, self.screen_h - panel_y * TILE))

        names = get_names_under_mouse(mouse_tile, entities, fov, game_map)
        self.font.draw_text(frame, names, 1, panel_y, C.LIGHT_GRAY)

        hp = player.fighter.hp
        max_hp = max(1, player.fighter.max_hp)
        bar_width = self.constants['bar_width']
        fill = int(bar_width * hp / max_hp)
        pygame.draw.rect(frame, C.DARKER_RED, (1 * TILE, (panel_y + 1) * TILE, bar_width * TILE, TILE))
        if fill > 0:
            pygame.draw.rect(frame, C.LIGHT_RED, (1 * TILE, (panel_y + 1) * TILE, fill * TILE, TILE))
        self.font.draw_text(frame, 'HP: {0}/{1}'.format(hp, max_hp), 2, panel_y + 1,
                            C.WHITE, vertical_center=True)

        self.font.draw_text(frame, 'Dungeon level: {0}'.format(game_map.dungeon_level),
                            1, panel_y + 3, C.LIGHT_GRAY)
        self.font.draw_text(frame, 'Ship parts: {0}/{1}'.format(
            player.quest.found_count, player.quest.parts_total), 1, panel_y + 4, C.GOLD)

        y = panel_y + 1
        for message in message_log.message:
            self.font.draw_text(frame, message.text, message_log.x, y, message.color)
            y += 1
