#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FontRenderer

Renders text with the hand-drawn bitmap font (``alienraid12x12.png``).

The atlas is a 32x8 grid of 12x12 glyphs. Glyph ``c`` lives at cell
``(c % 32, c // 32)`` (row-major, 32 columns) — the same mapping the
original game used through libtcod's ``FONT_LAYOUT_TCOD``.

Only the *preserved* character set is text. These are the glyphs the artist
hand-drew for the interface::

    0-9  !@#$%^&*()_+=-  a-z  A-Z  <>?;:,.[]/'"`~{}  space
    arrows (16 17 18 24 25 26 27 29 30 31)
    checkboxes (224 225)  radio boxes (9 10)

Every other code is treated as a *sprite* (mobs, player, equipment, terrain)
and is rendered procedurally — never through the font.
"""

import os

import pygame

TILE = 12
ATLAS_COLS = 32

# Radio / checkbox / arrow codes that are part of the interface charset.
_SPECIAL_TEXT_CODES = frozenset(
    (9, 10, 16, 17, 18, 24, 25, 26, 27, 29, 30, 31, 224, 225)
)


def is_text_glyph(code):
    """True if ``code`` belongs to the preserved interface character set."""
    if 32 <= code <= 126:  # printable ASCII (the artist's letters/symbols)
        return True
    return code in _SPECIAL_TEXT_CODES


class FontRenderer:
    def __init__(self, font_path='alienraid12x12.png', tile=TILE):
        self.tile = tile
        if not os.path.isfile(font_path):
            raise FileNotFoundError('Bitmap font not found: {0}'.format(font_path))

        atlas = pygame.image.load(font_path).convert_alpha()
        atlas_w, atlas_h = atlas.get_size()
        self.cols = atlas_w // tile

        self._glyphs = {}   # code -> tinted Surface (cached)
        self._atlas = atlas

    def glyph(self, code, color):
        """Return the (cached) tinted glyph surface for ``code`` in ``color``."""
        if not is_text_glyph(code):
            # Not part of the preserved charset: never rendered from the font.
            code = ord('?')
        key = (code, color)
        cached = self._glyphs.get(key)
        if cached is not None:
            return cached

        col = code % self.cols
        row = code // self.cols
        rect = pygame.Rect(col * self.tile, row * self.tile, self.tile, self.tile)
        glyph = self._atlas.subsurface(rect).copy()
        # Tint the white glyph with the requested color, keeping its alpha.
        glyph.fill(color, special_flags=pygame.BLEND_RGB_MULT)
        self._glyphs[key] = glyph
        return glyph

    def draw_char(self, surface, code, x, y, color):
        """Draw a single character at tile position (x, y)."""
        surface.blit(self.glyph(code, color), (x * self.tile, y * self.tile))

    def draw_text(self, surface, text, x, y, color):
        """Draw a string starting at tile position (x, y)."""
        for i, ch in enumerate(str(text)):
            code = ord(ch)
            if not is_text_glyph(code):
                code = ord('?')
            surface.blit(self.glyph(code, color), ((x + i) * self.tile, y * self.tile))
