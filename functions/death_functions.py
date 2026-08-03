# -*- coding: utf-8 -*-
"""Death handling (no libtcod). Kill the player = delete the save and die.
Kill a monster = turn it into a corpse and roll its species drop table."""

import os
from random import randint

from components.game_messages import Message
from components.game_states import GameStates
from functions.render_order import RenderOrder
from loader_functions.monsters import DROP_TABLES
from loader_functions.items import create_item
from loader_functions.random_utils import from_dungeon_level
from renderer import palette as C


def kill_player(player):
    # Delete the savegame on death so the player has to start over.
    if os.path.isfile('savegame.dat'):
        os.remove('savegame.dat')
    player.sprite_id = 'corpse'
    player.color = C.DARK_RED
    return Message('You died!', C.RED), GameStates.PLAYER_DEAD


def kill_monster(monster, dungeon_level=1):
    """Turn a monster into a corpse. Returns ``(message, dropped_item)``
    where ``dropped_item`` is a freshly created item Entity (or None)."""
    death_message = Message('{0} is dead!'.format(monster.name.capitalize()), C.ORANGE)
    monster.sprite_id = 'corpse'
    monster.color = C.DARK_RED
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.render_order = RenderOrder.CORPSE

    dropped_item = None
    species = getattr(monster, 'species', None)
    if species in DROP_TABLES:
        for item_choice, table in DROP_TABLES[species].items():
            chance = from_dungeon_level(table, dungeon_level)
            if chance > 0 and (chance >= 100 or randint(1, 100) <= chance):
                dropped_item = create_item(item_choice, dungeon_level,
                                           monster.x, monster.y)
                break

    return death_message, dropped_item
