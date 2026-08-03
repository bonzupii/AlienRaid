#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for AI state machines, memory, and telegraphed attacks (Phase 3)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from components.ai import KangaAI, WombatAI, GRAZE, HUNT
from components.entity import Entity
from components.fighter import Fighter
from map_objects.game_map import GameMap


class TestAIStates(unittest.TestCase):
    def setUp(self):
        self.w, self.h = 20, 20
        self.game_map = GameMap(self.w, self.h)
        self.game_map.blocked = bytearray(self.w * self.h)
        self.game_map.block_sight = bytearray(self.w * self.h)
        self.player = Entity(10, 10, 'player', (15, 77, 0), 'Player',
                             fighter=Fighter(100, 10, 10))

    def test_kanga_starts_grazing(self):
        self.assertEqual(KangaAI().state, GRAZE)

    def test_kanga_transitions_to_hunt(self):
        ai = KangaAI()
        monster = Entity(8, 10, 'kanga', (0, 0, 0), 'Kanga',
                         blocks=True, fighter=Fighter(100, 10, 10), ai=ai)
        ai.owner = monster

        fov_map = bytearray(self.w * self.h)
        fov_map[10 * self.w + 8] = 1  # monster tile lit
        fov_map[10 * self.w + 10] = 1  # player tile lit

        ai.take_turn(self.player, fov_map, self.game_map, [self.player, monster])

        # Player at distance 2 -> provoked -> hunting.
        self.assertEqual(ai.state, HUNT)

    def test_kanga_wont_attack_while_grazing(self):
        """A kanga that somehow stays in GRAZE refuses to attack."""
        ai = KangaAI()
        monster = Entity(9, 10, 'kanga', (0, 0, 0), 'Kanga',
                         blocks=True, fighter=Fighter(100, 10, 10), ai=ai)
        ai.owner = monster
        self.assertEqual(ai._should_attack(self.player, self.game_map, []), False)

    def test_wombat_ignores_until_hurt(self):
        ai = WombatAI()
        fighter = Fighter(100, 10, 10)
        monster = Entity(8, 10, 'wombat', (0, 0, 0), 'Wombat',
                         blocks=True, fighter=fighter, ai=ai)
        ai.owner = monster

        fov_map = bytearray(self.w * self.h)
        fov_map[10 * self.w + 8] = 1
        fov_map[10 * self.w + 10] = 1

        entities = [self.player, monster]

        # Before being hurt, it stays grazing.
        ai.take_turn(self.player, fov_map, self.game_map, entities)
        self.assertEqual(ai.state, GRAZE)

        # Hurt once -> hunting forever.
        fighter.take_damage(10, attacker=self.player)
        ai.take_turn(self.player, fov_map, self.game_map, entities)
        self.assertEqual(ai.state, HUNT)

    def test_telegraph_restores_sprite_after_kick(self):
        """The kanga kick telegraphs via kanga_rear, then the sprite returns
        to the normal pose when the kick lands."""
        ai = KangaAI()
        monster = Entity(9, 10, 'kanga', (0, 0, 0), 'Kanga',
                         blocks=True, fighter=Fighter(100, 10, 10), ai=ai)
        ai.owner = monster
        ai.charge = 1  # already wound up last turn

        results = ai._attack(self.player)
        self.assertEqual(monster.sprite_id, 'kanga',
                         'sprite not restored after the kick')
        self.assertTrue(any('kick' in r.get('message', '').text.lower()
                            for r in results if 'message' in r))

    def test_wombat_slow_tick(self):
        """SLOW=2 species act only every other turn."""
        ai = WombatAI()
        self.assertEqual(ai.SLOW, 2)
        self.assertEqual(ai.slow_tick % ai.SLOW, 0)


if __name__ == '__main__':
    unittest.main()
