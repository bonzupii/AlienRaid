#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for renderer/font16.py -- the hand-authored 16x16 procedural font.

The generated renderer/atlas_font.py (from tools/atlas_to_code.py) is the
pixel-exact ground truth of the old bitmap atlas; font16 is the new
hand-authored reinterpretation. These tests pin the two against the same
charset_map.json ground truth so the new font can never silently lose a
character the game renders.
"""
import os
import sys
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

import pygame

pygame.init()

from renderer import atlas_font
from renderer.font16 import GLYPHS, Font16, has_glyph, TILE
from renderer.font_renderer import get_char_map


class TestFont16(unittest.TestCase):
    def test_font16_covers_the_charset(self):
        """Every single-char glyph in charset_map.json (the ground truth
        for what the game may render as text) must exist in Font16."""
        char_map = get_char_map()
        missing = [ch for ch in char_map if len(ch) == 1 and not has_glyph(ch)]
        self.assertFalse(missing,
                         'Font16 missing glyphs: ' + ', '.join(repr(m) for m in missing))

    def test_font16_glyphs_have_atlas_reference(self):
        """Every Font16 glyph also exists in the pixel-exact atlas vectors,
        so the reinterpretation can be checked against ground truth."""
        for ch in GLYPHS:
            self.assertTrue(atlas_font.has_glyph(ch),
                            'no atlas reference for {0!r}'.format(ch))

    def test_glyph_renders_ink_at_16(self):
        font = Font16()
        surf = font.glyph('A', (255, 255, 255))
        self.assertEqual(surf.get_size(), (TILE, TILE))
        ink = sum(1 for y in range(TILE) for x in range(TILE)
                  if surf.get_at((x, y))[3] > 0)
        self.assertGreater(ink, 0, "'A' drew nothing")
        # Ink is 2px blocks (the integer x2 scale), never 1px stray pixels.
        self.assertTrue(any(
            surf.get_at((x, y))[3] > 0 and x + 1 < TILE
            and surf.get_at((x + 1, y))[3] > 0
            for y in range(TILE) for x in range(TILE)),
            'no 2px-wide stroke found')

    def test_space_is_blank(self):
        font = Font16()
        space = font.glyph(' ', (255, 255, 255))
        self.assertEqual(sum(1 for y in range(TILE) for x in range(TILE)
                             if space.get_at((x, y))[3] > 0), 0)

    def test_unknown_falls_back_to_question_mark(self):
        font = Font16()
        unknown = font.glyph('\u2665', (255, 255, 255))  # not in the charset
        fallback = font.glyph('?', (255, 255, 255))
        self.assertEqual(pygame.image.tostring(unknown, 'RGBA'),
                         pygame.image.tostring(fallback, 'RGBA'))


if __name__ == '__main__':
    unittest.main()
