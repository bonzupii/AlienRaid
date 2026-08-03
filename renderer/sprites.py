#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SpriteLoader — hand-authored pixel-art edition.

All mobs, the player, items, the trails, the ship and corpses are rendered as
**procedurally generated graphics**: 12x12 pixel maps, blitted pixel by pixel
and cached as ``pygame.Surface`` objects keyed by ``(sprite_id, color)``.

Each recipe is a list of strings (``''``/``'.'`` = transparent) painted onto a
12x12 SRCALPHA surface.  Characters map to colours derived from the entity's
base colour ``c``:

    o  hard outline        shade(c, 0.45)
    d  shadow / secondary  shade(c, 0.70)
    b  body fill           c
    l  top highlight       shade(c, 1.35)
    e  eye (near black)    w  white        k  black
    n  bone                a  wing membrane
    g  cockpit / core glow y  gold accent  r  red accent

12x12 style guide (unchanged from the original):
* a 1px dark rim defines every silhouette,
* light comes from above ('l' sits on the top rows),
* creatures face right and stand on the ground line (y = 10..11),
* eyes are dark pixels, with a white glint where room allows.
"""
import pygame
from renderer.palette import shade

TILE = 12

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
EYE = (20, 20, 20)

BONE = (224, 222, 210)      # skulls & crossed bones
WING = (205, 225, 255)      # insect wing membrane
GLOW = (140, 255, 220)      # alien cockpit / ship-part core
GOLD = (255, 210, 70)       # dropbear eyes, magpie beak
EMBER = (225, 60, 50)       # cassowary wattle


def _palette(c):
    """Standard shading ramp derived from the entity's base color."""
    return {
        'o': shade(c, 0.45),
        'd': shade(c, 0.70),
        'b': c,
        'l': shade(c, 1.35),
        'e': EYE,
        'w': WHITE,
        'k': BLACK,
    }


def _paint(surf, rows, pal, top=0):
    """Blit pixel-map ``rows`` onto ``surf``; unknown/blank cells stay clear."""
    for i, row in enumerate(rows):
        y = top + i
        if y >= TILE:
            break
        for x, ch in enumerate(row):
            if x >= TILE:
                break
            col = pal.get(ch)
            if col is not None:
                surf.set_at((x, y), col)


# ---------------------------------------------------------------------------
# Creatures — all face right, feet on the y = 10..11 ground line.
# ---------------------------------------------------------------------------

def _sprite_player(s, c):
    _paint(s, [
        "...d....d...",    # antennae
        "....d..d....",
        "....oooo....",    # big round head
        "..oobbbboo..",
        "..obwbbwbo..",    # eye glints
        "..obebbebo..",    # alien eyes
        "..oobbbboo..",
        "....oooo....",
        "...obllbo...",    # chest highlight
        "..obbbbbbo..",
        "..d..dd..d..",    # tentacle arms
        ".d..d..d..d.",
    ], _palette(c))


def _sprite_kanga(s, c):
    _paint(s, [
        ".......o.o..",    # ears
        ".......o.o..",
        "......oooo..",    # head
        ".....obbbeo.",
        "...oobbbbbdd",    # neck + dark snout
        "..olbbbbo...",    # chest
        "..obbbbbbo..",
        "..obbbddbod.",    # pouch + little arm
        "..dobbbbo...",    # tail
        ".d..obbbo...",
        ".d..d..d....",    # legs
        "d..dddddd...",    # tail tip + big foot
    ], _palette(c))


def _sprite_joey(s, c):
    _paint(s, [
        ".......o.o..",
        ".......o.o..",
        "......oooo..",
        ".....obbbeo.",
        ".....obbbbdd",
        "...oobbbbo..",
        "..obbbbbbo..",
        "..dobbbbbo..",
        ".d..d..d....",
        "d..dddddd...",
    ], _palette(c), top=1)


def _sprite_wallaby(s, c):
    _paint(s, [
        ".......o.o..",
        ".......o.o..",
        "......oooo..",
        ".....obbbeo.",
        ".....obbbbdd",
        "..oobbbbbo..",    # leaner, horizontal body
        ".obbbbbbbo..",
        "d.obbbbbbo..",    # long tail
        "dd..obbbbo..",
        "....d...d...",
        "...ddddddd..",    # long feet
    ], _palette(c))


