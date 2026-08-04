#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pygame menus (no libtcod). All drawing is via the FontRenderer (procedural
Font16) on the 16px UI grid (TILE = 16).

Every drawn menu registers per-option hit-rects (frame pixel coordinates)
plus the action dict each option fires, so a MOUSEBUTTONDOWN is equivalent
to the letter keys. Hover highlight via MOUSEMOTION (the launcher feeds the
cursor position in frame px via set_mouse()).

Tall menus (the examine popup) are SCROLLABLE: a ``scroll`` row offset plus
a ``max_height`` viewport, with up/down indicators drawn while content is
clipped. The launcher feeds wheel/arrow scroll offsets; the box itself is
always clamped fully inside the frame.
"""
import textwrap

import pygame

from components.fighter import HUNGER_MAX, HUNGER_LABELS, hunger_tier
from renderer import palette as C
from components import crafting

TILE = 16

# ---------------------------------------------------------------------------
# Global click/hover registry (frame-px coordinates)
# ---------------------------------------------------------------------------
_ACTIVE = {'rects': [], 'actions': []}
_MOUSE = None


def set_mouse(pos):
    global _MOUSE
    _MOUSE = pos


def get_mouse():
    return _MOUSE


def _register(rects, actions):
    _ACTIVE['rects'] = rects
    _ACTIVE['actions'] = actions


def clear_actions():
    """Drop every clickable rect. Called at the top of each frame render;
    the menu states re-register their own rects when they draw, so a menu
    shown on an earlier frame can never swallow a click during play."""
    _register([], [])


def action_at(pos):
    """The action dict of the option whose hit-rect contains ``pos``."""
    if not pos:
        return None
    for rect, act in zip(_ACTIVE['rects'], _ACTIVE['actions']):
        if rect.collidepoint(pos):
            return act
    return None


def hover_index():
    if not _MOUSE:
        return -1
    for i, rect in enumerate(_ACTIVE['rects']):
        if rect.collidepoint(_MOUSE):
            return i
    return -1


def _center(surface):
    return surface.get_width() // TILE, surface.get_height() // TILE


def _centered_x(surface, text):
    """Left tile column that horizontally centres ``text`` on the frame."""
    sw, _sh = _center(surface)
    return max(1, int(sw / 2 - len(str(text)) / 2))


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
    # width_tiles - 4: the text starts at x + 3 inside the box, so a wrapped
    # line of width_tiles - 4 chars ends one column inside the right edge.
    for line in header.split('\n'):
        if line:
            lines.extend(textwrap.wrap(line, max(4, width_tiles - 4)))
        else:
            lines.append('')
    return lines


def inventory_groups(items):
    """Group stacked inventory items by display name, preserving raw-list
    order: [(name, rep_index, count)]. The menu letters AND the keyboard
    hotkeys both index THIS list, so a stack of three med kits is ONE
    hotkey and the letter always resolves to the top item of that stack."""
    groups = []
    for idx, item in enumerate(items):
        for g in groups:
            if g[0] == item.name:
                g[2] += 1
                break
        else:
            groups.append([item.name, idx, 1])
    return groups


def inventory_item_at(player, letter_index):
    """Map a menu letter/hotkey (0-based GROUP position) to the top item of
    that stack in the raw inventory list; None when out of range. This is
    what keeps the lettered hotkeys aligned with the displayed menu even
    when stacks collapse the list."""
    groups = inventory_groups(player.inventory.items)
    if 0 <= letter_index < len(groups):
        return player.inventory.items[groups[letter_index][1]]
    return None


class Menu:
    """A drawable, clickable menu. Options may be strings or
    (text, color) tuples. ``actions`` parallels the options.

    With ``max_height`` the menu becomes a scrollable viewport: ``scroll``
    rows are skipped off the top, up/down indicators are drawn while
    content is clipped, and click-rects stay aligned to the visible window.
    """

    def __init__(self, header, options, width, actions=None, option_colors=None):
        self.header = header
        self.options = options
        self.width = width
        self.actions = actions or [None] * len(options)
        self.option_colors = option_colors or [C.LIGHT_GRAY] * len(options)
        self.rects = []

    def draw(self, surface, font, hover=-1, x=None, y=None,
             scroll=0, max_height=None):
        sw, sh = _center(surface)
        frame_w = max(8, sw - 4)      # widest the box can be on this frame
        # Header prose wraps cleanly at word boundaries. Menu OPTIONS are
        # NEVER wrapped and NEVER elided: the box sizes itself to its
        # longest line, so every entry is always shown in full.
        wrapped = _wrap(self.header, frame_w)
        option_lines = []
        letter_index = ord('a')
        for option in self.options:
            option_lines.append('({0}) {1}'.format(chr(letter_index), option))
            letter_index += 1
        longest = 4
        for line in wrapped:
            longest = max(longest, len(line))
        for line in option_lines:
            longest = max(longest, len(line))
        # Box width = longest line + 3-tile text inset + 1-tile margin.
        # Clamped only so the box itself always fits on the frame; lines
        # are drawn verbatim either way -- never truncated, never broken.
        width = max(self.width, min(longest + 4, frame_w))
        shown = option_lines

        content_rows = len(wrapped) + len(shown)
        total = content_rows + 2  # +2 box padding rows
        height = total
        if max_height is not None:
            height = max(3, min(total, max_height))
        if x is None:
            x = int(sw / 2 - width / 2)
        if y is None:
            y = int(sh / 2 - height / 2)
        # Clamp the box fully inside the frame so menus can never be pushed
        # off-screen or overlap the frame edge.
        x = max(1, min(x, max(1, sw - width - 1)))
        y = max(1, min(y, max(1, sh - height - 1)))
        _draw_box(surface, x, y, width, height)

        viewport = height - 2                       # content rows visible
        max_scroll = max(0, content_rows - viewport)
        scroll = max(0, min(scroll, max_scroll))

        # Flat content row list: (kind, opt_index, text, color).
        rows = []
        for line in wrapped:
            rows.append((0, None, line, C.WHITE))
        for i, line in enumerate(shown):
            color = self.option_colors[i] if i < len(self.option_colors) else C.LIGHT_GRAY
            rows.append((1, i, line, color))

        if scroll > 0:
            font.draw_text(surface, '▲', x + 1, y + 1, C.YELLOW)
        if scroll + viewport < content_rows:
            font.draw_text(surface, '▼', x + 1, y + height - 2, C.YELLOW)

        self.rects = []
        for row_idx, (kind, opt_idx, text, color) in enumerate(rows):
            if row_idx < scroll or row_idx >= scroll + viewport:
                continue
            ty = y + 1 + (row_idx - scroll)
            if kind == 0:
                font.draw_text(surface, text, x + 1, ty, color)
            else:
                if opt_idx == hover:
                    font.draw_text(surface, '>', x + 1, ty, C.YELLOW)
                line_color = C.WHITE if opt_idx == hover else color
                font.draw_text(surface, text, x + 3, ty, line_color)
                self.rects.append(pygame.Rect(
                    (x + 1) * TILE, ty * TILE,
                    (width - 2) * TILE, TILE))
        _register(self.rects, self.actions)
        self.width = width
        return (x, y, width, height)


def menu(surface, font, header, options, width, screen_width, screen_height,
         actions=None, option_colors=None):
    m = Menu(header, options, width, actions=actions, option_colors=option_colors)
    m.draw(surface, font, hover=hover_index())
    return m


def _equip_label(equipment, item):
    if equipment.top_right_tentacle == item:
        return ' (on top right tentacle)'
    if equipment.top_left_tentacle == item:
        return ' (on top left tentacle)'
    if equipment.bottom_right_tentacle == item:
        return ' (on bottom right tentacle)'
    if equipment.bottom_left_tentacle == item:
        return ' (on bottom left tentacle)'
    if equipment.chest_plate == item:
        return ' (on chest)'
    if equipment.helmet == item:
        return ' (on head)'
    if equipment.neck == item:
        return ' (on neck)'
    return ''


def inventory_menu(surface, font, header, player, inventory_width,
                   screen_width, screen_height, drop=False):
    # One lettered hotkey per STACK (not per raw item): the menu letters
    # and the keyboard hotkeys both index the group list, and the hotkey
    # resolves to the top item of its stack (inventory_item_at). This keeps
    # the letters aligned with what the menu displays.
    groups = inventory_groups(player.inventory.items)
    equipment = player.equipment
    options = []
    actions = []
    for i, (name, rep, count) in enumerate(groups):
        label = name
        if count > 1:
            label += ' x{0}'.format(count)
        label += _equip_label(equipment, player.inventory.items[rep])
        options.append(label)
        actions.append({'inventory_index': i})  # letter/group position
    if not options:
        options = ['Inventory is empty.']
        actions = [None]

    m = Menu(header, options, inventory_width, actions=actions)
    x, y, w, h = m.draw(surface, font, hover=hover_index())
    if not drop:
        # footer: craft button (also clickable)
        fy = y + h
        font.draw_text(surface, '[F5] craft parts', x + 1, fy, C.GOLD)
        rect = pygame.Rect((x + 1) * TILE, fy * TILE, (w - 2) * TILE, TILE)
        _ACTIVE['rects'].append(rect)
        _ACTIVE['actions'].append({'crafting': True})


def context_menu(surface, font, item, screen_width, screen_height):
    if item is None:
        return
    header = item.name
    options = ['use', 'equip', 'drop']
    actions = [{'context_use': True}, {'context_equip': True}, {'context_drop': True}]
    Menu(header, options, 30, actions=actions).draw(surface, font, hover=hover_index())


def crafting_menu(surface, font, player, screen_width, screen_height):
    options = []
    colors = []
    actions = []
    craftable = crafting.craftable(player)
    for i, rid in enumerate(crafting.RECIPES):
        name = crafting.result_name(rid)
        if craftable[rid]:
            options.append('Craft ' + name)
            colors.append(C.LIGHT_GREEN)
        else:
            options.append(name + ' (needs: ' + crafting.needs_text(rid, player) + ')')
            colors.append(C.DARK_GRAY)
        actions.append({'craft_index': i})
    Menu('Crafting. Press the key next to a recipe, or Esc to close.',
         options, 60, actions=actions, option_colors=colors).draw(
        surface, font, hover=hover_index())


def dialogue_menu(surface, font, header, options, screen_width, screen_height):
    actions = [{'dialogue_choice': i} for i in range(len(options))]
    Menu(header, options, 62, actions=actions).draw(surface, font, hover=hover_index())


def popup_box(surface, font, text, screen_width, screen_height, scroll=0):
    m = Menu(text, ['close'], 50, actions=[{'exit': True}])
    m.draw(surface, font, hover=hover_index(), scroll=scroll,
           max_height=screen_height - 8)


def main_menu(surface, font, background_image, screen_width, screen_height,
              remember_line=None, konami_footer=None):
    if background_image is not None:
        scaled = pygame.transform.smoothscale(background_image,
                                              (surface.get_width(), surface.get_height()))
        surface.blit(scaled, (0, 0))
    else:
        surface.fill((10, 10, 10))
    sw, sh = _center(surface)
    font.draw_text(surface, 'ALIEN RAID',
                   int(sw / 2 - 5), int(sh / 2 - 8), C.LIGHT_GREEN)
    copyright_line = '(C) 2019-2026 By Bonzupii <bonzupii@protonmail.com>'
    help_line = 'Please see the README.md file to learn about game controls.'
    font.draw_text(surface, copyright_line, _centered_x(surface, copyright_line),
                   sh - 2, C.LIGHT_GRAY)
    font.draw_text(surface, help_line, _centered_x(surface, help_line),
                   sh - 4, C.LIGHT_GRAY)
    if remember_line:
        font.draw_text(surface, remember_line, _centered_x(surface, remember_line),
                       sh - 7, C.LIGHT_RED)
    if konami_footer:
        font.draw_text(surface, konami_footer, _centered_x(surface, konami_footer),
                       sh - 9, C.LIGHT_VIOLET)
    menu(surface, font, '', ['Play a new game', 'Continue last game', 'Quit'],
         24, screen_width, screen_height,
         actions=[{'new_game': True}, {'load_game': True}, {'exit': True}])


def level_up_menu(surface, font, header, player, menu_width, screen_width, screen_height):
    options = [
        'Constitution (+250 HP, from {0})'.format(player.fighter.max_hp),
        'Strength (+12 attack, from {0})'.format(player.fighter.power),
        'Tough Skin (+12 defense, from {0})'.format(player.fighter.defense),
    ]
    menu(surface, font, header, options, menu_width, screen_width, screen_height,
         actions=[{'level_up': 'hp'}, {'level_up': 'str'}, {'level_up': 'def'}])


def character_screen(surface, font, player, width, height, screen_width, screen_height):
    sw, sh = _center(surface)
    x = sw // 2 - width // 2
    y = sh // 2 - height // 2
    _draw_box(surface, x, y, width, height)
    eq = player.equipment
    lines = [
        'Character Information',
        'Level: {0}   XP: {1}/{2}'.format(
            player.level.current_level, player.level.current_xp,
            player.level.experience_to_next_level),
        'Maximum HP: {0}   Current HP: {1}'.format(player.fighter.max_hp, player.fighter.hp),
        'Attack power: {0}   Defense: {1}'.format(player.fighter.power, player.fighter.defense),
        'Hunger: {0}/{1} ({2})'.format(
            getattr(player.fighter, 'hunger', HUNGER_MAX), HUNGER_MAX,
            HUNGER_LABELS[hunger_tier(player.fighter)]),
        '--------',
    ]
    slots = [
        ('top right tentacle', eq.top_right_tentacle),
        ('top left tentacle', eq.top_left_tentacle),
        ('bottom right tentacle', eq.bottom_right_tentacle),
        ('bottom left tentacle', eq.bottom_left_tentacle),
        ('chest', eq.chest_plate),
        ('head', eq.helmet),
        ('neck', eq.neck),
    ]
    for slot_name, item in slots:
        if item and item.equippable:
            bon = item.equippable
            bits = []
            if bon.power_bonus:
                bits.append('+{0} pow'.format(bon.power_bonus))
            if bon.defense_bonus:
                bits.append('+{0} def'.format(bon.defense_bonus))
            if bon.max_hp_bonus:
                bits.append('+{0} hp'.format(bon.max_hp_bonus))
            lines.append('{0}: {1} ({2}) (equipped)'.format(
                slot_name, item.name, ' '.join(bits) or 'no bonus'))
        else:
            lines.append('{0}: -'.format(slot_name))
    if player.fighter.status:
        lines.append('status: ' + ', '.join(
            '{0} ({1})'.format(k, v) for k, v in sorted(player.fighter.status.items())))
    else:
        lines.append('status: none')
    ty = y + 1
    for line in lines[:height - 2]:
        font.draw_text(surface, line, x + 1, ty, C.WHITE)
        ty += 1
    rect = pygame.Rect((x + 1) * TILE, ty * TILE, (width - 2) * TILE, TILE)
    font.draw_text(surface, '(esc) close', x + 1, ty, C.LIGHT_VIOLET)
    _register([rect], [{'exit': True}])


def victory_screen(surface, font, player, game_map, screen_width, screen_height):
    width, height = 62, 16
    sw, sh = _center(surface)
    x = sw // 2 - width // 2
    y = sh // 2 - height // 2
    _draw_box(surface, x, y, width, height)
    font.draw_text(surface, 'YOU ESCAPED!', x + 2, y + 1, C.LIGHT_GREEN)
    font.draw_text(surface, 'The ship hums back to life and lifts off', x + 2, y + 3, C.WHITE)
    font.draw_text(surface, 'from the Outback, trailing red dust.', x + 2, y + 4, C.WHITE)
    font.draw_text(surface, 'Depth reached: {0}   Parts salvaged: {1}/{2}'.format(
        game_map.dungeon_level, player.quest.found_count, player.quest.parts_total),
        x + 2, y + 6, C.LIGHT_GRAY)
    font.draw_text(surface, 'Final level: {0}'.format(player.level.current_level),
                   x + 2, y + 7, C.LIGHT_GRAY)
    epilogue = 'solo'
    if player.reputation is not None:
        epilogue = player.reputation.epilogue()
    for i, line in enumerate(EPILOGUES[epilogue]):
        font.draw_text(surface, line, x + 2, y + 9 + i, C.LIGHT_VIOLET)
    if player.reputation is not None and getattr(player.reputation, 'adf', 0) <= -15:
        font.draw_text(surface, 'A file with your name lands on an ADF colonel\'s desk.',
                       x + 2, y + 9 + len(EPILOGUES[epilogue]), C.LIGHT_RED)
    rects = []
    actions = [{'new_game': True}, {'exit': True}]
    for i, label in enumerate(('(a) fly again', '(b) main menu')):
        font.draw_text(surface, label, x + 2 + i * 20, y + height - 2, C.LIGHT_GRAY)
        rects.append(pygame.Rect((x + 2 + i * 20) * TILE, (y + height - 2) * TILE,
                                 18 * TILE, TILE))
    _register(rects, actions)


EPILOGUES = {
    'mib': [
        'Agent J flashes the neuralyzer at the launch glare.',
        '"You never saw anything. Nice documentary, though."',
        'A sequel is already filed under X-442.',
    ],
    'aecd': [
        'AECD debrief transcript: subject cooperative.',
        'All sightings logged, stamped, and classified.',
        'Your camera tape is now evidence item 11-C.',
    ],
    'solo': [
        'No agencies. No witnesses. Just you, the stars,',
        'and a quiet lift-off over the red dust.',
    ],
    'betrayal': [
        'MIB and AECD arrest EACH OTHER over jurisdiction.',
        'You leave mid-argument. Nobody watches you go.',
    ],
}


def death_overlay(surface, font, screen_width, screen_height):
    width, height = 48, 11
    sw, sh = _center(surface)
    x = sw // 2 - width // 2
    y = sh // 2 - height // 2
    _draw_box(surface, x, y, width, height)
    font.draw_text(surface, 'YOU HAVE DIED', x + 2, y + 1, C.LIGHT_RED)
    font.draw_text(surface, 'The Outback has claimed you.', x + 2, y + 3, C.WHITE)
    rects = []
    actions = [{'new_game': True}, {'exit': True}]
    for i, label in enumerate(('(a) try again', '(b) main menu')):
        font.draw_text(surface, label, x + 2 + i * 18, y + 6, C.LIGHT_GRAY)
        rects.append(pygame.Rect((x + 2 + i * 18) * TILE, (y + 6) * TILE,
                                 16 * TILE, TILE))
    _register(rects, actions)
