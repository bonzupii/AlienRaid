#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pygame menus (no libtcod). All drawing is via the FontRenderer."""

import textwrap

import pygame

from renderer import palette as C

TILE = 12


def _draw_box(surface, x, y, width_tiles, height_tiles):
    overlay = pygame.Surface((width_tiles * TILE, height_tiles * TILE), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 195))
    pygame.draw.rect(overlay, (110, 110, 110), overlay.get_rect(), 1)
    pygame.draw.rect(overlay, (40, 40, 40), overlay.get_rect().inflate(-2, -2), 1)
    surface.blit(overlay, (x * TILE, y * TILE))


def _wrap(header, width_tiles):
    lines = []
    if not header:
        return lines
    for line in header.split('\n'):
        if line:
            lines.extend(textwrap.wrap(line, max(4, width_tiles - 2)))
        else:
            lines.append('')
    return lines


def menu(surface, font, header, options, width, screen_width, screen_height):
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')

    wrapped = _wrap(header, width)
    height = len(wrapped) + len(options) + 2

    x = int(screen_width / 2 - width / 2)
    y = int(screen_height / 2 - height / 2)
    _draw_box(surface, x, y, width, height)

    ty = y + 1
    for line in wrapped:
        font.draw_text(surface, line, x + 1, ty, C.WHITE)
        ty += 1

    letter_index = ord('a')
    for option_text in options:
        font.draw_text(surface, '({0}) {1}'.format(chr(letter_index), option_text),
                       x + 1, ty, C.LIGHT_GRAY)
        ty += 1
        letter_index += 1


def inventory_menu(surface, font, header, player, inventory_width, screen_width, screen_height):
    if len(player.inventory.items) == 0:
        options = ['Inventory is empty.']
    else:
        options = []
        equipment = player.equipment
        for item in player.inventory.items:
            if equipment.top_right_tentacle == item:
                options.append('{0} (on top right tentacle)'.format(item.name))
            elif equipment.top_left_tentacle == item:
                options.append('{0} (on top left tentacle)'.format(item.name))
            elif equipment.bottom_right_tentacle == item:
                options.append('{0} (on bottom right tentacle)'.format(item.name))
            elif equipment.bottom_left_tentacle == item:
                options.append('{0} (on bottom left tentacle)'.format(item.name))
            elif equipment.chest_plate == item:
                options.append('{0} (on chest)'.format(item.name))
            elif equipment.helmet == item:
                options.append('{0} (on head)'.format(item.name))
            elif equipment.neck == item:
                options.append('{0} (on neck)'.format(item.name))
            else:
                options.append(item.name)

    menu(surface, font, header, options, inventory_width, screen_width, screen_height)


def main_menu(surface, font, background_image, screen_width, screen_height):
    if background_image is not None:
        scaled = pygame.transform.smoothscale(background_image,
                                              (screen_width * TILE, screen_height * TILE))
        surface.blit(scaled, (0, 0))
    else:
        surface.fill((10, 10, 10))

    font.draw_text(surface, 'ALIEN RAID',
                   int(screen_width / 2 - 5), int(screen_height / 2 - 6), C.LIGHT_GREEN)
    font.draw_text(surface, '(C) 2019-2026 By Bonzupii <bonzupii@protonmail.com>',
                   int(screen_width / 2 - 36), screen_height - 2, C.LIGHT_GRAY)
    font.draw_text(surface, 'Please see the README.md file to learn about game controls.',
                   int(screen_width / 2 - 30), screen_height - 4, C.LIGHT_GRAY)
    menu(surface, font, '', ['Play a new game', 'Continue last game', 'Quit'],
         24, screen_width, screen_height)


def level_up_menu(surface, font, header, player, menu_width, screen_width, screen_height):
    options = [
        'Constitution (+250 HP, from {0})'.format(player.fighter.max_hp),
        'Strength (+12 attack, from {0})'.format(player.fighter.power),
        'Tough Skin (+12 defense, from {0})'.format(player.fighter.defense),
    ]
    menu(surface, font, header, options, menu_width, screen_width, screen_height)


def character_screen(surface, font, player, width, height, screen_width, screen_height):
    x = screen_width // 2 - width // 2
    y = screen_height // 2 - height // 2
    _draw_box(surface, x, y, width, height)

    lines = [
        'Character Information',
        'Level: {0}'.format(player.level.current_level),
        'Experience: {0}'.format(player.level.current_xp),
        'Experience to level-up: {0}'.format(player.level.experience_to_next_level),
        '--------',
        'Maximum HP: {0}'.format(player.fighter.max_hp),
        'Current HP: {0}'.format(player.fighter.hp),
        'Attack power: {0}'.format(player.fighter.power),
        'Defense: {0}'.format(player.fighter.defense),
    ]
    ty = y + 1
    for line in lines:
        font.draw_text(surface, line, x + 1, ty, C.WHITE)
        ty += 1


def message_box(surface, font, header, width, screen_width, screen_height):
    menu(surface, font, header, [], width, screen_width, screen_height)


def victory_screen(surface, font, player, game_map, screen_width, screen_height):
    width, height = 56, 10
    x = screen_width // 2 - width // 2
    y = screen_height // 2 - height // 2
    _draw_box(surface, x, y, width, height)
    font.draw_text(surface, 'YOU ESCAPED!', x + 2, y + 1, C.LIGHT_GREEN)
    font.draw_text(surface, 'The ship hums back to life and lifts off', x + 2, y + 3, C.WHITE)
    font.draw_text(surface, 'from the Outback, trailing red dust.', x + 2, y + 4, C.WHITE)
    font.draw_text(surface, 'Depth reached: {0}   Parts salvaged: {1}/{2}'.format(
        game_map.dungeon_level, player.quest.found_count, player.quest.parts_total),
        x + 2, y + 6, C.LIGHT_GRAY)
    font.draw_text(surface, 'Final level: {0}'.format(player.level.current_level),
                   x + 2, y + 7, C.LIGHT_GRAY)
    font.draw_text(surface, 'Press Esc to return to the main menu.', x + 2, y + 8, C.LIGHT_VIOLET)


def death_overlay(surface, font, screen_width, screen_height):
    width, height = 48, 8
    x = screen_width // 2 - width // 2
    y = screen_height // 2 - height // 2
    _draw_box(surface, x, y, width, height)
    font.draw_text(surface, 'YOU HAVE DIED', x + 2, y + 1, C.LIGHT_RED)
    font.draw_text(surface, 'The Outback has claimed you.', x + 2, y + 3, C.WHITE)
    font.draw_text(surface, 'Press Esc to return to the main menu.', x + 2, y + 5, C.LIGHT_VIOLET)