def _sprite_wallaroo(s, c):
    _paint(s, [
        "......o.o...",
        "......o.o...",
        ".....ooooo..",
        "....obbbbeo.",
        "....obbbbbdd",
        ".oobbbbbbo..",
        "obbbbbbbbo..",    # bulky barrel body
        "obbbbbbbbod.",    # thick arm
        ".obbbbbbbod.",
        ".dobbbbbo...",
        "dd..d...d...",
        "d..dddddddd.",    # huge feet
    ], _palette(c))


def _sprite_tree_kanga(s, c):
    _paint(s, [
        ".....o..o...",
        ".....o..o...",
        "....ooooo...",
        "...obbbbeo.",
        "...obbbbdd..",
        "dd.obbbbo.dd",    # arms held out
        ".d.obbbbo.d.",
        "..obbbbbbo..",    # upright body
        "..obbbbbo...",
        "....d..d....",
        "...dd..dd...",
    ], _palette(c))


def _sprite_dingo(s, c):
    _paint(s, [
        "........o.o.",    # pointed ears
        "........o.o.",
        ".d.....oooo.",    # bushy tail raised
        "dd.....obebo",
        "dd.....obbdd",    # snout
        ".oobbbbbbo..",
        ".obbbbbbbo..",
        ".obbbbbbo...",
        "..dd...dd...",
        "..dd...dd...",
        "..dd...dd...",
        "..ddd..ddd..",
    ], _palette(c))


def _sprite_goanna(s, c):
    _paint(s, [
        "..........ll",    # forked tongue
        "d..........l",
        ".d......oooo",    # tail + head top
        "..dooooobebo",
        "..dobbbbbbdo",    # low body + jaw
        "....oooooo..",
        "...d....d...",    # splayed legs
        "..d......d..",
    ], _palette(c), top=3)


def _sprite_killer_bee(s, c):
    pal = _palette(c)
    pal['a'] = WING
    _paint(s, [
        "..aaa.aaa",     # wings
        ".........k.k",  # antennae
        "...ooooo.oo",   # thorax rim + head
        "..obkbkbooeo",  # striped abdomen
        "..obkbkbooeo",
        "..obkbkbo",
        "...obkbo",
        "...oooo",
        "..k",           # stinger
        ".k",
    ], pal, top=1)


def _sprite_dropbear(s, c):
    pal = _palette(c)
    pal['y'] = GOLD
    _paint(s, [
        "..dd..dd",      # ears
        ".oobbbbbo",
        "obyybbyybo",    # glowing eyes
        "obbbbbbbbo",
        "obbbddbbbo",    # big nose
        ".obbbbbbo",
        "..oooooo",
        ".d.d..d.d.",    # claws
    ], pal, top=3)


def _sprite_taipan(s, c):
    _paint(s, [
        ".......oooo",   # raised head
        ".......obeo",
        ".......obbol",  # tongue flick
        "......b",       # neck
        ".oooooo",       # coil
        ".obdbbbbo",
        ".obbbbbbo",
        ".ooooooo",
    ], _palette(c), top=3)


def _sprite_emu(s, c):
    _paint(s, [
        ".....ooo",
        "....obebd",     # beak
        ".....obb",
        ".....dd",       # dark neck
        ".....dd",
        "..ooooddoo",
        ".obbbbbbo",     # shaggy body
        ".obdbdbbo",
        ".obbbbbbo",
        ".ooooooo",
        "....d.d",       # long legs
        "...dd.dd",
    ], _palette(c))


def _sprite_wombat(s, c):
    _paint(s, [
        "..oo.oo",       # round ears
        ".oobbbbbbo",
        "obbbbbbbbo",
        "obbbbbbebbdd",  # eye + nose
        "obbbbbbbbddd",  # big nose
        ".oooooooo",
        "..dd..dd",      # stubby legs
    ], _palette(c), top=4)


def _sprite_magpie(s, c):
    pal = _palette(c)
    pal['y'] = GOLD
    _paint(s, [
        ".......oooo",
        "......obebo",
        "..ooooobbbyy",  # yellow beak
        ".obbbbbbo",
        ".obbbwwbo",     # white belly
        ".obbbwwo",
        "dd.oooooo",     # tail
        "dd..d.d",
        "d..dd.dd",
    ], pal, top=2)


