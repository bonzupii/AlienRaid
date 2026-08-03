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

12x12 style guide:
  * dark rim around each body part (silhouette definition),
  * main fill in the species colour,
  * a light top highlight for volume,
  * creatures face right and stand on the ground line (y = 10..11),
  * eyes are 1px dark dots, with a white glint where room allows.
"""

import pygame

from renderer.palette import shade

TILE = 12

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
EYE = (20, 20, 20)


def _ellipse(surf, color, rect):
    pygame.draw.ellipse(surf, color, pygame.Rect(rect))


def _circle(surf, color, center, radius):
    pygame.draw.circle(surf, color, (int(center[0]), int(center[1])), int(radius))


def _poly(surf, color, points):
    pygame.draw.polygon(surf, color, [(int(x), int(y)) for (x, y) in points])


def _line(surf, color, a, b, width=1):
    pygame.draw.line(surf, color, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), int(width))


def _oval(surf, c, rect):
    """Filled ellipse with a dark rim and a light top highlight."""
    pygame.draw.ellipse(surf, shade(c, 0.5),
                        (rect[0] - 1, rect[1] - 1, rect[2] + 2, rect[3] + 2))
    pygame.draw.ellipse(surf, c, rect)
    pygame.draw.ellipse(surf, shade(c, 1.35),
                        (rect[0] + 1, rect[1] + 1, max(1, rect[2] - 3), 1))


def _eye(surf, x, y):
    _circle(surf, EYE, (x, y), 1)


def _leg(surf, c, x, y0):
    """A simple dark leg from (x, y0) down to the ground line."""
    _line(surf, shade(c, 0.5), (x, y0), (x, 11), 1)


# ---------------------------------------------------------------------------
# Creature recipes. Each draws into a 12x12 SRCALPHA surface, tinted by the
# entity's base color (darker/lighter shades are derived from it).
# ---------------------------------------------------------------------------

def _sprite_player(s, c):
    dark = shade(c, 0.55)
    # tentacle arms
    for (x0, y0, x1, y1) in ((4, 8, 1, 11), (5, 8, 3, 11), (7, 8, 9, 11), (8, 8, 11, 10)):
        _line(s, dark, (x0, y0), (x1, y1), 2)
    # body
    _oval(s, c, (3, 4, 6, 7))
    _ellipse(s, shade(c, 1.2), (4, 5, 3, 2))          # chest
    # head
    _circle(s, dark, (6, 3), 4)
    _circle(s, c, (6, 3), 3)
    # big alien eyes
    _circle(s, (235, 245, 255), (5, 2), 1)
    _circle(s, (235, 245, 255), (7, 2), 1)
    _circle(s, EYE, (5, 2), 1)
    _circle(s, EYE, (7, 2), 1)
    # antennae
    _line(s, dark, (4, 0), (5, 1), 1)
    _line(s, dark, (8, 0), (7, 1), 1)


def _sprite_kanga(s, c):
    dark = shade(c, 0.5)
    # tail sweeping down-left
    _line(s, dark, (3, 10), (1, 6), 2)
    _line(s, dark, (1, 6), (0, 5), 1)
    # back leg + foot
    _line(s, dark, (3, 9), (5, 11), 2)
    _ellipse(s, dark, (2, 10, 4, 2))
    # upright body
    _oval(s, c, (2, 3, 7, 7))
    _ellipse(s, shade(c, 0.7), (3, 7, 4, 2))          # pouch
    # arms
    _line(s, dark, (3, 5), (2, 8), 1)
    _line(s, dark, (8, 5), (9, 8), 1)
    # head + ears + eye
    _circle(s, dark, (9, 3), 3)
    _circle(s, c, (9, 3), 2)
    _poly(s, dark, [(7, 2), (7, 0), (9, 2)])
    _poly(s, shade(c, 0.8), [(7, 2), (7, 1), (8, 2)])
    _eye(s, 10, 3)
    _ellipse(s, shade(c, 0.6), (10, 3, 2, 1))         # snout


def _sprite_joey(s, c):
    dark = shade(c, 0.5)
    _line(s, dark, (4, 10), (3, 8), 1)                # tail
    _oval(s, c, (3, 6, 5, 4))                         # body
    _leg(s, c, 4, 9)
    _leg(s, c, 6, 9)
    _circle(s, dark, (8, 5), 3)                       # head
    _circle(s, c, (8, 5), 2)
    _poly(s, shade(c, 0.8), [(6, 4), (6, 2), (8, 4)])  # ears
    _poly(s, shade(c, 0.8), [(8, 4), (8, 2), (10, 4)])
    _eye(s, 9, 4)
    _ellipse(s, shade(c, 0.6), (9, 5, 2, 1))          # snout


def _sprite_wallaby(s, c):
    dark = shade(c, 0.5)
    _line(s, dark, (3, 9), (1, 5), 2)                 # tail
    _oval(s, c, (2, 6, 7, 4))                         # body
    _leg(s, c, 3, 9)
    _leg(s, c, 6, 9)
    _circle(s, dark, (9, 4), 3)                       # head
    _circle(s, c, (9, 4), 2)
    # big ears
    _poly(s, shade(c, 0.8), [(7, 3), (7, 1), (9, 3)])
    _poly(s, shade(c, 0.8), [(9, 3), (9, 1), (11, 3)])
    _eye(s, 10, 4)
    _ellipse(s, shade(c, 0.6), (10, 4, 2, 1))         # snout


def _sprite_wallaroo(s, c):
    dark = shade(c, 0.5)
    _line(s, dark, (2, 10), (0, 6), 2)                # tail
    _line(s, dark, (3, 9), (5, 11), 2)                # leg
    _ellipse(s, dark, (2, 10, 4, 2))                  # foot
    _oval(s, c, (1, 3, 8, 7))                         # bulky barrel body
    _line(s, dark, (3, 5), (1, 7), 2)                 # thick arms
    _line(s, dark, (8, 5), (10, 7), 2)
    _circle(s, dark, (9, 3), 3)                       # head
    _circle(s, c, (9, 3), 2)
    _poly(s, dark, [(7, 2), (7, 0), (9, 2)])
    _poly(s, shade(c, 0.8), [(7, 2), (7, 1), (8, 2)])
    _eye(s, 10, 3)


def _sprite_tree_kanga(s, c):
    dark = shade(c, 0.5)
    _oval(s, c, (3, 3, 5, 7))                         # upright body
    _line(s, dark, (3, 6), (1, 8), 1)                 # arms out
    _line(s, dark, (8, 6), (10, 8), 1)
    _line(s, dark, (4, 10), (3, 11), 1)
    _line(s, dark, (7, 10), (8, 11), 1)
    _circle(s, dark, (6, 3), 3)                       # head
    _circle(s, c, (6, 3), 2)
    _poly(s, shade(c, 0.8), [(4, 2), (4, 0), (6, 2)])
    _poly(s, shade(c, 0.8), [(6, 2), (6, 0), (8, 2)])
    _eye(s, 7, 3)


def _sprite_dingo(s, c):
    dark = shade(c, 0.5)
    _line(s, dark, (1, 6), (0, 3), 2)                 # bushy tail up
    _oval(s, c, (2, 6, 7, 4))                         # body
    _leg(s, c, 3, 9)
    _leg(s, c, 7, 9)
    _circle(s, dark, (10, 5), 3)                      # head
    _circle(s, c, (10, 5), 2)
    _poly(s, shade(c, 0.8), [(9, 4), (9, 2), (11, 4)])  # pointed ears
    _poly(s, shade(c, 0.8), [(11, 4), (11, 2), (12, 4)])
    _eye(s, 11, 4)
    _ellipse(s, shade(c, 0.6), (11, 5, 2, 1))         # snout


def _sprite_goanna(s, c):
    dark = shade(c, 0.5)
    _line(s, dark, (2, 8), (0, 4), 2)                 # long tail
    _oval(s, c, (2, 6, 8, 3))                         # low body
    # splayed legs
    _line(s, dark, (3, 9), (3, 11), 1)
    _line(s, dark, (8, 9), (8, 11), 1)
    _line(s, dark, (2, 9), (1, 11), 1)
    _line(s, dark, (9, 9), (10, 11), 1)
    _circle(s, dark, (10, 5), 3)                      # head
    _circle(s, c, (10, 5), 2)
    _eye(s, 11, 4)
    _line(s, shade(c, 1.6), (12, 5), (11, 6), 1)      # tongue


def _sprite_killer_bee(s, c):
    dark = shade(c, 0.5)
    # wings
    _ellipse(s, (205, 225, 255), (2, 2, 3, 3))
    _ellipse(s, (205, 225, 255), (7, 2, 3, 3))
    # striped body
    _circle(s, dark, (6, 6), 4)
    _circle(s, c, (6, 6), 3)
    _line(s, BLACK, (5, 5), (5, 8), 1)
    _line(s, BLACK, (7, 5), (7, 8), 1)
    _line(s, BLACK, (4, 7), (8, 7), 1)
    # head + eye
    _circle(s, dark, (5, 4), 2)
    _circle(s, c, (5, 4), 1)
    _eye(s, 5, 4)
    # stinger + antennae
    _line(s, dark, (6, 9), (6, 11), 1)
    _line(s, BLACK, (4, 3), (3, 1), 1)
    _line(s, BLACK, (6, 3), (7, 1), 1)


def _sprite_dropbear(s, c):
    dark = shade(c, 0.5)
    _circle(s, dark, (6, 7), 5)                       # round body
    _circle(s, c, (6, 7), 4)
    _circle(s, shade(c, 0.8), (3, 4), 2)              # ears
    _circle(s, shade(c, 0.8), (9, 4), 2)
    _circle(s, (255, 220, 80), (4, 6), 1)             # glowing eyes
    _circle(s, (255, 220, 80), (8, 6), 1)
    _ellipse(s, shade(c, 0.35), (6, 8, 2, 1))         # nose
    _line(s, dark, (3, 11), (2, 9), 1)                # claws
    _line(s, dark, (6, 11), (6, 10), 1)
    _line(s, dark, (9, 11), (10, 9), 1)


def _sprite_taipan(s, c):
    dark = shade(c, 0.5)
    # coiled body
    _line(s, c, (2, 4), (4, 5), 2)
    _line(s, c, (4, 5), (3, 8), 2)
    _line(s, c, (3, 8), (7, 8), 2)
    _line(s, c, (7, 8), (8, 5), 2)
    # head
    _circle(s, dark, (9, 4), 3)
    _circle(s, c, (9, 4), 2)
    _eye(s, 10, 3)
    _line(s, shade(c, 1.6), (11, 3), (11, 5), 1)      # forked tongue


def _sprite_emu(s, c):
    dark = shade(c, 0.5)
    _line(s, dark, (5, 10), (5, 11), 1)               # legs
    _line(s, dark, (7, 10), (7, 11), 1)
    _oval(s, c, (3, 5, 6, 6))                         # big shaggy body
    # feather texture
    _line(s, dark, (4, 9), (6, 8), 1)
    _line(s, dark, (6, 9), (8, 8), 1)
    _line(s, dark, (5, 10), (7, 9), 1)
    _line(s, c, (6, 5), (6, 1), 2)                    # long neck
    _circle(s, dark, (6, 1), 3)                       # head
    _circle(s, c, (6, 1), 2)
    _poly(s, shade(c, 0.7), [(8, 1), (10, 2), (8, 2)])  # beak
    _eye(s, 7, 1)


def _sprite_wombat(s, c):
    dark = shade(c, 0.5)
    _oval(s, c, (2, 6, 8, 5))                         # barrel body
    _circle(s, shade(c, 0.8), (4, 4), 2)              # ears
    _circle(s, shade(c, 0.8), (7, 4), 2)
    _circle(s, dark, (9, 7), 3)                       # head
    _circle(s, c, (9, 7), 2)
    _ellipse(s, shade(c, 0.4), (10, 8, 2, 1))         # big nose
    _eye(s, 9, 6)
    _leg(s, c, 4, 10)
    _leg(s, c, 7, 10)


def _sprite_magpie(s, c):
    dark = shade(c, 0.5)
    _oval(s, c, (2, 6, 6, 4))                         # dark body
    _ellipse(s, WHITE, (4, 6, 3, 2))                  # white belly patch
    _line(s, dark, (3, 8), (6, 9), 2)                 # wing
    _leg(s, c, 4, 10)
    _leg(s, c, 7, 10)
    _circle(s, dark, (9, 5), 3)                       # head
    _circle(s, c, (9, 5), 2)
    _eye(s, 10, 4)
    _poly(s, (255, 200, 60), [(11, 5), (9, 6), (11, 7)])  # yellow beak


def _sprite_cassowary(s, c):
    dark = shade(c, 0.5)
    _line(s, dark, (4, 10), (4, 11), 1)               # legs
    _line(s, dark, (8, 10), (8, 11), 1)
    _poly(s, dark, [(2, 11), (3, 4), (10, 4), (10, 11)])   # body silhouette
    _poly(s, c, [(3, 11), (4, 5), (9, 5), (9, 11)])
    _ellipse(s, shade(c, 1.3), (4, 5, 3, 2))          # chest
    _line(s, c, (6, 5), (6, 1), 2)                    # neck
    _circle(s, dark, (6, 1), 3)                       # head
    _circle(s, c, (6, 1), 2)
    _poly(s, shade(c, 1.6), [(6, 0), (7, 0), (7, 2), (5, 2)])  # casque crest
    _poly(s, (230, 60, 60), [(5, 2), (8, 3), (5, 4)])          # red wattle
    _poly(s, (255, 170, 60), [(4, 3), (6, 3), (5, 4)])         # beak
    _eye(s, 7, 1)


def _sprite_crocodile(s, c):
    dark = shade(c, 0.5)
    _line(s, dark, (2, 8), (0, 5), 2)                 # tail
    _oval(s, c, (2, 6, 8, 4))                         # body
    _leg(s, c, 4, 10)
    _leg(s, c, 8, 10)
    # back ridges
    _line(s, shade(c, 1.4), (3, 6), (4, 5), 1)
    _line(s, shade(c, 1.4), (5, 6), (6, 5), 1)
    _line(s, shade(c, 1.4), (7, 6), (8, 5), 1)
    # head + snout
    _circle(s, dark, (10, 6), 3)
    _circle(s, c, (10, 6), 2)
    _eye(s, 10, 5)
    _poly(s, c, [(10, 7), (12, 7), (12, 9), (10, 9)])  # snout
    _line(s, WHITE, (11, 8), (11, 9), 1)               # teeth
    _line(s, WHITE, (12, 8), (12, 9), 1)


def _sprite_echidna(s, c):
    dark = shade(c, 0.5)
    quill = shade(c, 1.5)
    # quills along the back
    for (x, y) in ((3, 3), (4, 2), (5, 2), (6, 2), (7, 3), (8, 4)):
        _line(s, quill, (x, y), (x, y - 2), 1)
        _line(s, dark, (x, y), (x - 1, y - 1), 1)
    # round body
    _oval(s, c, (3, 4, 6, 5))
    # head + long snout
    _oval(s, c, (8, 5, 3, 2))
    _line(s, shade(c, 0.7), (10, 5), (11, 6), 1)
    _eye(s, 9, 5)
    _leg(s, c, 4, 8)
    _leg(s, c, 7, 8)


def _sprite_funnel_web(s, c):
    dark = shade(c, 0.55)
    # eight legs
    for (x0, y0, x1, y1) in ((5, 5, 2, 3), (6, 5, 4, 2), (5, 6, 1, 6), (6, 6, 3, 8),
                             (7, 5, 10, 3), (6, 5, 8, 2), (7, 6, 11, 6), (6, 6, 9, 8)):
        _line(s, dark, (x0, y0), (x1, y1), 1)
    # abdomen + cephalothorax
    _oval(s, c, (4, 5, 4, 4))
    _oval(s, c, (6, 4, 3, 2))
    # fangs
    _line(s, shade(c, 0.7), (8, 4), (9, 5), 1)
    _line(s, shade(c, 0.7), (8, 4), (9, 3), 1)
    # eyes
    _eye(s, 6, 4)
    _eye(s, 7, 4)


# ---------------------------------------------------------------------------
# Environment / actor sprites
# ---------------------------------------------------------------------------

def _sprite_corpse(s, c):
    dark = shade(c, 0.6)
    bone = (222, 222, 214)
    # crossed bones
    _line(s, bone, (2, 9), (7, 5), 2)
    _line(s, bone, (7, 9), (2, 5), 2)
    _line(s, bone, (1, 10), (3, 10), 1)
    _line(s, bone, (8, 4), (10, 4), 1)
    # skull
    _circle(s, bone, (6, 4), 3)
    _circle(s, dark, (5, 3), 1)                       # eye sockets
    _circle(s, dark, (7, 3), 1)
    pygame.draw.rect(s, dark, pygame.Rect(5, 5, 2, 2))  # nose hole


def _sprite_trail_down(s, c):
    dark = shade(c, 0.5)
    _poly(s, dark, [(2, 3), (10, 3), (6, 10)])
    _poly(s, c, [(3, 4), (9, 4), (6, 9)])
    _line(s, shade(c, 1.4), (4, 5), (8, 5), 1)


def _sprite_trail_up(s, c):
    dark = shade(c, 0.5)
    _poly(s, dark, [(2, 9), (10, 9), (6, 2)])
    _poly(s, c, [(3, 8), (9, 8), (6, 3)])
    _line(s, shade(c, 1.4), (4, 7), (8, 7), 1)


def _sprite_ship(s, c):
    dark = shade(c, 0.55)
    _ellipse(s, shade(c, 0.6), (1, 9, 10, 2))         # landing shadow
    _line(s, dark, (3, 9), (3, 11), 1)                # landing legs
    _line(s, dark, (9, 9), (9, 11), 1)
    _ellipse(s, dark, (0, 6, 12, 4))                  # saucer rim
    _ellipse(s, c, (1, 7, 10, 3))                     # saucer
    _ellipse(s, shade(c, 1.4), (2, 7, 4, 1))          # highlight
    _circle(s, dark, (6, 6), 4)                       # dome
    _circle(s, c, (6, 6), 3)
    _circle(s, (140, 255, 220), (6, 6), 1)            # cockpit glow


def _sprite_part(s, c):
    dark = shade(c, 0.55)
    _poly(s, dark, [(6, 0), (10, 3), (10, 7), (6, 10), (2, 7), (2, 3)])
    _poly(s, c, [(6, 1), (9, 3), (9, 7), (6, 9), (3, 7), (3, 3)])
    _circle(s, dark, (6, 5), 2)
    _circle(s, shade(c, 1.6), (6, 5), 1)


# ---------------------------------------------------------------------------
# Item / equipment icon recipes
# ---------------------------------------------------------------------------

def _icon_cross(s, c):
    _ellipse(s, shade(c, 0.8), (1, 1, 10, 10))
    _ellipse(s, c, (2, 2, 8, 8))
    pygame.draw.rect(s, WHITE, pygame.Rect(5, 3, 2, 6))
    pygame.draw.rect(s, WHITE, pygame.Rect(3, 5, 6, 2))


def _icon_bottle(s, c):
    dark = shade(c, 0.5)
    _ellipse(s, dark, (3, 1, 6, 2))                   # cap
    pygame.draw.rect(s, c, pygame.Rect(4, 2, 4, 2))   # neck
    pygame.draw.rect(s, dark, pygame.Rect(3, 3, 6, 7))  # body rim
    pygame.draw.rect(s, c, pygame.Rect(4, 4, 4, 5))   # body
    pygame.draw.rect(s, shade(c, 1.5), pygame.Rect(4, 5, 4, 2))  # label


def _icon_grenade(s, c):
    dark = shade(c, 0.6)
    _circle(s, dark, (6, 7), 4)
    _circle(s, c, (6, 7), 3)
    _line(s, shade(c, 0.4), (6, 3), (6, 4), 2)        # pin
    _circle(s, shade(c, 1.5), (7, 3), 1)


def _icon_gun(s, c):
    dark = shade(c, 0.5)
    pygame.draw.rect(s, dark, pygame.Rect(2, 5, 9, 3))
    pygame.draw.rect(s, c, pygame.Rect(3, 6, 7, 2))
    pygame.draw.rect(s, dark, pygame.Rect(8, 3, 2, 5))  # grip
    pygame.draw.rect(s, c, pygame.Rect(8, 4, 2, 4))
    pygame.draw.rect(s, shade(c, 1.5), pygame.Rect(3, 6, 3, 1))


def _icon_bolt(s, c):
    dark = shade(c, 0.5)
    _poly(s, dark, [(6, 0), (9, 0), (5, 6), (8, 6), (4, 12), (7, 5), (5, 5), (8, 0)])
    _poly(s, c, [(6, 1), (8, 1), (5, 6), (7, 6), (4, 11), (6, 5), (5, 5), (7, 1)])


def _icon_tentacle(s, c):
    _line(s, c, (2, 1), (5, 6), 2)
    _line(s, c, (5, 6), (3, 10), 2)
    _line(s, c, (5, 6), (8, 10), 2)
    _line(s, c, (5, 6), (10, 9), 2)
    _circle(s, shade(c, 1.5), (2, 1), 1)


def _icon_shield(s, c):
    dark = shade(c, 0.55)
    _poly(s, dark, [(6, 0), (11, 3), (11, 7), (6, 12), (1, 7), (1, 3)])
    _poly(s, c, [(6, 1), (10, 3), (10, 7), (6, 11), (2, 7), (2, 3)])
    _poly(s, shade(c, 1.35), [(6, 2), (9, 4), (9, 7), (6, 10), (3, 7), (3, 4)])
    _line(s, shade(c, 0.6), (6, 4), (6, 9), 1)


def _icon_twig(s, c):
    _line(s, c, (2, 10), (10, 2), 2)
    _ellipse(s, shade(c, 1.4), (1, 8, 2, 3))
    _ellipse(s, shade(c, 1.4), (7, 3, 2, 3))
    _ellipse(s, shade(c, 1.4), (4, 5, 2, 3))


def _icon_hat(s, c):
    dark = shade(c, 0.5)
    pygame.draw.rect(s, dark, pygame.Rect(1, 7, 10, 3))    # brim rim
    pygame.draw.rect(s, c, pygame.Rect(2, 8, 8, 2))        # brim
    _poly(s, dark, [(4, 8), (4, 3), (8, 3), (8, 8)])       # dome rim
    _poly(s, c, [(5, 8), (5, 4), (7, 4), (7, 8)])          # dome
    pygame.draw.rect(s, shade(c, 1.4), pygame.Rect(5, 4, 2, 3))  # band


def _icon_neck(s, c):
    dark = shade(c, 0.55)
    pygame.draw.circle(s, dark, (6, 6), 5, 2)
    pygame.draw.circle(s, c, (6, 6), 4, 1)
    _circle(s, shade(c, 1.5), (6, 6), 1)


def _icon_vest(s, c):
    dark = shade(c, 0.5)
    _poly(s, dark, [(4, 1), (8, 1), (10, 6), (8, 12), (4, 12), (2, 6)])
    _poly(s, c, [(5, 2), (7, 2), (9, 6), (7, 11), (5, 11), (3, 6)])
    _line(s, shade(c, 0.6), (6, 2), (6, 11), 1)
    _line(s, shade(c, 0.6), (4, 2), (6, 6), 1)
    _line(s, shade(c, 0.6), (8, 2), (6, 6), 1)


def _icon_boomerang(s, c):
    dark = shade(c, 0.5)
    _line(s, dark, (2, 1), (11, 7), 3)
    _line(s, c, (2, 2), (10, 7), 2)
    _line(s, c, (10, 7), (6, 11), 2)
    _line(s, shade(c, 1.5), (4, 3), (9, 7), 1)


def _icon_ration(s, c):
    dark = shade(c, 0.5)
    pygame.draw.rect(s, dark, pygame.Rect(3, 3, 6, 7))     # can rim
    pygame.draw.rect(s, c, pygame.Rect(4, 4, 4, 5))        # can
    pygame.draw.rect(s, shade(c, 1.5), pygame.Rect(4, 4, 4, 2))  # lid
    _circle(s, shade(c, 0.7), (6, 7), 1)


def _icon_tea(s, c):
    dark = shade(c, 0.5)
    pygame.draw.rect(s, dark, pygame.Rect(2, 6, 7, 5))     # cup rim
    pygame.draw.rect(s, c, pygame.Rect(3, 7, 5, 3))        # cup
    _line(s, c, (8, 7), (11, 8), 2)                        # handle
    _line(s, c, (11, 8), (11, 9), 1)
    _line(s, c, (8, 9), (11, 9), 1)
    _line(s, shade(c, 0.6), (3, 6), (3, 4), 1)             # steam
    _line(s, shade(c, 0.6), (5, 6), (5, 3), 1)
    _line(s, shade(c, 0.6), (7, 6), (7, 4), 1)


def _icon_star(s, c):
    dark = shade(c, 0.5)
    pts = [(6, 0), (8, 3), (11, 3), (9, 6), (10, 10), (6, 8), (2, 10), (3, 6), (1, 3), (4, 3)]
    _poly(s, dark, [(x + 1, y) for (x, y) in pts])
    _poly(s, c, pts)
    _circle(s, shade(c, 1.5), (6, 4), 1)


def _icon_tube(s, c):
    dark = shade(c, 0.5)
    _poly(s, dark, [(2, 1), (5, 1), (9, 11), (6, 11)])     # didgeridoo rim
    _poly(s, c, [(3, 2), (4, 2), (8, 10), (7, 10)])        # body
    _circle(s, shade(c, 1.5), (3, 2), 1)                   # mouthpiece
    _circle(s, shade(c, 0.7), (7, 10), 1)


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
    'echidna': _sprite_echidna,
    'funnel_web': _sprite_funnel_web,
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
    'icon_tube': _icon_tube,
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
