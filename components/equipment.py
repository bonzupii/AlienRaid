# -*- coding: utf-8 -*-
#
#  equipment.py
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
from components.equipment_slots import EquipmentSlots


class Equipment:
	def __init__(self, top_right_tentacle=None, top_left_tentacle=None, bottom_right_tentacle=None, bottom_left_tentacle=None, chest_plate=None, helmet=None, neck=None):
		self.top_right_tentacle = top_right_tentacle
		self.top_left_tentacle = top_left_tentacle
		self.bottom_right_tentacle = bottom_right_tentacle
		self.bottom_left_tentacle = bottom_left_tentacle
		self.chest_plate = chest_plate
		self.helmet = helmet
		self.neck = neck

	@property
	def max_hp_bonus(self):
		bonus = 0

		if self.top_right_tentacle and self.top_right_tentacle.equippable:
			bonus += self.top_right_tentacle.equippable.max_hp_bonus

		if self.top_left_tentacle and self.top_left_tentacle.equippable:
			bonus += self.top_left_tentacle.equippable.max_hp_bonus
			
		if self.bottom_right_tentacle and self.bottom_right_tentacle.equippable:
			bonus += self.bottom_right_tentacle.equippable.max_hp_bonus
			
		if self.bottom_left_tentacle and self.bottom_left_tentacle.equippable:
			bonus += self.bottom_left_tentacle.equippable.max_hp_bonus

		if self.chest_plate and self.chest_plate.equippable:
			bonus += self.chest_plate.equippable.max_hp_bonus
			
		if self.helmet and self.helmet.equippable:
			bonus += self.helmet.equippable.max_hp_bonus
			
		if self.neck and self.neck.equippable:
			bonus += self.neck.equippable.max_hp_bonus
			
		return bonus

	@property
	def power_bonus(self):
		bonus = 0

		if self.top_right_tentacle and self.top_right_tentacle.equippable:
			bonus += self.top_right_tentacle.equippable.power_bonus

		if self.top_left_tentacle and self.top_left_tentacle.equippable:
			bonus += self.top_left_tentacle.equippable.power_bonus
			
		if self.bottom_right_tentacle and self.bottom_right_tentacle.equippable:
			bonus += self.bottom_right_tentacle.equippable.power_bonus
			
		if self.bottom_left_tentacle and self.bottom_left_tentacle.equippable:
			bonus += self.bottom_left_tentacle.equippable.power_bonus
			
		if self.chest_plate and self.chest_plate.equippable:
			bonus += self.chest_plate.equippable.power_bonus
			
		if self.helmet and self.helmet.equippable:
			bonus += self.helmet.equippable.power_bonus
			
		if self.neck and self.neck.equippable:
			bonus += self.neck.equippable.power_bonus

		return bonus

	@property
	def defense_bonus(self):
		bonus = 0

		if self.top_right_tentacle and self.top_right_tentacle.equippable:
			bonus += self.top_right_tentacle.equippable.defense_bonus

		if self.top_left_tentacle and self.top_left_tentacle.equippable:
			bonus += self.top_left_tentacle.equippable.defense_bonus
			
		if self.bottom_right_tentacle and self.bottom_right_tentacle.equippable:
			bonus += self.bottom_right_tentacle.equippable.defense_bonus

			
		if self.bottom_left_tentacle and self.bottom_left_tentacle.equippable:
			bonus += self.bottom_left_tentacle.equippable.defense_bonus
			
		if self.chest_plate and self.chest_plate.equippable:
			bonus += self.chest_plate.equippable.defense_bonus
			
		if self.helmet and self.helmet.equippable:
			bonus += self.helmet.equippable.defense_bonus
			
		if self.neck and self.neck.equippable:
			bonus += self.neck.equippable.defense_bonus

		return bonus

	def toggle_equip(self, equippable_entity):
		results = []

		slot = equippable_entity.equippable.slot

		if slot == EquipmentSlots.CHEST_PLATE:
			if self.chest_plate == equippable_entity:
				self.chest_plate = None
				results.append({'dequipped': equippable_entity})
			else:
				if self.chest_plate:
					results.append({'dequipped': self.chest_plate})

				self.chest_plate = equippable_entity
				results.append({'equipped': equippable_entity})
				
		elif slot == EquipmentSlots.HELMET:
			if self.helmet == equippable_entity:
				self.helmet = None
				results.append({'dequipped': equippable_entity})
			else:
				if self.helmet:
					results.append({'dequipped': self.bottom_left_tentacle})

				self.helmet = equippable_entity
				results.append({'equipped': equippable_entity})
				
		elif slot == EquipmentSlots.NECK:
			if self.neck == equippable_entity:
				self.neck = None
				results.append({'dequipped': equippable_entity})
			else:
				if self.neck:
					results.append({'dequipped': self.bottom_left_tentacle})

				self.neck = equippable_entity
				results.append({'equipped': equippable_entity})

		elif slot == EquipmentSlots.TENTACLE:
			if self.top_right_tentacle == equippable_entity:
				self.top_right_tentacle = None
				results.append({'dequipped': equippable_entity})
			elif self.top_left_tentacle == equippable_entity:
				self.top_left_tentacle = None
				results.append({'dequipped': equippable_entity})
			elif self.bottom_right_tentacle == equippable_entity:
				self.bottom_right_tentacle = None
				results.append({'dequipped': equippable_entity})
			elif self.bottom_left_tentacle == equippable_entity:
				self.bottom_left_tentacle = None
				results.append({'dequipped': equippable_entity})
			else:
				if self.top_right_tentacle == None:
					self.top_right_tentacle = equippable_entity
					results.append({'equipped': equippable_entity})
				elif self.top_left_tentacle == None:
					self.top_left_tentacle= equippable_entity
					results.append({'equipped': equippable_entity})
				elif self.bottom_right_tentacle == None:
					self.bottom_right_tentacle= equippable_entity
					results.append({'equipped': equippable_entity})
				elif self.bottom_left_tentacle == None:
					self.bottom_left_tentacle= equippable_entity
					results.append({'equipped': equippable_entity})
				else:
					results.append({'dequipped': self.top_right_tentacle})
					self.top_right_tentacle = equippable_entity
					results.append({'equipped': self.top_right_tentacle})

		return results
