#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
atlas_to_code: convert the hand-drawn PNG font atlas into an EXACT,
lossless, vectorized code reference.

The atlas (alienraid12x12.png) is a 32x8 grid of 12x12 cells. charset_map.json
(the output of tools/identify_charset.py) says which cells are text glyphs
(``char_map``), which are leftover sprites and which are blank; only the
``char_map`` glyphs are converted, sprites/empties are recorded as ignored.

"Vectorized, lossless" representation: every glyph becomes a minimal cover of
axis-aligned uniform-color rectangles ``(x, y, w, h, r, g, b, a)`` -- horizontal
runs of identical RGBA pixels merged vertically. Rasterizing those rectangles
(with ``Surface.fill``, which writes exact RGBA on a SRCALPHA surface) at any
INTEGER scale reproduces the atlas pixel-exactly, anti-aliated edges and
colored ink included. The tool proves this: it re-rasterizes every glyph and
compares against the converted atlas cell byte-for-byte, and REFUSES to write
the output unless every glyph round-trips identically.

Output: ``renderer/atlas_font.py`` -- a generated, standalone module that
embeds the rectangle vectors plus a small AtlasFont draw API and a
``selftest`` that re-verifies losslessness against the PNG at any time. It is
the code ground truth for what the font looks like; the hand-authored 16x16
font (renderer/font16.py) is a reinterpretation that can be checked against
it. (12 -> 16 is a non-integer 4/3 scale, so exactness is defined at the
native 12x12 and integer multiples thereof.)

Run inside the dev shell:
    nix develop -c python tools/atlas_to_code.py                 # write renderer/atlas_font.py
    nix develop -c python tools/atlas_to_code.py --no-ascii      # without ASCII-art comments
    nix develop -c python tools/atlas_to_code.py --out /tmp/f.py # custom target
"""
import argparse
import importlib.util
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
_SPEC = importlib.util.spec_from_file_location(
    'identify_charset', os.path.join(ROOT, 'tools', 'identify_charset.py'))
IC = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(IC)

CELL = IC.CELL  # 12


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def load_char_data(json_path):
    """(char_map, sprite_cells, empty_cells) from charset_map.json."""
    with open(json_path) as f:
        data = json.load(f)
    char_map = data['char_map']
    # Space is a drawable glyph even when the JSON has no explicit label:
    # cell (0,0) is the blank/space cell in this font (FontRenderer's
    # convention). Without this a missing ' ' entry would KeyError emission.
    char_map.setdefault(' ', [0, 0])
    sprites = sorted(k for k, v in data['cells'].items()
                     if v.get('state') == IC.STATE_SPRITE)
    empties = sorted(k for k, v in data['cells'].items()
                     if v.get('state') == IC.STATE_EMPTY)
    return char_map, sprites, empties


def load_cells(atlas_path):
    """{(col, row): SRCALPHA Surface} with black converted to alpha -- the
    same conversion the game's FontRenderer applies."""
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))
    cells, _cols, _rows = IC.load_and_split(atlas_path, CELL)
    return cells


# ---------------------------------------------------------------------------
# Vectorization (exact rectangle cover)
# ---------------------------------------------------------------------------
def vectorize_cell(cell):
    """Minimal exact cover of a glyph cell: horizontal runs of identical
    RGBA pixels, merged vertically while the run stays identical.
    Returns a list of (x, y, w, h, r, g, b, a), sorted by (y, x)."""
    w, h = cell.get_size()
    px = {}
    for y in range(h):
        for x in range(w):
            px[(x, y)] = tuple(cell.get_at((x, y)))
    rects = []
    active = {}  # (x, w, rgba) -> [y0, height]
    for y in range(h):
        seen = set()
        x = 0
        while x < w:
            rgba = px[(x, y)]
            if rgba[3] == 0:
                x += 1
                continue
            x0 = x
            while x + 1 < w and px[(x + 1, y)] == rgba:
                x += 1
            key = (x0, x - x0 + 1, rgba)
            if key in active:
                active[key][1] += 1
            else:
                active[key] = [y, 1]
            seen.add(key)
            x += 1
        for key in list(active):
            if key not in seen:
                y0, hh = active.pop(key)
                rects.append((key[0], y0, key[1], hh) + key[2])
    for key, (y0, hh) in active.items():
        rects.append((key[0], y0, key[1], hh) + key[2])
    rects.sort(key=lambda r: (r[1], r[0]))
    return rects


def rasterize_vectors(rects, scale=1, size=CELL):
    """Paint a rectangle cover onto a SRCALPHA surface (exact RGBA)."""
    surf = pygame.Surface((size * scale, size * scale), pygame.SRCALPHA)
    for (x, y, w, h, r, g, b, a) in rects:
        surf.fill((r, g, b, a), (x * scale, y * scale, w * scale, h * scale))
    return surf


