#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GameMap with flat ``bytearray`` tile fields for speed.

Phase 1 replaced the rooms-and-corridors dungeon with a completely organic
generator: cellular-automata cave smoothing produces rocky outback terrain
(irregular clearings and winding passages -- no rectangles, no brick). After
smoothing, only the LARGEST open component is kept, and a post-pass
(``_ensure_connected``) carves winding tunnels to every gameplay-critical
entity (trails, ship, parts, NPCs) so the walkable region is always ONE
connected component.

Tile index is ``x + y * width``. ``blocked`` = walls/terrain you cannot walk
into, ``block_sight`` = walls that block vision, ``explored`` = tiles the
player has seen, ``brush`` = scrub that blocks sight but not movement.
"""
from random import randint, shuffle

from components.ai import HUNT
from components.trail import Trail
from components.quest import SHIP_PARTS, PART_COLORS
from components.entity import Entity
from components.game_messages import Message
from functions.render_order import RenderOrder
from loader_functions.random_utils import from_dungeon_level, random_choice_from_dict
from loader_functions.monsters import MONSTER_TABLES, create_monster
from loader_functions.items import ITEM_TABLES, create_item
from renderer import palette as C

LAST_FLOOR = 20
PART_FLOORS = [5, 10, 15, 20]
TRAIL_DOWN_COLOR = (180, 120, 40)
TRAIL_UP_COLOR = (120, 160, 60)

# NPC landmark floors (Phase F). Agent J sits on 12 so the quest flows
# downward: parts on 5/10, the neuralyzer on 11, J on 12, parts on 15/20.
MIB_FLOOR = 12
AECD_FLOOR = 11
ROADHOUSE_FLOORS = (7, 14)

# Floor 4.5: the pocket dimension marker used by the mystery trail.
POCKET_FLOOR = '4.5'


class GameMap:
    def __init__(self, width, height, dungeon_level=1):
        self.width = width
        self.height = height
        self.dungeon_level = dungeon_level
        self.blocked = bytearray([1]) * (width * height)
        self.block_sight = bytearray([1]) * (width * height)
        self.explored = bytearray(width * height)
        self.brush = bytearray(width * height)
        # Renderer cache key: bumped whenever the floor is regenerated so
        # the pre-rendered terrain cache always rebuilds.
        self.version = 1
        # Per-floor easter-egg state (reset on every new level).
        self.is_pocket = False        # floor 4.5 renders as magenta unknown tiles
        self.land_dispute = False     # cassowary vs kanga, once per floor
        self.swooping = False         # spring swoop, once per floor
        self.emu_war_memorial = False # floor 13 landmark pre-aggros emus

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
    def make_map(self, map_width, map_height, player, entities, start_at='first'):
        self._generate_cave()
        self._keep_largest_component()
        first_center = self._nearest_open(map_width // 4, map_height // 3)
        last_center = self._nearest_open(3 * map_width // 4, 2 * map_height // 3)
        if start_at == 'first':
            player.x, player.y = first_center
        else:
            px, py = self._find_free_tile(last_center[0], last_center[1], entities)
            player.x, player.y = px, py
        self._place_landmarks(entities)
        self._place_stairs_and_quest(first_center, last_center, entities)
        self._place_npc_camps(entities)
        self._ensure_connected(player, entities)
        self.place_entities(player, entities)
        self._place_brush(entities)

    # ------------------------------------------- organic cave generation
    def _generate_cave(self):
        """Random fill + 5 smoothing passes = rocky organic terrain."""
        w, h = self.width, self.height
        for y in range(h):
            base = y * w
            for x in range(w):
                if x < 2 or y < 2 or x >= w - 2 or y >= h - 2:
                    v = 1
                else:
                    v = 1 if randint(0, 99) < 44 else 0
                self.blocked[base + x] = v
                self.block_sight[base + x] = v
        for pass_num in range(5):
            self._smooth_pass()

    def _smooth_pass(self):
        w, h = self.width, self.height
        old = self.blocked
        new = bytearray(w * h)
        for y in range(h):
            base = y * w
            for x in range(w):
                if x < 2 or y < 2 or x >= w - 2 or y >= h - 2:
                    new[base + x] = 1
                    continue
                walls = 0
                for dy in (-1, 0, 1):
                    row = (y + dy) * w
                    for dx in (-1, 0, 1):
                        walls += old[row + x + dx]
                new[base + x] = 1 if walls >= 5 else 0
        self.blocked = new
        self.block_sight = bytearray(new)

    def _flood(self, sx, sy):
        """8-directional flood fill over open tiles; returns a bytearray."""
        w, h = self.width, self.height
        seen = bytearray(w * h)
        if self.blocked[sy * w + sx]:
            return seen
        seen[sy * w + sx] = 1
        stack = [(sx, sy)]
        while stack:
            x, y = stack.pop()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        i = ny * w + nx
                        if not seen[i] and not self.blocked[i]:
                            seen[i] = 1
                            stack.append((nx, ny))
        return seen

    def _keep_largest_component(self):
        """Fill every open pocket except the largest component."""
        w, h = self.width, self.height
        visited = bytearray(w * h)
        components = []
        for y in range(h):
            for x in range(w):
                i = y * w + x
                if not self.blocked[i] and not visited[i]:
                    comp = self._flood(x, y)
                    size = sum(comp)
                    for j in range(w * h):
                        if comp[j]:
                            visited[j] = 1
                    components.append((size, comp))
        if not components:
            # Degenerate: carve a clearing in the middle.
            cx, cy = w // 2, h // 2
            for y in range(cy - 3, cy + 4):
                for x in range(cx - 3, cx + 4):
                    self.blocked[self.idx(x, y)] = 0
                    self.block_sight[self.idx(x, y)] = 0
            return
        components.sort(key=lambda c: c[0])
        keep = components[-1][1]
        for y in range(h):
            base = y * w
            for x in range(w):
                if not self.blocked[base + x] and not keep[base + x]:
                    self.blocked[base + x] = 1
                    self.block_sight[base + x] = 1

    def _nearest_open(self, x, y):
        """Nearest open tile to (x, y) by expanding rings."""
        if not self.is_blocked(x, y):
            return (x, y)
        for radius in range(1, max(self.width, self.height)):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if max(abs(dx), abs(dy)) != radius:
                        continue
                    nx, ny = x + dx, y + dy
                    if self.in_bounds(nx, ny) and not self.blocked[self.idx(nx, ny)]:
                        return (nx, ny)
        return (x, y)

    def _carve_tunnel(self, x0, y0, x1, y1):
        """Winding tunnel: jog through a mid-point, carve open ground."""
        mid_x = (x0 + x1) // 2 + randint(-3, 3)
        mid_y = (y0 + y1) // 2 + randint(-3, 3)
        mid_x = max(2, min(self.width - 3, mid_x))
        mid_y = max(2, min(self.height - 3, mid_y))
        for (ax, ay, bx, by) in ((x0, y0, mid_x, mid_y), (mid_x, mid_y, x1, y1)):
            x, y = ax, ay
            while (x, y) != (bx, by):
                i = self.idx(x, y)
                self.blocked[i] = 0
                self.block_sight[i] = 0
                if x != bx:
                    x += 1 if bx > x else -1
                if y != by:
                    y += 1 if by > y else -1
        i = self.idx(x1, y1)
        self.blocked[i] = 0
        self.block_sight[i] = 0

    def _ensure_connected(self, player, entities):
        """Carve a tunnel to every critical entity the flood cannot reach."""
        for pass_num in range(4):
            seen = self._flood(player.x, player.y)
            missing = [e for e in entities
                       if (e.trail or e.ship or e.part_id or e.npc_id)
                       and not seen[self.idx(e.x, e.y)]]
            if not missing:
                return
            for e in missing:
                self._carve_tunnel(player.x, player.y, e.x, e.y)

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
            for i in range(randint(1, 2)):
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
            for i in range(randint(2, 4)):
                mx = randint(5, self.width - 8)
                my = randint(5, self.height - 8)
                self._stamp(['.#.', '###', '.#.'], mx, my, occupied=occupied)
        # Dingo fences: a long straight line with a passable gap.
        if level in [3, 7, 11, 15, 19]:
            fy = randint(10, self.height - 10)
            gap_x = randint(20, self.width - 20)
            for x in range(5, self.width - 5):
                idx = self.idx(x, fy)
                if abs(x - gap_x) <= 2:
                    self.blocked[idx] = 0
                    self.block_sight[idx] = 0
                elif (x, fy) not in occupied:
                    self.blocked[idx] = 1
                    self.block_sight[idx] = 1
        # Kopjes: rock outcrops that block everything (floors 11-20).
        if level in range(11, 21):
            for i in range(randint(1, 3)):
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
        # Emu War memorial (rare, floor 13): a rusted machine-gun nest with
        # a plaque and a locked chest holding Ned Kelly's breastplate. The
        # emus on that floor spawn pre-aggro'd, out of principle.
        if level == 13 and randint(1, 100) <= 30:
            self.emu_war_memorial = True
            self._place_emu_memorial(entities)
        # The rusty ute: a slab of warm tinnies in the tray (floors 1-5).
        if level <= 5 and randint(1, 100) <= 30:
            self._place_rusty_ute(entities)

    def _place_emu_memorial(self, entities):
        """The Emu War memorial: a rusted machine-gun nest with a plaque and
        a sealed chest (Ned Kelly's breastplate) under the wreckage."""
        mx = randint(8, self.width - 18)
        my = randint(8, self.height - 14)
        self._stamp([
            '...###...',
            '..#####..',
            '.##...##.',
            '.#..#..#.',
            '.#..#..#.',
            '.##...##.',
            '..#####..',
            '...###...',
        ], mx, my)
        plaque_x, plaque_y = self._find_free_tile(mx + 2, my + 2, entities)
        entities.append(create_item('emu_war_plaque', self.dungeon_level,
                                    plaque_x, plaque_y))
        chest_x, chest_y = self._find_free_tile(mx + 6, my + 4, entities)
        entities.append(create_item('ned_kelly_chest', self.dungeon_level,
                                    chest_x, chest_y))

    def _place_rusty_ute(self, entities):
        """A rusted ute with a slab of warm tinnies in the tray."""
        ux = randint(8, self.width - 18)
        uy = randint(8, self.height - 10)
        self._stamp([
            '....####....',
            '...######...',
            '..########.',
            '..########.',
        ], ux, uy)
        ute_x, ute_y = self._find_free_tile(ux + 4, uy + 2, entities)
        entities.append(Entity(ute_x, ute_y, 'ute', (140, 90, 60),
                               'Rusty ute', blocks=True,
                               render_order=RenderOrder.ACTOR))
        for dx in (-3, 0, 3):
            tx, ty = self._find_free_tile(ute_x + dx, ute_y + 1, entities)
            entities.append(create_item('tinny', self.dungeon_level, tx, ty))

    # ------------------------------------------------- NPC camps (Phase F)
    def _place_npc_camps(self, entities):
        level = self.dungeon_level
        occupied = {(e.x, e.y) for e in entities}
        if level == MIB_FLOOR:
            bx = randint(6, self.width - 16)
            by = randint(6, self.height - 12)
            self._stamp([
                '..######......',
                '.#wwwwww#.....',
                '.#wwwwww#.....',
                '..##ww##......',
                '...wwww.......',
                '...wwww.......',
            ], bx, by, occupied=occupied)
            nx, ny = self._find_free_tile(bx + 6, by + 5, entities)
            entities.append(Entity(nx, ny, 'agent_j_cameo', (20, 20, 20), 'Agent J',
                                   blocks=True, render_order=RenderOrder.ACTOR,
                                   npc_id='mib'))
        if level == AECD_FLOOR:
            cx = randint(6, self.width - 16)
            cy = randint(8, self.height - 10)
            self._stamp([
                '###..###..###',
                'wwwwwwwwwwwww',
                'wwwwwwwwwwwww',
                '###..###..###',
            ], cx, cy, occupied=occupied)
            nx, ny = self._find_free_tile(cx + 6, cy + 1, entities)
            entities.append(Entity(nx, ny, 'npc_aecd', (140, 120, 80), 'AECD Officer',
                                   blocks=True, render_order=RenderOrder.ACTOR,
                                   npc_id='aecd'))
            # The Officer HOLDS the confiscated neuralyzer; the player must
            # bribe it out of them (see functions/dialogue.py).
        if level in ROADHOUSE_FLOORS:
            rx = randint(6, self.width - 16)
            ry = randint(6, self.height - 12)
            self._stamp([
                '.########.',
                '#wwwwwwww#',
                '#wwwwwwww#',
                '#wwwwwwww#',
                '.###..###.',
            ], rx, ry, occupied=occupied)
            nx, ny = self._find_free_tile(rx + 5, ry + 2, entities)
            entities.append(Entity(nx, ny, 'npc_swaggie', (160, 90, 60), 'Swaggie',
                                   blocks=True, render_order=RenderOrder.ACTOR,
                                   npc_id='swaggie'))

    def _place_brush(self, entities):
        """Scatter sight-blocking scrub in small CLUSTERS on open ground.
        Clustered scrub (rather than independent 1-in-N tiles) keeps the
        shadowcast FOV readable: a lone 1x1 bush used to carve jagged
        blind spots mid-room, a clump reads as a deliberate thicket."""
        if self.dungeon_level <= 5:
            density = 15
        elif self.dungeon_level <= 10:
            density = 10
        elif self.dungeon_level <= 15:
            density = 5
        else:
            density = 2
        w, h = self.width, self.height
        occupied = {(e.x, e.y) for e in entities}
        # Cluster count scaled by the per-floor density, seeded from it so
        # higher density = more, larger thickets.
        clusters = max(1, (density * w * h) // 9000)
        for _ in range(clusters):
            cx = randint(4, w - 5)
            cy = randint(4, h - 5)
            size = randint(2, max(2, density // 4))
            for _ in range(size):
                x = cx + randint(-2, 2)
                y = cy + randint(-2, 2)
                idx = self.idx(x, y)
                if self.blocked[idx] == 0 and (x, y) not in occupied:
                    self.brush[idx] = 1
                    self.block_sight[idx] = 1

    def place_entities(self, player, entities):
        """Scatter monsters/items on random reachable free tiles with a
        minimum distance from the player and from each other."""
        level = self.dungeon_level
        max_monsters = from_dungeon_level([[4, 1], [6, 4], [8, 7], [10, 10], [12, 14]], level)
        min_monsters = from_dungeon_level([[2, 1], [4, 4], [6, 7], [8, 10], [10, 14]], level)
        max_items = from_dungeon_level([[3, 1], [5, 4], [7, 8]], level)
        number_of_monsters = randint(min_monsters, max_monsters)
        number_of_items = randint(1, max_items)
        monster_chances = {name: from_dungeon_level(table, level)
                           for name, table in MONSTER_TABLES.items()}
        item_chances = {name: from_dungeon_level(table, level)
                        for name, table in ITEM_TABLES.items()}
        seen = self._flood(player.x, player.y)
        free = []
        for y in range(self.height):
            for x in range(self.width):
                i = self.idx(x, y)
                if not self.blocked[i] and seen[i] and \
                        not any(e.x == x and e.y == y for e in entities):
                    free.append((x, y))
        shuffle(free)

        placed = []
        for (x, y) in free:
            if len(placed) >= number_of_monsters:
                break
            if abs(x - player.x) + abs(y - player.y) < 10:
                continue
            if any(abs(x - px) + abs(y - py) < 4 for (px, py) in placed):
                continue
            choice = random_choice_from_dict(monster_chances)
            monster = create_monster(choice, level, x, y)
            # Emu War memorial floor: the emus spawn pre-aggro'd toward the
            # player, out of principle.
            if self.emu_war_memorial and choice == 'emu':
                monster.ai.last_seen = (player.x, player.y)
                monster.ai.state = HUNT
            entities.append(monster)
            placed.append((x, y))

        placed = []
        for (x, y) in free:
            if len(placed) >= number_of_items:
                break
            if abs(x - player.x) + abs(y - player.y) < 4:
                continue
            if any(abs(x - px) + abs(y - py) < 2 for (px, py) in placed):
                continue
            choice = random_choice_from_dict(item_chances)
            entities.append(create_item(choice, level, x, y))
            placed.append((x, y))

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

        # The crashed ship on the surface (floor 1), plus the black box
        # lying beside it.
        if self.dungeon_level == 1:
            sx, sy = self._find_free_tile(last_x, last_y + 1, entities)
            ship = Entity(sx, sy, 'ship', C.SILVER, 'Your crashed ship',
                          render_order=RenderOrder.SHIP, ship=True)
            entities.append(ship)
            bx, by = self._find_free_tile(sx + 1, sy + 1, entities)
            entities.append(create_item('black_box', 1, bx, by))

        # The mystery trail to floor 4.5 (very rare, fixed to the first
        # part floor so it can only be found once per generation).
        if self.dungeon_level == 5 and randint(1, 100) <= 20:
            tx, ty = self._find_free_tile(first_x, first_y + 2, entities)
            mystery = Entity(tx, ty, 'trail_down', (190, 80, 200),
                             'Mysterious trail',
                             render_order=RenderOrder.TRAIL,
                             trail=Trail(direction='down', floor=POCKET_FLOOR))
            entities.append(mystery)

        # Salvageable ship part (wreckage) on the part floors.
        if self.dungeon_level in PART_FLOORS:
            part_id = next(pid for pid, (_, floor) in SHIP_PARTS.items() if floor == self.dungeon_level)
            part_name = SHIP_PARTS[part_id][0]
            px, py = self._find_free_tile(last_x, last_y - 1, entities)
            part = Entity(px, py, 'part', PART_COLORS[part_id], part_name,
                          render_order=RenderOrder.PART, part_id=part_id)
            entities.append(part)

    # ------------------------------------------------------------ transitions
    def go_down(self, player, message_log, constants, floor=None):
        """Descend. ``floor`` comes from the trail being used (so the
        mystery trail can dive to the 4.5 pocket); default is +1."""
        target = floor if floor is not None else self.dungeon_level + 1
        if target == POCKET_FLOOR:
            return self._enter_pocket(player, message_log, constants)
        self.dungeon_level = target
        from loader_functions.initialize_new_game import biome_for_level
        constants.setdefault('colors', {}).update(biome_for_level(self.dungeon_level))
        entities = self._new_level(player, message_log, constants, start_at='first', heal=True)
        message_log.add_message(Message('You take the trail and descend into the darkness.', C.LIGHT_VIOLET))
        return entities

    def go_up(self, player, message_log, constants, floor=None):
        """Ascend. ``floor`` comes from the trail (the pocket's exit trail
        returns to floor 5); default is -1."""
        target = floor if floor is not None else self.dungeon_level - 1
        self.dungeon_level = target
        from loader_functions.initialize_new_game import biome_for_level
        constants.setdefault('colors', {}).update(biome_for_level(self.dungeon_level))
        entities = self._new_level(player, message_log, constants, start_at='last', heal=False)
        message_log.add_message(Message('You climb back toward the surface.', C.LIGHT_GREEN))
        return entities

    def _enter_pocket(self, player, message_log, constants):
        """Floor 4.5: a tiny pocket dimension of magenta unknown tiles
        holding exactly one item -- the developer's mug. The renderer
        paints every tile with the unknown sprite while ``is_pocket``."""
        entities = [player]
        self.is_pocket = True
        w, h = 24, 18
        self.width, self.height = w, h
        self.blocked = bytearray([0]) * (w * h)
        self.block_sight = bytearray([0]) * (w * h)
        self.explored = bytearray(w * h)
        self.brush = bytearray(w * h)
        self.version += 1
        cx, cy = w // 2, h // 2
        player.x, player.y = cx, cy
        mug_x, mug_y = self._find_free_tile(cx + 5, cy, entities)
        entities.append(create_item('dev_mug', 4, mug_x, mug_y))
        up_x, up_y = self._find_free_tile(cx - 5, cy, entities)
        up_trail = Entity(up_x, up_y, 'trail_up', TRAIL_UP_COLOR, 'Trail back',
                          render_order=RenderOrder.TRAIL,
                          trail=Trail(direction='up', floor=5))
        entities.append(up_trail)
        message_log.add_message(Message(
            'You push through a curtain of scrub into a space that should not exist.',
            C.LIGHT_VIOLET))
        return entities

    def _new_level(self, player, message_log, constants, start_at='first', heal=True):
        entities = [player]
        # Restore the standard map dimensions (the pocket floor shrinks the
        # map; leaving it must grow it back) and reset per-floor egg state.
        self.width = constants['map_width']
        self.height = constants['map_height']
        self.is_pocket = False
        self.land_dispute = False
        self.swooping = False
        self.emu_war_memorial = False
        self.blocked = bytearray([1]) * (self.width * self.height)
        self.block_sight = bytearray([1]) * (self.width * self.height)
        self.explored = bytearray(self.width * self.height)
        self.brush = bytearray(self.width * self.height)
        self.version += 1
        self.make_map(constants['map_width'], constants['map_height'],
                      player, entities, start_at=start_at)
        if heal:
            player.fighter.heal(player.fighter.max_hp // 2)
            message_log.add_message(Message('You take a moment to rest and recover your strength.', C.LIGHT_VIOLET))
        return entities
