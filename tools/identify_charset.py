#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive character-identification tool for the hand-drawn bitmap font.

``alienraid12x12.png`` is a grid of 12x12 cells. Most cells are hand-drawn
*text* glyphs (0-9, punctuation, a-z, A-Z, arrows, checkboxes, radio boxes);
the rest are leftover sprites (mobs, terrain, equipment) that must NEVER be
used for text. This tool walks every cell and lets you label it:

    type any character key  -> cell contains that character
    Delete                  -> cell is a SPRITE (excluded from the charset)
    F2                      -> cell is empty (blank)
    F3                      -> undo, back to "unidentified"

What it does, in order:
  1. Loads the atlas and converts black -> alpha (brightness-to-alpha, so
     anti-aliased edges keep a smooth falloff and coloured glyphs keep
     their hue).
  2. Cuts it into individual CELL x CELL cells.
  3. Exports every cell as its own transparent PNG under charset_cells/
     (skip with --no-export) so you can also eyeball them in an image viewer.
  4. Opens a pygame window: click or arrow to a cell, then type/label it.
     Cells with no ink at all are pre-marked "empty" so you only look at
     the ones that matter. Progress is saved to charset_map.json after
     EVERY change, so you can quit (Esc / close button) and resume any time.
     Pixel-identical glyphs are grouped: the panel lists the identical
     cells, and F4 copies the current label onto all of them (handy for
     the duplicated letter rows).
  5. On quit it prints a summary plus the char -> cell map.

The GUI and dry-run show rows/columns 1-BASED (the way a human reads a
printed grid); the JSON keys them 0-based ("col_row").

The JSON tells the renderer exactly which cells are text and which are
sprites, so the FontRenderer mapping can be corrected from the file.

Run inside the dev shell:
    nix develop -c python tools/identify_charset.py            # GUI
    nix develop -c python tools/identify_charset.py --dry-run  # no GUI
