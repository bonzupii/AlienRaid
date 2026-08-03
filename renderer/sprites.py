#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SpriteLoader

All mobs, the player, items, the trails, the ship and corpses are rendered as
**procedurally generated graphics**: small drawings built from
``pygame.draw`` primitives (ellipses, circles, polygons, lines), cached as
``pygame.Surface`` objects keyed by ``(sprite_id, color)``.

No font glyph is ever used for these: every glyph that was previously paired
with a mob/player/equipment/landscape is treated as a sprite and drawn here.
"""

import pygame

from renderer.palette import shade

TILE = 12

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def _ellipse(surf, color, rect):
    pygame.draw.ellipse(surf, color, pygame.Rect(rect))


def _circle(surf, color, center, radius):
    pygame.draw.circle(surf, color, (int(center[0]), int(center[1])), int(radius))


def _poly(surf, color, points):
    pygame.draw.polygon(surf, color, [(int(x), int(y)) for (x, y) in points])


def _line(surf, color, a, b, width=1):
    pygame.draw.line(surf, color, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), int(width))


# ---------------------------------------------------------------------------
# Creature recipes. Each draws into a 12x12 SRCALPHA surface, tinted by the
# entity's base color (darker/lighter shades are derived from it).
# ---------------------------------------------------------------------------

def _sprite_player(s, c):
    dark = shade(c, 0.55)
    # tentacles
    _line(s, dark, (5, 9), (2, 11), 1)
    _line(s, dark, (7, 9), (10, 11), 1)
    _line(s, dark, (4, 9), (2, 7), 1)
    _line(s, dark, (8, 9), (10, 7), 1)
    # body
    _ellipse(s, c, (3, 4, 6, 7))
    _ellipse(s, shade(c, 1.3), (4, 5, 2, 3))
    # head
    _circle(s, shade(c, 1.15), (6, 4), 3)
    # eyes
    _circle(s, WHITE, (5, 3), 1)
    _circle(s, WHITE, (7, 3), 1)
    _circle(s, BLACK, (5, 3), 1)
    _circle(s, BLACK, (7, 3), 1)


def _sprite_kangaroo_like(s, c, body_rect, head_pos, head_r, ears=True, tail=True, ears_len=3):
    dark = shade(c, 0.6)
    if tail:
        _line(s, dark, (body_rect[0] + 1, body_rect[1] + body_rect[3] - 2),
              (body_rect[0] - 2, body_rect[1] + 2), 1)
    _ellipse(s, c, body_rect)
    _ellipse(s, shade(c, 1.25), (body_rect[0] + 1, body_rect[1] + 1,
                                 body_rect[2] - 2, body_rect[3] - 2))
    if ears:
        ex, ey = head_pos
        _poly(s, shade(c, 0.8), [(ex - 2, ey - 1), (ex - 2, ey - 1 - ears_len), (ex - 1, ey - 1)])
        _poly(s, shade(c, 0.8), [(ex + 1, ey - 1), (ex + 1, ey - 1 - ears_len), (ex + 2, ey - 1)])
    _circle(s, c, head_pos, head_r)
    # eye
    _circle(s, BLACK, (head_pos[0] + 1, head_pos[1] - 1), 1)


def _sprite_kanga(s, c):
    _sprite_kangaroo_like(s, c, (3, 5, 7, 5), (9, 4), 2, ears_len=4)
    _line(s, shade(c, 0.6), (4, 10), (4, 11), 1)
    _line(s, shade(c, 0.6), (8, 10), (8, 11), 1)


def _sprite_joey(s, c):
    _sprite_kangaroo_like(s, c, (4, 6, 5, 4), (7, 5), 2, ears_len=3)


def _sprite_wallaby(s, c):
    _sprite_kangaroo_like(s, c, (4, 5, 6, 5), (9, 4), 2, ears_len=4)


def _sprite_wallaroo(s, c):
    _sprite_kangaroo_like(s, c, (3, 6, 7, 4), (9, 5), 2, ears_len=3)


def _sprite_tree_kanga(s, c):
    # climbing pose: upright body
    _sprite_kangaroo_like(s, c, (4, 3, 5, 7), (6, 2), 2, ears_len=2)
    _line(s, shade(c, 0.6), (3, 6), (2, 8), 1)  # arm
    _line(s, shade(c, 0.6), (9, 6), (10, 8), 1)


def _sprite_dingo(s, c):
    dark = shade(c, 0.6)
    _line(s, dark, (2, 4), (1, 6), 1)          # tail up
    _ellipse(s, c, (2, 6, 8, 4))               # body
    # legs
    _line(s, dark, (3, 10), (3, 11), 1)
    _line(s, dark, (6, 10), (6, 11), 1)
    # head
    _circle(s, c, (10, 5), 2)
    _poly(s, shade(c, 0.8), [(9, 3), (9, 1), (10, 3)])
    _poly(s, shade(c, 0.8), [(11, 3), (11, 1), (12, 3)])
    _circle(s, BLACK, (11, 5), 1)


def _sprite_goanna(s, c):
    dark = shade(c, 0.6)
    _line(s, dark, (2, 8), (1, 6), 2)          # tail
    _ellipse(s, c, (2, 7, 8, 3))               # body
    _line(s, dark, (4, 10), (4, 11), 1)
    _line(s, dark, (7, 10), (7, 11), 1)
    _circle(s, c, (10, 6), 2)                  # head
    _circle(s, BLACK, (11, 6), 1)
    _line(s, shade(c, 1.4), (10, 7), (11, 8), 1)  # tongue


def _sprite_killer_bee(s, c):
    dark = shade(c, 0.5)
    _ellipse(s, (200, 200, 255), (3, 2, 6, 3))   # wings
    _circle(s, c, (6, 6), 3)                     # body
    _line(s, BLACK, (4, 5), (8, 5), 1)           # stripes
    _line(s, BLACK, (4, 7), (8, 7), 1)
    _line(s, shade(c, 0.5), (6, 9), (6, 11), 1)  # stinger
    _line(s, BLACK, (5, 3), (4, 1), 1)           # antennae
    _line(s, BLACK, (7, 3), (8, 1), 1)
    _circle(s, WHITE, (5, 5), 1)


def _sprite_dropbear(s, c):
    dark = shade(c, 0.6)
    _circle(s, c, (6, 7), 4)                     # body
    _circle(s, shade(c, 0.85), (4, 4), 2)        # ears
    _circle(s, shade(c, 0.85), (8, 4), 2)
    _circle(s, (255, 220, 80), (5, 6), 1)        # eyes
    _circle(s, (255, 220, 80), (7, 6), 1)
    _line(s, dark, (4, 11), (3, 10), 1)          # claws
    _line(s, dark, (6, 11), (6, 10), 1)
    _line(s, dark, (8, 11), (9, 10), 1)


def _sprite_taipan(s, c):
    dark = shade(c, 0.55)
    _line(s, c, (1, 3), (4, 6), 2)
    _line(s, c, (4, 6), (3, 8), 2)
    _line(s, c, (3, 8), (7, 9), 2)
    _circle(s, c, (8, 9), 2)                     # head
    _line(s, shade(c, 1.5), (9, 9), (11, 9), 1)  # tongue
    _circle(s, BLACK, (9, 9), 1)


def _sprite_emu(s, c):
    dark = shade(c, 0.6)
    _line(s, dark, (5, 10), (5, 11), 1)
    _line(s, dark, (7, 10), (7, 11), 1)
    _ellipse(s, c, (4, 5, 5, 6))                 # body
    _line(s, c, (6, 5), (6, 2), 2)               # neck
    _circle(s, c, (6, 1), 2)                     # head
    _poly(s, shade(c, 0.7), [(8, 1), (10, 2), (8, 2)])  # beak
    _circle(s, BLACK, (7, 1), 1)


def _sprite_wombat(s, c):
    dark = shade(c, 0.6)
    _ellipse(s, c, (2, 6, 8, 6))                 # body
    _circle(s, c, (9, 8), 2)                     # nose area
    _circle(s, shade(c, 0.7), (10, 8), 1)        # nose
    _circle(s, shade(c, 0.8), (4, 5), 2)         # ears
    _circle(s, shade(c, 0.8), (7, 5), 2)
    _circle(s, BLACK, (3, 6), 1)
    _circle(s, BLACK, (8, 6), 1)
    _line(s, dark, (3, 11), (3, 10), 1)
    _line(s, dark, (8, 11), (8, 10), 1)


def _sprite_magpie(s, c):
    dark = shade(c, 0.5)
    _ellipse(s, c, (2, 6, 6, 4))                 # body
    _ellipse(s, WHITE, (4, 6, 3, 2))             # white patch
    _circle(s, c, (9, 5), 2)                     # head
    _poly(s, (255, 200, 60), [(11, 5), (9, 6), (11, 7)])  # beak
    _line(s, dark, (3, 8), (6, 9), 2)            # wing
    _circle(s, BLACK, (9, 5), 1)


def _sprite_cassowary(s, c):
    dark = shade(c, 0.55)
    _line(s, dark, (4, 10), (4, 11), 1)
    _line(s, dark, (8, 10), (8, 11), 1)
    _poly(s, c, [(3, 11), (4, 4), (9, 4), (9, 11)])  # body
    _line(s, c, (6, 4), (6, 1), 1)               # neck
    _circle(s, c, (6, 1), 2)                     # head
    _poly(s, shade(c, 1.5), [(6, 0), (7, 0), (6, 2), (5, 0)])  # crest
    _poly(s, (255, 160, 60), [(5, 2), (8, 2), (6, 3)])       # beak
    _circle(s, BLACK, (6, 2), 1)


def _sprite_crocodile(s, c):
    dark = shade(c, 0.6)
    _line(s, dark, (2, 8), (1, 7), 1)            # tail
    _ellipse(s, c, (2, 7, 8, 3))                 # body
    _line(s, dark, (4, 10), (4, 11), 1)
    _line(s, dark, (7, 10), (7, 11), 1)
    _poly(s, c, [(10, 7), (12, 7), (12, 9), (10, 9)])  # snout
    _circle(s, shade(c, 1.3), (9, 7), 1)         # eye bump
    _circle(s, BLACK, (9, 7), 1)
    _line(s, WHITE, (11, 8), (12, 8), 1)         # teeth


# ---------------------------------------------------------------------------
# Environment / actor sprites
# ---------------------------------------------------------------------------

def _sprite_corpse(s, c):
    dark = shade(c, 0.7)
    _line(s, dark, (3, 3), (9, 9), 2)            # X
    _line(s, dark, (9, 3), (3, 9), 2)
    _circle(s, shade(c, 1.3), (3, 3), 1)
    _circle(s, shade(c, 1.3), (9, 9), 1)


def _sprite_trail_down(s, c):
    _poly(s, c, [(3, 4), (9, 4), (6, 9)])
    _line(s, shade(c, 1.4), (4, 5), (8, 5), 1)


def _sprite_trail_up(s, c):
    _poly(s, c, [(3, 8), (9, 8), (6, 3)])
    _line(s, shade(c, 1.4), (4, 7), (8, 7), 1)


def _sprite_ship(s, c):
    _ellipse(s, shade(c, 0.6), (1, 8, 10, 2))    # landing legs shadow
    _line(s, shade(c, 0.8), (3, 9), (3, 11), 1)
    _line(s, shade(c, 0.8), (9, 9), (9, 11), 1)
    _ellipse(s, c, (1, 7, 10, 3))                # saucer
    _ellipse(s, shade(c, 1.35), (2, 7, 3, 2))
    _circle(s, shade(c, 1.2), (6, 6), 3)         # dome
    _circle(s, (120, 255, 200), (6, 6), 1)       # cockpit glow


def _sprite_part(s, c):
    dark = shade(c, 0.6)
    _poly(s, c, [(6, 1), (9, 3), (9, 6), (6, 8), (3, 6), (3, 3)])  # hexagon
    _circle(s, dark, (6, 4), 2)
    _circle(s, shade(c, 1.5), (6, 4), 1)


# ---------------------------------------------------------------------------
# Item / equipment icon recipes
# ---------------------------------------------------------------------------

def _icon_cross(s, c):
    _ellipse(s, shade(c, 0.85), (1, 1, 10, 10))
    _rect = pygame.Rect(5, 2, 2, 8)
    pygame.draw.rect(s, WHITE, _rect)
    pygame.draw.rect(s, WHITE, pygame.Rect(2, 5, 8, 2))


def _icon_bottle(s, c):
    _ellipse(s, c, (3, 1, 6, 2))                 # cap
    pygame.draw.rect(s, c, pygame.Rect(4, 2, 4, 2))   # neck
    pygame.draw.rect(s, c, pygame.Rect(3, 4, 6, 6))   # body
    pygame.draw.rect(s, shade(c, 1.4), pygame.Rect(4, 5, 4, 2))  # label


def _icon_grenade(s, c):
    _circle(s, shade(c, 0.7), (6, 6), 4)
    _circle(s, c, (6, 6), 3)
    _line(s, shade(c, 0.5), (6, 2), (6, 3), 1)   # pin
    _circle(s, shade(c, 1.5), (7, 2), 1)


def _icon_gun(s, c):
    pygame.draw.rect(s, c, pygame.Rect(2, 5, 8, 2))   # barrel
    pygame.draw.rect(s, shade(c, 0.7), pygame.Rect(8, 3, 2, 5))  # grip
    pygame.draw.rect(s, shade(c, 1.4), pygame.Rect(2, 5, 2, 1))


def _icon_bolt(s, c):
    _poly(s, c, [(6, 1), (9, 1), (5, 6), (7, 6), (3, 11), (8, 5), (6, 5), (9, 1)])
    _poly(s, shade(c, 1.5), [(7, 1), (8, 1), (5, 5), (6, 5), (4, 8), (6, 3)])


def _icon_tentacle(s, c):
    _line(s, c, (2, 2), (5, 7), 2)
    _line(s, c, (5, 7), (3, 11), 2)
    _line(s, c, (5, 7), (8, 10), 2)
    _line(s, c, (5, 7), (10, 9), 2)
    _circle(s, shade(c, 1.4), (2, 2), 1)


def _icon_shield(s, c):
    _poly(s, c, [(6, 1), (10, 3), (10, 7), (6, 11), (2, 7), (2, 3)])
    _poly(s, shade(c, 1.3), [(6, 2), (8, 3), (8, 7), (6, 9), (4, 7), (4, 3)])
    _line(s, shade(c, 0.6), (6, 3), (6, 9), 1)


def _icon_twig(s, c):
    _line(s, c, (2, 10), (10, 2), 1)
    _ellipse(s, shade(c, 1.3), (1, 8, 2, 3))
    _ellipse(s, shade(c, 1.3), (7, 3, 2, 3))
    _ellipse(s, shade(c, 1.3), (4, 5, 2, 3))


def _icon_hat(s, c):
    pygame.draw.rect(s, shade(c, 0.7), pygame.Rect(2, 8, 8, 2))   # brim
    _poly(s, c, [(4, 8), (4, 3), (8, 3), (8, 8)])                # dome
    pygame.draw.rect(s, shade(c, 1.3), pygame.Rect(5, 4, 2, 3))  # band


def _icon_neck(s, c):
    pygame.draw.circle(s, c, (6, 6), 4, 2)       # ring
    _circle(s, shade(c, 1.4), (6, 6), 1)         # gem


def _icon_vest(s, c):
    _poly(s, c, [(4, 2), (8, 2), (9, 6), (8, 11), (4, 11), (3, 6)])
    _line(s, shade(c, 0.6), (6, 2), (6, 11), 1)
    _line(s, shade(c, 0.6), (4, 2), (6, 6), 1)
    _line(s, shade(c, 0.6), (8, 2), (6, 6), 1)


def _icon_boomerang(s, c):
    _line(s, c, (2, 2), (10, 8), 2)
    _line(s, c, (10, 8), (6, 11), 2)
    _line(s, shade(c, 1.4), (4, 4), (9, 8), 1)


def _icon_ration(s, c):
    pygame.draw.rect(s, c, pygame.Rect(3, 3, 6, 6))      # can
    pygame.draw.rect(s, shade(c, 1.4), pygame.Rect(3, 3, 6, 2))
    _circle(s, shade(c, 0.7), (6, 6), 1)


def _icon_tea(s, c):
    pygame.draw.rect(s, c, pygame.Rect(2, 6, 6, 4))      # cup
    _line(s, c, (8, 6), (10, 7), 1)
    _line(s, c, (10, 7), (10, 9), 1)
    _line(s, c, (8, 9), (10, 9), 1)
    _line(s, shade(c, 0.6), (3, 6), (3, 5), 1)           # steam
    _line(s, shade(c, 0.6), (5, 6), (5, 4), 1)
    _line(s, shade(c, 0.6), (7, 6), (7, 5), 1)


def _icon_star(s, c):
    _poly(s, c, [(6, 1), (7, 4), (10, 4), (8, 6), (9, 10), (6, 8), (3, 10), (4, 6), (2, 4), (5, 4)])
    _circle(s, shade(c, 1.5), (6, 5), 1)


def _sprite_unknown(s, c):
    pygame.draw.rect(s, (255, 0, 255), pygame.Rect(0, 0, TILE, TILE))


# Registry: sprite_id -> recipe callable(surface, color)
RECIPES = {
    'player': _sprite_player,
    'kanga': _sprite_kanga,
    'joey': _sprite_joey,
    'wallaby': _sprite_wallaby,
    'wallaroo': _sprite_wallaroo,
    'tree_kanga': _sprite_tree_kanga,
    'dingo': _sprite_dingo,
    'goanna': _sprite_goanna,
    'killer_bee': _sprite_killer_bee,
    'dropbear': _sprite_dropbear,
    'taipan': _sprite_taipan,
    'emu': _sprite_emu,
    'wombat': _sprite_wombat,
    'magpie': _sprite_magpie,
    'cassowary': _sprite_cassowary,
    'crocodile': _sprite_crocodile,
    'corpse': _sprite_corpse,
    'trail_down': _sprite_trail_down,
    'trail_up': _sprite_trail_up,
    'ship': _sprite_ship,
    'part': _sprite_part,
    # item/equipment icons
    'icon_cross': _icon_cross,
    'icon_bottle': _icon_bottle,
    'icon_grenade': _icon_grenade,
    'icon_gun': _icon_gun,
    'icon_bolt': _icon_bolt,
    'icon_tentacle': _icon_tentacle,
    'icon_shield': _icon_shield,
    'icon_twig': _icon_twig,
    'icon_hat': _icon_hat,
    'icon_neck': _icon_neck,
    'icon_vest': _icon_vest,
    'icon_boomerang': _icon_boomerang,
    'icon_ration': _icon_ration,
    'icon_tea': _icon_tea,
    'icon_star': _icon_star,
}


class SpriteLoader:
    """Caches procedurally generated entity sprites by (sprite_id, color)."""

    def __init__(self, tile=TILE):
        self.tile = tile
        self._cache = {}

    def get(self, sprite_id, color):
        key = (sprite_id, color)
        surf = self._cache.get(key)
        if surf is None:
            surf = pygame.Surface((self.tile, self.tile), pygame.SRCALPHA)
            recipe = RECIPES.get(sprite_id, _sprite_unknown)
            recipe(surf, color)
            self._cache[key] = surf
        return surf
