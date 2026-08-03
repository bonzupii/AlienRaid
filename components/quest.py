# -*- coding: utf-8 -*-
"""Quest component: salvage the crashed ship's missing parts.

The player must descend to recover every part, then return to the surface
and install them at the ship to escape.
"""

# part_id -> (display name, floor where it is found)
SHIP_PARTS = {
    'antimatter_core': ('Antimatter Core', 5),
    'nav_computer': ('Navigation Computer', 10),
    'power_coupling': ('Power Coupling', 15),
    'hull_plating': ('Hull Plating', 20),
}

PART_COLORS = {
    'antimatter_core': (255, 215, 0),     # gold
    'nav_computer': (0, 255, 255),        # cyan
    'power_coupling': (203, 204, 206),    # silver
    'hull_plating': (0, 255, 0),          # green
}


class Quest:
    def __init__(self):
        self.parts = []  # part ids salvaged so far (in order)

    @property
    def found_count(self):
        return len(self.parts)

    @property
    def parts_total(self):
        return len(SHIP_PARTS)

    def find_part(self, part_id):
        if part_id not in self.parts:
            self.parts.append(part_id)

    def has_part(self, part_id):
        return part_id in self.parts

    @property
    def complete(self):
        return self.found_count >= self.parts_total
