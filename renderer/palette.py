#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RGB color palette. Replaces every ``libtcod.Color(...)`` / ``libtcod.xxx``
color constant in the original game. All colors are plain ``(r, g, b)``
tuples so they can be passed straight to pygame and to the sprite loader.
"""

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

RED = (255, 0, 0)
LIGHT_RED = (255, 128, 128)
DARK_RED = (192, 0, 0)
DARKER_RED = (128, 0, 0)

GREEN = (0, 255, 0)
LIGHT_GREEN = (128, 255, 128)
DARK_GREEN = (0, 128, 0)
DARKER_GREEN = (0, 64, 0)

BLUE = (0, 0, 255)
LIGHT_BLUE = (128, 128, 255)
DARK_BLUE = (0, 0, 128)

CYAN = (0, 255, 255)
LIGHT_CYAN = (128, 255, 255)
DARK_CYAN = (0, 128, 128)

MAGENTA = (255, 0, 255)
PURPLE = (128, 0, 255)
DARK_PURPLE = (64, 0, 128)
VIOLET = (128, 0, 255)
LIGHT_VIOLET = (192, 128, 255)
DARK_VIOLET = (64, 0, 128)

YELLOW = (255, 255, 0)
LIGHT_YELLOW = (255, 255, 128)
DARK_YELLOW = (128, 128, 0)

ORANGE = (255, 128, 0)
LIGHT_ORANGE = (255, 192, 128)
DARK_ORANGE = (128, 64, 0)

BROWN = (166, 124, 82)
DARK_BROWN = (92, 64, 51)

SILVER = (203, 204, 206)
GOLD = (255, 215, 0)

GRAY = (128, 128, 128)
LIGHT_GRAY = (192, 192, 192)
DARK_GRAY = (128, 128, 128)
DARKER_GRAY = (64, 64, 64)

# Custom colors used by the original game's creatures and items.
KANGA_RED = (218, 42, 32)
DINGO_BROWN = (165, 42, 42)
GOANNA_GREEN = (25, 42, 0)
DROPBEAR_GREY = (33, 33, 33)
PLAYER_GREEN = (15, 77, 0)
MORPHINE_BROWN = (40, 30, 0)
MEDKIT_RED = (255, 30, 0)
TWIG_BROWN = (53, 38, 0)
HAT_GREEN = (20, 38, 0)
VEST_GREY = (30, 30, 30)
RAYGUN_SILVER = (180, 180, 180)
STUN_GREEN = (0, 40, 0)

# Terrain colors (matches the old game's outback palette).
DARK_WALL = (100, 20, 10)
DARK_GROUND = (170, 90, 10)
LIGHT_WALL = (140, 60, 10)
LIGHT_GROUND = (210, 130, 50)

# Default colors keyed by the names the old code used, for message text.
NAMED = {
    'white': WHITE,
    'black': BLACK,
    'red': RED,
    'light_red': LIGHT_RED,
    'dark_red': DARK_RED,
    'darker_red': DARKER_RED,
    'green': GREEN,
    'light_green': LIGHT_GREEN,
    'dark_green': DARK_GREEN,
    'darker_green': DARKER_GREEN,
    'blue': BLUE,
    'light_blue': LIGHT_BLUE,
    'dark_blue': DARK_BLUE,
    'cyan': CYAN,
    'light_cyan': LIGHT_CYAN,
    'dark_cyan': DARK_CYAN,
    'magenta': MAGENTA,
    'purple': PURPLE,
    'dark_purple': DARK_PURPLE,
    'violet': VIOLET,
    'light_violet': LIGHT_VIOLET,
    'dark_violet': DARK_VIOLET,
    'yellow': YELLOW,
    'light_yellow': LIGHT_YELLOW,
    'dark_yellow': DARK_YELLOW,
    'orange': ORANGE,
    'light_orange': LIGHT_ORANGE,
    'dark_orange': DARK_ORANGE,
    'brown': BROWN,
    'dark_brown': DARK_BROWN,
    'silver': SILVER,
    'gold': GOLD,
    'gray': GRAY,
    'light_gray': LIGHT_GRAY,
    'dark_gray': DARK_GRAY,
    'darker_gray': DARKER_GRAY,
}


def shade(color, factor):
    """Darken (factor < 1) or lighten (factor > 1) an RGB color."""
    r, g, b = color
    return (max(0, min(255, int(r * factor))),
            max(0, min(255, int(g * factor))),
            max(0, min(255, int(b * factor))))
