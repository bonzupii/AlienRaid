#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the easter-egg batch: outback folklore, meta/fourth-wall
pieces, secret gear and the system cross-interactions (quokka selfie,
acquired taste, land dispute, swooping season, the pocket floor)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from components.ai import (DropbearAI, DingoAI, MagpieAI, QuokkaAI, DisputeAI,
                           KangaAI, CassowaryAI, FLEE)
from components.equipment import Equipment
from components.equippable import Equippable
from components.entity import Entity
from components.fighter import Fighter
from components.game_messages import MessageLog
from components.game_states import GameStates
from components.inventory import Inventory
from components.equipment_slots import EquipmentSlots
import functions.death_functions as death_mod
from functions.death_functions import kill_player
from functions.item_functions import (eat_vegemite, eat_dropbear_meat,
                                      use_dads_thong, use_meat_pie, use_esky,
                                      use_ned_kelly_chest)
from functions.senses import NoiseMap
from functions.systems import wait_action
from functions.game_loop import _quokka_encounter, _maybe_land_dispute, _maybe_swooping
from loader_functions.items import create_item
from map_objects.game_map import GameMap, POCKET_FLOOR

CONSTANTS = {'map_width': 100, 'map_height': 48}


def make_player(hp=1000):
    player = Entity(0, 0, 'player', (15, 77, 0), 'Wrpgnyth', blocks=True,
                    fighter=Fighter(hp, 10, 40), inventory=Inventory(26),
                    equipment=Equipment())
    return player


def empty_map(w=24, h=18):
    gm = GameMap(w, h)
    gm.blocked = bytearray(w * h)
    gm.block_sight = bytearray(w * h)
    return gm


class TestAcquiredTaste(unittest.TestCase):
    def test_vegemite_third_ration_grants_acquired_taste(self):
        player = make_player()
        for _ in range(2):
            eat_vegemite(player, 150)
        self.assertFalse(player.fighter.acquired_taste)
        results = eat_vegemite(player, 150)
        self.assertTrue(player.fighter.acquired_taste)
        self.assertTrue(any('acquired a taste' in r.get('message', '').text
                            for r in results if 'message' in r))

    def test_first_tin_carries_the_disclaimer(self):
        """The first vegemite (the +1 defense one) rides in with the
        Marmite disclaimer; later tins do not repeat it."""
        player = make_player()
        results = eat_vegemite(player, 150)
        texts = [r.get('message', '').text for r in results if 'message' in r]
        self.assertEqual(player.vegemite_count, 1)
        self.assertTrue(any('Marmite is objectively superior' in t for t in texts))
        # A second tin must NOT repeat the first-tin disclaimer.
        results2 = eat_vegemite(player, 150)
        texts2 = [r.get('message', '').text for r in results2 if 'message' in r]
        self.assertFalse(any('Marmite is objectively superior' in t for t in texts2))

    def test_sixth_tin_walks_it_back(self):
        """On the sixth tin the disclaimer is walked back."""
        player = make_player()
        for _ in range(5):
            eat_vegemite(player, 150)
        results = eat_vegemite(player, 150)
        texts = [r.get('message', '').text for r in results if 'message' in r]
        self.assertEqual(player.vegemite_count, 6)
        self.assertTrue(any('international incident' in t for t in texts),
                        'sixth tin should walk the disclaimer back')

    def test_acquired_taste_stops_the_rest_timer_dropbear(self):
        player = make_player(hp=600)
        player.fighter.acquired_taste = True
        log = MessageLog(32, 66, 6)
        timer = 60  # over the threshold: without the taste this is lethal
        timer, state = wait_action(player, log, timer)
        self.assertEqual(state, GameStates.ENEMY_TURN)
        self.assertEqual(player.fighter.hp, 600)
        # It keeps healing forever; it can never die to the rest dropbear.
        for _ in range(20):
            timer, state = wait_action(player, log, timer)
            self.assertNotEqual(state, GameStates.PLAYER_DEAD)

    def test_dropbear_respects_the_smell(self):
        ai = DropbearAI()
        player = make_player()
        player.fighter.acquired_taste = True
        self.assertFalse(ai._should_attack(player, empty_map(), []))


class TestDropbearScentNoise(unittest.TestCase):
    def test_dropbear_meat_emits_a_scent_noise(self):
        player = make_player()
        nm = NoiseMap(20, 20)
        eat_dropbear_meat(player, 400, entities=[player], fov_map=None,
                          game_map=empty_map(20, 20), noise_map=nm)
        self.assertGreater(nm.get_noise_at(player.x, player.y), 0,
                           'dropbear meat must emit a scent noise event')
        self.assertEqual(nm.sources[0][3], 'dropbear_scent')


