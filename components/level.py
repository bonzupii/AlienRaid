# -*- coding: utf-8 -*-
#
#  level.py
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
class Level:
	def __init__(self, current_level=1, current_xp=0, level_up_base=300, level_up_factor=175):
		self.current_level = current_level
		self.current_xp = current_xp
		self.level_up_base = level_up_base
		self.level_up_factor = level_up_factor

	@property
	def experience_to_next_level(self):
		return self.level_up_base + self.current_level * self.level_up_factor

	def add_xp(self, xp):
		self.current_xp += xp

		if self.current_xp > self.experience_to_next_level:
			self.current_xp -= self.experience_to_next_level
			self.current_level += 1

			return True
		else:
			return False
