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
SPECIAL_GLYPHS = "←↑→↓▲▼◀▶↕↔☐☑○◉"


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
        # Every hand-drawn interface glyph must be labeled text in the map.
        for ch in PRESERVED + SPECIAL_GLYPHS + ' ':
            self.assertTrue(is_text_glyph(ord(ch)), 'expected text: ' + ch)
        self.assertTrue(is_text_glyph(' '))
        self.assertTrue(is_text_glyph('←'))

    def test_sprite_codes_are_not_text(self):
        # Chars that were paired with a mob/player/equipment/map (rendered
        # as sprites) or are plain unmapped symbols are never text.
        for code in (196, 179, 191, 218, 217, 192, 180, 195, 193, 194, 197,
                     205, 186, 187, 201, 188, 200, 185, 204, 176, 177, 178):
            self.assertFalse(is_text_glyph(code), 'expected sprite: ' + str(code))
        for ch in ('\t', '\n', '¶', '♠'):
            self.assertFalse(is_text_glyph(ch), 'expected non-text: ' + ch)

    def test_map_drives_cell_lookup(self):
        """The charset map (artist's hand-labeled layout) determines where
        each character lives in the atlas — not ASCII code arithmetic."""
        font = FontRenderer('alienraid12x12.png')
        # Ground truth from the labeled map: letters sit in rows 4/5 (1-based)
        # = 0-based rows 3/4, punctuation along row 1, specials in row 3.
        self.assertEqual(font.cell_for('a'), (0, 3))
        self.assertEqual(font.cell_for('z'), (25, 3))
        self.assertEqual(font.cell_for('A'), (0, 4))
        self.assertEqual(font.cell_for('Z'), (25, 4))
        self.assertEqual(font.cell_for('!'), (1, 0))
        self.assertEqual(font.cell_for('0'), (16, 0))
        self.assertEqual(font.cell_for('←'), (2, 2))
        self.assertEqual(font.cell_for('☑'), (11, 2))
        self.assertEqual(font.cell_for(' '), (0, 0))
        self.assertEqual(font.cell_for('?'), (31, 0))
        self.assertEqual(font.cell_for(196), font.cell_for('?'))  # fallback


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

    def test_glyphs_differ_by_cell(self):
        # Different characters must paint different pixels (they live in
        # different cells), or the map would be mapping two chars to one
        # glyph.
        font = FontRenderer('alienraid12x12.png')
        a_surf = pygame.Surface((12, 12))
        b_surf = pygame.Surface((12, 12))
        a_surf.fill((0, 0, 0))
        b_surf.fill((0, 0, 0))
        font.draw_char(a_surf, 'a', 0, 0, WHITE)
        font.draw_char(b_surf, 'b', 0, 0, WHITE)
        self.assertNotEqual(pygame.image.tostring(a_surf, 'RGB'),
                            pygame.image.tostring(b_surf, 'RGB'))

    def test_glyph_background_is_transparent(self):
        """Regression: glyphs must not paint a black box. The hand-drawn
        atlas is opaque black; drawing a letter over a coloured surface must
        let the background show through (black converted to alpha), or the
        HP bar text would sit on a black rectangle."""
        font = FontRenderer('alienraid12x12.png')
        red = (200, 30, 30)
        surf = pygame.Surface((12, 12))
        surf.fill(red)
        font.draw_char(surf, 'A', 0, 0, WHITE)
        red_visible = any(
            abs(r - red[0]) <= 30 and abs(g - red[1]) <= 30 and abs(b - red[2]) <= 30
            for y in range(12) for x in range(12)
            for r, g, b, *_ in [surf.get_at((x, y))])
        self.assertTrue(red_visible, 'opaque glyph box covered the background')

    def test_text_vertical_center(self):
        """Text drawn with vertical_center=True (the HP bar label) has its
        ink block centred within the 12px tile row."""
        font = FontRenderer('alienraid12x12.png')
        surf = pygame.Surface((120, 12), pygame.SRCALPHA)  # wide enough for the whole string
        surf.fill((0, 0, 0, 255))
        font.draw_text(surf, 'HP: 100/125', 0, 0, WHITE, vertical_center=True)
        ys = [y for y in range(12) for x in range(12)
              if surf.get_at((x, y))[3] > 24]
        self.assertTrue(ys, 'HP text drew nothing')
        mid = (min(ys) + max(ys)) / 2.0
        self.assertLessEqual(abs(mid - (12 - 1) / 2.0), 1.0,
                             'text ink not vertically centred in the row')

    def test_fallback_for_sprite_code(self):
        """An unmapped code falls back to '?' and paints exactly the same
        pixels as drawing '?' directly (on identical backgrounds).

        (Previously this compared a transparent-background blit against a
        black-filled blit; now that the atlas is alpha-correct, anti-aliased
        edge pixels legitimately blend differently over opaque black, so the
        comparison must use the same background.)"""
        font = FontRenderer('alienraid12x12.png')
        a = pygame.Surface((12, 12), pygame.SRCALPHA)
        b = pygame.Surface((12, 12), pygame.SRCALPHA)
        font.draw_char(a, 196, 0, 0, WHITE)  # unmapped -> '?' fallback
        font.draw_char(b, '?', 0, 0, WHITE)
        self.assertEqual(pygame.image.tostring(a, 'RGBA'),
                         pygame.image.tostring(b, 'RGBA'))
        self.assertGreater(_ink_count(a), 0, 'fallback glyph drew nothing')


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
