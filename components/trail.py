# -*- coding: utf-8 -*-
"""Trail (stairs) component. ``direction`` is 'down' or 'up'."""


class Trail:
    def __init__(self, direction='down', floor=None):
        self.direction = direction
        self.floor = floor
