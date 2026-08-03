# -*- coding: utf-8 -*-
"""Death handling (no libtcod)."""

import os

from components.game_messages import Message
from components.game_states import GameStates
from functions.render_order import RenderOrder
from renderer import palette as C


def kill_player(player):
    # Delete the savegame on death so the player has to start over.
    if os.path.isfile('savegame.dat'):
        os.remove('savegame.dat')
    player.sprite_id = 'corpse'
    player.color = C.DARK_RED
    return Message('You died!', C.RED), GameStates.PLAYER_DEAD


def kill_monster(monster):
    death_message = Message('{0} is dead!'.format(monster.name.capitalize()), C.ORANGE)
    monster.sprite_id = 'corpse'
    monster.color = C.DARK_RED
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.render_order = RenderOrder.CORPSE
    return death_message
