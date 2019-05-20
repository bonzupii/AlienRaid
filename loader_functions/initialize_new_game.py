#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  initialize_new_game.py
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
import tcod as libtcod

from components.equipment import Equipment
from components.equippable import Equippable
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level

from components.entity import Entity
from components.equipment_slots import EquipmentSlots
from components.game_messages import MessageLog
from components.game_states import GameStates

from functions.render_functions import RenderOrder

from map_objects.game_map import GameMap




def get_constants():
	window_title = 'Alien Raid'
	
	screen_width = 100
	screen_height = 55
	
	bar_width = 30
	panel_height = 7
	panel_y = screen_height - panel_height
	
	message_x = bar_width + 2
	message_width = screen_width - bar_width - 2
	message_height = panel_height - 1
	
	map_width = 100
	map_height = 48
	
	room_max_size = 18
	room_min_size = 3
	max_rooms = 400
	
	fov_algorithm = 0
	fov_light_walls = True
	fov_radius = 12
	
	colors = {
		'dark_wall': libtcod.Color(100, 20, 10),
		'dark_ground': libtcod.Color(170, 90, 10),
		'light_wall': libtcod.Color(140, 60, 10),
		'light_ground': libtcod.Color(210, 130, 50)
	}
	
	constants = {
		'window_title': window_title,
		'screen_width': screen_width,
		'screen_height': screen_height,
		'bar_width': bar_width,
		'panel_height': panel_height,
		'panel_y': panel_y,
		'message_x': message_x,
		'message_width': message_width,
		'message_height': message_height,
		'map_width': map_width,
		'map_height': map_height,
		'room_max_size': room_max_size,
		'room_min_size': room_min_size,
		'max_rooms': max_rooms,
		'fov_algorithm': fov_algorithm,
		'fov_light_walls': fov_light_walls,
		'fov_radius': fov_radius,
		'colors': colors
	}
	
	return constants
	
def get_game_variables(constants):
	fighter_component = Fighter(hp=1250, defense=10, power=40)
	inventory_component = Inventory(26)
	level_component = Level()
	equipment_component = Equipment()
	player = Entity(0, 0, 197, libtcod.Color(15, 77, 0), 'Wrpgnyth', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, inventory=inventory_component, level=level_component, equipment=equipment_component)
	entities = [player]
	
	equippable_component = Equippable(EquipmentSlots.TENTACLE, power_bonus=20)
	tentaclaws = Entity(0, 0, 218, libtcod.red, 'Tentaclaws', equippable=equippable_component)
	player.inventory.add_item(tentaclaws)
	player.equipment.toggle_equip(tentaclaws)
	
	equippable_component = Equippable(EquipmentSlots.TENTACLE, power_bonus=20, defense_bonus=20)
	aluminitetentasleeve = Entity(0, 0, 192, libtcod.silver, 'Aluminite Tentasleeve', equippable=equippable_component)
	player.inventory.add_item(aluminitetentasleeve)
	player.equipment.toggle_equip(aluminitetentasleeve)

	game_map = GameMap(constants['map_width'], constants['map_height'])
	game_map.make_map(constants['max_rooms'], constants['room_min_size'], constants['room_max_size'], constants['map_width'], constants['map_height'], player, entities)
	
	message_log = MessageLog(constants['message_x'], constants['message_width'], constants['message_height'])

	game_state = GameStates.PLAYERS_TURN

	return player, entities, game_map, message_log, game_state
