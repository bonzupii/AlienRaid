#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Game constants and new-game setup (no libtcod)."""

from components.equipment import Equipment
from components.equippable import Equippable
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from components.quest import Quest

from components.entity import Entity
from components.equipment_slots import EquipmentSlots
from components.game_messages import Message, MessageLog
from components.game_states import GameStates

from functions.render_order import RenderOrder

from map_objects.game_map import GameMap
from renderer import palette as C


def biome_for_level(level):
    """Color palette for the current biome band.

    1-5:   red-dirt scrub
    6-10:  creek country (billabongs)
    11-15: limestone caves
    16-20: the hollow (alien glow)
    """
    if level <= 5:
        return {
            'dark_wall': (100, 20, 10),
            'dark_ground': (170, 90, 10),
            'light_wall': (140, 60, 10),
            'light_ground': (210, 130, 50),
            'dark_brush': (130, 70, 15),
            'light_brush': (180, 110, 45),
        }
    elif level <= 10:
        return {
            'dark_wall': (80, 60, 40),
            'dark_ground': (140, 110, 70),
            'light_wall': (110, 90, 60),
            'light_ground': (180, 150, 100),
            'dark_brush': (100, 80, 50),
            'light_brush': (150, 120, 80),
        }
    elif level <= 15:
        return {
            'dark_wall': (90, 90, 90),
            'dark_ground': (60, 60, 60),
            'light_wall': (120, 120, 120),
            'light_ground': (90, 90, 90),
            'dark_brush': (70, 70, 70),
            'light_brush': (100, 100, 100),
        }
    else:
        return {
            'dark_wall': (60, 40, 80),
            'dark_ground': (40, 30, 60),
            'light_wall': (90, 70, 120),
            'light_ground': (70, 50, 100),
            'dark_brush': (50, 40, 70),
            'light_brush': (80, 60, 110),
        }


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

    fov_light_walls = True
    fov_radius = 12

    # Biome palette for the starting band (red dirt); deeper floors swap
    # palettes on transition (see GameMap.go_down / go_up).
    colors = biome_for_level(1)

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
        'fov_light_walls': fov_light_walls,
        'fov_radius': fov_radius,
        'colors': colors,
    }

    return constants


def get_game_variables(constants):
    fighter_component = Fighter(hp=1250, defense=10, power=40)
    inventory_component = Inventory(26)
    level_component = Level()
    equipment_component = Equipment()
    quest_component = Quest()

    player = Entity(0, 0, 'player', C.PLAYER_GREEN, 'Wrpgnyth', blocks=True,
                    render_order=RenderOrder.ACTOR, fighter=fighter_component,
                    inventory=inventory_component, level=level_component,
                    equipment=equipment_component, quest=quest_component)
    entities = [player]

    tentaclaws = Entity(0, 0, 'icon_tentacle', C.RED, 'Tentaclaws',
                        equippable=Equippable(EquipmentSlots.TENTACLE, power_bonus=20))
    player.inventory.add_item(tentaclaws)
    player.equipment.toggle_equip(tentaclaws)

    sleeve = Entity(0, 0, 'icon_tentacle', C.SILVER, 'Aluminite Tentasleeve',
                    equippable=Equippable(EquipmentSlots.TENTACLE,
                                          power_bonus=20, defense_bonus=20))
    player.inventory.add_item(sleeve)
    player.equipment.toggle_equip(sleeve)

    game_map = GameMap(constants['map_width'], constants['map_height'])
    game_map.make_map(constants['max_rooms'], constants['room_min_size'],
                      constants['room_max_size'], constants['map_width'],
                      constants['map_height'], player, entities)

    message_log = MessageLog(constants['message_x'], constants['message_width'],
                             constants['message_height'])
    message_log.add_message(Message(
        'You wake up in the wreckage of your ship. The Outback wants you dead. Salvage the missing parts and escape!',
        C.LIGHT_VIOLET))

    game_state = GameStates.PLAYERS_TURN

    return player, entities, game_map, message_log, game_state