def _sprite_cassowary(s, c):
    pal = _palette(c)
    pal['r'] = EMBER
    _paint(s, [
        "......ll",      # casque
        ".....ooo",
        "....obebd",
        ".....bbr",      # red wattle
        ".....bb",
        "..ooobboo",
        ".obbbbbbo",
        ".obdbdbbo",
        ".obbbbbbo",
        ".ooooooo",
        "...dd.dd",      # strong legs
        "..ddd.ddd",     # deadly claws
    ], pal)


def _sprite_crocodile(s, c):
    _paint(s, [
        ".d.l.l.l.o",      # tail, back ridges, eye bump
        ".dobbbbboebo",
        ".dobbbbbbbbb",    # long snout
        ".dobbbbbow.w",    # teeth
        ".dooooooo",
        "...d...d",
        "..dd..dd",
    ], _palette(c), top=5)


def _sprite_echidna(s, c):
    _paint(s, [
        "..l.l.l.l",       # quills
        "..ooooooo",
        ".obbbbbbbo",
        ".obbbbbbeodd",    # eye + long snout
        ".obbbbbbbod",
        "..ooooooo",
        "...d..d",
    ], _palette(c), top=4)


def _sprite_funnel_web(s, c):
    _paint(s, [
        "..d...d",         # legs
        "..oooooo",        # abdomen
        ".dobbbbo.d",
        "d.obbbboeeod",    # eyes
        ".dobbbboobo",     # cephalothorax
        "..oooooodd",      # fangs
        ".d..d.d..d",
    ], _palette(c), top=2)


# ---------------------------------------------------------------------------
# Environment / actor sprites
# ---------------------------------------------------------------------------

def _sprite_corpse(s, c):
    pal = _palette(c)
    pal['n'] = BONE
    pal['d'] = shade(c, 0.6)
    _paint(s, [
        "...nnnnn",      # skull
        "..nnnnnnn",
        "..ndnnndn",     # eye sockets
        "..nnndnnn",     # nose
        "...ndndn",      # teeth
        "..n...n",       # crossed bones
        "...n.n",
        "....n",
        "...n.n",
        "..n...n",
    ], pal, top=2)


def _sprite_trail_down(s, c):
    _paint(s, [
        "..obllbbbo",
        "...obbbbo",
        "...obbbbo",
        "....obbo",
        "....obbo",
        ".....oo",
        ".....d",
    ], _palette(c), top=3)


def _sprite_trail_up(s, c):
    _paint(s, [
        ".....d",
        ".....oo",
        "....obbo",
        "....obbo",
        "...obbbbo",
        "...obbbbo",
        "..obllbbbo",
    ], _palette(c), top=3)


def _sprite_ship(s, c):
    pal = _palette(c)
    pal['g'] = GLOW
    _paint(s, [
        "....oooo",        # dome
        "...obbbbo",
        "...obgbbo",       # cockpit glow
        "...obbbbo",
        ".oooooooooo",     # saucer rim
        "obllbbbbbbbo",
        ".obbbddbbbo",
        "...d...d",        # landing legs
        "..dd..dd",
    ], pal, top=2)


def _sprite_part(s, c):
    pal = _palette(c)
    pal['g'] = GLOW
    _paint(s, [
        "....oooo",
        "...olbbbo",
        "..obbbbbbo",
        "..obbggbbo",      # glowing core
        "..obbggbbo",
        "...obbbbo",
        "....oooo",
    ], pal, top=2)


# ---------------------------------------------------------------------------
# Item / equipment icons
# ---------------------------------------------------------------------------

def _icon_cross(s, c):
    _paint(s, [
        "....oooo",
        "...obbbbo",
        "..obbbbbbo",
        "..obbwwbbo",
        "..owwwwwwo",
        "..owwwwwwo",
        "..obbwwbbo",
        "..obbbbbbo",
        "...obbbbo",
        "....oooo",
    ], _palette(c), top=1)


def _icon_bottle(s, c):
    _paint(s, [
        ".....dd",       # cap
        ".....dd",
        "....obbo",      # neck
        "....obbo",
        "...obbbbo",
        "...obbbbo",
        "...obllbo",     # label
        "...obllbo",
        "...obbbbo",
        "...oooooo",
    ], _palette(c), top=1)


