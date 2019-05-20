# -*- coding: utf-8 -*-
#
#  game_states.py
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
from enum import Enum


class GameStates(Enum):
	PLAYERS_TURN = 1
	ENEMY_TURN = 2
	PLAYER_DEAD = 3
	SHOW_INVENTORY = 4
	DROP_INVENTORY = 5
	TARGETING = 6
	LEVEL_UP = 7
	CHARACTER_SCREEN = 8
	EQUIPMENT_SCREEN = 9
