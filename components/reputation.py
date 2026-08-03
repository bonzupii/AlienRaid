# -*- coding: utf-8 -*-
"""Reputation and quest-state tracking for MIB, AECD, and the Outback.

Faction standing is a plain integer score per faction; the victory
epilogue is derived from whichever faction the player buttered up
(MIB / AECD / both / neither).
"""


class Reputation:
    def __init__(self):
        self.mib = 0
        self.aecd = 0
        self.adf = 0
        self.mib_quest_state = 'not_started'  # not_started/given/neuralyzer_found/completed

    def update(self, faction, amount):
        if faction in ('mib', 'aecd', 'adf'):
            setattr(self, faction, getattr(self, faction) + amount)

    def epilogue(self):
        """Which victory epilogue to show, from the endgame standings."""
        if self.mib > 10 and self.aecd > 10:
            return 'betrayal'
        if self.mib > 10:
            return 'mib'
        if self.aecd > 10:
            return 'aecd'
        return 'solo'
