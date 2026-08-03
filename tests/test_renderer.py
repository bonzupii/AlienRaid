#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Headless smoke tests for the renderer (run with: python -m unittest ...).

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
from renderer.palette import WHITE, PLAYER_GREEN, KANGA_RED


PRESERVED = "0123456789!@#$%^&*()_+=-abcdefghijklmnopqrstuvwxyz" \
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ<>?;:,.[]/'`~{}"


class TestAssets(unittest.TestCase):
    def test_no_iccp_chunks(self):
        # libpng warns 'iCCP: CRC error' on the game's PNG assets; the
        # corrupt embedded colour-profile chunk must stay stripped.
        for path in ('alienraid12x12.png', 'menu_background.png'):
            if not os.path.isfile(path):
                continue
            with open(path, 'rb') as f:
                data = f.read()
            self.assertNotIn(b'iCCP', data, 'corrupt iCCP chunk still in ' + path)


class TestSdlImage(unittest.TestCase):
    def test_sdl_image_available(self):
        # Regression guard. Without SDL_image, pygame.image.load only
        # understands BMP and the font PNG fails with
        # "File is not a Windows BMP file". nixpkgs' pygame is built against
        # nix SDL2_image, so this must be True.
        self.assertTrue(pygame.image.get_extended(),
                        'pygame must be built with SDL_image support')


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
        # The atlas is a 32x8 grid of 12x12 glyphs.
        self.assertEqual(font.cols, 32)

        surf = pygame.Surface((120 * 12, 8 * 12))
        surf.fill((0, 0, 0))
        font.draw_text(surf, "Alien Raid 0.1a", 0, 0, WHITE)
        font.draw_text(surf, PRESERVED, 0, 2, WHITE)
        self.assertGreater(_ink_count(surf), 1000)

    def test_single_glyph_paints_its_cell(self):
        # Content assertion: drawing a letter actually paints pixels inside
        # that glyph's own 12x12 cell.
        font = FontRenderer('alienraid12x12.png')
        surf = pygame.Surface((12, 12))
        surf.fill((0, 0, 0))
        font.draw_char(surf, ord('A'), 0, 0, WHITE)
        self.assertGreater(_ink_count(surf), 0, "letter 'A' drew nothing")

    def test_fallback_for_sprite_code(self):
        font = FontRenderer('alienraid12x12.png')
        surf = pygame.Surface((12, 12), pygame.SRCALPHA)
        font.draw_char(surf, 196, 0, 0, WHITE)  # kanga code -> '?' fallback
        # shouldn't crash


class TestSpriteLoader(unittest.TestCase):
    def test_every_recipe_renders(self):
        loader = SpriteLoader()
        for name in sorted(RECIPES):
            surf = loader.get(name, KANGA_RED)
            # Content assertion: no recipe may be a blank/transparent tile.
            self.assertGreater(_ink_count(surf), 0, 'blank sprite: ' + name)

    def test_player_sprite_uses_its_color(self):
        loader = SpriteLoader()
        surf = loader.get('player', PLAYER_GREEN)
        found = False
        for y in range(surf.get_height()):
            for x in range(surf.get_width()):
                r, g, b, a = surf.get_at((x, y))
                if (abs(r - PLAYER_GREEN[0]) <= 45
                        and abs(g - PLAYER_GREEN[1]) <= 45
                        and abs(b - PLAYER_GREEN[2]) <= 45):
                    found = True
                    break
            if found:
                break
        self.assertTrue(found, 'player sprite has no pixels in its color')

    def test_cache(self):
        loader = SpriteLoader()
        a = loader.get('kanga', KANGA_RED)
        b = loader.get('kanga', KANGA_RED)
        c = loader.get('kanga', PLAYER_GREEN)
        self.assertIs(a, b)
        self.assertIsNot(a, c)


def _ink_count(surf):
    """Count non-black pixels of a surface (full resolution)."""
    w, h = surf.get_size()
    count = 0
    for y in range(h):
        for x in range(w):
            r, g, b, *_ = surf.get_at((x, y))
            if r + g + b > 24:
                count += 1
    return count


if __name__ == '__main__':
    unittest.main()
