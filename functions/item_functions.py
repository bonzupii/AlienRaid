#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  item_functions.py
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

from components.ai import StunnedMonster
from components.game_messages import Message
from components.game_states import GameStates
from random import randint

def heal(*args, **kwargs):
	entity = args[0]
	amount = kwargs.get('amount')
	
	results = []
	
	if entity.fighter.hp == entity.fighter.max_hp:
		results.append({'consumed': False, 'message': Message('You are already at full health', libtcod.yellow)})
	else:
		entity.fighter.heal(amount)
		results.append({'consumed': True, 'message': Message('Your wounds start to feel better!', libtcod.green)})
		
	return results
	
def morphine_pack(*args, **kwargs):
	entity = args[0]
	amount = kwargs.get('amount')
	
	results = []
	
	if entity.fighter.hp == entity.fighter.max_hp:
		results.append({'consumed': False, 'message': Message('You are already at full health', libtcod.yellow)})
	else:
		entity.fighter.heal(amount)
		results.append({'consumed': True, 'message': Message('Your wounds start to feel much better!', libtcod.green)})
		
	return results
	
def use_shock_charge(*args, **kwargs):
	caster = args[0]
	entities = kwargs.get('entities')
	fov_map = kwargs.get('fov_map')
	damage = kwargs.get('damage')
	maximum_range = kwargs.get('maximum_range')
	
	results = []
	
	target = None
	closest_distance = maximum_range + 1
	
	for entity in entities:
		if entity.fighter and entity != caster and libtcod.map_is_in_fov(fov_map, entity.x, entity.y):
			distance = caster.distance_to(entity)
			
			if distance < closest_distance:
				target = entity
				closest_distance = distance
				
	if target:
		results.append({'consumed': True, 'target': target, 'message': Message('A lightning bolt strikes the {0} with a loud thunder! It deals {1} damage.'.format(target.name, damage), libtcod.orange)})
		results.extend(target.fighter.take_damage(damage))
	else:
		results.append({'consumed': False, 'target': None, 'message': Message('No enemy is close enough to strike.', libtcod.red)})
		
	return results
	
def use_plasma_grenade(*args, **kwargs):
	entities = kwargs.get('entities')
	fov_map = kwargs.get('fov_map')
	damage = kwargs.get('damage')
	radius = kwargs.get('radius')
	target_x = kwargs.get('target_x')
	target_y = kwargs.get('target_y')
	
	results = []
	
	if not libtcod.map_is_in_fov(fov_map, target_x, target_y):
		results.append({'consumed': False, 'message': Message('You cannot target a tile outside of your field of view!', libtcod.yellow)})
		return results
		
	results.append({'consumed': True, 'message': Message('The plasma grenade explodes, burning everything within {0} tiles!'.format(radius), libtcod.orange)})
	
	for entity in entities:
		if entity.distance(target_x, target_y) <= radius and entity.fighter:
			results.append({'message': Message('The {0} gets burned for {1} hit points!'.format(entity.name, damage), libtcod.orange)})
			results.extend(entity.fighter.take_damage(damage))
			
	return results
	
def use_stun_grenade(*args, **kwargs):
	entities = kwargs.get('entities')
	fov_map = kwargs.get('fov_map')
	target_x = kwargs.get('target_x')
	target_y = kwargs.get('target_y')
	
	results = []
	
	if not libtcod.map_is_in_fov(fov_map, target_x, target_y):
		results.append({'consumed': False, 'message': Message('You cannot target a tile outside of your field of view!', libtcod.yellow)})
		return results
			
	for entity in entities:
		if entity.x == target_x and entity.y == target_y and entity.ai:
			stunned_ai = StunnedMonster(entity.ai, 10)
			
			stunned_ai.owner = entity
			entity.ai = stunned_ai
			
			results.append({'consumed': True, 'message': Message('The stun grenade explodes near the {0}! It reels and begins to stumble around as it tries to regain its bearings.'.format(entity.name), libtcod.light_green)})
			
			break
	else:
		results.append({'consumed': False, 'message': Message('There is no targetable enemy at that location!', libtcod.yellow)})
			
	return results

def use_ray_gun(*args, **kwargs):
	caster = args[0]
	entities = kwargs.get('entities')
	fov_map = kwargs.get('fov_map')
	damage = kwargs.get('damage')
	maximum_range = kwargs.get('maximum_range')

	results = []
	
	target = None
	closest_distance = maximum_range + 1
	
	for entity in entities:
		if entity.fighter and entity != caster and libtcod.map_is_in_fov(fov_map, entity.x, entity.y):
			distance = caster.distance_to(entity)
			
			if distance < closest_distance:
				target = entity
				closest_distance = distance
				
	if target:
		if randint(0, 100) >= 30:
			results.append({'consumed': False, 'target': target, 'message': Message('Pew! Pew! You hit the {0} with a searing ray blast! It takes {1} damage!'.format(target.name, damage), libtcod.orange)})
			results.extend(target.fighter.take_damage(damage))
		else:
			results.append({'consumed': False, 'target': target, 'message': Message('Pew! Pew! Pew! Pew! You miss the {0}!'.format(target.name), libtcod.dark_red)})
	else:
		results.append({'consumed': False, 'target': None, 'message': Message('No enemy is close enough to shoot.', libtcod.red)})
		
	return results
