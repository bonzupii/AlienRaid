#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procedural menu background (Phase A).

Replaces menu_background.png entirely -- the game never loads that file at
runtime. The art is loosely based on the old reference image: a dark
outback night vista with an alien-green face-glow, red dirt bands, dune
silhouettes, a low sun, scattered scrub and a star field.

Returns a 24/32-bit surface (an 8-bit surface would crash smoothscale).
Generated once at boot.
"""
import math
import random

import pygame

from renderer.palette import shade


def generate_menu_background(frame_w, frame_h):
    surface = pygame.Surface((frame_w, frame_h))
    rng = random.Random(20260803)

    # --- sky: deep red-violet gradient bands -------------------------------
    bands = [(8, 6, 10), (14, 8, 14), (24, 10, 16), (40, 14, 18),
             (66, 22, 20), (96, 34, 22), (128, 52, 26)]
    band_h = max(1, frame_h // len(bands))
    for i, color in enumerate(bands):
        pygame.draw.rect(surface, color,
                         (0, i * band_h, frame_w, band_h + 1))

    # --- star field ---------------------------------------------------------
    for i in range(220):
        x = rng.randint(0, frame_w - 1)
        y = rng.randint(0, int(frame_h * 0.55))
        b = rng.randint(60, 220)
        surface.set_at((x, y), (b, b, min(255, b + 30)))

    # --- setting sun disc ----------------------------------------------------
    sun_x = int(frame_w * 0.72)
    sun_y = int(frame_h * 0.62)
    for r, alpha in ((110, 26), (80, 40), (56, 90)):
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 120, 40, alpha), (r, r), r)
        surface.blit(glow, (sun_x - r, sun_y - r))
    pygame.draw.circle(surface, (255, 170, 80), (sun_x, sun_y), 42)
    pygame.draw.circle(surface, (255, 220, 150), (sun_x - 8, sun_y - 8), 20)

    # --- dune silhouettes -----------------------------------------------------
    horizon = int(frame_h * 0.66)
    dune_color = (30, 12, 10)
    pts = [(0, horizon + 30)]
    x = 0
    while x < frame_w:
        x += rng.randint(60, 160)
        pts.append((min(x, frame_w), horizon + rng.randint(-26, 26)))
    pts += [(frame_w, frame_h), (0, frame_h)]
    pygame.draw.polygon(surface, dune_color, pts)
    dune2 = [(0, horizon + 70)]
    x = 0
    while x < frame_w:
        x += rng.randint(80, 200)
        dune2.append((min(x, frame_w), horizon + 70 + rng.randint(-18, 30)))
    dune2 += [(frame_w, frame_h), (0, frame_h)]
    pygame.draw.polygon(surface, shade(dune_color, 0.6), dune2)

    # --- red-dirt foreground bands ---------------------------------------------
    for i in range(4):
        y0 = horizon + 90 + i * ((frame_h - horizon - 90) // 4)
        c = shade((120, 46, 20), 0.5 + i * 0.14)
        pygame.draw.rect(surface, c, (0, y0, frame_w, frame_h - y0))

    # --- scattered brush / termite mound hints ----------------------------------
    for i in range(60):
        x = rng.randint(0, frame_w - 6)
        y = rng.randint(horizon + 40, frame_h - 4)
        c = shade((90, 60, 25), rng.uniform(0.4, 0.9))
        w = rng.randint(2, 6)
        h = rng.randint(2, 5)
        pygame.draw.rect(surface, c, (x, y, w, h))
    for i in range(5):
        x = rng.randint(20, frame_w - 20)
        y = rng.randint(horizon + 60, frame_h - 10)
        h = rng.randint(10, 26)
        pygame.draw.polygon(surface, (52, 34, 22),
                            [(x, y), (x + h // 3, y - h), (x + 2 * h // 3, y)])

    # --- faint alien-green glow (the old cover's face-glow) ----------------------
    gx, gy = int(frame_w * 0.30), int(frame_h * 0.30)
    for r in range(220, 0, -10):
        alpha = int(26 * (1 - r / 220.0)) + 4
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (60, 220, 120, alpha), (r, r), r)
        surface.blit(glow, (gx - r, gy - r))
    # two faint eye glints
    for ex in (gx - 46, gx + 46):
        pygame.draw.circle(surface, (140, 255, 170), (ex, gy - 10), 5)
        halo = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(halo, (140, 255, 170, 60), (20, 20), 20)
        surface.blit(halo, (ex - 20, gy - 30))
    # radiating scratch lines like the reference art
    for i in range(26):
        ang = rng.uniform(0, 2 * math.pi)
        length = rng.randint(60, 260)
        x2 = gx + int(math.cos(ang) * length)
        y2 = gy + int(math.sin(ang) * length * 0.5)
        pygame.draw.line(surface, (30, 90, 50), (gx, gy), (x2, y2), 1)

    return surface.convert() if surface.get_bitsize() >= 24 else surface.convert_alpha()
