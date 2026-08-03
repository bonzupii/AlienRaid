# -*- coding: utf-8 -*-
"""Draw order for map entities (lowest draws first)."""

from enum import Enum


class RenderOrder(Enum):
    TRAIL = 1
    CORPSE = 2
    ITEM = 3
    PART = 4
    SHIP = 4
    ACTOR = 5