class TestSecretGear(unittest.TestCase):
    def test_dads_thong_claps_and_returns(self):
        player = make_player()
        gm = empty_map()
        fov = bytearray(24 * 18)
        dingo = Entity(3, 3, 'dingo', (0, 0, 0), 'Dingo',
                       fighter=Fighter(500, 5, 10))
        fov[3 * 24 + 3] = 1
        results = use_dads_thong(player, entities=[player, dingo],
                                 fov_map=fov, game_map=gm)
        self.assertTrue(any(r.get('consumed') for r in results))
        self.assertLess(dingo.fighter.hp, 500)
        self.assertTrue(any('single-plugger' in r.get('message', '').text
                            for r in results if 'message' in r))

    def test_meat_pie_scalds_then_heals(self):
        player = make_player(hp=500)
        player.fighter.base_max_hp = 2000  # give room for the +400 heal
        results = use_meat_pie(player)
        # -50 scald, +400 heal: net +350.
        self.assertEqual(player.fighter.hp, 850)
        self.assertTrue(any('Worth it' in r.get('message', '').text
                            for r in results if 'message' in r))

    def test_esky_raises_capacity_by_two(self):
        player = make_player()
        base = player.inventory.capacity
        use_esky(player)
        self.assertEqual(player.inventory.capacity, base + 2)
        self.assertEqual(player.inventory.bonus_capacity, 2)

    def test_ned_kelly_chest_grants_the_breastplate(self):
        player = make_player()
        results = use_ned_kelly_chest(player)
        self.assertTrue(any(r.get('consumed') for r in results))
        self.assertTrue(any(getattr(i, 'item_choice', None) == 'ned_kelly_breastplate'
                            for i in player.inventory.items))
        bp = next(i for i in player.inventory.items
                  if getattr(i, 'item_choice', None) == 'ned_kelly_breastplate')
        self.assertEqual(bp.equippable.defense_bonus, 90)

    def test_death_while_wearing_the_breastplate(self):
        player = make_player()
        bp = Entity(0, 0, 'icon_vest', (0, 0, 0), "Ned Kelly's Breastplate",
                    equippable=Equippable(EquipmentSlots.CHEST_PLATE))
        bp.item_choice = 'ned_kelly_breastplate'
        player.equipment.chest_plate = bp
        message, state = kill_player(player)
        self.assertEqual(message.text, 'Such is life.')
        self.assertEqual(state, GameStates.PLAYER_DEAD)
        death_mod.PLAYER_DIED_FLAG = False  # don't leak the session flag

    def test_spare_sunglasses_block_dingo_smell(self):
        ai = DingoAI()
        player = make_player()
        self.assertTrue(ai._can_smell(player))
        shades = Entity(0, 0, 'icon_hat', (0, 0, 0), 'Spare Sunglasses',
                        equippable=Equippable(EquipmentSlots.HELMET))
        shades.item_choice = 'spare_sunglasses'
        player.equipment.helmet = shades
        self.assertFalse(ai._can_smell(player))


class TestQuokkaCrossInteractions(unittest.TestCase):
    def test_selfie_once_per_game(self):
        player = make_player()
        quokka = Entity(1, 0, 'quokka', (0, 0, 0), 'Quokka',
                        fighter=Fighter(100, 1, 1), ai=QuokkaAI())
        quokka.ai.owner = quokka
        log = MessageLog(32, 66, 6)
        results = _quokka_encounter(player, quokka, log)
        self.assertTrue(any(r.get('xp') for r in results))
        self.assertTrue(getattr(player, '_quokka_selfie', False))
        results2 = _quokka_encounter(player, quokka, log)
        self.assertFalse(any(r.get('xp') for r in results2))

    def test_quokka_bone_club_makes_them_flee(self):
        player = make_player()
        player.inventory.add_item(create_item('quokka_bone_club', 12, 0, 0))
        quokka = Entity(1, 0, 'quokka', (0, 0, 0), 'Quokka',
                        fighter=Fighter(100, 1, 1), ai=QuokkaAI())
        quokka.ai.owner = quokka
        log = MessageLog(32, 66, 6)
        results = _quokka_encounter(player, quokka, log)
        self.assertFalse(any(r.get('xp') for r in results))
        self.assertEqual(quokka.ai.state, FLEE)

    def test_quokka_ai_flees_when_club_carried(self):
        player = make_player()
        player.inventory.add_item(create_item('quokka_bone_club', 12, 0, 0))
        gm = empty_map()
        fov = bytearray(24 * 18)
        quokka = Entity(5, 5, 'quokka', (0, 0, 0), 'Quokka',
                        fighter=Fighter(100, 1, 1), ai=QuokkaAI())
        quokka.ai.owner = quokka
        fov[5 * 24 + 5] = 1
        fov[0] = 1
        quokka.ai.take_turn(player, fov, gm, [player, quokka])
        self.assertEqual(quokka.ai.state, FLEE)


