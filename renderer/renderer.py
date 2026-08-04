#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Renderer: the pygame drawing pipeline on ONE 16px grid.

* The MAP grid is 16px (MAP_TILE): terrain, entities, FOV overlay.
* The UI grid is ALSO 16px (UI_TILE): the procedural Font16 font, the
  bottom HUD panel and every menu.

Frame: frame_w = map_width * 16 (1600), frame_h = map_height * 16 +
panel_height * 16 (880). The HUD panel lives directly below the map; panel
row r is at y = map_height * 16 + r * 16.

* The static *explored* terrain is pre-rendered onto a cached surface once
  per map generation (keyed on ``GameMap.version``, so a regenerated floor
  at the same dungeon level -- e.g. returning from the floor-4.5 pocket --
  always rebuilds); each frame we blit that cache, then overlay only the
  FOV-lit tiles and the visible dynamic entities.
* The pocket floor (floor 4.5) renders every tile as the magenta unknown
  sprite, bypassing normal terrain entirely.
* Walls/floors come in rocky VARIANT SETS (no brick gridlines).
* The bottom panel is a real HUD: gradient console, recessed HP/XP bars
  with gloss, a framed quest panel, a framed message-log pane and section
  dividers -- not text slapped on black.
* The window is adaptive: everything is drawn to an internal fixed-resolution
  frame which is then letterbox-scaled onto the actual window.
