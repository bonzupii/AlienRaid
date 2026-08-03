#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entity: a generic map object (player, monsters, items, trails, the ship).
All rendering is procedural via ``sprite_id``; there are no font characters
for entities anymore."""

import math

from components.item import Item
from functions.render_order import RenderOrder
from algorithms.pathfinding import astar_path


class Entity:
    def __init__(self, x, y, sprite_id, color, name, blocks=False,
                 render_order=RenderOrder.CORPSE, fighter=None, ai=None,
                 item=None, inventory=None, trail=None, level=None,
                 equipment=None, equippable=None, part_id=None, ship=False,
                 quest=None, reputation=None, npc_id=None):
        self.x = x
        self.y = y
        self.sprite_id = sprite_id
        self.color = color
        self.name = name
        self.blocks = blocks
        self.render_order = render_order
        self.fighter = fighter
        self.ai = ai
        self.item = item
        self.inventory = inventory
        self.trail = trail
        self.level = level
        self.equipment = equipment
        self.equippable = equippable
        self.part_id = part_id
        self.ship = ship
        self.quest = quest
        self.reputation = reputation
        self.npc_id = npc_id

        if self.fighter:
            self.fighter.owner = self
        if self.ai:
            self.ai.owner = self
        if self.item:
            self.item.owner = self
        if self.inventory:
            self.inventory.owner = self
        if self.trail:
            self.trail.owner = self
        if self.level:
            self.level.owner = self
        if self.equipment:
            self.equipment.owner = self
        if self.equippable:
            self.equippable.owner = self
            if not self.item:
                item = Item()
                self.item = item
                self.item.owner = self

        if self.quest:
            self.quest.owner = self

        if self.reputation:
            self.reputation.owner = self

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def move_towards(self, target_x, target_y, game_map, entities):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance == 0:
            return
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))

        if not (game_map.is_blocked(self.x + dx, self.y + dy) or
                get_blocking_entities_at_location(entities, self.x + dx, self.y + dy)):
            self.move(dx, dy)

    def move_astar(self, target, entities, game_map):
        """Pure-Python A* toward ``target``. Returns True if it moved."""
        block_extra = set()
        for entity in entities:
            if entity.blocks and entity is not self and entity is not target:
                block_extra.add((entity.x, entity.y))

        path = astar_path(game_map.blocked, game_map.width, game_map.height,
                          (self.x, self.y), (target.x, target.y),
                          block_extra=block_extra, max_steps=3000)

        if path and 1 < len(path) <= 25:
            nx, ny = path[1]
            self.x, self.y = nx, ny
            return True

        # Fallback: straight-line approach if no path is found.
        self.move_towards(target.x, target.y, game_map, entities)
        return False

    def distance(self, x, y):
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)


def get_blocking_entities_at_location(entities, destination_x, destination_y):
    for entity in entities:
        if entity.blocks and entity.x == destination_x and entity.y == destination_y:
            return entity
    return None