class TestFloorEvents(unittest.TestCase):
    def test_land_dispute_locks_eyes(self):
        gm = empty_map()
        fov = bytearray(24 * 18)
        kanga = Entity(5, 5, 'kanga', (0, 0, 0), 'Kanga',
                       fighter=Fighter(500, 10, 20), ai=KangaAI())
        kanga.ai.owner = kanga
        kanga.species = 'kanga'
        cassowary = Entity(6, 5, 'cassowary', (0, 0, 0), 'Cassowary',
                           fighter=Fighter(500, 10, 30), ai=CassowaryAI())
        cassowary.ai.owner = cassowary
        cassowary.species = 'cassowary'
        fov[5 * 24 + 5] = 1
        fov[5 * 24 + 6] = 1
        log = MessageLog(32, 66, 6)
        entities = [kanga, cassowary]
        _maybe_land_dispute(gm, entities, fov, log)
        self.assertTrue(gm.land_dispute)
        self.assertIsInstance(kanga.ai, DisputeAI)
        self.assertIsInstance(cassowary.ai, DisputeAI)
        self.assertTrue(any('lock eyes' in m.text for m in log.message))

    def test_land_dispute_needs_adjacent_pair_in_fov(self):
        gm = empty_map()
        fov = bytearray(24 * 18)
        kanga = Entity(1, 1, 'kanga', (0, 0, 0), 'Kanga',
                       fighter=Fighter(500, 10, 20), ai=KangaAI())
        kanga.ai.owner = kanga
        kanga.species = 'kanga'
        cassowary = Entity(10, 10, 'cassowary', (0, 0, 0), 'Cassowary',
                           fighter=Fighter(500, 10, 30), ai=CassowaryAI())
        cassowary.ai.owner = cassowary
        cassowary.species = 'cassowary'
        _maybe_land_dispute(gm, [kanga, cassowary], fov, MessageLog(32, 66, 6))
        self.assertFalse(gm.land_dispute)

    def test_swooping_season(self):
        gm = empty_map()
        magpie = Entity(5, 5, 'magpie', (0, 0, 0), 'Magpie',
                        fighter=Fighter(100, 5, 10), ai=MagpieAI())
        magpie.ai.owner = magpie
        magpie.species = 'magpie'
        log = MessageLog(32, 66, 6)
        _maybe_swooping(gm, [magpie], log)
        self.assertTrue(gm.swooping)
        self.assertTrue(magpie.ai.season_swoop)
        self.assertTrue(any('wear a helmet' in m.text for m in log.message))


class TestPocketFloor(unittest.TestCase):
    def test_pocket_floor_round_trip(self):
        player = make_player()
        gm = GameMap(100, 48, dungeon_level=5)
        entities = [player]
        gm.make_map(100, 48, player, entities)
        log = MessageLog(32, 66, 6)
        entities = gm.go_down(player, log, CONSTANTS, entities,
                              floor=POCKET_FLOOR)
        self.assertTrue(gm.is_pocket)
        self.assertEqual((gm.width, gm.height), (24, 18))
        mugs = [e for e in entities if getattr(e, 'item_choice', None) == 'dev_mug']
        self.assertEqual(len(mugs), 1)
        ups = [e for e in entities if e.trail and e.trail.direction == 'up']
        self.assertEqual(len(ups), 1)
        self.assertEqual(ups[0].trail.floor, 5)
        player.x, player.y = ups[0].x, ups[0].y
        entities = gm.go_up(player, log, CONSTANTS, entities, floor=5)
        self.assertFalse(gm.is_pocket)
        self.assertEqual(gm.dungeon_level, 5)
        self.assertEqual((gm.width, gm.height), (100, 48))


if __name__ == '__main__':
    unittest.main()
