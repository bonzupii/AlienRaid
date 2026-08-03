#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SpriteLoader — hand-authored pixel-art edition, v2.

v2 fixes learned from the rendered sheet:
* dark base colors (dropbear, magpie, funnel-web, vest...) get a LIGHT rim
  and lighter mid-tones so they never vanish into dark floors;
* no floating pixels: tongues, steam, pins and tails are anchored;
* 2px ears/tails/legs and cream underbellies make species silhouettes read.

Character map (``.``/``''`` = transparent):
    o  outline (dark rim, or light rim on dark bodies)
    d  shadow / secondary (lighter mid on dark bodies)
    b  body fill           l  top highlight
    u  cream underbelly    e  eye            w  white   k  black
    n  bone  a  wing membrane  g  glow  y  gold  r  red
"""
import pygame
from renderer.palette import shade

TILE = 12

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
EYE = (20, 20, 20)
BONE = (224, 222, 210)
WING = (205, 225, 255)
GLOW = (140, 255, 220)
GOLD = (255, 210, 70)
EMBER = (225, 60, 50)
CREAM = (235, 220, 185)


def _palette(c):
    """Shading ramp; dark bodies are rim-lit so they stay readable."""
    lum = sum(c) / 3.0
    if lum < 80:
        o = tuple(min(255, max(96, int(v * 2.8))) for v in c)
        d = tuple(min(255, max(64, int(v * 1.7))) for v in c)
        l = tuple(min(255, max(140, int(v * 3.2))) for v in c)
    else:
        o = shade(c, 0.45)
        d = shade(c, 0.70)
        l = shade(c, 1.35)
    return {'o': o, 'd': d, 'b': c, 'l': l, 'e': EYE, 'w': WHITE,
            'k': BLACK, 'u': CREAM}


def _paint(surf, rows, pal, top=0):
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
# Creatures
# ---------------------------------------------------------------------------

def _sprite_player(s, c):
    _paint(s, [
        "..d......d..",
        "...d....d...",
        "...oooooo...",
        "..obbbbbbo..",
        "..obwbbwbo..",
        "..obebbebo..",
        "..obbbbbbo..",
        "..oobbbboo..",
        "...obllbo...",
        ".obbbbbbbbo.",
        ".dd..dd..dd.",
        ".d..d..d..d.",
    ], _palette(c))


def _sprite_kanga(s, c):
    _paint(s, [
        ".......dd.dd",   # thick ears
        ".......dd.dd",
        ".......oooo.",
        ".......obbeo",
        "...oobbbbbdd",   # neck + snout
        "..odbbbbo...",
        "..odbbuuo...",   # cream belly
        "..odbbuuo...",
        ".ddobuuo....",   # tail joins body
        "dd..obbo....",
        "d...dd.dd...",
        "...ddddddd..",   # big foot
    ], _palette(c))


def _sprite_joey(s, c):
    _paint(s, [
        ".......d.d..",
        ".......d.d..",
        "......oooo..",
        "......obbeo.",
        "....oobbbdd.",
        "...obbbbo...",
        "...dbbuo....",
        "..ddobuo....",
        ".dd..obo....",
        "d...dddd....",
    ], _palette(c), top=1)


def _sprite_wallaby(s, c):
    _paint(s, [
        ".......d..d.",   # long ears
        ".......d..d.",
        ".......d..d.",
        "......oooo..",
        "......obbeo.",
        "......obbdd.",
        "..oobbbbo...",
        ".obbbbbbo...",
        "dd.obuuo....",
        "dd..obbo....",
        "d...d..d....",
        "...dddddd...",
    ], _palette(c))


def _sprite_wallaroo(s, c):
    _paint(s, [
        "......dd.dd.",
        "......dd.dd.",
        "......oooo..",
        ".....obbeo.",
        ".....obbbdd.",
        ".oobbbbbbo..",   # barrel body
        "obbbbbbbbo..",
        "obbbbbbubod.",   # thick arm
        ".obbbbbubod.",
        ".dobbbbuo...",
        "dd..dd..dd..",
        "d..dddddddd.",   # huge feet
    ], _palette(c))


def _sprite_tree_kanga(s, c):
    _paint(s, [
        "d....d..d...",   # long tail up + ears
        "d...ooooo...",
        "d...obbeo...",
        "d...obbbdd..",
        "dd.obbbbo.dd",   # arms out
        ".d.obuubo.d.",
        "...obuubo...",
        "...obbbbo...",
        "....obbo....",
        "....d..d....",
        "...dd..dd...",
    ], _palette(c))


def _sprite_dingo(s, c):
    _paint(s, [
        "........d.d.",
        "........d.d.",
        ".dd....oooo.",   # bushy tail, joined
        ".ddd...obbeo",
        "..dd...obbkd",   # black nose
        "..oobbbbbo..",
        ".obbbbbbbo..",
        ".obbbbbbbo..",
        ".obbbbbbo...",
        "..dd...dd...",
        "..dd...dd...",
        "..ddd..ddd..",
    ], _palette(c))


def _sprite_goanna(s, c):
    _paint(s, [
        "..........ll",   # forked tongue
        "d.......ooo.l",
        ".d.....obebl",   # tongue at mouth
        "..doooobbbbd",
        "..dbbbbbbbd.",
        "...oooooo...",
        "..dd....dd..",   # splayed legs
        ".d......d...",
    ], _palette(c), top=4)


def _sprite_killer_bee(s, c):
    pal = _palette(c)
    pal['a'] = WING
    _paint(s, [
        "..aaa.aaa",
        "....a..a.k.k",  # wings join thorax + antennae
        "...ooooo.oo",
        "..obkbkbooeo",
        "..obkbkbooeo",
        "..obkbkbo",
        "...obkbo",
        "...oooo",
        "..k",
        ".k",
    ], pal, top=1)


def _sprite_dropbear(s, c):
    pal = _palette(c)
    pal['y'] = GOLD
    _paint(s, [
        "..dd..dd..",   # light fluffy ears
        ".obbbbbbo.",
        "obyybbyybo",   # gold eyes
        "obbbbbbbbo",
        "obbbkkbbbo",   # black nose
        ".obbbbbbo.",
        "..oooooo..",
        ".l.l..l.l.",   # light claws
    ], pal, top=3)


def _sprite_taipan(s, c):
    _paint(s, [
        "..........ll",
        ".......ooo.l",
        ".......obed",   # tongue at mouth
        "......b",
        ".oooooo",
        ".odbbdbo",     # banding
        ".obbbdbo",
        ".ooooooo",
    ], _palette(c), top=3)


def _sprite_emu(s, c):
    _paint(s, [
        ".....ooo",
        "....obebd",
        ".....obb",
        ".....dd",
        ".....dd",
        ".....dd",
        "..ooooddoo",
        ".obbbbbbo",
        ".obdbdbbo",    # shaggy texture
        ".ooooooo",
        "....d.d",
        "...dd.dd",
    ], _palette(c))


def _sprite_wombat(s, c):
    _paint(s, [
        "..dd..dd..",
        ".obbbbbbo.",
        "obbbbbbbbo",
        "obbbbbbebbkk",  # black nose
        "obbbbbbbkkk",
        ".ollllllo.",    # light belly
        "..dd..dd..",
    ], _palette(c), top=4)


def _sprite_magpie(s, c):
    pal = _palette(c)
    pal['y'] = GOLD
    _paint(s, [
        ".......oooo",
        "......obebo",
        "..ooooobbbyy",
        ".owbbbbbo...",   # white nape
        ".obbbwwbo...",   # white belly
        ".obbwwwo....",
        "dd.oooooo...",   # tail
        "dd..d.d.....",
        "w..dd.dd....",   # white tail tip
    ], pal, top=2)


def _sprite_cassowary(s, c):
    pal = _palette(c)
    pal['r'] = EMBER
    _paint(s, [
        "......ll",      # casque
        ".....ooo",
        "....obebd",
        ".....bbr",      # wattle joined to neck
        ".....bb",
        "..ooobboo",
        ".obbbbbbo",
        ".obdbdbbo",
        ".ooooooo",
        "...dd.dd",
        "..ddd.ddd",     # dagger claws
    ], pal)


def _sprite_crocodile(s, c):
    _paint(s, [
        ".d.l.l.l.o",
        ".dobbbbboebo",
        ".dobbbbbbbbb",
        ".dobbbbboww.",   # teeth under jaw
        ".dooooooo",
        "...d...d",
        "..dd..dd",
    ], _palette(c), top=5)


def _sprite_echidna(s, c):
    _paint(s, [
        "...l..l..l..",
        "..ll.ll.ll..",   # joined quill triangles
        "..ooooooo...",
        ".obbbbbbo.",
        ".obbbbbbeodd",
        ".obbbbbbbod.",
        "..ouuuuuo...",
        "...d..d.....",
    ], _palette(c), top=4)


def _sprite_funnel_web(s, c):
    _paint(s, [
        ".dd....dd...",   # thick legs
        "..d....d....",
        "..oooooo..",
        ".dobbbbo.d",
        "ddobbbbowedd",   # glinting eyes
        ".dobbbbood.",
        "..oooooodd",     # fangs
        ".dd.dd.dd...",
    ], _palette(c), top=2)


# ---------------------------------------------------------------------------
# Environment / actor sprites
# ---------------------------------------------------------------------------

def _sprite_corpse(s, c):
    pal = _palette(c)
    pal['n'] = BONE
    pal['d'] = shade(c, 0.6)
    _paint(s, [
        "...nnnnn",
        "..nnnnnnn",
        "..ndnnndn",
        "..nnndnnn",
        "...ndndn",
        "..n...n",
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
        "....oooo",
        "...obbbbo",
        "...obgbbo",
        "...obbbbo",
        ".oooooooooo",
        "obllbbbbbbbo",
        ".obbbddbbbo",
        "...d...d",
        "..dd..dd",
    ], pal, top=2)


def _sprite_part(s, c):
    pal = _palette(c)
    pal['g'] = GLOW
    _paint(s, [
        "....oooo",
        "...olbbbo",
        "..obbbbbbo",
        "..obbggbbo",
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
        ".....dd",
        ".....dd",
        "....obbo",
        "....obbo",
        "...obbbbo",
        "...obllbo",
        "...obllbo",
        "...obbbbo",
        "...oooooo",
    ], _palette(c), top=1)


def _icon_grenade(s, c):
    _paint(s, [
        ".oo..ddd",     # ring + cap
        ".o.dd.d",      # strap joins ring to cap
        ".oo.dd.d",
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
        ".obbbbbbbbo",
        ".obllbbbbbo",
        ".obbbbbbbbo",
        "..dddd.d",
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
        "..oooooo",
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
        "..lb",
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
        ".........ll",
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
        "....oooo",
        "...obbbbo",
        "...obbbbo",
        "...obddbo",
        ".oooooooooo.",
        "obbbbbbbbbbo",
    ], _palette(c), top=4)


def _icon_neck(s, c):
    _paint(s, [
        "...oooooo",
        "..oo....oo",   # thicker chain
        "..o......o",
        "..o......o",
        "...o....o",
        "....oooo",
        ".....ll",
        ".....ll",
    ], _palette(c), top=1)


def _icon_vest(s, c):
    _paint(s, [
        "..ll....ll",   # light straps read on dark
        ".obbo..obbo",
        ".obllllbo",
        ".obbbbbbo",
        ".obdbbdbo",
        ".obdbbdbo",
        ".obllllbo",
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
        "...ollllo",
        "...obbbbo",
        "...ollllo",
        "...ollllo",
        "...obbbbo",
        "...oooooo",
    ], _palette(c), top=3)


def _icon_tea(s, c):
    _paint(s, [
        "....l.l",      # steam zigzag, connected
        "...l.l",
        "....l.l",
        "...l.l",
        "..oddddo",
        "..obbbbooo",
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
        ".........ld",
        "........dd",
        ".......ld",
        "......dd",
        ".....ld",
        "....dd",
        "...ld",
        "..dd",
        ".ddd",
        "dddd",
    ], _palette(c), top=1)


def _sprite_unknown(s, c):
    pygame.draw.rect(s, (255, 0, 255), pygame.Rect(0, 0, TILE, TILE))


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
