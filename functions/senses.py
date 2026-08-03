#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Noise system: monsters with HEARING can react to events outside their FOV.

Events (grenades, the didgeridoo, ...) emit a noise ring with a radius and
intensity that decays with distance. Every enemy turn the launcher clears the
map, then each monster with ``HEARING`` checks whether it stands inside a
noise ring and, if so, paths toward the loudest source instead of standing
dormant.
"""


class NoiseMap:
    """Per-turn noise events with a distance-decayed intensity field."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.noise = bytearray(width * height)  # intensity at each tile
        self.sources = []  # [(x, y, radius, kind)]

    def idx(self, x, y):
        return x + y * self.width

    def emit(self, x, y, radius, kind='generic'):
        """Emit a noise event at (x, y) with the given radius."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        self.sources.append((x, y, radius, kind))
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    dist = abs(dx) + abs(dy)  # Manhattan distance
                    if dist <= radius:
                        intensity = max(1, radius - dist)
                        idx = self.idx(nx, ny)
                        if intensity > self.noise[idx]:
                            self.noise[idx] = intensity

    def get_noise_at(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return 0
        return self.noise[self.idx(x, y)]

    def find_strongest_noise(self):
        """Return (x, y, intensity) of the loudest tile, or None."""
        max_intensity = 0
        best = None
        for y in range(self.height):
            base = y * self.width
            for x in range(self.width):
                intensity = self.noise[base + x]
                if intensity > max_intensity:
                    max_intensity = intensity
                    best = (x, y, intensity)
        return best

    def clear(self):
        """Reset for the next player turn (noise lasts one turn)."""
        self.noise = bytearray(self.width * self.height)
        self.sources.clear()
