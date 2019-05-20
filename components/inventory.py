# -*- coding: utf-8 -*-
#
#  inventory.py
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

from components.game_messages import Message

class Inventory:
	def __init__(self, capacity):
		self.capacity = capacity
		self.items = []

	def add_item(self, item):
		results = []

		if len(self.items) >= self.capacity:
			results.append({
				'item_added': None,
				'message': Message('You cannot carry any more, your inventory is full', libtcod.yellow)
			})
		else:
			results.append({
				'item_added': item,
				'message': Message('You pick up the {0}!'.format(item.name), libtcod.blue)
			})

			self.items.append(item)

		return results

	def use(self, item_entity, **kwargs):
		results = []

		item_component = item_entity.item

		if item_component.use_function is None:
			equippable_component = item_entity.equippable

			if equippable_component:
				results.append({'equip': item_entity})
			else:
				results.append({'message': Message('The {0} cannot be used'.format(item_entity.name), libtcod.yellow)})
		else:
			if item_component.targeting and not (kwargs.get('target_x') or kwargs.get('target_y')):
				results.append({'targeting': item_entity})
			else:
				kwargs = {**item_component.function_kwargs, **kwargs}
				item_use_results = item_component.use_function(self.owner, **kwargs)

				for item_use_result in item_use_results:
					if item_use_result.get('consumed'):
						self.remove_item(item_entity)

				results.extend(item_use_results)

		return results

	def remove_item(self, item):
		self.items.remove(item)

	def drop_item(self, item):
		results = []

		if self.owner.equipment.top_right_tentacle == item or self.owner.equipment.top_left_tentacle == item or self.owner.equipment.bottom_right_tentacle == item or self.owner.equipment.bottom_left_tentacle == item or self.owner.equipment.chest_plate == item or self.owner.equipment.helmet == item or self.owner.equipment.neck == item:
			self.owner.equipment.toggle_equip(item)

		item.x = self.owner.x
		item.y = self.owner.y

		self.remove_item(item)
		results.append({'item_dropped': item, 'message': Message('You dropped the {0}'.format(item.name),
																 libtcod.yellow)})

		return results
