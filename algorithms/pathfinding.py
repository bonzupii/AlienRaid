#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pathfinding: pure-Python A* using ``heapq``, operating on a flat
``bytearray`` of size ``width * height`` (index = ``x + y * width``).

API::

    astar_path(blocked, width, height, start, goal, block_extra=None,
               max_steps=2000) -> list[tuple[int, int]] | None

``blocked`` is a flat bytearray (1 == unwalkable terrain). ``block_extra``
optionally marks extra (x, y) positions as blocked (e.g. other monsters).
The returned path includes both endpoints.
"""

import heapq

# Precomputed 8-neighbour offsets: orthogonal first, then diagonals.
_NEIGHBORS = (
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (1, -1), (-1, 1), (1, 1),
)
_DIAG = 1.41421356
_SQRT2_MINUS_1 = 0.41421356


def astar_path(blocked, width, height, start, goal,
               block_extra=None, max_steps=2000):
    """Return the A* path from ``start`` to ``goal`` (both inclusive), or
    ``None`` if unreachable. Exits early once the search space is exhausted
    or ``max_steps`` nodes are closed (guards against pathological maps)."""
    sx, sy = start
    gx, gy = goal

    if not (0 <= gx < width and 0 <= gy < height):
        return None
    if blocked[gy * width + gx]:
        return None

    # g / f scores keyed by (x, y) are stored in flat lists to keep memory
    # churn low; the frontier still uses a heap.
    g_score = {(sx, sy): 0.0}
    came_from = {}

    def heuristic(px, py):
        dx = abs(px - gx)
        dy = abs(py - gy)
        # Octile distance (admissible for 8-directional movement).
        return (dx + dy) + _SQRT2_MINUS_1 * min(dx, dy)

    frontier = [(heuristic(sx, sy), 0, sx, sy)]
    counter = 1
    closed = 0
    closed_set = set()

    while frontier:
        _, _, x, y = heapq.heappop(frontier)
        if (x, y) == (gx, gy):
            return _reconstruct(came_from, start, (gx, gy))

        if (x, y) in closed_set:
            continue  # stale heap entry
        closed_set.add((x, y))

        closed += 1
        if closed > max_steps:
            return None

        for dx, dy in _NEIGHBORS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if blocked[ny * width + nx]:
                continue
            if block_extra and (nx, ny) in block_extra:
                continue

            step = _DIAG if dx and dy else 1.0
            tentative = g_score[(x, y)] + step
            if tentative < g_score.get((nx, ny), float('inf')):
                came_from[(nx, ny)] = (x, y)
                g_score[(nx, ny)] = tentative
                heapq.heappush(
                    frontier, (tentative + heuristic(nx, ny), counter, nx, ny))
                counter += 1

    return None


def _reconstruct(came_from, start, goal):
    path = [goal]
    node = goal
    while node != start:
        node = came_from.get(node)
        if node is None:
            return None
        path.append(node)
    path.reverse()
    return path
