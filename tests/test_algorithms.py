#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for algorithms/ (pure stdlib, no pygame required)."""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from algorithms.fov import compute_fov
from algorithms.pathfinding import astar_path


class TestFov(unittest.TestCase):
    def test_origin_visible_and_radius(self):
        w, h = 41, 41
        blocked = bytearray(w * h)
        vis = compute_fov(blocked, w, h, 20, 20, 5)
        self.assertEqual(vis[20 * w + 20], 1)
        # Distance ~7 straight east is outside radius 5.
        self.assertEqual(vis[20 * w + 27], 0)
        # Edge of radius is visible.
        self.assertEqual(vis[20 * w + 25], 1)

    def test_wall_blocks_sight(self):
        w, h = 41, 41
        blocked = bytearray(w * h)
        # Vertical wall at x=25, y in [18, 22]
        for y in range(18, 23):
            blocked[y * w + 25] = 1
        vis = compute_fov(blocked, w, h, 20, 20, 10)
        self.assertEqual(vis[20 * w + 24], 1)   # just before wall
        self.assertEqual(vis[20 * w + 26], 0)   # just behind wall
        # light_walls=True marks the wall tile itself visible.
        self.assertEqual(vis[20 * w + 25], 1)
        vis2 = compute_fov(blocked, w, h, 20, 20, 10, light_walls=False)
        self.assertEqual(vis2[20 * w + 25], 0)

    def test_open_plane_symmetric_disk(self):
        w, h = 41, 41
        blocked = bytearray(w * h)
        vis = compute_fov(blocked, w, h, 20, 20, 3)
        self.assertEqual(vis[20 * w + 23], 1)  # east 3 (edge of disk)
        self.assertEqual(vis[23 * w + 20], 1)  # south 3
        self.assertEqual(vis[22 * w + 22], 1)  # diagonal at distance sqrt(8)
        self.assertEqual(vis[23 * w + 23], 0)  # diagonal sqrt(18) > radius
        self.assertEqual(vis[20 * w + 24], 0)  # beyond radius


class TestAstar(unittest.TestCase):
    def setUp(self):
        self.w, self.h = 10, 10
        self.blocked = bytearray(self.w * self.h)

    def test_straight_line(self):
        path = astar_path(self.blocked, self.w, self.h, (0, 0), (4, 0))
        self.assertEqual(path, [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)])

    def test_diagonal_shortcut(self):
        path = astar_path(self.blocked, self.w, self.h, (0, 0), (2, 2))
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (2, 2))
        self.assertLessEqual(len(path), 3)

    def test_wall_detour(self):
        # Vertical wall with a gap at the top row (y=0).
        for y in range(1, self.h):
            self.blocked[y * self.w + 5] = 1
        path = astar_path(self.blocked, self.w, self.h, (0, 5), (9, 5))
        self.assertIsNotNone(path)
        self.assertEqual(path[0], (0, 5))
        self.assertEqual(path[-1], (9, 5))
        for (x, y) in path:
            self.assertFalse(x == 5 and y >= 1)  # never walks through the wall

    def test_unreachable_returns_none(self):
        for y in range(self.h):
            for x in range(0, 5):
                self.blocked[y * self.w + x] = 1
        self.assertIsNone(astar_path(self.blocked, self.w, self.h, (0, 0), (9, 9)))

    def test_block_extra(self):
        blocked_entities = {(2, 0), (3, 0), (1, 1), (1, -1) if False else (1, 0)}
        path = astar_path(self.blocked, self.w, self.h, (0, 0), (4, 0),
                          block_extra=blocked_entities)
        self.assertIsNotNone(path)
        for (x, y) in path:
            self.assertNotIn((x, y), blocked_entities)

    def test_goal_blocked_returns_none(self):
        self.blocked[0 * self.w + 4] = 1
        self.assertIsNone(astar_path(self.blocked, self.w, self.h, (0, 0), (4, 0)))


if __name__ == '__main__':
    unittest.main()
