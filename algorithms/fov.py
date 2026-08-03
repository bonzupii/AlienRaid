#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Field of view: pure-Python recursive shadowcasting operating on a flat
``bytearray`` of size ``width * height`` (index = ``x + y * width``).

API::

    compute_fov(blocked, width, height, x, y, radius, light_walls=True)
        -> bytearray   # 1 == visible

``blocked`` must be a bytearray-like where a non-zero value means the tile
blocks sight (walls).
"""

# Octant multipliers: (xx, xy, yx, yy) for each of the 8 octants.
_MULT = [
    (1, 0, 0, 1),
    (0, 1, 1, 0),
    (0, -1, 1, 0),
    (-1, 0, 0, 1),
    (-1, 0, 0, -1),
    (0, -1, -1, 0),
    (0, 1, -1, 0),
    (1, 0, 0, -1),
]


def compute_fov(blocked, width, height, x, y, radius, light_walls=True):
    """Return a ``bytearray`` with 1 for every tile visible from (x, y).

    ``blocked`` is a flat bytearray (1 == blocks sight). Out-of-bounds tiles
    behave as walls. The origin tile is always visible.
    """
    visible = bytearray(width * height)

    def set_lit(tx, ty):
        if 0 <= tx < width and 0 <= ty < height:
            visible[ty * width + tx] = 1

    def is_wall(tx, ty):
        if 0 <= tx < width and 0 <= ty < height:
            return blocked[ty * width + tx] != 0
        return True  # out of bounds behaves like a wall

    set_lit(x, y)

    for (xx, xy, yx, yy) in _MULT:
        _cast_light(set_lit, is_wall, width, height, x, y, radius, 1, 1.0, 0.0,
                    xx, xy, yx, yy, light_walls)

    return visible


def _cast_light(set_lit, is_wall, width, height, cx, cy, radius, row,
                start, end, xx, xy, yx, yy, light_walls):
    if start < end:
        return

    radius_squared = radius * radius

    for j in range(row, radius + 1):
        dx, dy = -j - 1, -j
        blocked = False

        while dx <= 0:
            dx += 1
            tx = cx + dx * xx + dy * xy
            ty = cy + dx * yx + dy * yy

            l_slope = (dx - 0.5) / (dy + 0.5)
            r_slope = (dx + 0.5) / (dy - 0.5)

            if start < r_slope:
                continue
            elif end > l_slope:
                break
            else:
                if dx * dx + dy * dy <= radius_squared:
                    if light_walls or not is_wall(tx, ty):
                        set_lit(tx, ty)

                if blocked:
                    if is_wall(tx, ty):
                        new_start = r_slope
                        continue
                    else:
                        blocked = False
                        start = new_start
                else:
                    if is_wall(tx, ty) and j < radius:
                        blocked = True
                        _cast_light(set_lit, is_wall, width, height, cx, cy,
                                    radius, j + 1, start, l_slope,
                                    xx, xy, yx, yy, light_walls)
                        new_start = r_slope

        if blocked:
            break
