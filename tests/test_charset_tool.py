#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the charset identification tool's pure functions.

The GUI itself is interactive (it needs a real display), so these tests
cover the headless pipeline: black->alpha conversion, cell cutting,
inkless-cell pre-marking, duplicate-glyph grouping, and the JSON
save/load round-trip that feeds the FontRenderer mapping.
"""
import importlib.util
import os
import sys
import tempfile
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

ROOT = os.path.join(os.path.dirname(__file__), os.pardir)
TOOL = os.path.join(ROOT, 'tools', 'identify_charset.py')
spec = importlib.util.spec_from_file_location('identify_charset', TOOL)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def make_atlas(tmpdir):
    """3x1 grid of 12x12 cells: cells (0,0) and (2,0) hold an identical
    white '+' glyph with a red dot (a hand-drawn duplicate pair); cell
    (1,0) is blank black."""
    surf = pygame.Surface((36, 12), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 255))
    for off in (0, 24):
        for p in ((5 + off, 5), (5 + off, 6), (6 + off, 5), (6 + off, 6),
                  (5 + off, 7), (6 + off, 7)):
            surf.set_at(p, (255, 255, 255, 255))
        surf.set_at((10 + off, 10), (255, 40, 40, 255))
    path = os.path.join(tmpdir, 'atlas.png')
    pygame.image.save(surf, path)
    return path


class TestCharsetTool(unittest.TestCase):
    def test_black_to_alpha_and_cut(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = make_atlas(tmp)
            cells, cols, rows = tool.load_and_split(path)
            self.assertEqual((cols, rows), (3, 1))
            glyph = cells[(0, 0)]
            self.assertEqual(glyph.get_size(), (12, 12))
            self.assertEqual(glyph.get_at((5, 5))[3], 255)   # white ink opaque
            self.assertEqual(glyph.get_at((0, 0))[3], 0)     # black -> transparent
            red = glyph.get_at((10, 10))                     # coloured ink kept
            self.assertGreater(red[0], 200)
            self.assertGreater(red[3], 200)

    def test_premark_inkless_cells_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = make_atlas(tmp)
            cells, cols, rows = tool.load_and_split(path)
            states = tool.new_states(cols, rows, cells)
            self.assertEqual(states[(0, 0)]['state'], tool.STATE_TODO)
            self.assertEqual(states[(2, 0)]['state'], tool.STATE_TODO)
            self.assertEqual(states[(1, 0)]['state'], tool.STATE_EMPTY)

    def test_export_cells(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = make_atlas(tmp)
            cells, cols, rows = tool.load_and_split(path)
            out = os.path.join(tmp, 'cells')
            tool.export_cells(cells, directory=out)
            for name in ('cell_00_00.png', 'cell_01_00.png', 'cell_02_00.png'):
                self.assertTrue(os.path.isfile(os.path.join(out, name)))

    def test_duplicate_groups(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = make_atlas(tmp)
            cells, cols, rows = tool.load_and_split(path)
            groups = [set(g) for g in tool.find_duplicate_groups(cells)]
            self.assertIn({(0, 0), (2, 0)}, groups,
                          'identical cells (0,0) and (2,0) not grouped')
            # The inkless cell is never grouped (it is pre-marked empty).
            self.assertFalse(any((1, 0) in g for g in groups))

    def test_batch_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = make_atlas(tmp)
            cells, cols, rows = tool.load_and_split(path)
            states = tool.new_states(cols, rows, cells)
            states[(0, 0)] = {'state': tool.STATE_CHAR, 'char': 'A'}
            group = next(g for g in tool.find_duplicate_groups(cells)
                         if (0, 0) in g)
            n = tool.batch_label(states, group, 'A')
            self.assertEqual(n, 1)
            self.assertEqual(states[(2, 0)],
                             {'state': tool.STATE_CHAR, 'char': 'A'})
            # The already-labelled cell is untouched.
            self.assertEqual(states[(0, 0)],
                             {'state': tool.STATE_CHAR, 'char': 'A'})

    def test_save_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = make_atlas(tmp)
            cells, cols, rows = tool.load_and_split(path)
            states = tool.new_states(cols, rows, cells)
            states[(0, 0)] = {'state': tool.STATE_CHAR, 'char': 'A'}
            states[(1, 0)] = {'state': tool.STATE_SPRITE}
            js = os.path.join(tmp, 'map.json')
            tool.save_states(js, path, 12, cols, rows, states)
            data, loaded = tool.load_states(js)
            self.assertEqual(loaded[(0, 0)], {'state': 'char', 'char': 'A'})
            self.assertEqual(loaded[(1, 0)], {'state': 'sprite'})
            self.assertEqual(data['char_map'], {'A': [0, 0]})
            self.assertEqual(data['cols'], 3)

    def test_special_glyph_palette(self):
        """The palette covers exactly the requested non-typeable glyphs
        (4 cardinal arrows, 4 triangles, vertical/horizontal double
        arrows, checkboxes, radio), no diagonals or diamonds, and every
        icon actually draws ink."""
        symbols = [s for s, _ in tool.SPECIAL_GLYPHS]
        self.assertEqual(len(symbols), 14)
        for needed in ('←', '↑', '→', '↓',
                       '▲', '▼', '◀', '▶',
                       '↕', '↔',
                       '☐', '☑', '○', '◉'):
            self.assertIn(needed, symbols)
        for banned in ('↖', '↗', '↙', '↘', '◆', '◇'):
            self.assertNotIn(banned, symbols)
        surf = pygame.Surface((24, 24), pygame.SRCALPHA)
        for sym, _ in tool.SPECIAL_GLYPHS:
            surf.fill((0, 0, 0, 0))
            tool._draw_special(surf, 12, 12, sym, (255, 255, 255, 255))
            ink = sum(1 for x in range(24) for y in range(24)
                      if surf.get_at((x, y))[3] > 0)
            self.assertGreater(ink, 0,
                               'palette symbol {0!r} drew nothing'.format(sym))

    def test_unicode_and_named_labels_roundtrip(self):
        """Special-glyph (unicode) and custom-name labels survive the JSON
        round-trip, and both appear in the char map."""
        with tempfile.TemporaryDirectory() as tmp:
            path = make_atlas(tmp)
            cells, cols, rows = tool.load_and_split(path)
            states = tool.new_states(cols, rows, cells)
            states[(0, 0)] = {'state': tool.STATE_CHAR, 'char': '←'}
            states[(2, 0)] = {'state': tool.STATE_CHAR, 'char': 'checkbox_checked'}
            js = os.path.join(tmp, 'map.json')
            tool.save_states(js, path, 12, cols, rows, states)
            data, loaded = tool.load_states(js)
            self.assertEqual(loaded[(0, 0)], {'state': 'char', 'char': '←'})
            self.assertEqual(loaded[(2, 0)],
                             {'state': 'char', 'char': 'checkbox_checked'})
            self.assertEqual(data['char_map']['←'], [0, 0])
            self.assertEqual(data['char_map']['checkbox_checked'], [2, 0])

    def test_duplicate_char_last_wins_and_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = make_atlas(tmp)
            cells, cols, rows = tool.load_and_split(path)
            states = tool.new_states(cols, rows, cells)
            states[(0, 0)] = {'state': tool.STATE_CHAR, 'char': 'X'}
            states[(1, 0)] = {'state': tool.STATE_CHAR, 'char': 'X'}
            char_map, dupes = tool.build_char_map(states)
            self.assertEqual(char_map['X'], [1, 0])  # last cell wins
            self.assertEqual(len(dupes), 1)


if __name__ == '__main__':
    unittest.main()
