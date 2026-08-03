#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Item use functions (no libtcod)."""

from random import randint

from components.ai import StunnedMonster
from components.game_messages import Message
from renderer import palette as C


def _in_fov(fov_map, game_map, x, y):
    if not (0 <= x < game_map.width and 0 <= y < game_map.height):
        return False
    return fov_map[y * game_map.width + x] != 0


def heal(entity, amount=200):
    results = []
    if entity.fighter.hp == entity.fighter.max_hp:
        results.append({'consumed': False, 'message': Message('You are already at full health', C.YELLOW)})
    else:
        entity.fighter.heal(amount)
        results.append({'consumed': True, 'message': Message('Your wounds start to feel better!', C.GREEN)})
    return results


def morphine_pack(entity, amount=350):
    results = []
    if entity.fighter.hp == entity.fighter.max_hp:
        results.append({'consumed': False, 'message': Message('You are already at full health', C.YELLOW)})
    else:
        entity.fighter.heal(amount)
        results.append({'consumed': True, 'message': Message('Your wounds start to feel much better!', C.GREEN)})
    return results


def gain_xp(entity, amount=400):
    return [{'consumed': True, 'xp': amount,
             'message': Message('You scarf down the bush tucker. (gained {0} XP)'.format(amount), C.GREEN)}]


def use_shock_charge(entity, entities=None, fov_map=None, game_map=None, damage=350, maximum_range=5):
    results = []
    target = None
    closest_distance = maximum_range + 1

    for e in entities:
        if e.fighter and e is not entity and _in_fov(fov_map, game_map, e.x, e.y):
            distance = entity.distance_to(e)
            if distance < closest_distance:
                target = e
                closest_distance = distance

    if target:
        results.append({'consumed': True, 'target': target,
                        'message': Message('A lightning bolt strikes the {0} with a loud thunder! It deals {1} damage.'.format(target.name, damage), C.ORANGE)})
        results.extend(target.fighter.take_damage(damage))
    else:
        results.append({'consumed': False, 'target': None,
                        'message': Message('No enemy is close enough to strike.', C.RED)})
    return results


def use_boomerang(entity, entities=None, fov_map=None, game_map=None, damage=120, maximum_range=8):
    results = []
    target = None
    closest_distance = maximum_range + 1

    for e in entities:
        if e.fighter and e is not entity and _in_fov(fov_map, game_map, e.x, e.y):
            distance = entity.distance_to(e)
            if distance < closest_distance:
                target = e
                closest_distance = distance

    if target:
        results.append({'consumed': True, 'target': target,
                        'message': Message('The boomerang arcs through the air and clonks the {0} for {1} damage, then returns to your hand!'.format(target.name, damage), C.LIGHT_ORANGE)})
        results.extend(target.fighter.take_damage(damage))
    else:
        results.append({'consumed': False, 'target': None,
                        'message': Message('No enemy is within range for the boomerang.', C.RED)})
    return results


def use_didgeridoo(entity, entities=None, fov_map=None, game_map=None, turns=6):
    results = []
    stunned = 0
    for e in entities:
        if e.ai and e is not entity and _in_fov(fov_map, game_map, e.x, e.y):
            stunned_ai = StunnedMonster(e.ai, turns)
            stunned_ai.owner = e
            e.ai = stunned_ai
            stunned += 1

    if stunned:
        results.append({'consumed': True,
                        'message': Message('You blow a deep, droning note on the didgeridoo. {0} nearby creature{1} reel{2}, dazed!'.format(
                            stunned, '' if stunned == 1 else 's', 's' if stunned == 1 else ''), C.LIGHT_VIOLET)})
    else:
        results.append({'consumed': False,
                        'message': Message('You play a lonely didgeridoo tune. No creatures are around to hear it.', C.LIGHT_GRAY)})
    return results


def use_plasma_grenade(entity, entities=None, fov_map=None, game_map=None, damage=250, radius=3, target_x=None, target_y=None):
    results = []

    if not _in_fov(fov_map, game_map, target_x, target_y):
        results.append({'consumed': False,
                        'message': Message('You cannot target a tile outside of your field of view!', C.YELLOW)})
        return results

    results.append({'consumed': True,
                    'message': Message('The plasma grenade explodes, burning everything within {0} tiles!'.format(radius), C.ORANGE)})

    for e in entities:
        if e.distance(target_x, target_y) <= radius and e.fighter:
            results.append({'message': Message('The {0} gets burned for {1} hit points!'.format(e.name, damage), C.ORANGE)})
            results.extend(e.fighter.take_damage(damage))
    return results


def use_stun_grenade(entity, entities=None, fov_map=None, game_map=None, target_x=None, target_y=None):
    results = []

    if not _in_fov(fov_map, game_map, target_x, target_y):
        results.append({'consumed': False,
                        'message': Message('You cannot target a tile outside of your field of view!', C.YELLOW)})
        return results

    for e in entities:
        if e.x == target_x and e.y == target_y and e.ai:
            stunned_ai = StunnedMonster(e.ai, 10)
            stunned_ai.owner = e
            e.ai = stunned_ai
            results.append({'consumed': True,
                            'message': Message('The stun grenade explodes near the {0}! It reels and stumbles around as it tries to regain its bearings.'.format(e.name), C.LIGHT_GREEN)})
            break
    else:
        results.append({'consumed': False,
                        'message': Message('There is no targetable enemy at that location!', C.YELLOW)})
    return results


def use_ray_gun(entity, entities=None, fov_map=None, game_map=None, damage=80, maximum_range=11):
    results = []
    target = None
    closest_distance = maximum_range + 1

    for e in entities:
        if e.fighter and e is not entity and _in_fov(fov_map, game_map, e.x, e.y):
            distance = entity.distance_to(e)
            if distance < closest_distance:
                target = e
                closest_distance = distance

    if target:
        if randint(0, 100) >= 30:
            results.append({'consumed': True, 'target': target,
                            'message': Message('Pew! Pew! You hit the {0} with a searing ray blast! It takes {1} damage!'.format(target.name, damage), C.ORANGE)})
            results.extend(target.fighter.take_damage(damage))
        else:
            results.append({'consumed': True, 'target': target,
                            'message': Message('Pew! Pew! Pew! Pew! You miss the {0}!'.format(target.name), C.DARK_RED)})
    else:
        results.append({'consumed': False, 'target': None,
                        'message': Message('No enemy is close enough to shoot.', C.RED)})
    return results
