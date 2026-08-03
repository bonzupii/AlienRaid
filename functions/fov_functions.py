#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FOV helpers: thin wrappers over the pure-Python shadowcasting in
``algorithms.fov`` (kept for compatibility; no libtcod)."""

from algorithms.fov import compute_fov


def initialize_fov(game_map):
    """Return the current FOV bytearray from the player's perspective."""
    return bytearray(game_map.width * game_map.height)


def recompute_fov(game_map, x, y, radius, light_walls=True):
    """Compute FOV from (x, y) over the map's block_sight array."""
    return compute_fov(game_map.block_sight, game_map.width, game_map.height,
                       x, y, radius, light_walls)
