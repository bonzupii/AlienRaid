#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monster templates: per-species stats, colors and AI classes."""

from random import randint

from components.ai import (KangaAI, JoeyAI, WallabyAI, WallarooAI, TreeKangaAI,
                           DingoAI, GoannaAI, KillerBeeAI, DropbearAI, TaipanAI,
                           EmuAI, WombatAI, MagpieAI, CassowaryAI, CrocodileAI,
                           EchidnaAI, FunnelWebAI)
from components.entity import Entity
from components.fighter import Fighter
from functions.render_order import RenderOrder
from renderer import palette as C

# spawn tables: [chance, min_dungeon_level] pairs (see random_utils)
MONSTER_TABLES = {
    'kanga':       [[0, 1], [25, 3], [45, 6], [50, 9], [40, 13], [25, 17]],
    'joey':        [[20, 1], [15, 2], [10, 4], [0, 8], [10, 9]],
    'wallaby':     [[25, 1], [30, 3], [20, 6], [10, 9], [5, 13]],
    'wallaroo':    [[0, 2], [15, 5], [30, 8], [30, 12], [20, 16]],
    'tree_kanga':  [[0, 4], [20, 7], [30, 10], [25, 14], [15, 18]],
    'dingo':       [[50, 1], [35, 4], [20, 7], [10, 10], [15, 11]],
    'goanna':      [[0, 5], [30, 8], [45, 11], [40, 14], [25, 18]],
    'killer_bee':  [[5, 1], [40, 7], [70, 10], [40, 12], [15, 15]],
    'dropbear':    [[0, 8], [20, 10], [40, 12], [50, 15], [60, 18]],
    'echidna':     [[0, 6], [20, 9], [30, 12], [30, 16], [20, 20]],
    'taipan':      [[0, 6], [25, 9], [40, 12], [35, 15], [20, 19]],
    'emu':         [[0, 3], [25, 6], [35, 9], [30, 13], [20, 17]],
    'funnel_web':  [[0, 5], [20, 8], [35, 11], [30, 14], [20, 18]],
    'wombat':      [[0, 4], [20, 7], [30, 10], [30, 14], [25, 18]],
    'magpie':      [[0, 5], [25, 8], [35, 11], [25, 15]],
    'cassowary':   [[0, 11], [15, 14], [25, 17], [30, 19]],
    'crocodile':   [[0, 14], [15, 17], [25, 20]],
}

