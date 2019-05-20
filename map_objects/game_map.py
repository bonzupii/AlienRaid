#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  game_map.py
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
from random import randint

from components.ai import BasicMonster
from components.equipment import EquipmentSlots
from components.equippable import Equippable
from components.fighter import Fighter
from components.item import Item
from components.trail import Trail
from components.entity import Entity
from components.game_messages import Message
from components.game_states import GameStates

from functions.item_functions import use_stun_grenade, use_plasma_grenade, use_shock_charge, heal, morphine_pack, use_ray_gun
from functions.render_functions import RenderOrder

from map_objects.rectangle import Rect
from map_objects.tile import Tile
from loader_functions.random_utils import from_dungeon_level, random_choice_from_dict

class GameMap:
	def __init__(self, width, height, dungeon_level=1):
		self.width = width
		self.height = height
		self.tiles = self.initialize_tiles()
		
		self.dungeon_level = dungeon_level
		
	def initialize_tiles(self):
		tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]
		
		
		return tiles
		
	def make_map(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities):
		rooms = []
		num_rooms = 0
		
		center_of_last_room_x = None
		center_of_last_room_y = None
		
		for r in range(max_rooms):
			# Random width and height
			w = randint(room_min_size, room_max_size)
			h = randint(room_min_size, room_max_size)
			# Random position without going out of the boundaries of the map
			x = randint(0, map_width - w - 1)
			y = randint(0, map_height - h - 1)
			
			# "Rect" class makes rectangles easier to work with
			new_room = Rect(x, y, w, h)
			
			# Run through the other rooms and see if they intersect with this one
			for other_room in rooms:
				if new_room.intersect(other_room):
					break
			else:
				# This means there are no intersections, so this room is valid
				
				# "Paint" it to the map's tiles
				self.create_room(new_room)
				
				# Center coordinates of new room, will be useful later
				(new_x, new_y) = new_room.center()
				
				center_of_last_room_x = new_x
				center_of_last_room_y = new_y
				
				if num_rooms == 0:
					# This is the first room, where the player starts at
					player.x = new_x
					player.y = new_y
				else:
					# All rooms after the first:
					# Connect it to the previous room with a tunnel
				
					# Center coordinates of previous room
					(prev_x, prev_y) = rooms[num_rooms - 1].center()
				
					# Flip a coin (random number that is either 0 or 1)
					if randint(0, 1) == 1:
						# First move horizontally, then vertically
						self.create_h_tunnel(prev_x, new_x, prev_y)
						self.create_v_tunnel(prev_y, new_y, new_x)
					else:
						# First move vertically, then horizontally
						self.create_v_tunnel(prev_y, new_y, prev_x)
						self.create_h_tunnel(prev_x, new_x, new_y)
						
				self.place_entities(new_room, entities)	
				# Finally, append the new room to the list
				rooms.append(new_room)
				num_rooms += 1
				
		trail_component = Trail(self.dungeon_level + 1)
		down_trail = Entity(center_of_last_room_x, center_of_last_room_y, 205, libtcod.Color(140, 60, 10), 'Trail', render_order=RenderOrder.TRAIL, trail=trail_component)
		entities.append(down_trail)
		
	def create_room(self, room):
		# Go through the tiles in the rectangle and make them passable
		for x in range(room.x1 + 1, room.x2):
			for y in range(room.y1 + 1, room.y2):
				self.tiles[x][y].blocked = False
				self.tiles[x][y].block_sight = False
				
	def create_h_tunnel(self, x1, x2, y):
		for x in range(min(x1, x2), max(x1, x2) + 1):
			self.tiles[x][y].blocked = False
			self.tiles[x][y].block_sight = False
			
	def create_v_tunnel(self, y1, y2, x):
		for y in range(min(y1, y2), max(y1, y2) + 1):
			self.tiles[x][y].blocked = False
			self.tiles[x][y].block_sight = False
			
	def place_entities(self, room, entities):
		max_monsters_per_room = from_dungeon_level([[2, 1], [3, 4], [5, 6], [7, 10]], self.dungeon_level)
		min_monsters_per_room = from_dungeon_level([[0, 1], [1, 4], [2, 6], [6, 10], [3, 11]], self.dungeon_level)
		max_items_per_room = from_dungeon_level([[1, 1], [2, 4], [3, 7]], self.dungeon_level)

		# Get a random number of monsters
		number_of_monsters = randint(min_monsters_per_room, max_monsters_per_room)
		number_of_items = randint(0, max_items_per_room)

			
		
		monster_chances = {
			'kanga': from_dungeon_level([[25, 3], [70, 6],[5, 10], [70, 11], [30, 16]], self.dungeon_level),
			'dingo': from_dungeon_level([[60, 1], [45, 4], [20, 7], [5, 10], [20, 11]], self.dungeon_level),
			'joey': from_dungeon_level([[20, 1], [15, 2], [10, 3], [0, 10], [10, 11]], self.dungeon_level),
			'goanna': from_dungeon_level([[20, 6], [70, 9], [10, 10], [70, 11], [55, 16]], self.dungeon_level),
			'killer_bees': from_dungeon_level([[5, 1], [100, 10], [5, 11]], self.dungeon_level),
			'dropbear': from_dungeon_level([[15, 9], [5, 10], [35, 11], [55, 14], [70, 16]], self.dungeon_level)
		}
		item_chances = {
			'lesser_med_kit': from_dungeon_level([[25, 1], [20, 5], [1, 7]], self.dungeon_level),
			'morphine_pack': from_dungeon_level([[5, 5], [20, 7], [5, 9]], self.dungeon_level),
			'tentacruels': from_dungeon_level([[5, 3]], self.dungeon_level),
			'energy_shield': from_dungeon_level([[15, 6]], self.dungeon_level),
			'plasma_grenade': from_dungeon_level([[10, 3], [12, 5]], self.dungeon_level),
			'stun_grenade': from_dungeon_level([[10, 2], [15, 4]], self.dungeon_level),
			'ray_gun': from_dungeon_level([[3, 6], [5, 8]], self.dungeon_level),
			'shock_charge': from_dungeon_level([[5,1], [13, 3]], self.dungeon_level),
			'med_kit': from_dungeon_level([[5, 7], [25, 9]], self.dungeon_level),
			'whippy_willow_twig': from_dungeon_level([[15, 1]], self.dungeon_level),
			'goanna_skin_hat': from_dungeon_level([[5, 1], [15, 3]], self.dungeon_level),
			'aluminite_neck_brace': from_dungeon_level([[5, 2], [10, 4]], self.dungeon_level),
			'dropbear_fur_vest': from_dungeon_level([[5, 3], [7, 6]], self.dungeon_level)
		}
		
		for i in range(number_of_monsters):
			# Choose a random location in the room
			x = randint(room.x1 + 1, room.x2 - 1)
			y = randint(room.y1 + 1, room.y2 - 1)
			
			if not any([entity for entity in entities if entity.x == x and entity.y == y]):
				monster_choice = random_choice_from_dict(monster_chances)
				if monster_choice == 'kanga':
					statbase = randint(30, 45) + self.dungeon_level
					rand_hp = statbase * 15
					rand_def = statbase
					rand_power = round(statbase * 2.5)
					rand_xp = statbase * 3
					fighter_component = Fighter(hp=rand_hp, defense=rand_def, power=rand_power, xp=rand_xp)
					ai_component = BasicMonster()
					monster = Entity(x, y, 196, libtcod.Color(218, 42, 32), 'Kanga', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
				elif monster_choice == 'dingo':
					statbase = randint(15, 20) + self.dungeon_level
					rand_hp = statbase * 15
					rand_def = statbase
					rand_power = round(statbase * 3.5)
					rand_xp = statbase * 3
					fighter_component = Fighter(hp=rand_hp, defense=rand_def, power=rand_power, xp=rand_xp)
					ai_component = BasicMonster()
					monster = Entity(x, y, 191, libtcod.Color(165, 42, 42), 'Dingo', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
				elif monster_choice == 'goanna':
					statbase = randint(45, 55) + self.dungeon_level
					rand_hp = statbase * 15
					rand_def = statbase
					rand_power = statbase * 3
					rand_xp = statbase * 3
					fighter_component = Fighter(hp=rand_hp, defense=rand_def, power=rand_power, xp=rand_xp)
					ai_component = BasicMonster()
					monster = Entity(x, y, 186, libtcod.Color(25, 42, 0), 'Goanna', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
				elif monster_choice == 'dropbear':
					statbase = randint(60, 65) + self.dungeon_level
					rand_hp = statbase * 10
					rand_def = statbase + self.dungeon_level
					rand_power = statbase * 4
					rand_xp = statbase * 4
					fighter_component = Fighter(hp=rand_hp, defense=rand_def, power=rand_power, xp=rand_xp)
					ai_component = BasicMonster()
					monster = Entity(x, y, 191, libtcod.Color(33, 33, 33), 'Dropbear', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
				elif monster_choice == 'killer_bees':
					statbase = randint(8, 10) + self.dungeon_level
					rand_hp = statbase * 7
					rand_def = statbase
					rand_power = round(statbase * 12)
					rand_xp = round(statbase * 2.5)
					fighter_component = Fighter(hp=rand_hp, defense=rand_def, power=rand_power, xp=rand_xp)
					ai_component = BasicMonster()
					monster = Entity(x, y, 201, libtcod.yellow, 'Killer Bee', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
				else:
					statbase = randint(9, 20) + self.dungeon_level
					rand_hp = statbase * 15
					rand_def = statbase
					rand_power = round(statbase * 2.5)
					rand_xp = statbase * 3
					fighter_component = Fighter(hp=rand_hp, defense=rand_def, power=rand_power, xp=rand_xp)
					ai_component = BasicMonster()
					monster = Entity(x, y, 179, libtcod.Color(218, 42, 32), 'Joey', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
					
				entities.append(monster)
		for i in range(number_of_items):
			x = randint(room.x1 + 1, room.x2 - 1)
			y = randint(room.y1 + 1, room.y2 - 1)
			
			if not any([entity for entity in entities if entity.x == x and entity.y == y]):
				item_choice = random_choice_from_dict(item_chances)
				
				if item_choice == 'lesser_med_kit':
					item_component = Item(use_function=heal, amount=200)
					item = Entity(x, y, 195, libtcod.violet, 'Lesser Med Kit', render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'morphine_pack':
					item_component = Item(use_function=morphine_pack, amount=350)
					item = Entity(x, y, 195, libtcod.Color(40, 30, 0), 'Morphine Pack', render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'med_kit':
					item_component = Item(use_function=morphine_pack, amount=500)
					item = Entity(x, y, 195, libtcod.Color(255, 30, 0), 'Med Kit', render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'tentacruels':
					equippable_component = Equippable(EquipmentSlots.TENTACLE, power_bonus=40)
					item = Entity(x, y, 218, libtcod.purple, 'Tentacruel', equippable=equippable_component)
				elif item_choice == 'energy_shield':
					equippable_component = Equippable(EquipmentSlots.TENTACLE, defense_bonus=50, max_hp_bonus=250)
					item = Entity(x, y, 217, libtcod.cyan, 'Energy Shield', equippable=equippable_component)
				elif item_choice == 'whippy_willow_twig':
					equippable_component = Equippable(EquipmentSlots.TENTACLE, power_bonus=15)
					item = Entity(x, y, 188, libtcod.Color(53, 38, 0), 'Whippy Willow Twig', equippable=equippable_component)
				elif item_choice == 'goanna_skin_hat':
					equippable_component = Equippable(EquipmentSlots.HELMET, power_bonus=5, defense_bonus=10)
					item = Entity(x, y, 200, libtcod.Color(20, 38, 0), 'Goanna Skin Hat', equippable=equippable_component)
				elif item_choice == 'aluminite_neck_brace':
					equippable_component = Equippable(EquipmentSlots.NECK, defense_bonus=5)
					item = Entity(x, y, 204, libtcod.silver, 'Aluminite Neck Brace', equippable=equippable_component)
				elif item_choice == 'dropbear_fur_vest':
					equippable_component = Equippable(EquipmentSlots.CHEST_PLATE, max_hp_bonus=100, defense_bonus=25)
					item = Entity(x, y, 185, libtcod.Color(30, 30, 30), 'Dropbear Fur Vest', equippable=equippable_component)
				elif item_choice == 'plasma_grenade':
					item_component = Item(use_function=use_plasma_grenade, targeting=True, targeting_message=Message('Left-click an enemy to lob the Plasma Grenade at it, or right-click to cancel.', libtcod.light_cyan), damage=250, radius=3)
					item = Entity(x, y, 193, libtcod.cyan, 'Plasma Grenade', render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'ray_gun':
					item_component = Item(use_function=use_ray_gun, damage=80, maximum_range=11)
					item = Entity(x, y, 187, libtcod.Color(180, 180, 180), 'Ray Gun', render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'stun_grenade':
					item_component = Item(use_function=use_stun_grenade, targeting=True, targeting_message=Message('Left-click an enemy to lob the Stun Grenade at it, or right-click to cancel.', libtcod.light_cyan))
					item = Entity(x, y, 193, libtcod.Color(0, 40, 0), 'Stun Grenade', render_order=RenderOrder.ITEM, item=item_component)
				else:
					item_component = Item(use_function=use_shock_charge, damage=350, maximum_range=5)
					item = Entity(x, y, 194, libtcod.yellow, 'Shock Charge', render_order=RenderOrder.ITEM, item=item_component)
					
				entities.append(item)
				
	def is_blocked(self, x, y):
		if self.tiles[x][y].blocked:
			return True
			
		return False
	
	def next_floor(self, player, message_log, constants):
		self.dungeon_level += 1
		entities = [player]
		
		self.tiles = self.initialize_tiles()
		self.make_map(constants['max_rooms'], constants['room_min_size'], constants['room_max_size'], constants['map_width'], constants['map_height'], player, entities)
		
		player.fighter.heal(player.fighter.max_hp // 2)
		
		message_log.add_message(Message('You take a moment to rest, and recover your strenth.', libtcod.light_violet))
		
		return entities
