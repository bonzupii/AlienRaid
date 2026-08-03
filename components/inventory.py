#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventory (no libtcod)."""

from components.game_messages import Message
from renderer import palette as C


class Inventory:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = []

    def add_item(self, item):
        results = []
        if len(self.items) >= self.capacity:
            results.append({
                'item_added': None,
                'message': Message('You cannot carry any more, your inventory is full', C.YELLOW)
            })
        else:
            results.append({
                'item_added': item,
                'message': Message('You pick up the {0}!'.format(item.name), C.BLUE)
            })
            self.items.append(item)
        return results

    def use(self, item_entity, **kwargs):
        results = []
        item_component = item_entity.item

        if item_component.use_function is None:
            equippable_component = item_entity.equippable
            if equippable_component:
                results.append({'equip': item_entity})
            else:
                results.append({'message': Message('The {0} cannot be used'.format(item_entity.name), C.YELLOW)})
        else:
            if item_component.targeting and not (kwargs.get('target_x') or kwargs.get('target_y')):
                results.append({'targeting': item_entity})
            else:
                kwargs = {**item_component.function_kwargs, **kwargs}
                item_use_results = item_component.use_function(self.owner, **kwargs)

                for item_use_result in item_use_results:
                    if item_use_result.get('consumed'):
                        self.remove_item(item_entity)
                results.extend(item_use_results)

        return results

    def remove_item(self, item):
        self.items.remove(item)

    def drop_item(self, item, game_map=None, entities=None):
        """Drop an item onto the map. If the player's tile is blocked by
        another creature, drop on the nearest adjacent free tile instead
        (Phase E drop UX)."""
        results = []
        equipment = self.owner.equipment
        equipped = (equipment.top_right_tentacle == item or equipment.top_left_tentacle == item or
                    equipment.bottom_right_tentacle == item or equipment.bottom_left_tentacle == item or
                    equipment.chest_plate == item or equipment.helmet == item or equipment.neck == item)
        if equipped:
            self.owner.equipment.toggle_equip(item)

        drop_x, drop_y = self.owner.x, self.owner.y
        if game_map and entities:
            blocked_here = any(e is not self.owner and e.blocks
                               and e.x == drop_x and e.y == drop_y for e in entities)
            if blocked_here:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = drop_x + dx, drop_y + dy
                        if (not game_map.is_blocked(nx, ny) and
                                not any(e.blocks and e.x == nx and e.y == ny for e in entities)):
                            drop_x, drop_y = nx, ny
                            break
                    else:
                        continue
                    break

        item.x = drop_x
        item.y = drop_y

        self.remove_item(item)
        results.append({'item_dropped': item,
                        'message': Message('You dropped the {0}'.format(item.name), C.YELLOW)})
        return results
