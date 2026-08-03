#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procedural menu background (Phase A, v2 -- the ghost-face edition).

Replaces menu_background.png entirely -- the game never loads that file at
runtime. A near-black green field with a stippled alien face on the right
(two glowing eyes), horizontal scratch-streaks raking left, and a soft CRT
scanline/vignette -- the mood of the old cover, no dunes, no sun.

Returns a 24/32-bit surface (an 8-bit surface would crash smoothscale).
Generated once at boot.
"""
import math
import random

import pygame

from renderer.palette import shade


def _face_ink(u, v):
    """Green-ink intensity (0..1) at normalized face coords (u, v in
    [-1, 1]); layered symmetric feature fields read as a portrait."""
    r = math.hypot(u, v)
    if r > 1.0:
        return 0.0
    ink = 0.55 * max(0.0, 1.0 - abs(r - 0.92) / 0.10)   # skull contour
    ink = max(ink, 0.10 * (1.0 - r))                    # faint inner fill
    if -0.80 < v < -0.30 and abs(u) < 0.55:             # forehead plate
        ink = max(ink, 0.50 * (1.0 - abs(u) / 0.55))
    for s in (-1, 1):
        du = abs(u - s * 0.40)
        if du < 0.28 and -0.36 < v < -0.20:             # brow ridge
            ink = max(ink, 0.65 * (1.0 - du / 0.28))
        if ((u - s * 0.40) ** 2) / 0.055 + ((v + 0.02) ** 2) / 0.02 < 1.0:
            ink *= 0.25                                 # socket carve
        if math.hypot((u - s * 0.40) / 0.10, (v + 0.02) / 0.07) < 1.0:
            ink = 1.0                                   # eye core
    if abs(u) < 0.07 and -0.10 < v < 0.42:              # nose ridge
        ink = max(ink, 0.45)
    if math.hypot(abs(u) - 0.13, v - 0.44) < 0.06:      # nostrils
        ink = max(ink, 0.50)
    if abs(u) < 0.30 and 0.60 < v < 0.68:               # mouth line
        ink = max(ink, 0.35)
    if abs(u) < 0.22 and 0.72 < v < 0.78:               # lower lip
        ink = max(ink, 0.45)
    if math.hypot((abs(u) - 0.62) / 0.18, (v - 0.25) / 0.30) < 1.0:
        ink = max(ink, 0.30)                            # cheekbone
    return min(1.0, ink)


def _stipple_face(surface, rng, cx, cy, rx, ry):
    """Sample the face field into jittered 1px green dots (dot-matrix
    portrait, like the reference cover)."""
    w, h = surface.get_size()
    for gy in range(-ry, ry, 3):
        v = gy / float(ry)
        for gx in range(-rx, rx, 3):
            ink = _face_ink(gx / float(rx), v)
            if ink <= 0.03 or rng.random() > 0.08 + ink * 0.85:
                continue
            x = cx + gx + rng.randint(-1, 1)
            y = cy + gy + rng.randint(-1, 1)
            if 0 <= x < w and 0 <= y < h:
                g = 60 + int(195 * ink)
                col = (g // 4, g, g // 2)
                surface.set_at((x, y), col)
                if ink > 0.55 and rng.random() < 0.4 and x + 1 < w:
                    surface.set_at((x + 1, y), shade(col, 0.6))


def _eye_glow(surface, cx, cy, rx, ry):
    for s in (-1, 1):
        ex = int(cx + s * 0.40 * rx)
        ey = int(cy - 0.02 * ry)
        for r, a in ((52, 18), (34, 34), (18, 80), (9, 150)):
            halo = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo, (140, 255, 170, a), (r, r), r)
            surface.blit(halo, (ex - r, ey - r))
        pygame.draw.circle(surface, (225, 255, 230), (ex, ey), 4)
        flare = pygame.Surface((260, 7), pygame.SRCALPHA)
        for x in range(260):
            a = int(110 * (1 - abs(x - 130) / 130.0))
            flare.fill((160, 255, 190, a), (x, 0, 1, 7))
        surface.blit(flare, (ex - 130, ey - 3))


def _streaks(surface, rng, cx, cy, rx, ry, frame_w, frame_h):
    """Horizontal scratch lines raking left from the face, plus a few
    short right-side scratches."""
    ov = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
    for i in range(170):
        y = int(cy + rng.gauss(0.0, ry * 0.55))
        if not 0 <= y < frame_h:
            continue
        x1 = cx - int(rng.uniform(0.1, 1.0) * rx)
        x0 = max(0, x1 - int(rng.uniform(60, frame_w * 0.8)))
        g = rng.randint(110, 235)
        pygame.draw.line(ov, (g // 4, g, g // 2, rng.randint(14, 80)),
                         (x0, y), (x1, y), 1)
    for i in range(26):
        y = int(cy + rng.gauss(0.0, ry * 0.5))
        if not 0 <= y < frame_h:
            continue
        x0 = cx + int(rng.uniform(0.9, 1.2) * rx)
        x1 = min(frame_w - 1, x0 + rng.randint(20, 160))
        g = rng.randint(90, 200)
        pygame.draw.line(ov, (g // 4, g, g // 2, rng.randint(12, 50)),
                         (x0, y), (x1, y), 1)
    surface.blit(ov, (0, 0))


def _specks(surface, rng, cx, cy, rx, ry, frame_w, frame_h):
    for i in range(1400):
        x = rng.randrange(frame_w)
        y = rng.randrange(frame_h)
        near = math.hypot((x - cx) / (rx * 2.2), (y - cy) / (ry * 1.6)) < 1.0
        if near or rng.random() < 0.25:
            g = rng.randint(50, 190) if near else rng.randint(30, 90)
            surface.set_at((x, y), (g // 4, g, g // 2))


def _crt(surface, frame_w, frame_h):
    ov = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
    for y in range(0, frame_h, 3):                      # scanlines
        pygame.draw.line(ov, (0, 0, 0, 22), (0, y), (frame_w, y), 1)
    for i in range(0, min(frame_w, frame_h) // 2, 2):   # vignette
        a = max(0, 46 - i // 4)
        if a == 0:
            break
        pygame.draw.rect(ov, (0, 0, 0, a),
                         (i, i, frame_w - 2 * i, frame_h - 2 * i), 1)
    surface.blit(ov, (0, 0))


def generate_menu_background(frame_w, frame_h):
    surface = pygame.Surface((frame_w, frame_h))
    rng = random.Random(0xA11E)
    for y in range(frame_h):  # near-black, green-tinted, brighter mid-band
        t = math.sin(math.pi * y / float(frame_h))
        pygame.draw.line(surface,
                         (2 + int(5 * t), 4 + int(9 * t), 3 + int(6 * t)),
                         (0, y), (frame_w, y), 1)
    cx, cy = int(frame_w * 0.68), int(frame_h * 0.44)
    rx, ry = int(frame_w * 0.11), int(frame_h * 0.30)
    for rw, rh, a in ((rx * 6, ry * 4, 10), (rx * 4, ry * 2.6, 12),
                      (rx * 2.4, ry * 1.6, 14)):
        amb = pygame.Surface((int(rw) * 2, int(rh) * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(amb, (30, 90, 50, a), amb.get_rect())
        surface.blit(amb, (cx - int(rw), cy - int(rh)))
    _stipple_face(surface, rng, cx, cy, rx, ry)
    _eye_glow(surface, cx, cy, rx, ry)
    _streaks(surface, rng, cx, cy, rx, ry, frame_w, frame_h)
    _specks(surface, rng, cx, cy, rx, ry, frame_w, frame_h)
    _crt(surface, frame_w, frame_h)
    return surface
