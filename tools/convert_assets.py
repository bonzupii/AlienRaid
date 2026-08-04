#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert the game's PNG assets to 32-bit RGBA and strip corrupt iCCP chunks.

Why: the menu background was a paletted (8-bit) PNG, so pygame loaded it as
an 8-bit surface and ``pygame.transform.smoothscale`` crashed the main menu
("Only 24-bit or 32-bit surfaces can be smoothly scaled"). libpng also warns
about a corrupt iCCP (embedded colour profile) chunk in the assets.

Re-encoding every asset as 32-bit RGBA fixes both problems at the source —
no defensive guards in code. PNG re-encoding is lossless, and this script
verifies the pixels are identical before and after.

Run inside the dev shell:
    nix develop -c python tools/convert_assets.py alienraid12x12.png menu_background.png
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame


def convert(path):
    if not os.path.isfile(path):
        raise SystemExit('not found: ' + path)

    pygame.display.set_mode((1, 1))
    original = pygame.image.load(path)
    converted = original.convert_alpha()  # 32-bit RGBA, loses nothing
    pixels = pygame.image.tostring(converted, 'RGBA')

    # Write to a temp path, verify, then atomically replace the original —
    # a failed check can never destroy the original asset.
    tmp = path + '.new'
    pygame.image.save(converted, tmp)

    reloaded = pygame.image.load(tmp)
    if pygame.image.tostring(reloaded.convert_alpha(), 'RGBA') != pixels:
        raise SystemExit('pixel mismatch (left at {0}): {1}'.format(tmp, path))
    with open(tmp, 'rb') as f:
        has_iccp = b'iCCP' in f.read()
    if has_iccp:
        raise SystemExit('iCCP chunk still present (left at {0}): {1}'.format(tmp, path))
    os.replace(tmp, path)

    w, h = reloaded.get_size()
    print('converted {0} -> 32-bit RGBA {1}x{2}'.format(path, w, h))


if __name__ == '__main__':
    for path in sys.argv[1:]:
        convert(path)
