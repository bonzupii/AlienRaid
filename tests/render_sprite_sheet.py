#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render every procedural sprite into a labeled sprite sheet for visual
analysis, plus a reference sheet of the preserved font charset.

Sprites are shown at 4x (nearest-neighbour) so the pixel art is actually
visible, with the name label drawn beside each cell — never overlapping.

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

from renderer.font_renderer import FontRenderer, is_text_glyph
from renderer.sprites import SpriteLoader, RECIPES
from renderer import palette as P

TILE = 12
SCALE = 4                 # sprite magnification for the sheet
SPRITE_PX = TILE * SCALE  # 48
COLS = 6
LABEL_W_TILES = 20
CELL_W = SPRITE_PX + 2 * TILE + LABEL_W_TILES * TILE
CELL_H = SPRITE_PX + 2 * TILE
PAD = 10

# Representative in-game color for each sprite so the sheet shows them as
# they will appear in the game.
SAMPLE_COLORS = {
    'player': P.PLAYER_GREEN,
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
    sheet_w = PAD * 2 + COLS * CELL_W
    sheet_h = PAD * 2 + 2 * TILE + rows * CELL_H
    sheet = pygame.Surface((sheet_w, sheet_h))
    sheet.fill((24, 24, 24))

    font.draw_text(sheet, 'AlienRaid procedural sprites (4x, labels beside)',
                   PAD // TILE, PAD // TILE, P.WHITE)

    for i, name in enumerate(names):
        col = i % COLS
        row = i // COLS
        cx = PAD + col * CELL_W
        cy = PAD + 2 * TILE + row * CELL_H
        color = SAMPLE_COLORS.get(name, P.KANGA_RED)

        # 4x sprite on a checkerboard so transparency is visible.
        _checkerboard(sheet, cx, cy)
        sprite = loader.get(name, color)
        big = pygame.transform.scale(sprite, (SPRITE_PX, SPRITE_PX))
        sheet.blit(big, (cx, cy))

        # Label clearly to the right of the sprite, vertically centred.
        label_x = (cx + SPRITE_PX + TILE) // TILE
        label_y = (cy + (SPRITE_PX - TILE) // 2) // TILE
        font.draw_text(sheet, name, label_x, label_y, P.LIGHT_GRAY)

    pygame.image.save(sheet, 'sprite_sheet.png')
    print('saved sprite_sheet.png ({0}x{1})'.format(*sheet.get_size()))


def render_charset_sheet():
    """Reference sheet of the preserved font charset (glyph + code label)."""
    font = FontRenderer()
    codes = list(range(32, 127)) + [9, 10, 16, 17, 18, 24, 25, 26, 27, 29, 30, 31, 224, 225]
    cell_w, cell_h = 5 * TILE, 2 * TILE
    ccols = 16
    rows = (len(codes) + ccols - 1) // ccols
    sheet_w = ccols * cell_w + PAD * 2
    sheet_h = PAD * 2 + 2 * TILE + rows * cell_h
    sheet = pygame.Surface((sheet_w, sheet_h))
    sheet.fill((24, 24, 24))

    font.draw_text(sheet, 'Preserved font charset (glyph + code)', PAD // TILE, PAD // TILE, P.WHITE)

    for i, code in enumerate(codes):
        col = i % ccols
        row = i // ccols
        cx = PAD + col * cell_w
        cy = PAD + 2 * TILE + row * cell_h
        if is_text_glyph(code):
            font.draw_char(sheet, code, cx // TILE, cy // TILE, P.WHITE)
        label = str(code)
        if 32 <= code <= 126:
            label += ' ' + chr(code)
        font.draw_text(sheet, label, cx // TILE + 2, cy // TILE + 1, P.LIGHT_GRAY)

    pygame.image.save(sheet, 'charset_sheet.png')
    print('saved charset_sheet.png ({0}x{1})'.format(*sheet.get_size()))


if __name__ == '__main__':
    render_sprite_sheet()
    render_charset_sheet()
