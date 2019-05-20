# -*- coding: utf-8 -*-
#
#  random_utils.py
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
from random import randint


def from_dungeon_level(table, dungeon_level):
	for (value, level) in reversed(table):
		if dungeon_level >= level:
			return value

	return 0


def random_choice_index(chances):
	random_chance = randint(1, sum(chances))

	running_sum = 0
	choice = 0
	for w in chances:
		running_sum += w

		if random_chance <= running_sum:
			return choice
		choice += 1


def random_choice_from_dict(choice_dict):
	choices = list(choice_dict.keys())
	chances = list(choice_dict.values())

	return choices[random_choice_index(chances)]
