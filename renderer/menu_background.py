#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procedural menu background -- Phase A, v3 (pixel-art edition).

The v2 "vector" renderer (alpha halo circles, floating 1px dots, smooth
flares) read as janky.  This version renders the same composition as proper
pixel art instead:

  * the scene is painted into a tiny offscreen canvas (~120 rows tall, chunk
    size derived from the window height),
  * every shade comes from a fixed 13-step green palette,
  * gradients are ordered (Bayer) + noise dithered, so shading reads as
    deliberate pixel stipple -- the dot-matrix portrait of the old cover,
  * the tiny canvas is blown up nearest-neighbour, so every pixel is a fat
    crisp chunk.  No anti-aliasing, no alpha smearing.

Composition matches the reference cover: near-black green field, stippled
alien face on the right with two glowing eyes, scratch streaks and hair
spikes raking left, chunky scanlines + vignette.

Easter egg -- menu idle blink:
    leave the main menu untouched for ~3 minutes and the face's eyes blink
    once (half -> closed -> half).  any input resets the idle timer.

Integration:

    backdrop = menu_background.MenuBackdrop(W, H)     # once at boot
    ...
    backdrop.update(dt, events)                       # every frame
    screen.blit(backdrop.surface, (0, 0))

`generate_menu_background(w, h)` is kept for call sites that only want the
static frame (returns the eyes-open surface).
"""

import math
import random

import pygame

# ---------------------------------------------------------------- palette

PALETTE = (
    (2, 5, 3), (6, 12, 7), (11, 22, 12), (17, 34, 18),
    (24, 48, 26), (33, 66, 36), (45, 88, 48), (60, 112, 64),
    (80, 140, 86), (105, 170, 110), (140, 205, 145),
    (180, 235, 185), (225, 255, 228),
)

_BAYER4 = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)


def _hash01(x, y, seed):
    """Deterministic per-pixel noise in [0, 1)."""
    h = (x * 374761393 + y * 668265263 + seed * 1013904223) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65536.0


def _face_ink(u, v):
    """Green-ink intensity (0..1) at normalized face coords (u, v in
    [-1, 1]); layered symmetric feature fields read as a portrait.
    Eyes are NOT drawn here -- they live in _add_eyes so they can blink."""
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


class MenuBackdrop:
    """Owns the menu background surfaces + the idle-blink easter egg."""

    IDLE_BLINK_SECONDS = 180.0                    # ~3 minutes untouched
    _BLINK_SCRIPT = (("half", 0.06), ("closed", 0.12), ("half", 0.06))

    def __init__(self, frame_w, frame_h, seed=0xA11E):
        self.frame_size = (frame_w, frame_h)
        self.ps = max(3, frame_h // 120)          # chunky pixel size
        art_w = -(-frame_w // self.ps)
        art_h = -(-frame_h // self.ps)

        rng = random.Random(seed)
        field, geo = self._base_field(art_w, art_h, rng, seed)

        self.frames = {}
        for state in ("open", "half", "closed"):
            f = [row[:] for row in field]         # shared texture, new eyes
            self._add_eyes(f, geo, state)
            self._post(f, art_w, art_h)
            self.frames[state] = self._finish(f, art_w, art_h)

        self.surface = self.frames["open"]
        self.idle = 0.0
        self._script = []
        self._t = 0.0

    # ------------------------------------------------------------ painting

    @staticmethod
    def _base_field(w, h, rng, seed):
        cx, cy = w * 0.68, h * 0.44
        rx, ry = max(9.0, w * 0.11), h * 0.30
        field = [[0.0] * w for _ in range(h)]

        for y in range(h):                        # dark band + ambient glow
            band = 0.015 + 0.05 * math.sin(math.pi * y / h)
            for x in range(w):
                d = math.hypot((x - cx) / (rx * 3.0), (y - cy) / (ry * 1.9))
                field[y][x] = band + (0.10 * (1 - d) ** 2 if d < 1 else 0.0)

        for y in range(h):                        # stippled portrait
            v = (y - cy) / ry
            row = field[y]
            for x in range(w):
                ink = _face_ink((x - cx) / rx, v)
                if ink > 0.0:
                    ink *= 0.78 + 0.5 * _hash01(x, y, seed & 0xFFFF)
                    if ink > row[x]:
                        row[x] = min(1.0, ink)

        def rake(y0, x0, x1, it, slope=0.0):
            """One scratch streak, brighter toward the face, with gaps."""
            if not (0 <= y0 < h) or x1 <= x0:
                return
            span = x1 - x0
            for x in range(x0, x1 + 1):
                y = int(y0 - slope * (x1 - x))
                if not 0 <= y < h:
                    continue
                n = _hash01(x, y, 77)
                if n < 0.16:
                    continue
                val = it * (0.6 + 0.8 * n) * (0.4 + 0.6 * (x - x0) / span)
                if val > field[y][x]:
                    field[y][x] = val

        for i in range(110):                      # long left rakes
            y = int(cy + rng.gauss(0, ry * 0.55))
            x1 = int(cx - rng.uniform(0.05, 1.0) * rx)
            x0 = max(0, x1 - rng.randint(10, int(w * 0.75)))
            rake(y, x0, x1, rng.uniform(0.10, 0.45), rng.uniform(-0.06, 0.10))
        for i in range(20):                       # short right scratches
            y = int(cy + rng.gauss(0, ry * 0.5))
            x0 = int(cx + rng.uniform(0.9, 1.25) * rx)
            x1 = min(w - 1, x0 + rng.randint(4, 30))
            rake(y, x0, x1, rng.uniform(0.08, 0.30))
        for i in range(16):                       # hair spikes, up-left
            x1 = int(cx + rng.uniform(-0.8, 0.8) * rx)
            y1 = int(cy - ry * rng.uniform(0.70, 1.05))
            x0 = max(0, x1 - rng.randint(8, int(w * 0.30)))
            rake(y1, x0, x1, rng.uniform(0.12, 0.40), rng.uniform(0.12, 0.45))

        for i in range(int(w * h * 0.04)):        # phosphor specks
            x = rng.randrange(w)
            y = rng.randrange(h)
            near = math.hypot((x - cx) / (rx * 2.2), (y - cy) / (ry * 1.6)) < 1
            val = rng.uniform(0.15, 0.55) if near else rng.uniform(0.05, 0.18)
            if val > field[y][x]:
                field[y][x] = val

        return field, (cx, cy, rx, ry)

    @staticmethod
    def _add_eyes(field, geo, state):
        cx, cy, rx, ry = geo
        w, h = len(field[0]), len(field)
        glow = {"open": 1.0, "half": 0.45, "closed": 0.0}[state]
        flare = {"open": 1.0, "half": 0.40, "closed": 0.0}[state]
        for s in (-1, 1):
            ex = cx + s * 0.40 * rx
            ey = cy - 0.02 * ry
            xi, yi = int(round(ex)), int(round(ey))

            if glow:                              # phosphor halo
                for y in range(max(0, yi - int(ry * 0.25)),
                               min(h, yi + int(ry * 0.25) + 1)):
                    for x in range(max(0, xi - int(rx * 0.60)),
                                   min(w, xi + int(rx * 0.60) + 1)):
                        d = math.hypot((x - ex) / (rx * 0.55),
                                       (y - ey) / (ry * 0.20))
                        if d < 1.0:
                            val = 0.55 * (1 - d) ** 2 * glow
                            if val > field[y][x]:
                                field[y][x] = val

            crx, cry = max(1.6, rx * 0.10), max(1.0, ry * 0.055)
            if state == "open":                   # bright core
                for y in range(max(0, yi - 2), min(h, yi + 3)):
                    for x in range(max(0, xi - 3), min(w, xi + 4)):
                        if ((x - ex) / crx) ** 2 + ((y - ey) / cry) ** 2 < 1.0:
                            field[y][x] = 1.0
            elif state == "half":                 # lid halfway down
                for y in range(yi, min(h, yi + 3)):
                    for x in range(max(0, xi - 3), min(w, xi + 4)):
                        if ((x - ex) / crx) ** 2 + ((y - ey) / cry) ** 2 < 1.0:
                            field[y][x] = max(field[y][x], 0.85)
                for x in range(xi - 3, xi + 4):
                    if 0 <= x < w:
                        field[yi][x] = max(field[yi][x], 0.30)
            else:                                 # closed: lid line + shadow
                r = max(2, int(rx * 0.12))
                for x in range(xi - r, xi + r + 1):
                    if not 0 <= x < w:
                        continue
                    y = yi + (1 if abs(x - xi) > r - 1 else 0)
                    if y < h:
                        field[y][x] = max(field[y][x],
                                          0.32 * (1.0 - abs(x - xi) / (r + 1)))
                for x in range(xi - r + 1, xi + r):
                    if 0 <= x < w and yi + 1 < h:
                        field[yi + 1][x] *= 0.35

            if flare:                             # horizontal flare
                L = int(rx * 3.0)
                for dx in range(-L, L + 1):
                    x = xi + dx
                    if not 0 <= x < w:
                        continue
                    a = (1 - abs(dx) / L) ** 1.6 * 0.30 * flare
                    if a > field[yi][x]:
                        field[yi][x] = a
                    if abs(dx) < L // 3:
                        for y in (yi - 1, yi + 1):
                            if 0 <= y < h and a * 0.5 > field[y][x]:
                                field[y][x] = a * 0.5

    @staticmethod
    def _post(field, w, h):
        """Chunky scanlines + vignette, baked into the field pre-quantize."""
        for y in range(h):
            sl = 0.85 if y & 1 else 1.0
            row = field[y]
            for x in range(w):
                d = math.hypot((x - w * 0.5) / (w * 0.62),
                               (y - h * 0.5) / (h * 0.66))
                vig = 1.0 - min(1.0, max(0.0, (d - 0.55) / 0.60)) ** 1.5 * 0.85
                row[x] *= vig * sl

    def _finish(self, field, w, h):
        """Dither to palette, then nearest-neighbour blow-up + center crop."""
        art = pygame.Surface((w, h))
        top = len(PALETTE) - 1
        for y in range(h):
            by = _BAYER4[y & 3]
            for x in range(w):
                t = max(0.0, min(1.0, field[y][x])) * top
                i = int(t)
                f = t - i
                thr = (0.65 * (1 - (by[x & 3] + 0.5) / 16.0)
                       + 0.35 * (1 - _hash01(x, y, 999)))
                if i < top and f > thr:
                    i += 1
                art.set_at((x, y), PALETTE[i])
        big = pygame.transform.scale(art, (w * self.ps, h * self.ps))
        ox = (w * self.ps - self.frame_size[0]) // 2
        oy = (h * self.ps - self.frame_size[1]) // 2
        return big.subsurface(
            (ox, oy, self.frame_size[0], self.frame_size[1])).copy()

    # ------------------------------------------------------- idle blink egg

    def poke(self):
        """Any user input resets the idle timer (the face stays awake)."""
        self.idle = 0.0

    def start_blink(self):
        """Blink once: half -> closed -> half (~0.24 s)."""
        if self._script:
            return
        self._script = list(self._BLINK_SCRIPT) + [("open", 0.0)]
        state, dur = self._script.pop(0)
        self.surface = self.frames[state]
        self._t = dur
        self.idle = 0.0

    def update(self, dt, events=()):
        """Call once per frame. Passing the frame's event list counts any
        input as activity; with no input for IDLE_BLINK_SECONDS the face
        blinks once, then the timer restarts."""
        if events:
            self.poke()
        if self._script:
            self._t -= dt
            while self._t <= 0 and self._script:
                state, dur = self._script.pop(0)
                self.surface = self.frames[state]
                self._t += dur
        else:
            self.idle += dt
            if self.idle >= self.IDLE_BLINK_SECONDS:
                self.start_blink()


def generate_menu_background(frame_w, frame_h):
    """Static eyes-open frame; kept for old call sites."""
    return MenuBackdrop(frame_w, frame_h).frames["open"]


if __name__ == "__main__":
    pygame.init()
    W, H = 960, 540
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("menu backdrop preview (B = blink now)")
    backdrop = MenuBackdrop(W, H)
    clock = pygame.time.Clock()
    while True:
        dt = clock.tick(60) / 1000.0
        evs = pygame.event.get()
        for ev in evs:
            if ev.type == pygame.QUIT:
                raise SystemExit
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_b:
                backdrop.start_blink()
        backdrop.update(dt, evs)
        screen.blit(backdrop.surface, (0, 0))
        pygame.display.flip()