"""

import argparse
import json
import os
import sys

import pygame

CELL = 12
EXPORT_DIR = 'charset_cells'
DEFAULT_JSON = 'charset_map.json'

STATE_TODO = 'todo'
STATE_CHAR = 'char'
STATE_SPRITE = 'sprite'
STATE_EMPTY = 'empty'

# Translucent overlays drawn over each labelled cell in the overview grid.
STATE_COLORS = {
    STATE_CHAR:   (46, 204, 113, 90),    # green  -> text glyph
    STATE_SPRITE: (231, 76, 60, 120),    # red    -> sprite, deleted
    STATE_EMPTY:  (127, 140, 141, 70),   # grey   -> blank
}
STATE_LABEL = {
    STATE_TODO:   'unidentified',
    STATE_CHAR:   'character',
    STATE_SPRITE: 'SPRITE — deleted from charset',
    STATE_EMPTY:  'empty',
}

HINTS = (
    'type a character = label cell | Delete = sprite | F2 = empty | F3 = undo',
    'arrows / click = select | Tab = next unidentified | wheel = zoom',
    'F4 = copy label to identical cells | Esc = save & quit',
)


# ---------------------------------------------------------------------------
# Pure helpers (also used by tests / dry-run)
# ---------------------------------------------------------------------------

def resolve_atlas(arg):
    """--atlas may be a path anywhere; the default lives in the repo root."""
    if arg and os.path.isfile(arg):
        return arg
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
    return os.path.join(root, arg or 'alienraid12x12.png')


def convert_black_to_alpha(surface):
    """Brightness -> alpha. Black becomes fully transparent, anti-aliased
    edges keep a smooth falloff, and coloured glyph pixels keep their hue."""
    w, h = surface.get_size()
    for y in range(h):
        for x in range(w):
            r, g, b, _ = surface.get_at((x, y))
            surface.set_at((x, y), (r, g, b, max(r, g, b)))
    return surface


def load_and_split(atlas_path, cell=CELL):
    """Load the atlas, convert black->alpha, return {(col, row): Surface}."""
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))
    atlas = pygame.image.load(atlas_path).convert_alpha()
    convert_black_to_alpha(atlas)
    w, h = atlas.get_size()
    cols, rows = w // cell, h // cell
    if cols * cell != w or rows * cell != h:
        print('warning: atlas {0}x{1} is not a whole multiple of {2}'.format(w, h, cell))
    cells = {}
    for r in range(rows):
        for c in range(cols):
            src = pygame.Rect(c * cell, r * cell, cell, cell)
            surf = pygame.Surface((cell, cell), pygame.SRCALPHA)
            surf.blit(atlas, (0, 0), src)
            cells[(c, r)] = surf
    return cells, cols, rows


def cell_has_ink(cell):
    for y in range(cell.get_height()):
        for x in range(cell.get_width()):
            if cell.get_at((x, y))[3] > 24:
                return True
    return False


def find_duplicate_groups(cells):
    """Group pixel-identical cells (inkless cells are skipped - they are
    all identical trivially and already pre-marked empty). Returns a list
    of groups, each a sorted list of (col, row) tuples."""
    from collections import defaultdict
    by_sig = defaultdict(list)
    for key, surf in cells.items():
        if not cell_has_ink(surf):
            continue
        by_sig[pygame.image.tostring(surf, 'RGBA')].append(key)
    groups = [sorted(v) for v in by_sig.values() if len(v) >= 2]
    groups.sort(key=lambda g: g[0])
    return groups


def batch_label(states, group, char):
    """Apply a character label to every cell in ``group`` that is still
    unidentified. Returns how many cells were labelled."""
    n = 0
    for cell in group:
        if states[cell]['state'] == STATE_TODO:
            states[cell] = {'state': STATE_CHAR, 'char': char}
            n += 1
    return n


def new_states(cols, rows, cells):
    """Every cell starts 'todo', except inkless cells which are pre-marked
    'empty' so you never have to look at blank space."""
    states = {}
    for r in range(rows):
        for c in range(cols):
            if cell_has_ink(cells[(c, r)]):
                states[(c, r)] = {'state': STATE_TODO}
            else:
                states[(c, r)] = {'state': STATE_EMPTY}
    return states


def export_cells(cells, directory=EXPORT_DIR):
    os.makedirs(directory, exist_ok=True)
    for (c, r), surf in sorted(cells.items()):
        pygame.image.save(surf, os.path.join(directory, 'cell_{0:02d}_{1:02d}.png'.format(c, r)))
    print('exported {0} cells to {1}/'.format(len(cells), directory))


def _key(c, r):
    return '{0}_{1}'.format(c, r)


def load_states(path):
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        data = json.load(f)
    states = {}
    for k, v in data['cells'].items():
        c, r = k.split('_')
        states[(int(c), int(r))] = v
    return data, states


def build_char_map(states):
    """char -> [col, row]; on duplicates the LAST cell wins and the dupes
    are returned so the user can fix them."""
    char_map = {}
    dupes = []
    for (c, r), v in states.items():
        if v['state'] == STATE_CHAR and v.get('char') is not None:
            ch = v['char']
            if ch in char_map:
                dupes.append((ch, tuple(char_map[ch]), (c, r)))
            char_map[ch] = [c, r]
    return char_map, dupes


def save_states(path, atlas_path, cell, cols, rows, states):
    """Atomic save (temp + replace) so a crash never destroys progress."""
    char_map, dupes = build_char_map(states)
    payload = {
        'atlas': os.path.basename(atlas_path),
        'cell_size': cell,
        'cols': cols,
        'rows': rows,
        'note': 'cells are keyed 0-based ("col_row"); the GUI/dry-run show 1-based',
        'export_dir': EXPORT_DIR,
        'cells': {_key(c, r): v for (c, r), v in sorted(states.items())},
        'char_map': char_map,
    }
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    os.replace(tmp, path)
    return dupes


def summarize(states):
    counts = {s: 0 for s in (STATE_TODO, STATE_CHAR, STATE_SPRITE, STATE_EMPTY)}
    for v in states.values():
        counts[v['state']] += 1
    return counts


def _identified(states):
    counts = summarize(states)
    return counts[STATE_CHAR] + counts[STATE_SPRITE] + counts[STATE_EMPTY]


# ---------------------------------------------------------------------------
# Dry run (headless: convert + export + report, never touches the JSON)
# ---------------------------------------------------------------------------

def dry_run(atlas_path, cell, export):
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    pygame.init()
    pygame.display.set_mode((1, 1))
    cells, cols, rows = load_and_split(atlas_path, cell)
    if export:
        export_cells(cells)
    states = new_states(cols, rows, cells)
    counts = summarize(states)
    print('atlas {0}: {1}x{2} cells (cell size {3})'.format(
        os.path.basename(atlas_path), cols, rows, cell))
    print('pre-marked empty (no ink): {0}'.format(counts[STATE_EMPTY]))
    print('needs identification:      {0}'.format(counts[STATE_TODO]))
    for r in range(rows):
        inked = sum(1 for c in range(cols) if cell_has_ink(cells[(c, r)]))
        print('  row {0}: {1}/{2} cells have ink'.format(r + 1, inked, cols))
    groups = find_duplicate_groups(cells)
    if groups:
        print('identical-glyph groups ({0}):'.format(len(groups)))
        for g in groups:
            print('  ' + ' '.join('({0},{1})'.format(c + 1, r + 1) for c, r in g))


# ---------------------------------------------------------------------------
# Interactive GUI
# ---------------------------------------------------------------------------

def _checker(surface, x, y, w, h, sq, c1=(30, 36, 42), c2=(39, 46, 53)):
    for yy in range(0, h, sq):
        for xx in range(0, w, sq):
            color = c1 if ((xx // sq) + (yy // sq)) % 2 == 0 else c2
            surface.fill(color, (x + xx, y + yy, min(sq, w - xx), min(sq, h - yy)))


def _next_todo(states, cols, rows, after):
    order = [(c, r) for r in range(rows) for c in range(cols)]
    idx = order.index(after)
    for i in range(1, len(order) + 1):
        cell = order[(idx + i) % len(order)]
        if states[cell]['state'] == STATE_TODO:
            return cell
    return after


def run_gui(atlas_path, cell, json_path, export):
    pygame.init()
    screen = pygame.display.set_mode((1280, 760), pygame.RESIZABLE)
    pygame.display.set_caption(
        'AlienRaid charset identification — {0}'.format(os.path.basename(atlas_path)))
    clock = pygame.time.Clock()

    cells, cols, rows = load_and_split(atlas_path, cell)
    if export:
        export_cells(cells)
    groups_by_cell = {}
    for group in find_duplicate_groups(cells):
        for member in group:
            groups_by_cell[member] = group
    loaded = load_states(json_path)
    if loaded is not None:
        _, states = loaded
        for k, v in new_states(cols, rows, cells).items():
            states.setdefault(k, v)
        print('resumed {0} ({1} cells identified)'.format(json_path, _identified(states)))
    else:
        states = new_states(cols, rows, cells)
        print('fresh run: {0} cells need identification'.format(
            summarize(states)[STATE_TODO]))

    def save():
        dupes = save_states(json_path, atlas_path, cell, cols, rows, states)
        return dupes

    selected = None
    for (c, r) in sorted(states):
        if states[(c, r)]['state'] == STATE_TODO:
            selected = (c, r)
            break
    if selected is None:
        selected = (0, 0)

    font = pygame.font.Font(None, 22)
    font_big = pygame.font.Font(None, 34)
    scaled = {}  # zoom -> {(c, r): scaled surface}

    def cell_scaled(c, r, zoom):
        bucket = scaled.get(zoom)
        if bucket is None:
            bucket = scaled[zoom] = {}
        surf = bucket.get((c, r))
        if surf is None:
            surf = pygame.transform.scale(cells[(c, r)], (cell * zoom, cell * zoom))
            bucket[(c, r)] = surf
        return surf

    def assign(state, char=None):
        entry = {'state': state}
        if char is not None:
            entry['char'] = char
        states[selected] = entry
        save()
        return _next_todo(states, cols, rows, selected)

    running = True
    zw = 3          # overview zoom (px per atlas px)
    ovx = ovy = 0   # placeholders until the first layout pass
    needs_fit = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                needs_fit = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_TAB:
                    selected = _next_todo(states, cols, rows, selected)
                elif event.key == pygame.K_DELETE:
                    selected = assign(STATE_SPRITE)
                elif event.key == pygame.K_F2:
                    selected = assign(STATE_EMPTY)
                elif event.key == pygame.K_F3:
                    states[selected] = {'state': STATE_TODO}
                    save()
                elif event.key == pygame.K_F4:
                    st = states[selected]
                    if st['state'] == STATE_CHAR:
                        group = groups_by_cell.get(selected)
                        if group and batch_label(states, group, st['char']):
                            save()
                elif event.key == pygame.K_UP:
                    selected = (selected[0], (selected[1] - 1) % rows)
                elif event.key == pygame.K_DOWN:
                    selected = (selected[0], (selected[1] + 1) % rows)
                elif event.key == pygame.K_LEFT:
                    selected = ((selected[0] - 1) % cols, selected[1])
                elif event.key == pygame.K_RIGHT:
                    selected = ((selected[0] + 1) % cols, selected[1])
                else:
                    ch = event.unicode
                    if ch and ch.isprintable():
                        selected = assign(STATE_CHAR, ch)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if event.button in (4, 5):
                    zw = max(1, min(8, zw + (1 if event.button == 4 else -1)))
                else:
                    c = (mx - ovx) // (cell * zw)
                    r = (my - ovy) // (cell * zw)
                    if 0 <= c < cols and 0 <= r < rows:
                        selected = (c, r)
            elif event.type == pygame.MOUSEWHEEL:
                zw = max(1, min(8, zw + event.y))

        # --- layout from current window size (adapts to tiling WMs) --------
        W, H = screen.get_size()
        right_w = max(280, min(430, W // 3))
        left_w = W - right_w - 56
        if needs_fit:   # fit zoom to width once, then keep the user's zoom
            zw = max(1, min(8, left_w // (cell * cols)))
            needs_fit = False
        overview_w = cell * cols * zw
        overview_h = cell * rows * zw
        ovx = 20
        ovy = max(70, (H - overview_h) // 2)
        bz = max(4, min(40, (H - 260) // cell))
        big = cell * bz
        bx = W - right_w + 30

        # --- draw ----------------------------------------------------------
        screen.fill((12, 16, 20))
        counts = summarize(states)

        head = '{0}  {1}x{2} cells'.format(os.path.basename(atlas_path), cols, rows)
        screen.blit(font.render(head, True, (200, 210, 220)), (20, 14))
        screen.blit(font.render(
            'characters {0} | sprites {1} | empty {2} | remaining {3}'.format(
                counts[STATE_CHAR], counts[STATE_SPRITE],
                counts[STATE_EMPTY], counts[STATE_TODO]),
            True, (120, 132, 144)), (20, 42))

        # overview grid
        _checker(screen, ovx, ovy, overview_w, overview_h, max(3, zw))
        for r in range(rows):
            for c in range(cols):
                x = ovx + c * cell * zw
                y = ovy + r * cell * zw
                screen.blit(cell_scaled(c, r, zw), (x, y))
                st = states[(c, r)]['state']
                if st in STATE_COLORS:
                    ov = pygame.Surface((cell * zw, cell * zw), pygame.SRCALPHA)
                    ov.fill(STATE_COLORS[st])
                    screen.blit(ov, (x, y))
                if (c, r) == selected:
                    pygame.draw.rect(screen, (255, 220, 80),
                                     (x - 1, y - 1, cell * zw + 2, cell * zw + 2), 2)

        # right panel: big selected cell
        pygame.draw.rect(screen, (18, 23, 28), (W - right_w, 0, right_w, H))
        pygame.draw.line(screen, (40, 48, 56), (W - right_w, 0), (W - right_w, H))
        c0, r0 = selected
        n = r0 * cols + c0 + 1
        screen.blit(font.render(
            'cell ({0},{1})  #{2}/{3}'.format(c0 + 1, r0 + 1, n, cols * rows),
            True, (230, 240, 250)), (bx, 40))
        st = states[selected]['state']
        screen.blit(font.render(STATE_LABEL[st], True, (150, 160, 170)), (bx, 66))
        yy = 92
        if st == STATE_CHAR:
            screen.blit(font_big.render(repr(states[selected].get('char', '')),
                                        True, (255, 240, 150)), (bx, yy))
            yy += 40
        siblings = [g for g in groups_by_cell.get(selected, []) if g != selected]
        if siblings:
            text = 'identical cells: ' + ', '.join(
                '({0},{1})'.format(c + 1, r + 1) for c, r in siblings[:6])
            screen.blit(font.render(text, True, (150, 160, 170)), (bx, yy))
            screen.blit(font.render('F4 = label them all the same', True,
                                    (110, 122, 134)), (bx, yy + 22))
            yy += 48
        by = max(160, yy + 12)
        _checker(screen, bx, by, big, big, max(3, bz))
        screen.blit(cell_scaled(c0, r0, bz), (bx, by))
        pygame.draw.rect(screen, (80, 92, 104), (bx, by, big, big), 1)

        # hints
        y = H - 46
        for line in HINTS:
            screen.blit(font.render(line, True, (110, 122, 134)), (20, y))
            y += 24

        pygame.display.flip()
        clock.tick(60)

    dupes = save()
    counts = summarize(states)
    print('--- done ---')
    print('saved {0}'.format(json_path))
    print('characters {0} | sprites {1} | empty {2} | unidentified {3}'.format(
        counts[STATE_CHAR], counts[STATE_SPRITE], counts[STATE_EMPTY], counts[STATE_TODO]))
    char_map, _ = build_char_map(states)
    print('char -> cell map ({0} characters):'.format(len(char_map)))
    for ch in sorted(char_map):
        print('  {0!r}: {1}'.format(ch, char_map[ch]))
    for ch, first, second in dupes:
        print('warning: character {0!r} appears in cells {1} and {2} '
              '(using {1})'.format(ch, first, second))
    pygame.quit()
    return 0


# ---------------------------------------------------------------------------

def main(argv):
    ap = argparse.ArgumentParser(
        description='Identify the glyphs in the hand-drawn bitmap font.',
        epilog='In the GUI: type a character to label the selected cell, '
               'Delete = sprite, F2 = empty, F3 = undo, Tab = next '
               'unidentified, Esc = save & quit.')
    ap.add_argument('--atlas', default='alienraid12x12.png',
                    help='atlas PNG (default: alienraid12x12.png in repo root)')
    ap.add_argument('--cell-size', type=int, default=CELL)
    ap.add_argument('--json', default=DEFAULT_JSON, help='output JSON path')
    ap.add_argument('--no-export', action='store_true',
                    help="don't write the individual cell PNGs")
    ap.add_argument('--dry-run', action='store_true',
                    help='headless: convert, export and report; no GUI, no JSON')
    args = ap.parse_args(argv)

    atlas_path = resolve_atlas(args.atlas)
    if not os.path.isfile(atlas_path):
        raise SystemExit('atlas not found: {0}'.format(atlas_path))

    if args.dry_run:
        dry_run(atlas_path, args.cell_size, not args.no_export)
        return 0
    return run_gui(atlas_path, args.cell_size, args.json, not args.no_export)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
