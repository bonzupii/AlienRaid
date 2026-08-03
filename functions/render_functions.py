#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render helpers (no libtcod). RenderOrder lives in functions.render_order."""

from functions.render_order import RenderOrder  # noqa: F401  (re-export)

from algorithms.fov import compute_fov  # noqa: F401  (convenience re-export)


def get_names_under_mouse(mouse_tile, entities, fov_map, game_map):
    """Names of visible entities at the tile under the mouse cursor."""
    (x, y) = mouse_tile
    names = [entity.name for entity in entities
             if entity.x == x and entity.y == y and _visible(fov_map, game_map, entity)]
    names = ', '.join(names)
    return names.capitalize()


def _visible(fov_map, game_map, entity):
    if not (0 <= entity.x < game_map.width and 0 <= entity.y < game_map.height):
        return False
    return fov_map[entity.y * game_map.width + entity.x] != 0
