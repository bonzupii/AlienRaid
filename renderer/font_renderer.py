#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FontRenderer

Renders text with the hand-drawn bitmap font (``alienraid12x12.png``).

The atlas is a 32x8 grid of 12x12 cells, but the cells are NOT laid out in
ASCII order — the artist hand-placed every glyph. ``charset_map.json`` (the
output of ``tools/identify_charset.py``) is the ground truth: it maps each
character to its atlas cell ``(col, row)``. This renderer looks characters
up in that map instead of assuming ``code % 32, code // 32``.

Only characters present in the map are text. Anything else (a mob code, an
unmapped character) falls back to ``?`` — never to a random glyph.
"""

import json
import os

import pygame

TILE = 12
DEFAULT_MAP = 'charset_map.json'

_CHAR_MAP_CACHE = None
_ATLAS_CACHE = {}


def _load_atlas(font_path):
    """Load the bitmap font once and convert its opaque black background to
    transparency (brightness-to-alpha, the same conversion
    ``tools/identify_charset.py`` applies). Without this every glyph blits as
    a black box — invisible on black panels but visible over coloured UI
    such as the HP bar. Anti-aliased edges keep a smooth alpha falloff."""
    atlas = _ATLAS_CACHE.get(font_path)
    if atlas is None:
        if pygame.display.get_surface() is None:
            # A display must exist for convert_alpha(); headless runs get a
            # 1x1 dummy window (SDL_VIDEODRIVER=dummy).
            pygame.display.set_mode((1, 1))
        atlas = pygame.image.load(font_path).convert_alpha()
        for y in range(atlas.get_height()):
            for x in range(atlas.get_width()):
                r, g, b, _ = atlas.get_at((x, y))
                atlas.set_at((x, y), (r, g, b, max(r, g, b)))
        _ATLAS_CACHE[font_path] = atlas
    return atlas


def get_char_map(path=DEFAULT_MAP):
    """char -> (col, row) from the labeled charset map, plus the blank
    atlas cell (0,0) as space. Loaded once and shared by both
    ``is_text_glyph`` and every ``FontRenderer`` so the two can never
    disagree about the layout."""
    global _CHAR_MAP_CACHE
    if _CHAR_MAP_CACHE is None:
        with open(path) as f:
            data = json.load(f)
        char_map = {ch: (col, row) for ch, (col, row) in data['char_map'].items()}
        if ' ' not in char_map:
            # Cell (0,0) is the blank/space cell in this font.
            char_map[' '] = (0, 0)
        _CHAR_MAP_CACHE = char_map
    return _CHAR_MAP_CACHE


def is_text_glyph(code):
    """True if the character (int code or str) is in the labeled charset."""
    ch = chr(code) if isinstance(code, int) else code
    return ch in get_char_map()


class FontRenderer:
    def __init__(self, font_path='alienraid12x12.png', map_path=DEFAULT_MAP,
                 tile=TILE):
        self.tile = tile
        if not os.path.isfile(font_path):
            raise FileNotFoundError('Bitmap font not found: {0}'.format(font_path))
        if not os.path.isfile(map_path):
            raise FileNotFoundError(
                'Charset map not found: {0}. Generate it with '
                'tools/identify_charset.py.'.format(map_path))

        atlas = _load_atlas(font_path)
        self.cols = atlas.get_width() // tile
        self.char_map = get_char_map(map_path)
        self._glyphs = {}          # (char, color) -> tinted Surface (cached)
        self._ink_rows_cache = {}  # char -> (min_y, max_y) ink rows, or None
        self._atlas = atlas

    def cell_for(self, ch):
        """Atlas cell (col, row) for a character (or str); '?' if unknown."""
        if isinstance(ch, int):
            ch = chr(ch)
        if ch not in self.char_map:
            ch = '?'
        col, row = self.char_map[ch]
        return (col, row)

    def glyph(self, code, color):
        """Return the (cached) tinted glyph surface for ``code`` in ``color``."""
        ch = chr(code) if isinstance(code, int) else code
        if ch not in self.char_map:
            # Not in the labeled charset: never rendered from the font.
            ch = '?'
        key = (ch, color)
        cached = self._glyphs.get(key)
        if cached is not None:
            return cached

        col, row = self.char_map[ch]
        rect = pygame.Rect(col * self.tile, row * self.tile, self.tile, self.tile)
        glyph = self._atlas.subsurface(rect).copy()
        # Tint the glyph with the requested color, keeping its alpha.
        glyph.fill(color, special_flags=pygame.BLEND_RGB_MULT)
        self._glyphs[key] = glyph
        return glyph

    def _ink_rows(self, ch):
        """Vertical (min_y, max_y) rows of visible ink for ``ch``, or None
        for a blank cell (space). Used to vertically centre text drawn over
        coloured bars."""
        if ch in self._ink_rows_cache:
            return self._ink_rows_cache[ch]
        col, row = self.char_map[ch]
        rect = pygame.Rect(col * self.tile, row * self.tile, self.tile, self.tile)
        cell = self._atlas.subsurface(rect)
        min_y = max_y = None
        for y in range(self.tile):
            for x in range(self.tile):
                if cell.get_at((x, y))[3] > 24:
                    if min_y is None:
                        min_y = y
                    max_y = y
                    break
        result = None if min_y is None else (min_y, max_y)
        self._ink_rows_cache[ch] = result
        return result

    def draw_char(self, surface, code, x, y, color, y_px_offset=0):
        """Draw a single character at tile position (x, y), optionally
        shifted by ``y_px_offset`` pixels (used for vertical centring)."""
        ch = chr(code) if isinstance(code, int) else code
        if ch == ' ':
            return
        surface.blit(self.glyph(ch, color),
                     (x * self.tile, y * self.tile + y_px_offset))

    def draw_text(self, surface, text, x, y, color, vertical_center=False):
        """Draw a string starting at tile position (x, y).

        With ``vertical_center=True`` the string's ink block is vertically
        centred inside its tile row (for text overlaid on coloured bars).
        """
        text = str(text)
        y_px_offset = 0
        if vertical_center:
            rows = []
            for ch in text:
                r = self._ink_rows(ch)
                if r is not None:
                    rows.append(r)
            if rows:
                top = min(r[0] for r in rows)
                bottom = max(r[1] for r in rows)
                y_px_offset = (self.tile - (bottom - top + 1)) // 2 - top
        for i, ch in enumerate(text):
            self.draw_char(surface, ch, x + i, y, color, y_px_offset=y_px_offset)
