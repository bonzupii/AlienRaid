#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GameMap with flat ``bytearray`` tile fields for speed.

Tile index is ``x + y * width``. ``blocked`` = walls/terrain you cannot walk
into, ``block_sight`` = walls that block vision, ``explored`` = tiles the
player has seen. The renderer caches these into surfaces.
"""

from random import randint

from components.trail import Trail
from components.quest import SHIP_PARTS, PART_COLORS
from components.entity import Entity
from components.game_messages import Message
from functions.render_order import RenderOrder
from loader_functions.random_utils import from_dungeon_level, random_choice_from_dict
from loader_functions.monsters import MONSTER_TABLES, create_monster
from loader_functions.items import ITEM_TABLES, create_item
from map_objects.rectangle import Rect
from renderer import palette as C

LAST_FLOOR = 20
PART_FLOORS = [5, 10, 15, 20]

TRAIL_DOWN_COLOR = (180, 120, 40)
TRAIL_UP_COLOR = (120, 160, 60)


class GameMap:
    def __init__(self, width, height, dungeon_level=1):
        self.width = width
        self.height = height
        self.dungeon_level = dungeon_level
        self.blocked = bytearray([1]) * (width * height)
        self.block_sight = bytearray([1]) * (width * height)
        self.explored = bytearray(width * height)
        self.brush = bytearray(width * height)

    # ------------------------------------------------------------- tile utils
    def idx(self, x, y):
        return x + y * self.width

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_blocked(self, x, y):
        if not self.in_bounds(x, y):
            return True
        return self.blocked[self.idx(x, y)] != 0

    def is_wall(self, x, y):
        if not self.in_bounds(x, y):
            return True
        return self.block_sight[self.idx(x, y)] != 0

    def is_brush(self, x, y):
        """Scrub/grass that blocks sight but not movement."""
        if not self.in_bounds(x, y):
            return False
        return self.brush[self.idx(x, y)] != 0

    def _find_free_tile(self, x, y, entities):
        """Nearest free tile to (x, y), used to place stairs/ship/parts."""
        if not self.is_blocked(x, y) and not any(e.blocks and e.x == x and e.y == y
                                                for e in entities):
            return (x, y)
        for radius in range(1, 8):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    nx, ny = x + dx, y + dy
                    if not self.is_blocked(nx, ny) and not any(e.blocks and e.x == nx and e.y == ny
                                                              for e in entities):
                        return (nx, ny)
        return (x, y)

    # ------------------------------------------------------------ generation
    def make_map(self, max_rooms, room_min_size, room_max_size, map_width,
                 map_height, player, entities, start_at='first'):
        rooms = []
        num_rooms = 0
        first_center = (0, 0)
        last_center = (0, 0)

        for r in range(max_rooms):
            w = randint(room_min_size, room_max_size)
            h = randint(room_min_size, room_max_size)
            x = randint(0, map_width - w - 1)
            y = randint(0, map_height - h - 1)
            new_room = Rect(x, y, w, h)

            for other_room in rooms:
                if new_room.intersect(other_room):
                    break
            else:
                self.create_room(new_room)
                (new_x, new_y) = new_room.center()
                last_center = (new_x, new_y)
                if num_rooms == 0:
                    first_center = (new_x, new_y)

                if num_rooms == 0:
                    player.x = new_x
                    player.y = new_y
                else:
                    (prev_x, prev_y) = rooms[num_rooms - 1].center()
                    # Winding tracks: jog through a mid-point so corridors
                    # feel like bush trails instead of straight tunnels.
                    if randint(0, 1) == 1:
                        mid_x = (prev_x + new_x) // 2 + randint(-2, 2)
                        mid_x = max(1, min(self.width - 2, mid_x))
                        self.create_h_tunnel(prev_x, mid_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, mid_x)
                        self.create_h_tunnel(mid_x, new_x, new_y)
                    else:
                        mid_y = (prev_y + new_y) // 2 + randint(-2, 2)
                        mid_y = max(1, min(self.height - 2, mid_y))
                        self.create_v_tunnel(prev_y, mid_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, mid_y)
                        self.create_v_tunnel(mid_y, new_y, new_x)

                self.place_entities(new_room, entities)
                rooms.append(new_room)
                num_rooms += 1

        if start_at == 'last':
            px, py = self._find_free_tile(last_center[0], last_center[1], entities)
            player.x, player.y = px, py

        self._place_landmarks(entities)
        self._place_stairs_and_quest(first_center, last_center, entities)
        self._place_brush(entities)

    def create_room(self, room):
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.blocked[self.idx(x, y)] = 0
                self.block_sight[self.idx(x, y)] = 0

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.blocked[self.idx(x, y)] = 0
            self.block_sight[self.idx(x, y)] = 0

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.blocked[self.idx(x, y)] = 0
            self.block_sight[self.idx(x, y)] = 0

    # ------------------------------------------------------------ landmarks
    def _stamp(self, pattern, x, y, occupied=None):
        """Stamp a small set-piece onto the map. ``#`` = solid,
        ``.``/``w`` = passable ground (w = billabong water). Tiles already
        holding an entity are left alone so nothing spawns inside a wall."""
        occupied = occupied or set()
        for dy, row in enumerate(pattern):
            for dx, ch in enumerate(row):
                nx, ny = x + dx, y + dy
                if not self.in_bounds(nx, ny):
                    continue
                if (nx, ny) in occupied:
                    continue
                idx = self.idx(nx, ny)
                if ch == '#':
                    self.blocked[idx] = 1
                    self.block_sight[idx] = 1
                elif ch in ('.', 'w'):
                    self.blocked[idx] = 0
                    self.block_sight[idx] = 0

    def _place_landmarks(self, entities):
        """Stamp outback set-pieces appropriate for the current floor."""
        level = self.dungeon_level
        occupied = {(e.x, e.y) for e in entities}

        # Billabongs: water pools, croc ambush country (floors 6-10).
        if level in range(6, 11):
            for _ in range(randint(1, 2)):
                bx = randint(5, self.width - 10)
                by = randint(5, self.height - 10)
                self._stamp([
                    '...www...',
                    '..wwwww..',
                    '.wwwwwww.',
                    'wwwwwwwww',
                    '.wwwwwww.',
                    '..wwwww..',
                    '...www...',
                ], bx, by, occupied=occupied)

        # Termite mounds: pillar clusters (floors 1-15).
        if level in range(1, 16):
            for _ in range(randint(2, 4)):
                mx = randint(5, self.width - 8)
                my = randint(5, self.height - 8)
                self._stamp(['.#.', '###', '.#.'], mx, my, occupied=occupied)

        # Dingo fences: a long straight line with a gap (signature chokepoint).
        if level in [3, 7, 11, 15, 19]:
            fy = randint(10, self.height - 10)
            gap_x = randint(20, self.width - 20)
            for x in range(5, self.width - 5):
                if abs(x - gap_x) > 2 and (x, fy) not in occupied:
                    idx = self.idx(x, fy)
                    self.blocked[idx] = 1
                    self.block_sight[idx] = 1

        # Kopjes: rock outcrops that block everything (floors 11-20).
        if level in range(11, 21):
            for _ in range(randint(1, 3)):
                kx = randint(5, self.width - 12)
                ky = randint(5, self.height - 12)
                self._stamp([
                    '....####....',
                    '...######...',
                    '..########..',
                    '.##########.',
                    '############',
                    '.##########.',
                ], kx, ky, occupied=occupied)

    def _place_brush(self, entities):
        """Scatter sight-blocking scrub on open ground (dappled FOV)."""
        if self.dungeon_level <= 5:
            density = 15
        elif self.dungeon_level <= 10:
            density = 10
        elif self.dungeon_level <= 15:
            density = 5
        else:
            density = 2

        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                idx = self.idx(x, y)
                if self.blocked[idx] == 0 and randint(1, 100) <= density:
                    if not any(e.x == x and e.y == y for e in entities):
                        self.brush[idx] = 1
                        self.block_sight[idx] = 1

    def place_entities(self, room, entities):
        level = self.dungeon_level
        max_monsters = from_dungeon_level([[2, 1], [3, 4], [4, 7], [6, 10], [7, 14]], level)
        min_monsters = from_dungeon_level([[0, 1], [1, 4], [2, 7], [3, 10], [4, 14]], level)
        max_items = from_dungeon_level([[1, 1], [2, 4], [3, 8]], level)

        number_of_monsters = randint(min_monsters, max_monsters)
        number_of_items = randint(0, max_items)

        monster_chances = {name: from_dungeon_level(table, level)
                           for name, table in MONSTER_TABLES.items()}
        item_chances = {name: from_dungeon_level(table, level)
                        for name, table in ITEM_TABLES.items()}

        for i in range(number_of_monsters):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            if not any(entity for entity in entities if entity.x == x and entity.y == y):
                choice = random_choice_from_dict(monster_chances)
                entities.append(create_monster(choice, level, x, y))

        for i in range(number_of_items):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            if not any(entity for entity in entities if entity.x == x and entity.y == y):
                choice = random_choice_from_dict(item_chances)
                entities.append(create_item(choice, level, x, y))

    # ----------------------------------------------- stairs / ship / quest
    def _place_stairs_and_quest(self, first_center, last_center, entities):
        first_x, first_y = first_center
        last_x, last_y = last_center

        # Up-trail: back to the previous floor, near where you arrive.
        if self.dungeon_level >= 2:
            tx, ty = self._find_free_tile(first_x, first_y, entities)
            up_trail = Entity(tx, ty, 'trail_up', TRAIL_UP_COLOR, 'Trail up',
                              render_order=RenderOrder.TRAIL,
                              trail=Trail(direction='up', floor=self.dungeon_level - 1))
            entities.append(up_trail)

        # Down-trail: deeper, unless this is the deepest floor.
        if self.dungeon_level < LAST_FLOOR:
            tx, ty = self._find_free_tile(last_x, last_y, entities)
            down_trail = Entity(tx, ty, 'trail_down', TRAIL_DOWN_COLOR, 'Trail down',
                                render_order=RenderOrder.TRAIL,
                                trail=Trail(direction='down', floor=self.dungeon_level + 1))
            entities.append(down_trail)

        # The crashed ship on the surface (floor 1).
        if self.dungeon_level == 1:
            sx, sy = self._find_free_tile(last_x, last_y + 1, entities)
            ship = Entity(sx, sy, 'ship', C.SILVER, 'Your crashed ship',
                          render_order=RenderOrder.SHIP, ship=True)
            entities.append(ship)

        # Salvageable ship part (wreckage) on the part floors.
        if self.dungeon_level in PART_FLOORS:
            part_id = next(pid for pid, (_, floor) in SHIP_PARTS.items() if floor == self.dungeon_level)
            part_name = SHIP_PARTS[part_id][0]
            px, py = self._find_free_tile(last_x, last_y - 1, entities)
            part = Entity(px, py, 'part', PART_COLORS[part_id], part_name,
                          render_order=RenderOrder.PART, part_id=part_id)
            entities.append(part)

    # ------------------------------------------------------------ transitions
    def go_down(self, player, message_log, constants):
        self.dungeon_level += 1
        from loader_functions.initialize_new_game import biome_for_level
        constants.setdefault('colors', {}).update(biome_for_level(self.dungeon_level))
        entities = self._new_level(player, message_log, constants, start_at='first', heal=True)
        message_log.add_message(Message('You take the trail and descend into the darkness.', C.LIGHT_VIOLET))
        return entities

    def go_up(self, player, message_log, constants):
        self.dungeon_level -= 1
        from loader_functions.initialize_new_game import biome_for_level
        constants.setdefault('colors', {}).update(biome_for_level(self.dungeon_level))
        entities = self._new_level(player, message_log, constants, start_at='last', heal=False)
        message_log.add_message(Message('You climb back toward the surface.', C.LIGHT_GREEN))
        return entities

    def _new_level(self, player, message_log, constants, start_at='first', heal=True):
        entities = [player]
        self.blocked = bytearray([1]) * (self.width * self.height)
        self.block_sight = bytearray([1]) * (self.width * self.height)
        self.explored = bytearray(self.width * self.height)
        self.brush = bytearray(self.width * self.height)
        self.make_map(constants['max_rooms'], constants['room_min_size'],
                      constants['room_max_size'], constants['map_width'],
                      constants['map_height'], player, entities, start_at=start_at)
        if heal:
            player.fighter.heal(player.fighter.max_hp // 2)
            message_log.add_message(Message('You take a moment to rest and recover your strength.', C.LIGHT_VIOLET))
        return entities
