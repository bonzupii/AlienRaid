#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  launcher.py
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
import os

from functions.death_functions import kill_monster, kill_player
from components.entity import get_blocking_entities_at_location
from functions.fov_functions import initialize_fov, recompute_fov
from components.game_messages import Message
from components.game_states import GameStates
from components.input_handler import handle_keys, handle_mouse, handle_main_menu
from loader_functions.initialize_new_game import get_constants, get_game_variables
from loader_functions.data_loaders import load_game, save_game
from components.menus import main_menu, message_box
from functions.render_functions import clear_all, render_all
from random import randint

print("AlienRaid Copyright (C) 2019  Bonzu <bonzupii@protonmail.com>\nThis program comes with ABSOLUTELY NO WARRANTY.\nThis is free software, and you are welcome to redistribute it under\ncertain conditions.\nSee enclosed LICENSE.md for details.\n")

def play_game(player, entities, game_map, message_log, game_state, con, panel, constants):
	fov_recompute = True

	fov_map = initialize_fov(game_map)

	key = libtcod.Key()
	mouse = libtcod.Mouse()

	game_state = GameStates.PLAYERS_TURN
	previous_game_state = game_state

	targeting_item = None
	
	wait_timer = 0

	while not libtcod.console_is_window_closed():
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

		if fov_recompute:
			recompute_fov(fov_map, player.x, player.y, constants['fov_radius'], constants['fov_light_walls'], constants['fov_algorithm'])

		render_all(con, panel, entities, player, game_map, fov_map, fov_recompute, message_log, constants['screen_width'], constants['screen_height'], constants['bar_width'], constants['panel_height'], constants['panel_y'], mouse, constants['colors'], game_state)

		fov_recompute = False

		libtcod.console_flush()

		clear_all(con, entities)

		action = handle_keys(key, game_state)
		mouse_action = handle_mouse(mouse)

		move = action.get('move')
		wait = action.get('wait')
		pickup = action.get('pickup')
		show_inventory = action.get('show_inventory')
		drop_inventory = action.get('drop_inventory')
		inventory_index = action.get('inventory_index')
		take_trail = action.get('take_trail')
		level_up = action.get('level_up')
		show_character_screen = action.get('show_character_screen')
		checkpoint = action.get('checkpoint')
		exit = action.get('exit')
		fullscreen = action.get('fullscreen')

		left_click = mouse_action.get('left_click')
		right_click = mouse_action.get('right_click')

		player_turn_results = []
		
		if player.fighter.max_hp < player.fighter.hp:
			player.fighter.hp = player.fighter.max_hp

		if move and game_state == GameStates.PLAYERS_TURN:
			dx, dy = move
			destination_x = player.x + dx
			destination_y = player.y + dy
			
			if wait_timer > 0:
				if randint(0, 7) == 7:
					wait_timer = wait_timer - 5

			passive_regen = randint(0, 20)
			if passive_regen == 20 and player.fighter.hp < player.fighter.max_hp:
				if player.fighter.hp >= player.fighter.max_hp - round((player.fighter.max_hp / 150)):
					player.fighter.hp = player.fighter.max_hp
					message_log.add_message(Message('Your wounds are completely healed!', libtcod.green))
				else:
					player.fighter.hp = player.fighter.hp + round((player.fighter.max_hp / 150))
				
			if not game_map.is_blocked(destination_x, destination_y):
				target = get_blocking_entities_at_location(entities, destination_x, destination_y)

				if target:
					attack_results = player.fighter.attack(target)
					player_turn_results.extend(attack_results)
				else:
					player.move(dx, dy)

					fov_recompute = True

				game_state = GameStates.ENEMY_TURN
				
		elif wait:
			if wait_timer <= 55:
				wait_timer = wait_timer + 5
				if player.fighter.hp < player.fighter.max_hp:
					if player.fighter.hp >= player.fighter.max_hp - round((player.fighter.max_hp / 50)):
						player.fighter.hp = player.fighter.max_hp
						message_log.add_message(Message('You rest for a moment. Your wounds are completely healed!', libtcod.green))
						game_state = GameStates.ENEMY_TURN
					else:
						player.fighter.hp = player.fighter.hp + round((player.fighter.max_hp / 50))
						message_log.add_message(Message('You rest for a moment. Your wounds are beginning to feel slightly better.', libtcod.green))
						game_state = GameStates.ENEMY_TURN
				else:
					message_log.add_message(Message('You rest for a moment.', libtcod.yellow))
					game_state = GameStates.ENEMY_TURN
			elif wait_timer >= 56:
				if player.fighter.hp >= 501:
					player.fighter.hp = player.fighter.hp - 500
					message_log.add_message(Message('You begin to rest, but the Dropbear drops down on your back and begins feasting on your flesh!', libtcod.dark_red))
					game_state = GameStates.ENEMY_TURN
				elif player.fighter.hp <= 500:
					player.fighter.hp = player.fighter.hp - 500
					message_log.add_message(Message('You begin to rest, but the Dropbear drops down on your back and feasts on your flesh!', libtcod.dark_red))
					player.char = 180
					player.color = libtcod.dark_red
					if not os.path.isfile('savegame.dat'):
						pass
					else:
						os.remove('savegame.dat')
					message_log.add_message(Message('You died!', libtcod.red))
					game_state = GameStates.PLAYER_DEAD
					


		elif pickup and game_state == GameStates.PLAYERS_TURN:
			for entity in entities:
				if entity.item and entity.x == player.x and entity.y == player.y:
					pickup_results = player.inventory.add_item(entity)
					player_turn_results.extend(pickup_results)

					break
			else:
				message_log.add_message(Message('There is nothing here to pick up.', libtcod.yellow))

		if show_inventory:
			previous_game_state = game_state
			game_state = GameStates.SHOW_INVENTORY

		if drop_inventory:
			previous_game_state = game_state
			game_state = GameStates.DROP_INVENTORY

		if inventory_index is not None and previous_game_state != GameStates.PLAYER_DEAD and inventory_index < len(player.inventory.items):
			item = player.inventory.items[inventory_index]

			if game_state == GameStates.SHOW_INVENTORY:
				player_turn_results.extend(player.inventory.use(item, entities=entities, fov_map=fov_map))
				game_state = GameStates.ENEMY_TURN
			elif game_state == GameStates.DROP_INVENTORY:
				player_turn_results.extend(player.inventory.drop_item(item))
				
		if take_trail and game_state == GameStates.PLAYERS_TURN:
			for entity in entities:
				if entity.trail and entity.x == player.x and entity.y == player.y:
					entities = game_map.next_floor(player, message_log, constants)
					fov_map = initialize_fov(game_map)
					fov_recompute = True
					con.clear()
					
					break
					
			else:
				message_log.add_message(Message('There is no trail here.', libtcod.yellow))

		if level_up:
			if player.fighter.hp <= player.fighter.max_hp - round((player.fighter.max_hp / 7)):
				player.fighter.hp = player.fighter.hp + round((player.fighter.max_hp / 7))
			else:
				player.fighter.hp = player.fighter.max_hp
			if level_up == 'hp':
				player.fighter.base_max_hp += 250
				player.fighter.hp += 250
			elif level_up == 'str':
				player.fighter.base_power += 12
			elif level_up == 'def':
				player.fighter.base_defense += 12
				
			game_state = previous_game_state
			
		if show_character_screen:
			previous_game_state = game_state
			game_state = GameStates.CHARACTER_SCREEN
			
		if game_state == GameStates.TARGETING:
			if left_click:
				target_x, target_y = left_click

				item_use_results = player.inventory.use(targeting_item, entities=entities, fov_map=fov_map, target_x=target_x, target_y=target_y)
				player_turn_results.extend(item_use_results)
			elif right_click:
				player_turn_results.append({'targeting_cancelled': True})
				
		if checkpoint:
			save_game(player, entities, game_map, message_log, game_state)
			message_log.add_message(Message('Your game has been saved.', libtcod.green))

		if exit:
			if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY, GameStates.CHARACTER_SCREEN):
				game_state = previous_game_state
			elif game_state == GameStates.TARGETING:
				player_turn_results.append({'targeting_cancelled': True})
			else:
				save_game(player, entities, game_map, message_log, game_state)

				return True

		if fullscreen:
			libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

		for player_turn_result in player_turn_results:
			message = player_turn_result.get('message')
			dead_entity = player_turn_result.get('dead')
			item_added = player_turn_result.get('item_added')
			item_consumed = player_turn_result.get('consumed')
			item_dropped = player_turn_result.get('item_dropped')
			equip = player_turn_result.get('equip')
			targeting = player_turn_result.get('targeting')
			targeting_cancelled = player_turn_result.get('targeting_cancelled')
			xp = player_turn_result.get('xp')

			if message:
				message_log.add_message(message)

			if dead_entity:
				if dead_entity == player:
					message, gamestate = kill_player(dead_entity)
				else:
					message = kill_monster(dead_entity)

				message_log.add_message(message)

			if item_added:
				entities.remove(item_added)

				game_state = GameStates.ENEMY_TURN

			if item_consumed:
				game_state = GameStates.ENEMY_TURN
				
			if item_dropped:
				entities.append(item_dropped)
				
				game_state = GameStates.ENEMY_TURN
				
			if equip:
				equip_results = player.equipment.toggle_equip(equip)
				
				for equip_result in equip_results:
					equipped = equip_result.get('equipped')
					dequipped = equip_result.get('dequipped')
					
					if equipped:
						message_log.add_message(Message('You equipped the {0}'.format(equipped.name)))
						
					if dequipped:
						message_log.add_message(Message('You unequipped the {0}'.format(dequipped.name)))
						
				game_state = GameStates.ENEMY_TURN

			if targeting:
				previous_game_state = GameStates.PLAYERS_TURN
				game_state = GameStates.TARGETING
				
				targeting_item = targeting
				
				message_log.add_message(targeting_item.item.targeting_message)

			if targeting_cancelled:
				game_state = previous_game_state
				
				message_log.add_message(Message('Targeting cancelled.'))
				
			if xp:
				leveled_up = player.level.add_xp(xp)
				message_log.add_message(Message('You gain {0} experience points.'.format(xp)))
				
				if leveled_up:
					message_log.add_message(Message('Your battle skills grow stronger! Welcome to level {0}'.format(player.level.current_level) + '!', libtcod.yellow))
					previous_game_state = game_state
					game_state = GameStates.LEVEL_UP

		if game_state == GameStates.ENEMY_TURN:
			for entity in entities:
				if entity.ai:
					enemy_turn_results = entity.ai.take_turn(player, fov_map, game_map, entities)

					for enemy_turn_result in enemy_turn_results:
						message = enemy_turn_result.get('message')
						dead_entity = enemy_turn_result.get('dead')

						if message:
							message_log.add_message(message)

						if dead_entity:
							if dead_entity == player:
								message, game_state = kill_player(dead_entity)
							else:
								message = kill_monster(dead_entity)

							message_log.add_message(message)

							if game_state == GameStates.PLAYER_DEAD:
								break

					if game_state == GameStates.PLAYER_DEAD:
						break
			else:
				game_state = GameStates.PLAYERS_TURN


