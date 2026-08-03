#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Headless smoke tests for the renderer (run with .venv/bin/python).

Uses SDL_VIDEODRIVER=dummy so no window is needed.
"""
import os
import sys
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

import pygame

pygame.init()

from renderer.font_renderer import FontRenderer, is_text_glyph
from renderer.sprites import SpriteLoader, RECIPES
from renderer.palette import WHITE, PLAYER_GREEN, KANGA_RED, SILVER


PRESERVED = "0123456789!@#$%^&*()_+=-abcdefghijklmnopqrstuvwxyz" \
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ<>?;:,.[]/'`~{}"


class TestCharset(unittest.TestCase):
    def test_preserved_chars_are_text(self):
        for ch in PRESERVED:
            self.assertTrue(is_text_glyph(ord(ch)), 'expected text: ' + ch)
        self.assertTrue(is_text_glyph(ord(' ')))
        for code in (9, 10, 16, 17, 18, 24, 25, 26, 27, 29, 30, 31, 224, 225):
            self.assertTrue(is_text_glyph(code), 'expected text: ' + str(code))

    def test_sprite_codes_are_not_text(self):
        # Every glyph that was paired with a mob/player/equipment/map.
        for code in (196, 179, 191, 218, 217, 192, 180, 195, 193, 194, 197,
                     205, 186, 187, 201, 188, 200, 185, 204, 176, 177, 178):
            self.assertFalse(is_text_glyph(code), 'expected sprite: ' + str(code))


class TestFontRenderer(unittest.TestCase):
    def test_load_and_draw(self):
        font = FontRenderer('alienraid12x12.png')
        surf = pygame.Surface((120 * 12, 8 * 12))
        surf.fill((0, 0, 0))
        font.draw_text(surf, "Alien Raid 0.1a", 0, 0, WHITE)
        font.draw_text(surf, PRESERVED, 0, 2, WHITE)
        self.assertGreater(_ink_count(surf), 1000)

    def test_fallback_for_sprite_code(self):
        font = FontRenderer('alienraid12x12.png')
        surf = pygame.Surface((12, 12), pygame.SRCALPHA)
        font.draw_char(surf, 196, 0, 0, WHITE)  # kanga code -> '?' fallback
        # shouldn't crash


class TestSpriteLoader(unittest.TestCase):
    def test_all_recipes_render(self):
        loader = SpriteLoader()
        surf = pygame.Surface((12 * 20, 12 * 12))
        surf.fill((0, 0, 0))
        for i, name in enumerate(sorted(RECIPES)):
            x = (i % 20) * 12
            y = (i // 20) * 12
            surf.blit(loader.get(name, KANGA_RED), (x, y))
        self.assertGreater(_ink_count(surf), 1000)

    def test_cache(self):
        loader = SpriteLoader()
        a = loader.get('kanga', KANGA_RED)
        b = loader.get('kanga', KANGA_RED)
        c = loader.get('kanga', PLAYER_GREEN)
        self.assertIs(a, b)
        self.assertIsNot(a, c)


def _ink_count(surf):
    """Count non-black pixels by sampling."""
    w, h = surf.get_size()
    count = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b, *_ = surf.get_at((x, y))
            if r + g + b > 24:
                count += 1
    return count


if __name__ == '__main__':
    unittest.main()