"""
import random

import pygame

from components.game_states import GameStates
from components.fighter import HUNGER_MAX, HUNGER_LABELS, hunger_tier
from components import menus
from functions.render_order import RenderOrder  # noqa: F401
from functions.render_functions import get_names_under_mouse
from renderer.font_renderer import FontRenderer
from renderer.sprites import SpriteLoader
from renderer import palette as C

MAP_TILE = 16
UI_TILE = 16


def build_render_model(entities, fov, game_map):
    """Flat list of (x, y, type, sprite_id_or_char, color, layer) tuples."""
    model = []
    width = game_map.width
    for entity in entities:
        if not (0 <= entity.x < width and 0 <= entity.y < game_map.height):
            continue
        in_fov = fov[entity.y * width + entity.x] != 0
        on_explored = entity.trail or entity.ship or entity.part_id
        if not in_fov and not (on_explored and game_map.explored[entity.y * width + entity.x]):
            continue
        model.append((entity.x, entity.y, 'sprite', entity.sprite_id,
                      entity.color, entity.render_order.value))
    return model


class Renderer:
    def __init__(self, constants):
        self.constants = constants
        self.tile = MAP_TILE
        self.screen_w = constants['map_width'] * MAP_TILE
        self.screen_h = constants['map_height'] * MAP_TILE + \
            constants['panel_height'] * UI_TILE
        self.frame = pygame.Surface((self.screen_w, self.screen_h))
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h),
                                              pygame.RESIZABLE)
        pygame.display.set_caption(constants['window_title'])
        self.font = FontRenderer()
        self.sprites = SpriteLoader()
        self.terrain_cache = None
        self._dark_walls = None
        self._dark_floors = None
        self._light_walls = None
        self._light_floors = None
        self._dark_brush = None
        self._light_brush = None
        self._cached_version = None
        self._panel_bg = None
        self.fullscreen = False
        self._scale = 1.0
        self._offset = (0, 0)

    # ------------------------------------------------------------- tiles
    @staticmethod
    def _make_wall_tiles(base):
        """3-4 rocky wall variants: rough facets, cracks, edge shading.
        NO brick gridlines."""
        variants = []
        for v in range(4):
            s = pygame.Surface((MAP_TILE, MAP_TILE))
            s.fill(base)
            dark = C.shade(base, 0.62)
            dark2 = C.shade(base, 0.8)
            bright = C.shade(base, 1.35)
            bright2 = C.shade(base, 1.15)
            # 2px rim: lit top edge, shaded bottom/right, dark left face.
            s.fill(dark, (0, 0, 2, MAP_TILE))
            s.fill(dark2, (0, MAP_TILE - 2, MAP_TILE, 2))
            s.fill(dark2, (MAP_TILE - 2, 0, 2, MAP_TILE))
            s.fill(bright, (2, 0, MAP_TILE - 2, 2))
            rng = random.Random(100 + v)
            # rough facets: a few light/dark chunks, no regular grid.
            for i in range(3):
                fx = rng.randint(3, 10)
                fy = rng.randint(3, 11)
                s.fill(bright2, (fx, fy, rng.randint(2, 4), rng.randint(1, 3)))
            for i in range(2):
                fx = rng.randint(3, 10)
                fy = rng.randint(4, 11)
                s.fill(dark2, (fx, fy, rng.randint(2, 3), rng.randint(1, 2)))
            # a wandering crack.
            cx = rng.randint(4, 12)
            cy = rng.randint(3, 5)
            for i in range(7):
                if 2 <= cx < 14 and 2 <= cy < 14:
                    s.fill(dark, (cx, cy, 1, 1))
                cx += rng.choice((-1, 0, 0, 1))
                cy += 1
            variants.append(s)
        return variants

    @staticmethod
    def _make_floor_tiles(base):
        """Dirt / gravel / pebble floor variants."""
        variants = []
        for v in range(3):
            s = pygame.Surface((MAP_TILE, MAP_TILE))
            s.fill(base)
            dark = C.shade(base, 0.82)
            bright = C.shade(base, 1.22)
            rng = random.Random(50 + v)
            for i in range(8):
                s.fill(dark, (rng.randint(1, 14), rng.randint(1, 14), 1, 1))
            for i in range(5):
                s.fill(bright, (rng.randint(1, 14), rng.randint(1, 14), 1, 1))
            if v == 1:  # gravel: paired specks
                for i in range(3):
                    x = rng.randint(2, 12)
                    y = rng.randint(2, 12)
                    s.fill(dark, (x, y, 2, 1))
            if v == 2:  # pebble cluster
                px = rng.randint(4, 10)
                py = rng.randint(4, 10)
                s.fill(bright, (px, py, 2, 2))
                s.fill(dark, (px, py + 2, 2, 1))
                s.fill(dark, (px + 2, py + 1, 1, 1))
            variants.append(s)
        return variants

    # ------------------------------------------------------------- terrain
    def rebuild_terrain(self, game_map):
        colors = self.constants['colors']
        self.terrain_cache = pygame.Surface(
            (game_map.width * MAP_TILE, game_map.height * MAP_TILE))
        self.terrain_cache.fill((0, 0, 0))
        self._dark_walls = self._make_wall_tiles(colors['dark_wall'])
        self._dark_floors = self._make_floor_tiles(colors['dark_ground'])
        self._light_walls = self._make_wall_tiles(colors['light_wall'])
        self._light_floors = self._make_floor_tiles(colors['light_ground'])
        self._dark_brush = self._make_floor_tiles(colors['dark_brush'])
        self._light_brush = self._make_floor_tiles(colors['light_brush'])
        self._cached_version = game_map.version
        width, height = game_map.width, game_map.height
        for y in range(height):
            base = y * width
            for x in range(width):
                if game_map.explored[base + x]:
                    self._stamp_dark(game_map, x, y)

    def _variant(self, variants, x, y):
        return variants[(x * 7 + y * 13) % len(variants)]

    def _stamp_dark(self, game_map, x, y):
        if game_map.is_brush(x, y):
            tile = self._dark_brush[0]
        elif game_map.is_wall(x, y):
            tile = self._variant(self._dark_walls, x, y)
        else:
            tile = self._variant(self._dark_floors, x, y)
        self.terrain_cache.blit(tile, (x * MAP_TILE, y * MAP_TILE))

    def _sync_level(self, game_map):
        if self.terrain_cache is None or self._cached_version != game_map.version:
            self.rebuild_terrain(game_map)

    # ------------------------------------------------------------- window
    def present(self):
        """Letterbox-scale the internal frame onto the actual window."""
        fw, fh = self.frame.get_size()
        sw, sh = self.screen.get_size()
        scale = min(sw / fw, sh / fh)
        tw = max(1, int(fw * scale))
        th = max(1, int(fh * scale))
        if (tw, th) == (fw, fh):
            self.screen.blit(self.frame, (0, 0))
            self._offset = (0, 0)
        else:
            scaled = pygame.transform.smoothscale(self.frame, (tw, th))
            self.screen.fill((0, 0, 0))
            self._offset = ((sw - tw) // 2, (sh - th) // 2)
            self.screen.blit(scaled, self._offset)
        self._scale = tw / fw

    def resize(self, width, height):
        self.screen = pygame.display.set_mode((max(1, width), max(1, height)),
                                              pygame.RESIZABLE)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = (pygame.FULLSCREEN | pygame.RESIZABLE) if self.fullscreen else pygame.RESIZABLE
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h), flags)

    def screen_to_frame(self, pos):
        """Window px -> internal frame px, or None outside the frame."""
        mx, my = pos
        ox, oy = self._offset
        fx = (mx - ox) / self._scale
        fy = (my - oy) / self._scale
        if 0 <= fx < self.screen_w and 0 <= fy < self.screen_h:
            return (int(fx), int(fy))
        return None

    def screen_to_tile(self, pos):
        """Window px -> map tile coords, or None outside the map area."""
        frame = self.screen_to_frame(pos)
        if frame is None:
            return None
        fx, fy = frame
        if fy >= self.constants['map_height'] * MAP_TILE:
            return None
        tx = int(fx // MAP_TILE)
        ty = int(fy // MAP_TILE)
        if 0 <= tx < self.constants['map_width'] and 0 <= ty < self.constants['map_height']:
            return (tx, ty)
        return None

    # ------------------------------------------------------------- frame
    def render(self, game_map, fov, entities, player, message_log, game_state,
               mouse_tile, dialogue=None, popup=None, context_index=None,
               popup_scroll=0):
        self._sync_level(game_map)
        # No menu on screen yet: drop any clickable rects left over from a
        # previous frame's menu (death/victory screens register exit/new_game
        # rects, which must never fire during play). Menu states below
        # re-register their own rects when they draw.
        menus.clear_actions()
        width, height = game_map.width, game_map.height
        map_surf = pygame.Surface((width * MAP_TILE, height * MAP_TILE))
        if getattr(game_map, 'is_pocket', False):
            # Floor 4.5: every tile is a magenta unknown block.
            magenta = self.sprites.get('__pocket_tile__', (255, 0, 255))
            for y in range(height):
                for x in range(width):
                    map_surf.blit(magenta, (x * MAP_TILE, y * MAP_TILE))
        else:
            map_surf.blit(self.terrain_cache, (0, 0))
            for y in range(height):
                base = y * width
                for x in range(width):
                    if fov[base + x]:
                        if not game_map.explored[base + x]:
                            game_map.explored[base + x] = 1
                            self._stamp_dark(game_map, x, y)
                        if game_map.is_brush(x, y):
                            light = self._light_brush[0]
                        elif game_map.is_wall(x, y):
                            light = self._variant(self._light_walls, x, y)
                        else:
                            light = self._variant(self._light_floors, x, y)
                        map_surf.blit(light, (x * MAP_TILE, y * MAP_TILE))
        model = build_render_model(entities, fov, game_map)
        model.sort(key=lambda item: item[5])
        for (x, y, kind, sprite_id, color, _layer) in model:
            if kind == 'text':
                self.font.draw_char(map_surf, sprite_id, x, y, color)
            else:
                map_surf.blit(self.sprites.get(sprite_id, color),
                              (x * MAP_TILE, y * MAP_TILE))
        # Hover cursor: a small procedural triangle on the hovered map tile.
        if mouse_tile is not None:
            hx, hy = mouse_tile
            if 0 <= hx < width and 0 <= hy < height and fov[hy * width + hx]:
                px, py = hx * MAP_TILE, hy * MAP_TILE
                pygame.draw.polygon(map_surf, C.WHITE, [
                    (px + 2, py + 2), (px + 7, py + 5), (px + 2, py + 8)])
        self.frame.blit(map_surf, (0, 0))
        self._draw_panel(game_map, entities, player, message_log, fov, mouse_tile)

        sw = self.constants['screen_width']
        sh = self.constants['screen_height']
        if game_state == GameStates.SHOW_INVENTORY:
            menus.inventory_menu(self.frame, self.font,
                                 'Press the key next to an item to use it, or Esc to cancel.\n',
                                 player, 50, sw, sh)
        elif game_state == GameStates.DROP_INVENTORY:
            menus.inventory_menu(self.frame, self.font,
                                 'Press the key next to an item to drop it, or Esc to cancel.\n',
                                 player, 50, sw, sh, drop=True)
        elif game_state == GameStates.ITEM_CONTEXT:
            items = player.inventory.items
            item = items[context_index] if context_index is not None and context_index < len(items) else None
            menus.context_menu(self.frame, self.font, item, sw, sh)
        elif game_state == GameStates.CRAFTING:
            menus.crafting_menu(self.frame, self.font, player, sw, sh)
        elif game_state == GameStates.LEVEL_UP:
            menus.level_up_menu(self.frame, self.font, 'Level up! Choose a stat to raise:',
                                player, 40, sw, sh)
        elif game_state == GameStates.CHARACTER_SCREEN:
            menus.character_screen(self.frame, self.font, player, 44, 20, sw, sh)
        elif game_state == GameStates.POPUP:
            menus.popup_box(self.frame, self.font, popup or '', sw, sh, scroll=popup_scroll)
        elif game_state == GameStates.DIALOGUE and dialogue is not None:
            menus.dialogue_menu(self.frame, self.font, dialogue[0], dialogue[1], sw, sh)
        elif game_state == GameStates.VICTORY:
            menus.victory_screen(self.frame, self.font, player, game_map, sw, sh)
        elif game_state == GameStates.PLAYER_DEAD:
            menus.death_overlay(self.frame, self.font, sw, sh)
        self.present()

    # ------------------------------------------------------------- HUD panel
    def _ensure_panel_bg(self):
        """Build the console background once: a warm red-dirt gradient with
        speckle noise, a bezel top edge (with rivets) and the bar/log
        divider column."""
        if self._panel_bg is not None:
            return
        w = self.screen_w
        h = self.constants['panel_height'] * UI_TILE
        bg = pygame.Surface((w, h))
        top = (48, 32, 23)
        mid = (24, 17, 14)
        bottom = (9, 8, 9)
        for y in range(h):
            t = y / max(1, h - 1)
            if t < 0.5:
                f = t * 2
                col = tuple(int(top[i] + (mid[i] - top[i]) * f) for i in range(3))
            else:
                f = (t - 0.5) * 2
                col = tuple(int(mid[i] + (bottom[i] - mid[i]) * f) for i in range(3))
            pygame.draw.line(bg, col, (0, y), (w, y))
        rng = random.Random(4242)
        for _ in range(w * h // 40):
            x = rng.randrange(w)
            y = rng.randrange(h)
            r, g, b = bg.get_at((x, y))[:3]
            delta = rng.randint(-8, 8)
            bg.set_at((x, y), (max(0, min(255, r + delta)),
                               max(0, min(255, g + delta)),
                               max(0, min(255, b + delta))))
        # Bezel: light top edge with a dark seam under it, plus rivets.
        pygame.draw.line(bg, (60, 44, 32), (0, 0), (w, 0))
        pygame.draw.line(bg, (28, 19, 15), (0, 1), (w, 1))
        for fx in (w // 8, 3 * w // 8, 5 * w // 8, 7 * w // 8):
            pygame.draw.rect(bg, (74, 56, 42), (fx - 1, 3, 2, 2))
            pygame.draw.rect(bg, (32, 22, 17), (fx, 4, 1, 1))
        # The bar/log divider column: dark seam with a bright edge.
        dx = self.constants['bar_width'] * UI_TILE
        pygame.draw.line(bg, (24, 17, 13), (dx, 0), (dx, h))
        pygame.draw.line(bg, (56, 42, 33), (dx + 1, 0), (dx + 1, h))
        self._panel_bg = bg

    def _hud_bar(self, frame, tile_x, py, width, ratio, dark, bright, label):
        """A recessed HUD meter: dark slot, rim, vertical-gradient fill
        with a gloss line, segment ticks and an end cap."""
        x0 = tile_x * UI_TILE
        w = width * UI_TILE
        slot = pygame.Rect(x0, py, w, UI_TILE)
        pygame.draw.rect(frame, (10, 8, 8), slot)
        pygame.draw.rect(frame, (58, 46, 38), slot, 1)
        pygame.draw.line(frame, (0, 0, 0), (x0 + 1, py + UI_TILE - 2),
                         (x0 + w - 2, py + UI_TILE - 2))
        fill_w = int(w * max(0.0, min(1.0, ratio)))
        if fill_w > 0:
            fill = pygame.Rect(x0 + 1, py + 1, fill_w - 1, UI_TILE - 2)
            for fy in range(fill.h):
                f = fy / max(1, fill.h - 1)
                col = tuple(int(dark[i] + (bright[i] - dark[i]) * (1 - f) * 0.7)
                            for i in range(3))
                pygame.draw.line(frame, col, (fill.x, fill.y + fy),
                                 (fill.x + fill.w - 1, fill.y + fy))
            pygame.draw.line(frame, C.shade(bright, 1.3),
                             (fill.x, fill.y), (fill.x + fill.w - 1, fill.y))
            pygame.draw.line(frame, C.shade(dark, 1.25),
                             (fill.x + fill.w - 1, fill.y),
                             (fill.x + fill.w - 1, fill.y + fill.h - 1))
            for tx in range(x0 + 5, x0 + w - 2, 6):
                pygame.draw.line(frame, (0, 0, 0), (tx, py + 2),
                                 (tx, py + UI_TILE - 3))
        self.font.draw_text(frame, label, tile_x + 1, py // UI_TILE,
                            C.WHITE, vertical_center=True)

    _STATUS_BADGES = {
        'webbed': (C.WHITE, 'WEB'),
        'speed': (C.GOLD, 'SPD'),
        'invisible': (C.LIGHT_BLUE, 'INV'),
        'poison_resist': (C.LIGHT_GREEN, 'RES'),
    }

    def _draw_status_row(self, frame, py, bar_width, statuses):
        """Row 6: coloured badges for active effects, or the compact key
        hint when nothing is active. Badges never overflow the column."""
        if not statuses:
            self.font.draw_text(frame, 'z wait g grab . use i inv',
                                1, py // UI_TILE, C.DARK_GRAY)
            return
        tx = 1
        for key in sorted(statuses):
            color, label = self._STATUS_BADGES.get(
                key, (C.LIGHT_GRAY, key.upper()[:3]))
            if tx + 1 + len(label) > bar_width:
                break
            sx = tx * UI_TILE
            pygame.draw.rect(frame, color, (sx + 1, py + 3, 6, 10))
            pygame.draw.rect(frame, C.shade(color, 0.55),
                             (sx + 1, py + 3, 6, 10), 1)
            self.font.draw_text(frame, label, tx + 1, py // UI_TILE, C.WHITE)
            tx += 1 + len(label)

    def _draw_panel(self, game_map, entities, player, message_log, fov, mouse_tile):
        map_px = self.constants['map_height'] * MAP_TILE   # panel pixel origin
        frame = self.frame
        self._ensure_panel_bg()
        frame.blit(self._panel_bg, (0, map_px))
        bar_width = self.constants['bar_width']

        def row_y(r):
            return map_px + r * UI_TILE

        # ------------------------------------------------ left column
        # Row 0: names under the mouse (clamped to the column).
        names = ''
        if mouse_tile is not None:
            names = get_names_under_mouse(mouse_tile, entities, fov, game_map)
        max_names = bar_width - 2
        if len(names) > max_names:
            names = names[:max_names - 3] + '...'
        self.font.draw_text(frame, names, 1, row_y(0) // UI_TILE, C.LIGHT_GRAY)

        # Rows 1-2: HP / XP meters.
        hp = player.fighter.hp
        max_hp = max(1, player.fighter.max_hp)
        self._hud_bar(frame, 1, row_y(1), bar_width, hp / max_hp,
                      C.DARKER_RED, C.LIGHT_RED,
                      'HP {0}/{1}'.format(hp, max_hp))
        xp = player.level.current_xp
        xp_next = max(1, player.level.experience_to_next_level)
        self._hud_bar(frame, 2, row_y(2), bar_width, min(1.0, xp / xp_next),
                      C.DARK_BLUE, C.LIGHT_BLUE,
                      'XP {0}/{1}  Lv {2}'.format(xp, xp_next,
                                                  player.level.current_level))

        # Row 3: hunger meter (satiety drains; colour shifts with the tier).
        pygame.draw.line(frame, (36, 25, 20), (0, row_y(3) - 2),
                         (bar_width * UI_TILE, row_y(3) - 2))
        hunger = getattr(player.fighter, 'hunger', HUNGER_MAX)
        tier = hunger_tier(player.fighter)
        if tier == 'starving':
            h_fill, h_bright = C.DARKER_RED, C.LIGHT_RED
        elif tier == 'hungry':
            h_fill, h_bright = (92, 58, 16), (235, 175, 70)
        else:
            h_fill, h_bright = C.DARKER_GREEN, C.LIGHT_GREEN
        self._hud_bar(frame, 3, row_y(3), bar_width,
                      max(0.0, min(1.0, hunger / HUNGER_MAX)),
                      h_fill, h_bright,
                      'Hunger: {0}'.format(HUNGER_LABELS[tier]))

        # Rows 4-5: ship parts -- gold header with a mini progress meter,
        # then all four part checkboxes on a single line.
        pygame.draw.line(frame, (36, 25, 20), (0, row_y(4) - 2),
                         (bar_width * UI_TILE, row_y(4) - 2))
        parts = player.quest.found_count
        parts_total = player.quest.parts_total
        self.font.draw_text(frame, 'Ship parts: {0}/{1}'.format(parts, parts_total),
                            1, row_y(4) // UI_TILE, C.GOLD)
        px0 = 1 * UI_TILE
        pmax = (bar_width - 2) * UI_TILE
        # 1px meter along the row's very bottom edge, clear of the glyph
        # ink (Font16 ink ends at +14), so it never collides with the text.
        pygame.draw.rect(frame, (12, 10, 10), (px0, row_y(4) + 15, pmax, 1))
        pygame.draw.rect(frame, (205, 165, 60),
                         (px0, row_y(4) + 15,
                          max(0, int(pmax * parts / max(1, parts_total))), 1))
        from components.quest import SHIP_PARTS
        short = {'antimatter_core': 'Core', 'nav_computer': 'Nav',
                 'power_coupling': 'Coup', 'hull_plating': 'Plat'}
        line = ' '.join(
            ('☑' if player.quest.has_part(pid) else '☐') + ' ' + short[pid]
            for pid in SHIP_PARTS)
        self.font.draw_text(frame, line, 1, row_y(5) // UI_TILE, C.LIGHT_GRAY)
        pygame.draw.line(frame, (36, 25, 20), (0, row_y(6) - 2),
                         (bar_width * UI_TILE, row_y(6) - 2))

        # Row 6: active status badges, or the compact key hint when clear.
        self._draw_status_row(frame, row_y(6), bar_width,
                              getattr(player.fighter, 'status', {}) or {})

        # ------------------------------------------------ right column
        # Row 0: dungeon level readout.
        if getattr(game_map, 'is_pocket', False):
            level_text = 'DUNGEON LV 4.5'
        else:
            level_text = 'DUNGEON LV {0}'.format(game_map.dungeon_level)
        self.font.draw_text(frame, level_text, self.constants['message_x'],
                            row_y(0) // UI_TILE, C.LIGHT_GRAY)

        # Rows 1-6: framed message-log pane.
        log_x0 = (bar_width + 1) * UI_TILE
        log_x1 = self.screen_w - UI_TILE
        log_top = row_y(1)
        log_bot = row_y(self.constants['panel_height'])
        pygame.draw.rect(frame, (13, 11, 11), (log_x0, log_top, log_x1 - log_x0, log_bot - log_top))
        pygame.draw.rect(frame, (52, 40, 34), (log_x0, log_top, log_x1 - log_x0, log_bot - log_top), 1)
        pygame.draw.rect(frame, C.VIOLET, (log_x0, log_top, 2, log_bot - log_top))
        y = row_y(1) // UI_TILE
        for message in message_log.message:
            self.font.draw_text(frame, message.text, message_log.x, y, message.color)
            y += 1