def main():
	constants = get_constants()
	
	libtcod.console_set_custom_font('alienraid12x12.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
	
	libtcod.console_init_root(constants['screen_width'], constants['screen_height'], constants['window_title'], False, libtcod.RENDERER_SDL2)
	
	con = libtcod.console.Console(constants['screen_width'], constants['screen_height'])
	panel = libtcod.console.Console(constants['screen_width'], constants['panel_height'])
	
	player = None
	entities = []
	game_map = None
	message_log = None
	game_state = None
	
	show_main_menu = True
	show_load_error_message = False
	
	main_menu_background_image = libtcod.image_load('menu_background.png')
	
	key = libtcod.Key()
	mouse = libtcod.Mouse()
	
	while not libtcod.console_is_window_closed():
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
		
		if show_main_menu:
			main_menu(con, main_menu_background_image, constants['screen_width'], constants['screen_height'])
			
			if show_load_error_message:
				message_box(con, 'No saved game to load', 50, constants['screen_width'], constants['screen_height'])

			libtcod.console_flush()
			
			action = handle_main_menu(key)
			
			new_game = action.get('new_game')
			load_saved_game = action.get('load_game')
			exit_game = action.get('exit')
			
			if show_load_error_message and (new_game or load_saved_game or exit_game):
				show_load_error_message = False
			elif new_game:
				player, entities, game_map, message_log, game_state = get_game_variables(constants)
				game_state = GameStates.PLAYERS_TURN

				show_main_menu = False
			elif load_saved_game:
				try:
					player, entities, game_map, message_log, game_state = load_game()
					show_main_menu = False
				except FileNotFoundError:
					show_load_error_message = True
			elif exit_game:
				break

		else:
			con.clear()
			play_game(player, entities, game_map, message_log, game_state, con, panel, constants)

			show_main_menu = True


if __name__ == '__main__':
	main()