def _icon_grenade(s, c):
    _paint(s, [
        ".oo..ddd",      # pin ring + cap
        ".o....d",
        ".oo...d",
        "...oooooo",
        "..olbbbbbo",
        "..obbbbbbo",
        "..obbbbbbo",
        "..obbbbbbo",
        "...obbbbo",
        "...oooooo",
    ], _palette(c), top=1)


def _icon_gun(s, c):
    _paint(s, [
        ".obbbbbbbbo",   # slide
        ".obllbbbbbo",
        ".obbbbbbbbo",
        "..dddd.d",      # grip + trigger
        "..dddd",
        ".dddd",
        ".dddd",
    ], _palette(c), top=5)


def _icon_bolt(s, c):
    _paint(s, [
        "....oooo",
        "...ollbo",
        "..ollbo",
        "..olbo",
        "..oooooo",      # the jog
        "....olbo",
        "...olbo",
        "..olbo",
        ".olbo",
        ".olo",
    ], _palette(c), top=1)


def _icon_tentacle(s, c):
    _paint(s, [
        "....lb",
        "...bb",
        "..lb",          # suckers
        "..bb",
        "...lb",
        "....bb",
        ".....lb",
        "....bb",
        "...bb",
        "..bbbb",
    ], _palette(c), top=1)


def _icon_shield(s, c):
    _paint(s, [
        ".oooooooooo",
        ".obllbbbbbo",
        ".obbbbbbbbo",
        ".obbbbbbbbo",
        ".obbbbbbbbo",
        "..obbbbbbo",
        "..obbbbbbo",
        "...obbbbo",
        "....obbo",
        ".....oo",
    ], _palette(c), top=1)


def _icon_twig(s, c):
    _paint(s, [
        ".........ll",   # leaves
        "........dd",
        ".......dd",
        "...ll.dd",
        "...l..dd",
        "....dd",
        "...dd",
        "..dd",
        ".dd",
        "dd",
    ], _palette(c), top=1)


def _icon_hat(s, c):
    _paint(s, [
        "....oooo",      # dome
        "...obbbbo",
        "...obbbbo",
        "...obddbo",     # band
        ".oooooooooo.",  # brim
        "obbbbbbbbbbo",
    ], _palette(c), top=4)


def _icon_neck(s, c):
    _paint(s, [
        "...oooooo",
        "..o......o",
        "..o......o",
        "..o......o",
        "...o....o",
        "....oooo",
        ".....ll",       # pendant
        ".....ll",
    ], _palette(c), top=1)


def _icon_vest(s, c):
    _paint(s, [
        "..oo....oo",    # shoulder straps
        ".obbo..obbo",
        ".obbbbbbo",
        ".obbbbbbo",
        ".obdbbdbo",     # pockets
        ".obdbbdbo",
        ".obbbbbbo",
        "..obbbbo",
        "..oooooo",
    ], _palette(c), top=2)


def _icon_boomerang(s, c):
    _paint(s, [
        ".ld......ld",
        "..ld....ld",
        "...ld..ld",
        "....lldd",
        "....lldd",
        ".....ld",
    ], _palette(c), top=2)


def _icon_ration(s, c):
    _paint(s, [
        "...oooooo",
        "...ollllo",     # lid
        "...obbbbo",
        "...ollllo",     # label
        "...ollllo",
        "...obbbbo",
        "...oooooo",
    ], _palette(c), top=3)


def _icon_tea(s, c):
    _paint(s, [
        "....l.l",       # steam
        "",
        "....l.l",
        "",
        "..oddddo",      # tea surface
        "..obbbbooo",    # cup + handle
        "..obbbbo.o",
        "..obbbbooo",
        "...oooo",
    ], _palette(c), top=1)


def _icon_star(s, c):
    _paint(s, [
        ".....oo",
        "....ollo",
        "...ollllo",
        ".ollllllllo.",
        "..ollllllo",
        "...ollllo",
        "..oll..llo",
        ".oll....llo",
        ".ol......lo",
        "ol........lo",
    ], _palette(c), top=1)


def _icon_tube(s, c):
    _paint(s, [
        ".........ld",   # mouthpiece
        "........dd",
        ".......ld",     # painted dots
        "......dd",
        ".....ld",
        "....dd",
        "...ld",
        "..dd",
        ".ddd",          # bell
        "dddd",
    ], _palette(c), top=1)


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
