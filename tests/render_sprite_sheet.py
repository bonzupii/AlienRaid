#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render every procedural sprite into a labeled sprite sheet for visual
analysis, plus a section showing the map/environment tiles (wall / floor /
brush variants, dark and light), plus a reference sheet of the preserved
font charset.

Sprites are shown at 4x (nearest-neighbour) so the 16x16 pixel art is
actually visible, with the name label drawn beside each cell -- never
overlapping.

Run from the project root (inside the dev shell):
    nix develop -c python tests/render_sprite_sheet.py

Outputs ``sprite_sheet.png`` and ``charset_sheet.png`` in the project root.
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

import pygame

pygame.init()

from renderer.font_renderer import FontRenderer
from renderer.sprites import SpriteLoader, RECIPES, TILE as SPRITE_TILE
from renderer.renderer import Renderer
from loader_functions.initialize_new_game import biome_for_level
from renderer import palette as P

UI_TILE = 16
SCALE = 4                       # sprite magnification for the sheet
SPRITE_PX = SPRITE_TILE * SCALE  # 64
COLS = 6
LABEL_W_TILES = 20
CELL_W = SPRITE_PX + 2 * UI_TILE + LABEL_W_TILES * UI_TILE
CELL_H = SPRITE_PX + 2 * UI_TILE
PAD = 10

# Representative in-game color for each sprite so the sheet shows them as
# they will appear in the game.
SAMPLE_COLORS = {
    'player': P.PLAYER_GREEN,
    'player_sunglasses': P.PLAYER_GREEN,
    'ute': (140, 90, 60),
    'kanga': P.KANGA_RED,
    'joey': P.KANGA_RED,
    'wallaby': (205, 133, 63),
    'wallaroo': (139, 90, 43),
    'tree_kanga': (160, 82, 45),
    'dingo': P.DINGO_BROWN,
    'goanna': P.GOANNA_GREEN,
    'killer_bee': P.YELLOW,
    'dropbear': P.DROPBEAR_GREY,
    'taipan': (139, 125, 60),
    'emu': (110, 90, 60),
    'wombat': (90, 90, 90),
    'magpie': (20, 20, 20),
    'cassowary': (40, 60, 120),
    'crocodile': (30, 80, 40),
    'echidna': (120, 90, 60),
    'funnel_web': (40, 30, 30),
    'corpse': P.DARK_RED,
    'trail_down': (180, 120, 40),
    'trail_up': (120, 160, 60),
    'ship': P.SILVER,
    'part': P.GOLD,
    'agent_j_cameo': (20, 20, 20),
    'npc_aecd': (140, 120, 80),
    'npc_swaggie': (160, 90, 60),
    'icon_cross': (255, 30, 0),
    'icon_bottle': (40, 30, 0),
    'icon_grenade': P.CYAN,
    'icon_gun': (180, 180, 180),
    'icon_bolt': P.YELLOW,
    'icon_tentacle': P.PURPLE,
    'icon_shield': P.CYAN,
    'icon_twig': (53, 38, 0),
    'icon_hat': (20, 38, 0),
    'icon_neck': P.SILVER,
    'icon_vest': (30, 30, 30),
    'icon_boomerang': (160, 120, 40),
    'icon_ration': (120, 160, 60),
    'icon_tea': (60, 120, 60),
    'icon_star': P.GOLD,
    'icon_tube': (120, 80, 40),
    'icon_neuralyzer': P.SILVER,
    'icon_datalog': (60, 60, 70),
}


