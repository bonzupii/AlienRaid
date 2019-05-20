# -*- coding: utf-8 -*-
#
#  data_loaders.py
#  
#  Copyright 2019 Bonzu <bonzupii@protonmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#  
#  
import os

import shelve

from components.game_states import GameStates


def save_game(player, entities, game_map, message_log, game_state):
	if game_state == GameStates.PLAYER_DEAD:
		pass
	else:
		with shelve.open('savegame.dat', 'n') as data_file:
			data_file['player_index'] = entities.index(player)
			data_file['entities'] = entities
			data_file['game_map'] = game_map
			data_file['message_log'] = message_log
			data_file['game_state'] = game_state


def load_game():
	if not os.path.isfile('savegame.dat'):
		raise FileNotFoundError

	with shelve.open('savegame.dat', 'r') as data_file:
		player_index = data_file['player_index']
		entities = data_file['entities']
		game_map = data_file['game_map']
		message_log = data_file['message_log']
		game_state = data_file['game_state']

	player = entities[player_index]

	return player, entities, game_map, message_log, game_state