def verify_lossless(cells, vectors_by_char, char_map):
    """Byte-exact round-trip check. Returns a list of mismatch messages."""
    problems = []
    for ch, (col, row) in char_map.items():
        if len(ch) != 1:
            continue
        original = cells[(col, row)]
        # A fully blank cell (e.g. the space glyph) vectorizes to zero
        # rectangles; a blank raster round-trips it exactly.
        raster = rasterize_vectors(vectors_by_char.get(ch, ()))
        if pygame.image.tostring(raster, 'RGBA') != \
                pygame.image.tostring(original, 'RGBA'):
            problems.append('glyph {0!r} at cell ({1},{2}) does not '
                            'round-trip'.format(ch, col, row))
    return problems


# ---------------------------------------------------------------------------
# Emission
# ---------------------------------------------------------------------------
def _ascii_art(rects):
    """12 comment lines showing the glyph mask, for human readability."""
    grid = [['.'] * CELL for _ in range(CELL)]
    for (x, y, w, h, _r, _g, _b, a) in rects:
        if a > 0:
            for yy in range(y, min(CELL, y + h)):
                for xx in range(x, min(CELL, x + w)):
                    grid[yy][xx] = '#'
    return ['    # ' + ''.join(row) for row in grid]


def emit_module(path, vectors_by_char, char_map, sprites, empties,
                atlas_name, ascii_art=True):
    """Write the generated reference module."""
    order = sorted((ch for ch in char_map if len(ch) == 1),
                   key=lambda ch: (char_map[ch][1], char_map[ch][0]))
    if ' ' not in vectors_by_char:
        order_with_space = [' '] + order
    else:
        order_with_space = order
    L = []
    a = L.append
    a('# -*- coding: utf-8 -*-')
    a('"""GENERATED FILE -- do not edit by hand.')
    a('')
    a('Exact vectorized code reference of {0}.'.format(atlas_name))
    a('Produced by tools/atlas_to_code.py; verified pixel-exact at generation.')
    a('')
    a('Each glyph is a cover of uniform-color rectangles (x, y, w, h, r, g, b, a);')
    a('rasterize()/AtlasFont repaint them with Surface.fill on a SRCALPHA surface,')
    a('which writes exact RGBA, so any integer scale reproduces the atlas')
    a('bit-for-bit (after the standard black->alpha conversion). Cells marked')
    a('"sprite" or "empty" in charset_map.json are excluded from the charset and')
    a('listed below for reference.')
    a('')
    a('Selftest: python -m renderer.atlas_font')
    a('"""')
    a('import importlib.util')
    a('import json')
    a('import os')
    a('')
    a('import pygame')
    a('')
    a('TILE = {0}'.format(CELL))
    a('')
    a('# char -> atlas cell (col, row), from charset_map.json')
    a('CHAR_MAP = {0}'.format(
        '{' + ', '.join('{0}: {1}'.format(json.dumps(ch, ensure_ascii=False),
                                          list(char_map[ch])) for ch in order_with_space) + '}'))
    a('')
    a('# cells excluded from the charset: leftover sprites / blank cells')
    a('IGNORED_SPRITE_CELLS = {0}'.format(list(sprites)))
    a('IGNORED_EMPTY_CELLS = {0}'.format(list(empties)))
    a('')
    a('# char -> ((x, y, w, h, r, g, b, a), ...) uniform-color rectangles')
    a('GLYPH_VECTORS = {')
    for ch in order_with_space:
        rects = vectors_by_char.get(ch, ())
        a('    {0}: ('.format(json.dumps(ch, ensure_ascii=False)))
        if ascii_art and rects:
            L.extend(_ascii_art(rects))
        for rect in rects:
            a('        {0},'.format(rect))
        a('    ),')
    a('}')
    a('')
    a('')
    a('def rasterize(ch, scale=1, color=None):')
    a('    """Repaint a glyph from its rectangle cover (exact RGBA). With')
    a('    ``color``, the stored rgb is multiplied (like FontRenderer tint)."""')
    a('    surf = pygame.Surface((TILE * scale, TILE * scale), pygame.SRCALPHA)')
    a('    for (x, y, w, h, r, g, b, al) in GLYPH_VECTORS.get(ch, ()):')
    a('        if color is not None:')
    a('            r = r * color[0] // 255')
    a('            g = g * color[1] // 255')
    a('            b = b * color[2] // 255')
    a('        surf.fill((r, g, b, al), (x * scale, y * scale, w * scale, h * scale))')
    a('    return surf')
    a('')
    a('')
    a('def has_glyph(ch):')
    a('    return ch in GLYPH_VECTORS')
    a('')
    a('')
    a('class AtlasFont:')
    a('    """Drop-in-ish reference renderer (positions in TILE*scale units)."""')
    a('')
    a('    tile = TILE')
    a('')
    a('    def __init__(self, scale=1):')
    a('        self.scale = scale')
    a('')
    a('    def draw_char(self, surface, ch, x, y, color=None, y_px_offset=0):')
    a('        if ch == " " or ch not in GLYPH_VECTORS:')
    a('            return')
    a('        surface.blit(rasterize(ch, self.scale, color),')
    a('                     (x * TILE * self.scale, y * TILE * self.scale + y_px_offset))')
    a('')
    a('    def draw_text(self, surface, text, x, y, color=None):')
    a('        for i, ch in enumerate(str(text)):')
    a('            self.draw_char(surface, ch, x + i, y, color)')
    a('')
    a('')
    a('def selftest(atlas="alienraid12x12.png", map_path="charset_map.json"):')
    a('    """Re-verify the vectors against the PNG: byte-exact or fail."""')
    a('    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)')
    a('    atlas = atlas if os.path.isfile(atlas) else os.path.join(root, atlas)')
    a('    map_path = map_path if os.path.isfile(map_path) else os.path.join(root, map_path)')
    a('    if not (os.path.isfile(atlas) and os.path.isfile(map_path)):')
    a('        print("selftest skipped: atlas/map not found")')
    a('        return 0')
    a('    tool = os.path.join(root, "tools", "atlas_to_code.py")')
    a('    spec = importlib.util.spec_from_file_location("atlas_to_code", tool)')
    a('    mod = importlib.util.module_from_spec(spec)')
    a('    spec.loader.exec_module(mod)')
    a('    cells = mod.load_cells(atlas)')
    a('    char_map, _s, _e = mod.load_char_data(map_path)')
    a('    bad = 0')
    a('    for ch, (col, row) in sorted(char_map.items()):')
    a('        if len(ch) != 1:')
    a('            continue')
    a('        want = pygame.image.tostring(cells[(col, row)], "RGBA")')
    a('        got = pygame.image.tostring(rasterize(ch), "RGBA")')
    a('        if want != got:')
    a('            print("MISMATCH: {0!r}".format(ch))')
    a('            bad += 1')
    a('    if bad:')
    a('        print("{0} glyphs differ from the atlas".format(bad))')
    a('        return 1')
    a('    print("OK: {0} glyphs round-trip pixel-exact".format(')
    a('        sum(1 for c in char_map if len(c) == 1)))')
    a('    return 0')
    a('')
    a('')
    a('if __name__ == "__main__":')
    a('    raise SystemExit(selftest())')
    a('')
    with open(path, 'w') as f:
        f.write('\n'.join(L))
    return len(order_with_space)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv):
    ap = argparse.ArgumentParser(
        description='Convert the PNG font atlas into an exact vectorized '
                    'code reference (renderer/atlas_font.py).')
    ap.add_argument('--atlas', default='alienraid12x12.png')
    ap.add_argument('--json', default='charset_map.json')
    ap.add_argument('--out', default=os.path.join('renderer', 'atlas_font.py'))
    ap.add_argument('--no-ascii', action='store_true',
                    help='do not embed ASCII-art glyph comments')
    args = ap.parse_args(argv)

    atlas_path = args.atlas if os.path.isfile(args.atlas) else \
        os.path.join(ROOT, args.atlas)
    json_path = args.json if os.path.isfile(args.json) else \
        os.path.join(ROOT, args.json)
    out_path = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    if not os.path.isfile(atlas_path):
        raise SystemExit('atlas not found: ' + atlas_path)
    if not os.path.isfile(json_path):
        raise SystemExit('charset map not found: ' + json_path)

    pygame.init()
    cells = load_cells(atlas_path)
    char_map, sprites, empties = load_char_data(json_path)

    vectors = {' ': ()}
    total_rects = 0
    for ch, (col, row) in sorted(char_map.items()):
        if len(ch) != 1:
            print('skipping multi-char label: {0!r}'.format(ch))
            continue
        rects = vectorize_cell(cells[(col, row)])
        vectors[ch] = tuple(rects)
        total_rects += len(rects)

    problems = verify_lossless(cells, vectors, char_map)
    if problems:
        for p in problems:
            print('LOSSLESS CHECK FAILED: ' + p)
        raise SystemExit('refusing to write {0}: round-trip not exact'.format(out_path))

    n = emit_module(out_path, vectors, char_map, sprites, empties,
                    os.path.basename(atlas_path), ascii_art=not args.no_ascii)
    print('wrote {0} ({1} glyphs, {2} rectangles, verified pixel-exact)'.format(
        out_path, n, total_rects))
    print('ignored: {0} sprite cells, {1} empty cells'.format(len(sprites), len(empties)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