def _checkerboard(surface, x, y, size=SPRITE_PX, step=4):
    """Light checkerboard behind a sprite so transparency is visible."""
    for yy in range(0, size, step):
        for xx in range(0, size, step):
            if ((xx // step) + (yy // step)) % 2 == 0:
                pygame.draw.rect(surface, (58, 58, 58), (x + xx, y + yy, step, step))


def render_sprite_sheet():
    font = FontRenderer()
    loader = SpriteLoader()
    names = sorted(RECIPES)
    rows = (len(names) + COLS - 1) // COLS
    sprite_area_h = PAD * 2 + 2 * UI_TILE + rows * CELL_H
    env_area_h = 3 * (4 * UI_TILE + SPRITE_PX + UI_TILE) + 3 * UI_TILE
    sheet_w = PAD * 2 + COLS * CELL_W
    sheet_h = sprite_area_h + env_area_h
    sheet = pygame.Surface((sheet_w, sheet_h))
    sheet.fill((24, 24, 24))
    font.draw_text(sheet, 'AlienRaid procedural sprites (16x16 at 4x, labels beside)',
                   PAD // UI_TILE, PAD // UI_TILE, P.WHITE)
    for i, name in enumerate(names):
        col = i % COLS
        row = i // COLS
        cx = PAD + col * CELL_W
        cy = PAD + 2 * UI_TILE + row * CELL_H
        color = SAMPLE_COLORS.get(name, P.KANGA_RED)
        _checkerboard(sheet, cx, cy)
        sprite = loader.get(name, color)
        big = pygame.transform.scale(sprite, (SPRITE_PX, SPRITE_PX))
        sheet.blit(big, (cx, cy))
        label_x = (cx + SPRITE_PX + UI_TILE) // UI_TILE
        label_y = (cy + (SPRITE_PX - UI_TILE) // 2) // UI_TILE
        font.draw_text(sheet, name, label_x, label_y, P.LIGHT_GRAY)

    _render_env_tiles(sheet, font, sprite_area_h)
    pygame.image.save(sheet, 'sprite_sheet.png')
    print('saved sprite_sheet.png ({0}x{1})'.format(*sheet.get_size()))


def _render_env_tiles(sheet, font, y0):
    """Map/environment tiles: wall/floor/brush variants, dark and light,
    each shown at 4x with its variant label underneath."""
    colors = biome_for_level(1)
    groups = (
        ('wall', Renderer._make_wall_tiles(colors['dark_wall']),
                 Renderer._make_wall_tiles(colors['light_wall'])),
        ('floor', Renderer._make_floor_tiles(colors['dark_ground']),
                  Renderer._make_floor_tiles(colors['light_ground'])),
        ('brush', Renderer._make_floor_tiles(colors['dark_brush']),
                  Renderer._make_floor_tiles(colors['light_brush'])),
    )
    cell = SPRITE_PX + 2 * UI_TILE
    x = PAD
    y = y0 + 2 * UI_TILE
    font.draw_text(sheet, 'Environment tiles (16x16 at 4x):',
                   x // UI_TILE, (y0 // UI_TILE), P.LIGHT_GREEN)
    y += UI_TILE
    for name, dark_variants, light_variants in groups:
        font.draw_text(sheet, name, x // UI_TILE, y // UI_TILE, P.LIGHT_GRAY)
        row_y = y + 2 * UI_TILE
        cx = x + 2 * UI_TILE
        for label, variants in (('dark', dark_variants), ('light', light_variants)):
            for v, tile in enumerate(variants):
                big = pygame.transform.scale(tile, (SPRITE_PX, SPRITE_PX))
                sheet.blit(big, (cx, row_y))
                font.draw_text(sheet, '{0} v{1}'.format(label, v),
                               cx // UI_TILE, (row_y + SPRITE_PX) // UI_TILE + 1,
                               P.LIGHT_GRAY)
                cx += cell
            cx += 5 * UI_TILE
        y = row_y + SPRITE_PX + 3 * UI_TILE


def render_charset_sheet():
    """Reference sheet of the actual charset: every char in the labeled map
    (charset_map.json) with its atlas cell coordinates."""
    font = FontRenderer()
    chars = sorted((ch for ch in font.char_map if len(ch) == 1),
                   key=lambda ch: (font.char_map[ch][1], font.char_map[ch][0]))
    cell_w, cell_h = 6 * UI_TILE, 2 * UI_TILE
    ccols = 16
    rows = (len(chars) + ccols - 1) // ccols
    sheet_w = ccols * cell_w + PAD * 2
    sheet_h = PAD * 2 + 2 * UI_TILE + rows * cell_h
    sheet = pygame.Surface((sheet_w, sheet_h))
    sheet.fill((24, 24, 24))
    font.draw_text(sheet, 'Labeled charset (char + atlas cell)',
                   PAD // UI_TILE, PAD // UI_TILE, P.WHITE)
    for i, ch in enumerate(chars):
        col = i % ccols
        row = i // ccols
        cx = PAD + col * cell_w
        cy = PAD + 2 * UI_TILE + row * cell_h
        if ch != ' ':
            font.draw_char(sheet, ch, cx // UI_TILE, cy // UI_TILE, P.WHITE)
        col_, row_ = font.char_map[ch]
        label = repr(ch) + ' {0},{1}'.format(col_, row_)
        font.draw_text(sheet, label, cx // UI_TILE + 2, cy // UI_TILE + 1, P.LIGHT_GRAY)
    pygame.image.save(sheet, 'charset_sheet.png')
    print('saved charset_sheet.png ({0}x{1})'.format(*sheet.get_size()))


if __name__ == '__main__':
    render_sprite_sheet()
    render_charset_sheet()
