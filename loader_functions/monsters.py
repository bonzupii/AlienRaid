#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monster templates: per-species stats, colors and AI classes."""

from random import randint

from components.ai import (KangaAI, JoeyAI, WallabyAI, WallarooAI, TreeKangaAI,
                           DingoAI, GoannaAI, KillerBeeAI, DropbearAI, TaipanAI,
                           EmuAI, WombatAI, MagpieAI, CassowaryAI, CrocodileAI,
                           EchidnaAI, FunnelWebAI, QuokkaAI, ThornyDevilAI,
                           BlueTongueAI, WedgeTailedEagleAI, FeralCamelAI,
                           PythonAI, RedbackAI)
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
    'quokka':      [[0, 2], [15, 5], [20, 8], [15, 12]],
    'thorny_devil':   [[0, 6], [20, 9], [25, 13], [20, 17]],
    'blue_tongue':    [[0, 4], [15, 7], [20, 11], [15, 15]],
    'wedge_tailed_eagle': [[0, 8], [10, 11], [15, 15], [10, 19]],
    'feral_camel':    [[0, 10], [10, 13], [15, 16], [10, 19]],
    'python':         [[0, 12], [15, 15], [20, 18]],
    'redback':        [[0, 3], [20, 6], [30, 10], [25, 14], [20, 18]],
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
    'quokka':      {'hp': 8, 'power': 1.5, 'def': 0.8, 'xp': 2.0, 'min': 10, 'max': 18, 'color': (180, 140, 100)},
    'thorny_devil':    {'hp': 12, 'power': 2.2, 'def': 2.5, 'xp': 3.0, 'thorns': 0.8, 'min': 16, 'max': 28, 'color': (160, 120, 80)},
    'blue_tongue':     {'hp': 11, 'power': 2.0, 'def': 1.2, 'xp': 2.8, 'min': 14, 'max': 24, 'color': (100, 80, 60)},
    'wedge_tailed_eagle': {'hp': 14, 'power': 3.5, 'def': 1.3, 'xp': 4.0, 'min': 20, 'max': 32, 'color': (80, 60, 40)},
    'feral_camel':     {'hp': 25, 'power': 2.8, 'def': 2.0, 'xp': 4.5, 'min': 30, 'max': 45, 'color': (200, 180, 140)},
    'python':          {'hp': 18, 'power': 3.2, 'def': 1.5, 'xp': 4.2, 'min': 24, 'max': 38, 'color': (100, 80, 50)},
    'redback':         {'hp': 6, 'power': 8.0, 'def': 0.7, 'xp': 2.5, 'min': 8, 'max': 14, 'color': (40, 20, 20)},
}

# species -> { item_choice: [[chance, min_level]] } dropped on death (Phase C)
DROP_TABLES = {
    'emu':         {'emu_egg': [[100, 1]]},
    'dropbear':    {'dropbear_meat': [[100, 1]]},
    'taipan':      {'taipan_meat': [[100, 1]]},
    'cassowary':   {'cassowary_crest_crown': [[100, 1]]},
    'crocodile':   {'croc_hide_cuirass': [[100, 1]],
                    'esky_of_holding': [[30, 1]]},
    'killer_bee':  {'golden_wattle_salve': [[50, 1]]},
    'dingo':       {'whippy_willow_twig': [[50, 1]]},
    'wombat':      {'wombat_hide_cuirass': [[50, 1]]},
    'echidna':     {'goanna_skin_hat': [[50, 1]]},
    'kanga':       {'boomerang': [[50, 1]]},
}

AI_CLASSES = {
    'kanga': KangaAI, 'joey': JoeyAI, 'wallaby': WallabyAI,
    'wallaroo': WallarooAI, 'tree_kanga': TreeKangaAI, 'dingo': DingoAI,
    'goanna': GoannaAI, 'killer_bee': KillerBeeAI,    'dropbear': DropbearAI, 'echidna': EchidnaAI, 'taipan': TaipanAI,
    'emu': EmuAI, 'funnel_web': FunnelWebAI, 'wombat': WombatAI,
    'magpie': MagpieAI, 'cassowary': CassowaryAI, 'crocodile': CrocodileAI,
    'quokka': QuokkaAI, 'thorny_devil': ThornyDevilAI,
    'blue_tongue': BlueTongueAI, 'wedge_tailed_eagle': WedgeTailedEagleAI,
    'feral_camel': FeralCamelAI, 'python': PythonAI, 'redback': RedbackAI,
}

DISPLAY_NAMES = {
    'kanga': 'Kanga', 'joey': 'Joey', 'wallaby': 'Wallaby',
    'wallaroo': 'Wallaroo', 'tree_kanga': 'Tree Kanga', 'dingo': 'Dingo',
    'goanna': 'Goanna', 'killer_bee': 'Killer Bee',    'dropbear': 'Dropbear', 'echidna': 'Echidna', 'taipan': 'Taipan',
    'emu': 'Emu', 'funnel_web': 'Funnel-web Spider', 'wombat': 'Wombat',
    'magpie': 'Magpie', 'cassowary': 'Cassowary', 'crocodile': 'Crocodile',
    'quokka': 'Quokka', 'thorny_devil': 'Thorny Devil',
    'blue_tongue': 'Blue-tongue Lizard', 'wedge_tailed_eagle': 'Wedge-tailed Eagle',
    'feral_camel': 'Feral Camel', 'python': 'Python', 'redback': 'Redback Spider',
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
    monster.species = choice
    return monster
