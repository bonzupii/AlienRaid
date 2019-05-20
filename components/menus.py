#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  menus.py
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


def menu(con, header, options, width, screen_width, screen_height):
	if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')
	
	# Calculate total height for the header (after auto-wrap) and one line per option
	header_height = libtcod.console_get_height_rect(con, 0, 0, width, screen_height, header)
	height = len(options) + header_height
	
	# Create an off-screen console that represents the menu's window
	window = libtcod.console_new(width, height)
	
	# Print the header, with auto-wrap
	libtcod.console_set_default_foreground(window, libtcod.white)
	libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)
	
	# Print all of the options
	y = header_height
	letter_index = ord('a')
	for option_text in options:
		text = '(' + chr(letter_index) + ') ' + option_text
		libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
		y += 1
		letter_index += 1
		
	# Blit the contents of "window" to the root console
	x = int(screen_width / 2 - width / 2)
	y = int(screen_height / 2 - height / 2)
	libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
	
def inventory_menu(con, header, player, inventory_width, screen_width, screen_height):
	# Show a menu with each item in the inventory 
	if len(player.inventory.items) == 0:
		options = ['Inventory is empty.']
	else:
		options = []
		
		for item in player.inventory.items:
			if player.equipment.top_right_tentacle == item:
				options.append('{0} (on top right tentacle)'.format(item.name))
			elif player.equipment.top_left_tentacle == item:
				options.append('{0} (on top left tentacle)'.format(item.name))
			elif player.equipment.bottom_right_tentacle == item:
				options.append('{0} (on bottom right tentacle)'.format(item.name))
			elif player.equipment.bottom_left_tentacle == item:
				options.append('{0} (on bottom left tentacle)'.format(item.name))
			elif player.equipment.chest_plate == item:
				options.append('{0} (on chest)'.format(item.name))
			elif player.equipment.helmet == item:
				options.append('{0} (on head)'.format(item.name))
			elif player.equipment.neck == item:
				options.append('{0} (on neck)'.format(item.name))
			else:
				options.append(item.name)
		
	menu(con, header, options, inventory_width, screen_width, screen_height)

def main_menu(con, background_image, screen_width, screen_height):
	libtcod.image_blit_2x(background_image, 0, 0, 0)
	
	libtcod.console_set_default_foreground(0, libtcod.light_green)
	libtcod.console_print_ex(0, int(screen_width / 2), int(screen_height / 2) - 4, libtcod.BKGND_NONE, libtcod.CENTER, 'ALIEN RAID')
	libtcod.console_print_ex(0, int(screen_width / 2), int(screen_height - 2), libtcod.BKGND_NONE, libtcod.CENTER, '(C) 2019 By Bonzu Pippinpaddlopsikopolis III <bonzupii@protonmail.com>')
	libtcod.console_print_ex(0, int(screen_width / 2), int(screen_height - 4), libtcod.BKGND_NONE, libtcod.CENTER, 'Please see the README.md file to learn about game controls.')
	menu(con, '', ['Play a new game', 'Continue last game', 'Quit'], 24,  screen_width, screen_height)
	
def level_up_menu(con, header, player, menu_width, screen_width, screen_height):
	options = ['Constitution (+250 HP, from {0}'.format(player.fighter.max_hp),
			   'Strength (+12 attack, from {0}'.format(player.fighter.power),
			   'Tough Skin (+12 defense, from {0}'.format(player.fighter.defense)]
			   
	menu(con, header, options, menu_width, screen_width, screen_height)
	
def character_screen(player, character_screen_width, character_screen_height, screen_width, screen_height):
	window = libtcod.console_new(character_screen_width, character_screen_height)
	
	libtcod.console_set_default_foreground(window, libtcod.white)
	
	libtcod.console_print_rect_ex(window, 0, 1, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, 'Character Information')
	libtcod.console_print_rect_ex(window, 0, 2, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, 'Level: {0}'.format(player.level.current_level))
	libtcod.console_print_rect_ex(window, 0, 3, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, 'Experience: {0}'.format(player.level.current_xp))
	libtcod.console_print_rect_ex(window, 0, 4, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, 'Experience to level-up: {0}'.format(player.level.experience_to_next_level))
	libtcod.console_print_rect_ex(window, 0, 5, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, '--------')
	libtcod.console_print_rect_ex(window, 0, 6, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, 'Maximum HP: {0}'.format(player.fighter.max_hp))
	libtcod.console_print_rect_ex(window, 0, 7, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, 'Current HP: {0}'.format(player.fighter.hp))
	libtcod.console_print_rect_ex(window, 0, 8, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, 'Attack power: {0}'.format(player.fighter.power))
	libtcod.console_print_rect_ex(window, 0, 9, character_screen_width, character_screen_height, libtcod.BKGND_NONE, libtcod.LEFT, 'Defense: {0}'.format(player.fighter.defense))
	x = screen_width // 2 - character_screen_width // 2
	y = screen_height // 2 - character_screen_height // 2
	libtcod.console_blit(window, 0, 0,  character_screen_width, character_screen_height, 0, x, y, 1.0, 0.7)
	
def message_box(con, header, width, screen_width, screen_height):
	menu(con, header, [], width, screen_width, screen_height)