# stat multipliers. statbase = randint(min, max) + min(level, 15)
TEMPLATES = {
    'kanga':       {'hp': 14, 'power': 2.6, 'def': 1.0, 'xp': 3.0, 'min': 22, 'max': 34, 'color': C.KANGA_RED},
    'joey':        {'hp': 14, 'power': 2.2, 'def': 1.0, 'xp': 2.6, 'min': 9,  'max': 18, 'color': C.KANGA_RED},
    'wallaby':     {'hp': 12, 'power': 2.4, 'def': 1.0, 'xp': 2.8, 'min': 12, 'max': 20, 'color': (205, 133, 63)},
    'wallaroo':    {'hp': 16, 'power': 3.0, 'def': 1.2, 'xp': 3.4, 'min': 18, 'max': 30, 'color': (139, 90, 43)},
    'tree_kanga':  {'hp': 15, 'power': 2.8, 'def': 1.1, 'xp': 3.2, 'min': 16, 'max': 28, 'color': (160, 82, 45)},
    'dingo':       {'hp': 14, 'power': 3.2, 'def': 1.0, 'xp': 3.0, 'min': 14, 'max': 22, 'color': C.DINGO_BROWN},
    'goanna':      {'hp': 14, 'power': 3.0, 'def': 1.1, 'xp': 3.2, 'min': 20, 'max': 32, 'color': C.GOANNA_GREEN},
    'killer_bee':  {'hp': 7,  'power': 9.0, 'def': 1.0, 'xp': 2.2, 'min': 8,  'max': 12, 'color': C.YELLOW},
    'dropbear':    {'hp': 10, 'power': 3.6, 'def': 1.3, 'xp': 4.0, 'min': 30, 'max': 40, 'color': C.DROPBEAR_GREY},
    'echidna':     {'hp': 16, 'power': 1.8, 'def': 3.0, 'xp': 3.6, 'thorns': 0.5, 'min': 18, 'max': 30, 'color': (120, 90, 60)},
    'funnel_web':  {'hp': 9,  'power': 6.0, 'def': 0.9, 'xp': 3.0, 'min': 10, 'max': 18, 'color': (40, 30, 30)},
    'taipan':      {'hp': 12, 'power': 3.4, 'def': 1.0, 'xp': 3.6, 'min': 16, 'max': 26, 'color': (139, 125, 60)},
    'emu':         {'hp': 13, 'power': 2.6, 'def': 1.0, 'xp': 3.0, 'min': 16, 'max': 26, 'color': (110, 90, 60)},
    'wombat':      {'hp': 18, 'power': 2.4, 'def': 2.0, 'xp': 3.4, 'min': 20, 'max': 32, 'color': (90, 90, 90)},
    'magpie':      {'hp': 10, 'power': 2.8, 'def': 1.0, 'xp': 2.8, 'min': 10, 'max': 18, 'color': (20, 20, 20)},
    'cassowary':   {'hp': 17, 'power': 3.8, 'def': 1.5, 'xp': 5.0, 'min': 26, 'max': 38, 'color': (40, 60, 120)},
    'crocodile':   {'hp': 20, 'power': 3.6, 'def': 1.8, 'xp': 5.0, 'min': 30, 'max': 44, 'color': (30, 80, 40)},
}

AI_CLASSES = {
    'kanga': KangaAI, 'joey': JoeyAI, 'wallaby': WallabyAI,
    'wallaroo': WallarooAI, 'tree_kanga': TreeKangaAI, 'dingo': DingoAI,
    'goanna': GoannaAI, 'killer_bee': KillerBeeAI,    'dropbear': DropbearAI, 'echidna': EchidnaAI, 'taipan': TaipanAI,
    'emu': EmuAI, 'funnel_web': FunnelWebAI, 'wombat': WombatAI,
    'magpie': MagpieAI, 'cassowary': CassowaryAI, 'crocodile': CrocodileAI,
}

DISPLAY_NAMES = {
    'kanga': 'Kanga', 'joey': 'Joey', 'wallaby': 'Wallaby',
    'wallaroo': 'Wallaroo', 'tree_kanga': 'Tree Kanga', 'dingo': 'Dingo',
    'goanna': 'Goanna', 'killer_bee': 'Killer Bee',    'dropbear': 'Dropbear', 'echidna': 'Echidna', 'taipan': 'Taipan',
    'emu': 'Emu', 'funnel_web': 'Funnel-web Spider', 'wombat': 'Wombat',
    'magpie': 'Magpie', 'cassowary': 'Cassowary', 'crocodile': 'Crocodile',
}


def create_monster(choice, dungeon_level, x, y):
    """Build a monster Entity of the given species at (x, y)."""
    t = TEMPLATES[choice]
    statbase = randint(t['min'], t['max']) + min(dungeon_level, 15)
    hp = int(statbase * t['hp'])
    power = int(statbase * t['power'])
    defense = int(statbase * t['def']) + dungeon_level
    xp = int(statbase * t['xp'])
    thorns = int(statbase * t.get('thorns', 0))

    fighter = Fighter(hp=hp, defense=defense, power=power, xp=xp, thorns=thorns)
    ai = AI_CLASSES[choice]()
    monster = Entity(x, y, choice, t['color'], DISPLAY_NAMES[choice],
                     blocks=True, render_order=RenderOrder.ACTOR,
                     fighter=fighter, ai=ai)
    return monster
