#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/atlas_to_code.py: the PNG -> vectorized-code conversion
must be exact and lossless (rasterizing the emitted rectangles reproduces
the atlas cell byte-for-byte), and the emitted module must be importable
and carry the charset/ignored-cell metadata from charset_map.json."""
import importlib.util
import json
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


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(ROOT, relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TOOL = _load('atlas_to_code', os.path.join('tools', 'atlas_to_code.py'))
IC = _load('identify_charset', os.path.join('tools', 'identify_charset.py'))


def make_atlas(tmpdir):
    """3x1 grid of 12x12 cells mirroring the REAL atlas layout: cell (0,0)
    is blank black (the space cell the tool reserves), (1,0) holds a white
    '+' with a red anti-alias-ish dot, and (2,0) holds the same '+' as a
    leftover sprite cell."""
    surf = pygame.Surface((36, 12), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 255))
    for off in (12, 24):
        for p in ((5 + off, 5), (5 + off, 6), (6 + off, 5), (6 + off, 6),
                  (5 + off, 7), (6 + off, 7)):
            surf.set_at(p, (255, 255, 255, 255))
        surf.set_at((10 + off, 10), (255, 40, 40, 255))
    path = os.path.join(tmpdir, 'atlas.png')
    pygame.image.save(surf, path)
    return path


def make_map_json(tmpdir, atlas_path):
    payload = {
        'atlas': os.path.basename(atlas_path),
        'cell_size': 12,
        'cols': 3,
        'rows': 1,
        'cells': {
            '0_0': {'state': 'empty'},
            '1_0': {'state': 'char', 'char': '+'},
            '2_0': {'state': 'sprite'},
        },
        'char_map': {'+': [1, 0]},
    }
    path = os.path.join(tmpdir, 'charset_map.json')
    with open(path, 'w') as f:
        json.dump(payload, f)
    return path


class TestAtlasToCode(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.atlas = make_atlas(self.tmp.name)
        self.json = make_map_json(self.tmp.name, self.atlas)
        self.cells, _c, _r = IC.load_and_split(self.atlas, 12)

    def tearDown(self):
        self.tmp.cleanup()

    def test_vectorize_roundtrip_is_lossless(self):
        """The rectangle cover must repaint to the exact original RGBA,
        including the colored (non-white) ink pixel."""
        vectors = TOOL.vectorize_cell(self.cells[(1, 0)])
        self.assertGreater(len(vectors), 0)
        raster = TOOL.rasterize_vectors(vectors)
        self.assertEqual(pygame.image.tostring(raster, 'RGBA'),
                         pygame.image.tostring(self.cells[(1, 0)], 'RGBA'))
        # The red dot survives as its own rectangle.
        self.assertTrue(any(r[4:] == (255, 40, 40, 255) for r in vectors),
                        'colored ink not preserved as a rectangle')

    def test_runs_are_merged(self):
        """Vertical merging keeps the cover minimal: the 2x3 '+' stem is a
        single rectangle, not six 1px ones."""
        vectors = TOOL.vectorize_cell(self.cells[(1, 0)])
        self.assertIn((5, 5, 2, 3, 255, 255, 255, 255), vectors)

    def test_verify_lossless_passes_and_detects(self):
        char_map, sprites, empties = TOOL.load_char_data(self.json)
        # The tool injects ' ' -> cell (0,0) (the blank space cell); a blank
        # glyph with zero vectors must round-trip exactly, not KeyError.
        self.assertIn(' ', char_map)
        vectors = {'+': tuple(TOOL.vectorize_cell(self.cells[(1, 0)]))}
        self.assertEqual(TOOL.verify_lossless(self.cells, vectors, char_map), [])
        broken = {'+': vectors['+'][:-1]}  # drop the red dot -> mismatch
        self.assertEqual(len(TOOL.verify_lossless(self.cells, broken, char_map)), 1)

    def test_emit_module_metadata_and_ignored_cells(self):
        char_map, sprites, empties = TOOL.load_char_data(self.json)
        vectors = {' ': (), '+': tuple(TOOL.vectorize_cell(self.cells[(1, 0)]))}
        out = os.path.join(self.tmp.name, 'atlas_font.py')
        TOOL.emit_module(out, vectors, char_map, sprites, empties,
                         'atlas.png', ascii_art=True)
        with open(out) as f:
            text = f.read()
        self.assertIn('IGNORED_SPRITE_CELLS = [\'2_0\']', text)
        self.assertIn('IGNORED_EMPTY_CELLS = [\'0_0\']', text)
        self.assertIn('GLYPH_VECTORS = {', text)
        # ASCII-art comment block present for the '+' glyph.
        self.assertIn('# .....##.....', text)
        # The emitted module imports and rasterizes identically.
        spec = importlib.util.spec_from_file_location('gen_atlas_font', out)
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        self.assertEqual(gen.TILE, 12)
        self.assertTrue(gen.has_glyph('+'))
        self.assertTrue(gen.has_glyph(' '))
        self.assertFalse(gen.has_glyph('x'))  # not in this charset
        self.assertEqual(pygame.image.tostring(gen.rasterize('+'), 'RGBA'),
                         pygame.image.tostring(self.cells[(1, 0)], 'RGBA'))
        # Integer-scale raster is the exact nearest-neighbour expansion.
        big = gen.rasterize('+', scale=2)
        small = gen.rasterize('+')
        for y in range(12):
            for x in range(12):
                self.assertEqual(big.get_at((x * 2, y * 2)), small.get_at((x, y)))


if __name__ == '__main__':
    unittest.main()
