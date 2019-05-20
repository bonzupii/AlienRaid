#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  game_messages.py
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

import textwrap


class Message:
	def __init__(self, text, color=libtcod.white):
		self.text = text
		self.color = color
		
		
class MessageLog:
	def __init__(self, x, width, height):
		self.message = []
		self.x = x
		self.width = width
		self.height = height
		
	def add_message(self, message):
		# Split the message if necessary, among multiple lines
		new_message_lines = textwrap.wrap(message.text, self.width)
		
		for line in new_message_lines:
			# If the buffer is full, remove the first line to make room for the new one
			if len(self.message) == self.height:
				del self.message[0]
				
			# Add the new line as a Message object, with the text and the color
			self.message.append(Message(line, message.color))
