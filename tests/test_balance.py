#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Qwen's roguelike-balance pass (hunger clock, slower
out-of-combat healing, persistent dungeon floors, single-use saves, and the
eating intrinsics) plus the Claude menu-backdrop redesign and the morphine
disclaimer egg."""
import os
import shelve
import sys
import unittest
from unittest import mock

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from components.ai import HeuristicMonster, DingoAI
from components.entity import Entity
from components.equipment import Equipment
from components.fighter import (Fighter, HUNGER_MAX, HUNGRY_AT, STARVING_AT,
                                hunger_tier)
from components.game_messages import MessageLog
from components.game_states import GameStates
from components.inventory import Inventory
import functions.death_functions as death_mod
from functions.death_functions import kill_player
from functions.item_functions import eat_vegemite, morphine_pack
from functions.senses import NoiseMap
from functions.systems import (passive_regen, wait_action, speed_free_action,
                               tick_hunger)
from loader_functions.data_loaders import save_game, load_game
from map_objects.game_map import GameMap, POCKET_FLOOR

CONSTANTS = {'map_width': 100, 'map_height': 48}


def make_player(hp=1250):
    player = Entity(0, 0, 'player', (15, 77, 0), 'Wrpgnyth', blocks=True,
                    fighter=Fighter(hp, 10, 40), inventory=Inventory(26),
                    equipment=Equipment())
    return player


def empty_map(w=24, h=18):
    gm = GameMap(w, h)
    gm.blocked = bytearray(w * h)
    gm.block_sight = bytearray(w * h)
    return gm


class TestHungerClock(unittest.TestCase):
    def test_player_starts_full_and_tiers(self):
        player = make_player()
        self.assertEqual(player.fighter.hunger, HUNGER_MAX)
        self.assertEqual(hunger_tier(player.fighter), 'well-fed')
        player.fighter.hunger = HUNGRY_AT
        self.assertEqual(hunger_tier(player.fighter), 'hungry')
        player.fighter.hunger = STARVING_AT
        self.assertEqual(hunger_tier(player.fighter), 'starving')

    def test_food_feeds_medicine_does_not(self):
        player = make_player()
        player.fighter.hunger = 100
        eat_vegemite(player, 150)
        self.assertEqual(player.fighter.hunger, 250)
        # Medicine heals but never feeds.
        hurt = make_player(hp=1000)
        hurt.fighter.hunger = 100
        morphine_pack(hurt, amount=350)
        self.assertEqual(hurt.fighter.hunger, 100)
        self.assertEqual(hurt.fighter.hp, hurt.fighter.max_hp)  # capped heal

    def test_hunger_ticks_down_and_logs_tier_change(self):
        player = make_player()
        player.fighter.hunger = HUNGRY_AT + 1
        log = MessageLog(32, 66, 6)
        self.assertFalse(tick_hunger(player, log))
        self.assertEqual(player.fighter.hunger, HUNGRY_AT)
        self.assertEqual(hunger_tier(player.fighter), 'hungry')
        self.assertTrue(any('getting hungry' in m.text for m in log.message))

    def test_starvation_drains_through_the_death_path(self):
        player = make_player(hp=10)
        player.fighter.hunger = 0
        log = MessageLog(32, 66, 6)
        died = False
        for _ in range(20):
            if tick_hunger(player, log):
                died = True
                break
        self.assertTrue(died)
        self.assertLessEqual(player.fighter.hp, 0)
        self.assertTrue(death_mod.PLAYER_DIED_FLAG)
        death_mod.PLAYER_DIED_FLAG = False

    def test_hungry_stops_passive_regen(self):
        player = make_player()
        player.fighter.hp = 100
        log = MessageLog(32, 66, 6)
        player.fighter.hunger = HUNGRY_AT
        with mock.patch('functions.systems.randint', return_value=39):
            passive_regen(player, log)
        self.assertEqual(player.fighter.hp, 100, 'hunger must gate regen')
        player.fighter.hunger = HUNGER_MAX
        with mock.patch('functions.systems.randint', return_value=39):
            passive_regen(player, log)
        self.assertGreater(player.fighter.hp, 100)

    def test_hungry_stops_wait_healing(self):
        player = make_player()
        player.fighter.hp = 100
        player.fighter.hunger = HUNGRY_AT
        log = MessageLog(32, 66, 6)
        timer, state = wait_action(player, log, 0)
        self.assertEqual(player.fighter.hp, 100, 'hunger must gate rest heal')
        self.assertEqual(state, GameStates.ENEMY_TURN)
        self.assertTrue(any('too hungry' in m.text for m in log.message))


class TestSlowerHealing(unittest.TestCase):
    def test_descend_rest_heals_a_tenth(self):
        player = make_player()
        gm = GameMap(100, 48)
        entities = [player]
        gm.make_map(100, 48, player, entities)
        player.fighter.hp = 250  # 1000 missing; //10 = 125
        entities = gm.go_down(player, MessageLog(32, 66, 6), CONSTANTS,
                              entities)
        self.assertEqual(player.fighter.hp, 375)


class TestSpeedIntrinsic(unittest.TestCase):
    def test_speed_free_action_parity(self):
        player = make_player()
        self.assertFalse(speed_free_action(player))
        self.assertFalse(speed_free_action(player))
        player.fighter.add_status('speed', 10)
        results = [speed_free_action(player) for _ in range(4)]
        self.assertEqual(results, [False, True, False, True])


class TestPoisonResistIntrinsic(unittest.TestCase):
    def test_venom_damage_halved_while_resistant(self):
        ai = HeuristicMonster()
        player = make_player()
        self.assertEqual(ai._venom_damage(player, 100), 100)
        player.fighter.add_status('poison_resist', 20)
        self.assertEqual(ai._venom_damage(player, 100), 50)
        self.assertEqual(ai._venom_damage(player, 1), 1)  # floor at 1


class TestInvisibleIntrinsic(unittest.TestCase):
    def test_invisible_blocks_new_visual_last_seen(self):
        gm = empty_map(20, 20)
        fov = bytearray([1]) * 400
        player = make_player()
        player.x, player.y = 2, 2
        player.fighter.add_status('invisible', 15)
        monster = Entity(10, 10, 'wombat', (0, 0, 0), 'Wombat',
                         fighter=Fighter(100, 5, 10), ai=HeuristicMonster())
        monster.ai.take_turn(player, fov, gm, [player, monster])
        self.assertIsNone(monster.ai.last_seen,
                          'invisible player must not be visually acquired')

    def test_visible_player_is_acquired(self):
        gm = empty_map(20, 20)
        fov = bytearray([1]) * 400
        player = make_player()
        player.x, player.y = 2, 2
        monster = Entity(10, 10, 'wombat', (0, 0, 0), 'Wombat',
                         fighter=Fighter(100, 5, 10), ai=HeuristicMonster())
        monster.ai.take_turn(player, fov, gm, [player, monster])
        self.assertEqual(monster.ai.last_seen, (2, 2))

    def test_smell_still_tracks_the_invisible(self):
        gm = empty_map(20, 20)
        fov = bytearray([1]) * 400
        player = make_player()
        player.x, player.y = 2, 2
        player.fighter.add_status('invisible', 15)
        dingo = Entity(9, 2, 'dingo', (0, 0, 0), 'Dingo',
                       fighter=Fighter(100, 5, 10), ai=DingoAI())
        dingo.ai.take_turn(player, fov, gm, [player, dingo])
        self.assertEqual(dingo.ai.last_seen, (2, 2),
                         'scent-tracking must still work while invisible')


class TestPersistentFloors(unittest.TestCase):
    def test_floor_state_persists_across_transitions(self):
        player = make_player()
        gm = GameMap(100, 48)
        entities = [player]
        gm.make_map(100, 48, player, entities)
        log = MessageLog(32, 66, 6)

        monsters = [e for e in entities if e.ai]
        self.assertGreaterEqual(len(monsters), 2, 'floor 1 should spawn monsters')
        keep, victim = monsters[0], monsters[1]
        entities.remove(victim)  # simulate a kill

        entities = gm.go_down(player, log, CONSTANTS, entities)
        self.assertEqual(gm.dungeon_level, 2)
        floor2_monster = next(e for e in entities if e.ai)

        # Ascend: floor 1 is restored, NOT regenerated.
        entities = gm.go_up(player, log, CONSTANTS, entities)
        self.assertEqual(gm.dungeon_level, 1)
        self.assertIn(keep, entities, 'surviving monster must persist')
        self.assertNotIn(victim, entities, 'killed monster must stay dead')
        self.assertTrue(any(e.ship for e in entities),
                        'the ship must still be on restored floor 1')

        # Descend again: floor 2 is restored with the same monster object.
        entities = gm.go_down(player, log, CONSTANTS, entities)
        self.assertEqual(gm.dungeon_level, 2)
        self.assertIn(floor2_monster, entities,
                      'floor 2 must restore the same monster, not respawn it')


class TestSingleUseSave(unittest.TestCase):
    def tearDown(self):
        for suffix in ('', '.dir', '.bak'):
            path = 'savegame.dat' + suffix
            if os.path.isfile(path):
                os.remove(path)

    def test_save_round_trips_and_is_consumed_on_load(self):
        player = make_player()
        gm = GameMap(100, 48)
        entities = [player]
        gm.make_map(100, 48, player, entities)
        log = MessageLog(32, 66, 6)
        # Visit floor 2 and return so the cache holds floors 1 and 2.
        entities = gm.go_down(player, log, CONSTANTS, entities)
        entities = gm.go_up(player, log, CONSTANTS, entities)

        save_game(player, entities, gm, log, GameStates.PLAYERS_TURN)
        self.assertTrue(os.path.isfile('savegame.dat'))

        p, ent, gmap, mlog, gstate = load_game()
        self.assertFalse(os.path.isfile('savegame.dat'),
                         'a checkpoint save must be consumed on load')
        self.assertEqual(gmap.dungeon_level, 1)
        self.assertIn(1, gmap.floor_cache)
        self.assertIn(2, gmap.floor_cache)
        # Unpickling makes a fresh object; compare content, not identity.
        self.assertEqual(p.name, player.name)
        self.assertEqual(p.fighter.hp, player.fighter.hp)

    def test_old_save_without_floor_cache_loads(self):
        player = make_player()
        gm = GameMap(100, 48)
        entities = [player]
        gm.make_map(100, 48, player, entities)
        del gm.floor_cache  # simulate a pre-persistent-floors save
        with shelve.open('savegame.dat', 'n') as f:
            f['player_index'] = 0
            f['entities'] = entities
            f['game_map'] = gm
            f['message_log'] = MessageLog(32, 66, 6)
            f['game_state'] = GameStates.PLAYERS_TURN
        p, ent, gmap, mlog, gstate = load_game()
        self.assertEqual(gmap.floor_cache, {})
        self.assertEqual(gmap.dungeon_level, 1)
        # Unpickling makes a fresh object; compare content, not identity.
        self.assertEqual(p.name, player.name)
        self.assertEqual(p.fighter.hp, player.fighter.hp)


class TestMorphineDisclaimer(unittest.TestCase):
    def test_morphine_carries_the_disclaimer_once(self):
        player = make_player()
        player.fighter.hp = 500
        results = morphine_pack(player, amount=350, is_morphine=True)
        texts = [r.get('message', '').text for r in results if 'message' in r]
        self.assertTrue(any('Go with it' in t for t in texts))
        self.assertTrue(any('350 HP' in t for t in texts))
        self.assertTrue(player.morphine_used)
        # Second use: no repeat of the joke.
        player.fighter.hp = 500
        results2 = morphine_pack(player, amount=350, is_morphine=True)
        texts2 = [r.get('message', '').text for r in results2 if 'message' in r]
        self.assertFalse(any('Go with it' in t for t in texts2))

    def test_med_kit_stays_silent(self):
        player = make_player()
        player.fighter.hp = 500
        results = morphine_pack(player, amount=500)  # med kit path
        texts = [r.get('message', '').text for r in results if 'message' in r]
        self.assertFalse(any('Go with it' in t for t in texts))


class TestMenuBackdropRedesign(unittest.TestCase):
    def test_backdrop_renders_frames_and_blinks(self):
        from renderer.menu_background import MenuBackdrop
        bd = MenuBackdrop(96, 54)
        for state in ('open', 'half', 'closed'):
            self.assertEqual(bd.frames[state].get_size(), (96, 54))
        bd.start_blink()
        for _ in range(10):
            bd.update(0.05)
        self.assertIs(bd.surface, bd.frames['open'],
                      'blink script must return to the open frame')


if __name__ == '__main__':
    unittest.main()
