#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SpriteLoader -- hand-authored pixel-art edition, v3 (16x16).

Phase 0 re-authors EVERY recipe at 16x16. No nearest-neighbour or
smoothscale upscaling of the old 12x12 art (12 -> 16 is a non-integer 4/3
and looks broken); every sprite is redrawn by hand for the taller cell.

16x16 style guide:
* 1-2px rim ('o') on every silhouette; dark bodies get a LIGHT rim so they
  never vanish into dark floors (see _palette).
* Light from above: 'l' highlights on top edges, 'd' shade underneath.
* Creatures face right; feet on the y=14-15 ground line. Every sprite has
  ink at y >= 13 -- the silhouettes FILL the taller cell; the extra rows go
  to legs, tails, wings, or a ground shadow, never to padding.
* 2px eyes ('e') with a white glint ('w') where room allows.
* Cream underbellies ('u') keep species silhouettes readable.
* Pixel maps are plain ASCII art: only the palette characters below and
  '.' for transparent. No runtime string munging.

Character map ('.' = transparent):
o  outline (dark rim, or light rim on dark bodies)
d  shadow / secondary (lighter mid on dark bodies)
b  body fill           l  top highlight
u  cream underbelly    e  eye            w  white   k  black
n  bone  a  wing membrane  g  glow  y  gold  r  red  t  blue tongue
"""
import pygame
from renderer.palette import shade

TILE = 16
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
        "....dd....dd....",
        "...dd......dd...",
        "...o........o...",
        "..oooooooooooo..",
        ".obbbbbbbbbbbbo.",
        ".obwwbbbbbbwwbo.",
        ".obwebbbbbbebbo.",
        ".obbbbbbbbbbbbo.",
        "..obbbbbbbbbbo..",
        "...oobbbbbboo...",
        "...obllllllbo...",
        ".obbbbbbbbbbbbo.",
        ".dbbo.dddd.obbd.",
        ".d..d.dddd.d..d.",
        ".d...d..d...d...",
        "dd...d..d...dd..",
    ], _palette(c))


def _sprite_player_sunglasses(s, c):
    """The player with the Konami-code cosmetic sunglasses (dark band
    over the eyes with a glint at each temple)."""
    _paint(s, [
        "....dd....dd....",
        "...dd......dd...",
        "...o........o...",
        "..oooooooooooo..",
        ".obbbbbbbbbbbbo.",
        ".obkkkkkkkkkbo..",
        ".obwkkkkkkkkwbo.",
        ".obbbbbbbbbbbbo.",
        "..obbbbbbbbbbo..",
        "...oobbbbbboo...",
        "...obllllllbo...",
        ".obbbbbbbbbbbbo.",
        ".dbbo.dddd.obbd.",
        ".d..d.dddd.d..d.",
        ".d...d..d...d...",
        "dd...d..d...dd..",
    ], _palette(c))


def _sprite_ute(s, c):
    pal = _palette(c)
    pal['y'] = GOLD
    _paint(s, [
        "................",
        "................",
        "................",
        "................",
        ".........ooo....",
        "........obwko...",
        "..y.y...obkko...",
        ".oyyyyo..obbbbo.",
        ".olbbbbbbbbbbbo.",
        ".obdbbbbbbdbbdo.",
        ".oooooooooooooo.",
        "..kk......kk....",
        "..kwk.....kwk...",
        "..kk......kk....",
        "................",
        "................",
    ], pal)


def _sprite_kanga(s, c):
    _paint(s, [
        ".........o.o....",
        ".........ooo....",
        "........obbo....",
        "........obweo...",
        "........obbo....",
        ".......obbuo....",
        "......obbuuo....",
        ".....obbuuuo....",
        "....obbbuuuo....",
        "...obbbbuuoob...",
        "..oobbbbuuo.....",
        ".odbbbbbo.......",
        ".oddbbbo........",
        ".dd..obbbbo.....",
        "..d..obbbbbo....",
        ".....dd..dd.....",
    ], _palette(c))


def _sprite_joey(s, c):
    _paint(s, [
        "................",
        "................",
        ".........d.d....",
        ".........d.d....",
        "........oooo....",
        "........obbeo...",
        "......oobbbdd...",
        ".....obbbbo.....",
        ".....dbbuuo.....",
        "....ddbuuo......",
        "...ddobuo.......",
        "..dd.obo........",
        ".d...obo........",
        ".....d.dd.......",
        "....ddddd.......",
        "...ddd.ddd......",
    ], _palette(c))


def _sprite_wallaby(s, c):
    _paint(s, [
        ".........d...d..",
        ".........d...d..",
        ".........d...d..",
        "........ooooo...",
        "........obbeo...",
        "........obbdd...",
        "....oobbbbbo....",
        "...obbbbbbbo....",
        "..obbbbbbuuo....",
        ".dd.obbbuuo.....",
        ".dd..obbbbo.....",
        "dd...obbo.......",
        "d....obbo.......",
        ".....d..d.......",
        "....dd..dd......",
        "...dddd.ddd.....",
    ], _palette(c))


def _sprite_wallaroo(s, c):
    _paint(s, [
        "........dd.dd...",
        "........dd.dd...",
        "........oooo....",
        ".......obbeo....",
        ".......obbbdd...",
        "...oobbbbbbbo...",
        "..obbbbbbbbbo...",
        ".obbbbbbbbbbo...",
        ".obbbbbbbubod...",
        ".obbbbbbbubod...",
        ".dobbbbbbuuo....",
        ".dobbbbbbo......",
        "..oddddbbo......",
        "..dd...dd.dd....",
        ".ddd...ddddd....",
        "dddd..ddddddd...",
    ], _palette(c))


def _sprite_tree_kanga(s, c):
    _paint(s, [
        ".d....d...d.....",
        ".d....d...d.....",
        ".d...oooooo.....",
        ".d...obbeo......",
        ".d...obbbdd.....",
        "dd..obbbbo.dd...",
        ".d.obbbbbbo.dd..",
        ".d.obbuubbo.d...",
        "...obbuubbo.....",
        "...obbbbbbo.....",
        "....obbbbo......",
        "....obbbbo......",
        ".....obbo.......",
        ".....d..d.......",
        "....dd..dd......",
        "...ddd..ddd.....",
    ], _palette(c))


def _sprite_dingo(s, c):
    _paint(s, [
        "..........o.o...",
        "..........ooo...",
        ".........obwek..",
        ".........obbo...",
        "........obbuo...",
        ".......obbbuo...",
        ".d....obbbbuo...",
        ".dd..obbbbbuo...",
        ".dddobbbbbbbo...",
        "..ddobbbbbbbo...",
        "...oobbbbbbo....",
        "....b..b..b.b...",
        "....b..b..b.b...",
        "....b..b..b.b...",
        "...dd.dd.dd.dd..",
        "................",
    ], _palette(c))


def _sprite_goanna(s, c):
    pal = _palette(c)
    pal['r'] = EMBER
    _paint(s, [
        "................",
        "................",
        "................",
        "................",
        "............oo..",
        "...........oweo.",
        "...........obbor",
        "..........obbo..",
        ".........obbo...",
        ".o....oobbbo....",
        ".dobbbbbbbbbo...",
        "dobdbdbdbbbbo...",
        "ddobbbbbbbbo....",
        ".d.o..o..o..o...",
        "...dd.dd.dd.dd..",
        "................",
    ], pal)


def _sprite_killer_bee(s, c):
    pal = _palette(c)
    pal['a'] = WING
    _paint(s, [
        "................",
        ".....aa.aa......",
        "....aaaaaaa.....",
        ".....a.a..k.k...",
        "..oobbbboo.oo...",
        ".obkbkbkbo.oeo..",
        ".obkbkbkbo.obo..",
        ".obkbkbkbo..o...",
        "k.obkbkbo.......",
        "..oobbbo........",
        "...k..k..k......",
        "..k....k...k....",
        "................",
        "................",
        "................",
        "................",
    ], pal)


def _sprite_dropbear(s, c):
    pal = _palette(c)
    pal['y'] = GOLD
    _paint(s, [
        "................",
        "................",
        "................",
        "...dd....dd.....",
        "..dd......dd....",
        ".obbbbbbbbbbo...",
        "obyybbbbbyybo...",
        "obyybbbbbyybo...",
        "obbbbbbbbbbbbo..",
        "obbbbkkkbbbbo...",
        ".obbbbbbbbbbo...",
        "..obbbbbbbo.....",
        "...oooooo.......",
        "..l.l..l.l......",
        ".ll.l..l.ll.....",
        "................",
    ], pal)


def _sprite_taipan(s, c):
    pal = _palette(c)
    pal['r'] = EMBER
    _paint(s, [
        "................",
        "..........ooo...",
        ".........obweo.r",
        ".........obbbo.r",
        "........obbuo..r",
        "........obbuo...",
        ".......obbuo....",
        "......obbuo.....",
        "....oobbbboo....",
        "...obbbbbbbo....",
        "...obddddbbo....",
        "..obbbbbbbbo....",
        "..obbdddbbbo....",
        "...ouuuuuuo.....",
        "....oooooo......",
        "................",
    ], pal)


def _sprite_emu(s, c):
    _paint(s, [
        "................",
        "........ooo.....",
        ".......obebd....",
        "........obbd....",
        "........obb.....",
        ".........dd.....",
        ".........dd.....",
        ".........dd.....",
        "....ooooddoo....",
        "...obbbbbbbo....",
        "...obdbdbdbbo...",
        "...obbbbbbbo....",
        "...ooooooo......",
        ".....dd.dd......",
        "....dd..dd......",
        "...ddd..ddd.....",
    ], _palette(c))


def _sprite_wombat(s, c):
    _paint(s, [
        "................",
        "................",
        "................",
        "................",
        "...dd....dd.....",
        "..obbbbbbbbo....",
        ".obbbbbbbbbbo...",
        "obbbbbbbbbbekk..",
        "obbbbbbbbbbokk..",
        "obbbbbbbbbbo....",
        ".olllllllllo....",
        "..ooooooooo.....",
        "...dd...dd......",
        "...dd...dd......",
        "..ddd...ddd.....",
        "................",
    ], _palette(c))


def _sprite_magpie(s, c):
    pal = _palette(c)
    pal['y'] = GOLD
    _paint(s, [
        "................",
        "................",
        "..........oooo..",
        ".........obebbo.",
        ".....ooooobbyy..",
        "....owbbbbbbo...",
        "...obbbbwwbo....",
        "...obbbwwwo.....",
        "...obbwwwo......",
        "..ddoooooo......",
        ".dd..d.d........",
        ".d..dd.dd.......",
        "w...d..d........",
        "ww..............",
        "................",
        "................",
    ], pal)


def _sprite_cassowary(s, c):
    pal = _palette(c)
    pal['r'] = EMBER
    _paint(s, [
        "................",
        ".........ll.....",
        "........ooo.....",
        ".......obebd....",
        "........obbr....",
        "........obbr....",
        "........obb.....",
        "....ooobboo.....",
        "...obbbbbbbo....",
        "...obdbdbbbo....",
        "...obbbbbbbo....",
        "...oooooooo.....",
        ".....dd.dd......",
        "....dd..dd......",
        "...ddd..ddd.....",
        "..dddd..dddd....",
    ], pal)


def _sprite_crocodile(s, c):
    _paint(s, [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "..d.l.l.l.l.o...",
        "..dobbbbbboebo..",
        "..dobbbbbbbbbb..",
        "..dobbbbbbbbbb..",
        "..dobbbbboww....",
        "..dooooooo......",
        "....d...d.......",
        "...dd...dd......",
        "..ddd...ddd.....",
        "................",
    ], _palette(c))


def _sprite_echidna(s, c):
    _paint(s, [
        "................",
        "................",
        "................",
        "................",
        "...l..l..l..l...",
        "..ll.ll.ll.ll...",
        "..ooooooooooo...",
        ".obbbbbbbbbbo...",
        ".obbbbbbbbbbeodd",
        ".obbbbbbbbbbod..",
        ".obbbbbbbbbbo...",
        "..ouuuuuuuo.....",
        "...oooooooo.....",
        "....d..d........",
        "...dd..dd.......",
        "................",
    ], _palette(c))


def _sprite_funnel_web(s, c):
    _paint(s, [
        "................",
        "................",
        "..dd......dd....",
        "...d......d.....",
        "...ooooooo......",
        "..dobbbbbbo.d...",
        ".dobbbbbowedd...",
        "ddobbbbbbood....",
        ".dobbbbbbood....",
        "..ooooooodd.....",
        "...dd.dd........",
        "..dd...dd.......",
        ".d.......d......",
        "................",
        "................",
        "................",
    ], _palette(c))


def _sprite_quokka(s, c):
    _paint(s, [
        "................",
        "................",
        "................",
        ".........dd.....",
        ".........dd.....",
        "........oooo....",
        ".......obbeo....",
        ".......obbdd....",
        ".....oobbo......",
        "....obbbbo......",
        "...obbbbbbo.....",
        "...obbbbbbo.....",
        "...obbbbbo......",
        "....ooooo.......",
        "...d..d..d......",
        "..dd..dd.dd.....",
    ], _palette(c))


def _sprite_thorny_devil(s, c):
    _paint(s, [
        "................",
        "................",
        "................",
        "................",
        "................",
        "..l.l.l.l.l.....",
        "..ooooooooo.....",
        ".obbbbbbbbbbo...",
        ".obbbbbbbbeod...",
        ".obbbbbbbbbbod..",
        ".obbbbbbbbbbo...",
        "..ouuuuuuo......",
        "...oooooo.......",
        "....d..d........",
        "...dd..dd.......",
        "................",
    ], _palette(c))


def _sprite_blue_tongue(s, c):
    pal = _palette(c)
    pal['t'] = (70, 140, 235)  # the namesake blue tongue
    _paint(s, [
        "................",
        "................",
        "................",
        "................",
        "................",
        "..........ooo...",
        "..........obe...",
        "..........obt...",
        ".........bt.....",
        "........b.......",
        "....oooooo......",
        "...obbbbbbo.....",
        "...ooooooo......",
        ".....d..d.......",
        "....dd..dd......",
        "................",
    ], pal)


def _sprite_wedge_tailed_eagle(s, c):
    pal = _palette(c)
    pal['a'] = WING
    pal['y'] = GOLD
    _paint(s, [
        "......aa........",
        "......ala.......",
        ".....abba.......",
        ".....abba.......",
        "....abbba.......",
        "....abbba.......",
        "..ooabbbaaooo...",
        ".odobbbbbbbbeoy.",
        "..oobbbbbboo....",
        "....abbba.......",
        "....abbba.......",
        ".....abba.......",
        ".....abba.......",
        "......ada.......",
        "......aa........",
        "................",
    ], pal)


def _sprite_feral_camel(s, c):
    _paint(s, [
        "............oo..",
        "...........oweo.",
        "...........obbod",
        "..........obbo..",
        "..........obbo..",
        ".........obbo...",
        ".........obbo...",
        ".obbo...obbo....",
        "dobbbobbbbbo....",
        "odbbbbbbbbbbo...",
        "obuubbbbbbbo....",
        ".obbbbbbbbo.....",
        "..obbbbbbbo.....",
        "...b..b..b..b...",
        "...b..b..b..b...",
        "..dd.dd.dd.dd...",
    ], _palette(c))

def _sprite_python(s, c):
    """Python: heavy constrictor in a low triple-strand coil (two open
    negative-space gaps so it reads as rope, not a fish), raised S-neck,
    small distinct head at upper right with eye + glint and a forked
    tongue, tail flicking out to the ground on the right."""
    pal = _palette(c)
    pal['r'] = EMBER
    _paint(s, [
        "................",
        "..........olo...",
        ".........obweo.r",
        ".........obbbor.",
        ".........obbo..r",
        "........obuo....",
        ".......obbuo....",
        "..olbbbbbbbbo...",
        ".oddddddddddo...",
        ".oooooooooooo...",
        ".olbbbbbbbbbo...",
        ".oddddddddddo...",
        ".oooooooooooo...",
        ".olbbbbbbbbbobbo",
        ".oddddddddddo..o",
        "..bbooooobb.....",
    ], pal)

def _sprite_redback(s, c):
    pal = _palette(c)
    pal['r'] = EMBER
    _paint(s, [
        "................",
        "................",
        "................",
        "................",
        "................",
        "...d.....d......",
        "..ooooooo.......",
        "..orrrro........",
        ".ddobbbood......",
        ".obbbbbbo.......",
        "..obbbbo........",
        "...oooo.........",
        "..d..d.d........",
        ".dd....dd.......",
        "................",
        "................",
    ], pal)


# ---------------------------------------------------------------------------
# NPCs (Phase F)
# ---------------------------------------------------------------------------
def _sprite_npc_aecd(s, c):
    """Khaki officer with a clipboard."""
    pal = _palette(c)
    pal['n'] = BONE
    _paint(s, [
        "................",
        "................",
        "......oooo......",
        ".....obbbbo.....",
        ".....obebbo.....",
        ".....obbbbo.....",
        "......obbo......",
        "....ooooooo.....",
        "...obbbbbbbo....",
        "...obbnnnbbo....",   # clipboard
        "...obbnnnbbo....",
        "...obbnbbbo.....",
        "...obbbbbbbo....",
        "...obbbbbbbo....",
        "....oo...oo.....",
        "....oo...oo.....",
    ], pal)


def _sprite_npc_swaggie(s, c):
    """Roadhouse keeper: akubra hat, towel over shoulder."""
    pal = _palette(c)
    pal['w'] = (220, 210, 190)
    _paint(s, [
        "................",
        "................",
        "......oooo......",
        ".....obbbbo.....",
        ".oooooooooooo...",
        "obbbbbbbbbbbo...",
        ".ooooooooooo....",
        ".....obebbo.....",
        ".....obbbbo.....",
        "....ooooooo.....",
        "...owbbbbbbo....",
        "...owbbbbbbo....",
        "...owbbbbbbo....",
        "...obbbbbbbo....",
        "....oo...oo.....",
        "....oo...oo.....",
    ], pal)


def _sprite_will_smith(s, c):
    """Will Smith: buzz cut, sunglasses, big smile, black suit."""
    pal = _palette(c)
    _paint(s, [
        "................",
        ".....kkkkkk.....",   # buzz cut
        "....kkkkkkkk....",
        "....kddddddk....",   # hair sheen
        "....obbbbbbo....",   # forehead
        "...obbbbbbbbo...",
        "...okkkkkkkko...",   # sunglasses
        "...okkbbbbkko...",   # lenses + nose bridge
        "...obbbbbbbbo...",
        "....obwwwwbo....",   # the smile
        "....obbbbbbo....",   # chin
        ".....obbbbo.....",   # neck
        "....okwwwwko....",   # suit + shirt
        "...okwwkkwwko...",   # collar + black tie
        "...okkkkkkkko...",
        "...oo....oo.....",   # shoes
    ], pal)


# ---------------------------------------------------------------------------
# Telegraph poses (defined before RECIPES so the registry can reference them)
# ---------------------------------------------------------------------------
def _sprite_kanga_rear(s, c):
    """Kanga rearing back, telegraphing a kick."""
    _paint(s, [
        "........o.o.....",
        "........o.o.....",
        ".......oooo.....",
        "......obbbeo....",
        "....oobbbbbdd...",
        "...olbbbbbbo....",
        "...obbbbbbbo....",
        "...obbbddbbo....",
        "...obbbbbbo.d...",
        "..d.obbbbo......",
        "..d..obbo.......",
        ".d...obbo.......",
        "d....d..d.......",
        "....dd..dd......",
        "....dd..dd......",
        "...ddd..ddd.....",
    ], _palette(c))


def _sprite_cassowary_rear(s, c):
    """Cassowary rearing for its dagger-claw strike."""
    pal = _palette(c)
    pal['r'] = EMBER
    _paint(s, [
        "................",
        ".........ll.....",
        "........ooo.....",
        ".......obebd....",
        "........obbr....",
        "........obbr....",
        "........obb.....",
        "....ooobboo.....",
        "...obbbbbbbo....",
        "...obdbdbbbo....",
        "...obbbbbbbbo...",
        "...obbbbbbbbo...",
        "...oooooooo.....",
        ".....dd.dd......",
        "....dd...dd.....",
        "...ddd...ddd....",
    ], pal)


# ---------------------------------------------------------------------------
# Environment / actor sprites
# ---------------------------------------------------------------------------
def _sprite_corpse(s, c):
    pal = _palette(c)
    pal['n'] = BONE
    pal['d'] = shade(c, 0.6)
    _paint(s, [
        "................",
        "................",
        "................",
        "....nnnnnnn.....",
        "...nnnnnnnnn....",
        "...nndnnnndn....",
        "...nnnndnnnn....",
        "....dddnddd.....",
        ".....n...n......",
        "......n.n.......",
        ".......n........",
        "......n.n.......",
        ".....n...n......",
        "....n.....n.....",
        "................",
        "................",
    ], pal)


def _sprite_trail_down(s, c):
    _paint(s, [
        "................",
        "................",
        "................",
        "................",
        "....obllbbbo....",
        ".....obbbbo.....",
        ".....obbbbo.....",
        "......obbo......",
        "......obbo......",
        "......obbo......",
        ".......oo.......",
        ".......oo.......",
        "........o.......",
        "................",
        "................",
        "................",
    ], _palette(c))


def _sprite_trail_up(s, c):
    _paint(s, [
        "................",
        ".......d........",
        "........o.......",
        ".......oo.......",
        ".......oo.......",
        "......obbo......",
        "......obbo......",
        "......obbo......",
        ".....obbbbo.....",
        ".....obbbbo.....",
        "....obllbbbo....",
        "................",
        "................",
        "................",
        "................",
        "................",
    ], _palette(c))


def _sprite_ship(s, c):
    pal = _palette(c)
    pal['g'] = GLOW
    _paint(s, [
        "....dd..........",
        ".....dd.........",
        "......dd........",
        "......oooo......",
        ".....obggbo.....",
        ".....obbbbo.....",
        "...oobbbbbboo...",
        "..obllbbbbbbbo..",
        ".obbbbbbbbbbbbo.",
        ".obbbbddbbbbbo..",
        "..obbbdddbbbo...",
        "...oooooooooo...",
        "...o........o...",
        "................",
        "................",
        "................",
    ], pal)


def _sprite_part(s, c):
    pal = _palette(c)
    pal['g'] = GLOW
    _paint(s, [
        "................",
        "................",
        "................",
        ".....oooooo.....",
        "....olbbbbbo....",
        "...obbbbbbbbo...",
        "...obbggbbbo....",
        "...obbggbbbo....",
        "...obbggbbbo....",
        "....obbbbo......",
        ".....oooo.......",
        "................",
        "................",
        "................",
        "................",
        "................",
    ], pal)


# ---------------------------------------------------------------------------
# Item / equipment icons (ground shadow on y=13-15)
# ---------------------------------------------------------------------------
def _icon_cross(s, c):
    _paint(s, [
        "................",
        "................",
        "......oooo......",
        ".....obbbbo.....",
        "...ollllllllo...",
        "...obbbbbbbbo...",
        "...obbbwwbbbo...",
        "...obbbwwbbbo...",
        "...obwwwwwwbo...",
        "...obwwwwwwbo...",
        "...obbbwwbbbo...",
        "...obbbwwbbbo...",
        "...oddddddddo....",
        "....ooddddoo....",
        ".....oooooo.....",
        "................",
    ], _palette(c))


def _icon_bottle(s, c):
    _paint(s, [
        "................",
        "......dd........",
        "......dd........",
        ".....obbo.......",
        ".....obbo.......",
        "....obbbbo......",
        "....obllbo......",
        "....obllbo......",
        "....obllbo......",
        "....obbbbo......",
        "....obbbbo......",
        "....oooooo......",
        "................",
        "................",
        "................",
        "................",
    ], _palette(c))


def _icon_grenade(s, c):
    _paint(s, [
        "................",
        "..oo...ddd......",
        "..o.dd.d........",
        "..oo.dd.d.......",
        "....oooooo......",
        "...olbbbbbo.....",
        "...obbbbbbo.....",
        "...obbbbbbo.....",
        "...obbbbbbo.....",
        "...obbbbbbo.....",
        "....obbbbo......",
        "....oooooo......",
        "................",
        "................",
        "................",
        "................",
    ], _palette(c))


def _icon_gun(s, c):
    _paint(s, [
        "................",
        "................",
        "................",
        "................",
        "................",
        "..obbbbbbbbbo...",
        "..obllbbbbbbo...",
        "..obbbbbbbbbo...",
        "..obbbbbbbbbo...",
        "...dddd.d.......",
        "...dddd.........",
        "...dddd.........",
        "..dddd..........",
        "..dddd..........",
        "..dddd..........",
        "................",
    ], _palette(c))


def _icon_bolt(s, c):
    # The hand-tuned bolt-jog from the 12x12 original, preserved.
    _paint(s, [
        "................",
        "........oooo....",
        ".......ollbo....",
        "......ollbo.....",
        ".....olbo.......",
        "....ollllbo.....",
        "......olbo......",
        ".....olbo.......",
        "....olbo........",
        "...olbo.........",
        "...olo..........",
        "..olo...........",
        "..oo............",
        ".o..............",
        "................",
        "................",
    ], _palette(c))


def _icon_tentacle(s, c):
    _paint(s, [
        "................",
        ".....lb.........",
        "....bb..........",
        "...lb...........",
        "...bb...........",
        "....lb..........",
        "....bb..........",
        ".....lb.........",
        ".....bb.........",
        "....lb..........",
        "....bb..........",
        "...bb...........",
        "...bbb..........",
        "..bbbb..........",
        ".bbbb...........",
        ".bbbb............",
    ], _palette(c))


def _icon_shield(s, c):
    pal = _palette(c)
    pal['g'] = GLOW
    _paint(s, [
        "................",
        "..oooooooooooo..",
        "..obllbbbbbbdo..",
        "..obbbbbbbbbdo..",
        "..obbbggbbbbdo..",
        "...obbggggbdo...",
        "...obbggggbdo...",
        "...obbbggbbdo...",
        "....obbggbdo....",
        "....obbbbbdo....",
        ".....obbbdo.....",
        "......obdo......",
        ".......oo.......",
        "................",
        "................",
        "................",
    ], pal)


def _icon_twig(s, c):
    _paint(s, [
        "................",
        ".............ll.",
        "............dd..",
        "...l.......dd...",
        "....l...dd......",
        "....l..dd.......",
        "....ldd.........",
        "....dd..........",
        "...dd...........",
        "...dd...........",
        "..dd............",
        "..dd............",
        ".dd.............",
        ".dd.............",
        "dd..............",
        "d...............",
    ], _palette(c))


def _icon_hat(s, c):
    _paint(s, [
        "................",
        "................",
        "................",
        "................",
        "......oooo......",
        ".....obbbbo.....",
        ".....obbbbo.....",
        ".....obddbo.....",
        ".....obbbbo.....",
        "..ooooooooooo...",
        ".obbbbbbbbbbbo..",
        ".obbbbbbbbbbbo..",
        "..oooooooooo....",
        "................",
        "................",
        "................",
    ], _palette(c))


def _icon_neck(s, c):
    _paint(s, [
        "................",
        "....ooooooo.....",
        "...oo.....oo....",
        "..o.........o...",
        "..o.........o...",
        "..o.........o...",
        "...o.......o....",
        "....o.....o.....",
        ".....ooooo......",
        "......ll........",
        "......ll........",
        "......ll........",
        "................",
        "................",
        "................",
        "................",
    ], _palette(c))


def _icon_vest(s, c):
    _paint(s, [
        "................",
        "................",
        "...ll....ll.....",
        "..obbo..obbo....",
        "..obbo..obbo....",
        "..obllllllbo....",
        "..obbbbbbbbo....",
        "..obdbbddbbo....",
        "..obdbbddbbo....",
        "..obdbbddbbo....",
        "..obllllllbo....",
        "...obbbbbbo.....",
        "...ooooooo......",
        "................",
        "................",
        "................",
    ], _palette(c))


def _icon_boomerang(s, c):
    _paint(s, [
        "................",
        "..ooo...........",
        ".oblo...........",
        ".obbo...........",
        ".obbo...........",
        ".obbo...........",
        ".obbo...........",
        ".obbo...........",
        ".obbo...........",
        ".obllllllllbo...",
        ".obbbwwbbbbo....",
        "..oooooooooo....",
        "................",
        "................",
        "................",
        "................",
    ], _palette(c))


def _icon_ration(s, c):
    _paint(s, [
        "................",
        "................",
        "................",
        "................",
        "....ooooooo.....",
        "....olllllo.....",
        "....obbbbo......",
        "....olllllo.....",
        "....olllllo.....",
        "....olllllo.....",
        "....obbbbo......",
        "....ooooooo.....",
        "................",
        "................",
        "................",
        "................",
    ], _palette(c))


def _icon_tea(s, c):
    _paint(s, [
        "................",
        ".....l.l........",
        "....l.l.........",
        ".....l.l........",
        "....l.l.........",
        "...oddddo.......",
        "...obbbbooo.....",
        "...obbbbo.o.....",
        "...obbbbooo.....",
        "...obbbbo.......",
        "....oooo........",
        "................",
        "................",
        "................",
        "................",
        "................",
    ], _palette(c))


def _icon_star(s, c):
    _paint(s, [
        ".......oo.......",
        "......obbo......",
        "......obbo......",
        ".....obbbbo.....",
        "....obbbbbbo....",
        "...obwbbbbbbo...",
        ".oobbbbbbbbbboo.",
        "obbbbbbwbbbbbbbo",
        ".oobbbbbbbbbboo.",
        "...obbbbbbbbo...",
        "....obbbbbbo....",
        ".....obbbbo.....",
        "......obbo......",
        "......obbo......",
        ".......oo.......",
        "................",
    ], _palette(c))


def _icon_tube(s, c):
    _paint(s, [
        "................",
        "............oo..",
        "...........okbo.",
        "...........lbo..",
        "..........lbo...",
        "..........ldo...",
        ".........lbo....",
        ".........lbo....",
        "........lbo.....",
        "........ldo.....",
        ".......lbo......",
        "......lbbo......",
        ".....lbbbo......",
        "....olbbbbo.....",
        "...obkkkkbo.....",
        "...oooooooo.....",
    ], _palette(c))


def _icon_neuralyzer(s, c):
    """The MIB neuralyzer: chrome wand with a red flash lens."""
    pal = _palette(c)
    pal['r'] = EMBER
    _paint(s, [
        "................",
        "................",
        "................",
        "......oooo......",
        ".....orrrro.....",
        ".....oooooo.....",
        "....olbbbbbo....",
        "....obbbbbbo....",
        "....oblllbbo....",
        "....obbbbbbo....",
        "....obbbbbbo....",
        "....obbbbbbo....",
        "....ooooooo.....",
        "................",
        "................",
        "................",
    ], pal)


def _icon_datalog(s, c):
    """Alien data-log slab with a glow stripe."""
    pal = _palette(c)
    pal['g'] = GLOW
    _paint(s, [
        "................",
        "................",
        "................",
        "....ooooooo.....",
        "...obbbbbbbbo...",
        "...obgggggbo....",
        "...obbbbbbbbo...",
        "...obbllbbbo....",
        "...obbbbbbbbo...",
        "...obgggggbo....",
        "...obbbbbbbbo...",
        "...ooooooooo....",
        "................",
        "................",
        "................",
        "................",
    ], pal)


def _sprite_unknown(s, c):
    pygame.draw.rect(s, (255, 0, 255), pygame.Rect(0, 0, TILE, TILE))


RECIPES = {
    'player': _sprite_player,
    'player_sunglasses': _sprite_player_sunglasses,
    'ute': _sprite_ute,
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
    'quokka': _sprite_quokka,
    'thorny_devil': _sprite_thorny_devil,
    'blue_tongue': _sprite_blue_tongue,
    'wedge_tailed_eagle': _sprite_wedge_tailed_eagle,
    'feral_camel': _sprite_feral_camel,
    'python': _sprite_python,
    'redback': _sprite_redback,
    'kanga_rear': _sprite_kanga_rear,
    'cassowary_rear': _sprite_cassowary_rear,
    'agent_j_cameo': _sprite_will_smith,
    'npc_aecd': _sprite_npc_aecd,
    'npc_swaggie': _sprite_npc_swaggie,
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
    'icon_neuralyzer': _icon_neuralyzer,
    'icon_datalog': _icon_datalog,
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
