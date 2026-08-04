#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Item use functions (no libtcod)."""

from random import randint

from components.ai import StunnedMonster, DingoAI, FLEE
from components.fighter import HUNGER_MAX
from components.game_messages import Message
from renderer import palette as C


def _feed(entity, amount):
    """Food satisfies hunger; medicine never does (Qwen balance rule)."""
    fighter = entity.fighter
    fighter.hunger = min(HUNGER_MAX, getattr(fighter, 'hunger', HUNGER_MAX) + amount)


def _in_fov(fov_map, game_map, x, y):
    if not (0 <= x < game_map.width and 0 <= y < game_map.height):
        return False
    return fov_map[y * game_map.width + x] != 0


def heal(entity, amount=200, entities=None, fov_map=None, game_map=None, noise_map=None):
    results = []
    if entity.fighter.hp == entity.fighter.max_hp:
        results.append({'consumed': False, 'message': Message('You are already at full health', C.YELLOW)})
    else:
        entity.fighter.heal(amount)
        results.append({'consumed': True, 'message': Message('Your wounds start to feel better!', C.GREEN)})
    return results


def morphine_pack(entity, amount=350, entities=None, fov_map=None, game_map=None,
                  noise_map=None, is_morphine=False):
    results = []
    if entity.fighter.hp == entity.fighter.max_hp:
        results.append({'consumed': False, 'message': Message('You are already at full health', C.YELLOW)})
    else:
        healed_hp = min(amount, entity.fighter.max_hp - entity.fighter.hp)
        entity.fighter.heal(amount)
        results.append({'consumed': True, 'message': Message('Your wounds start to feel much better!', C.GREEN)})

        # Easter egg: only the real Morphine Pack carries the disclaimer --
        # the Med Kit shares this function and must stay silent (a bandage
        # kit isn't going to make the nervous-system gag land). One-shot.
        if is_morphine and not getattr(entity, 'morphine_used', False):
            entity.morphine_used = True
            disclaimer_text = (
                "Yeah, yeah. I know. We have no reason to believe that aliens "
                "have any biological similarity to human beings whatsoever, or "
                "that morphine would have any kind of similar effect on "
                "Wrpgnyth as it does to us. In any case, it heals you for "
                "{0} HP. Just... OK? Go with it.".format(healed_hp)
            )
            results.append({'message': Message(disclaimer_text, C.LIGHT_VIOLET)})

    return results


def gain_xp(entity, amount=400, entities=None, fov_map=None, game_map=None, noise_map=None):
    """Bush tucker: XP + it feeds you (food, not medicine)."""
    _feed(entity, 200)
    return [{'consumed': True, 'xp': amount,
             'message': Message('You scarf down the bush tucker. (gained {0} XP)'.format(amount), C.GREEN)}]


def use_shock_charge(entity, entities=None, fov_map=None, game_map=None, damage=350, maximum_range=5, noise_map=None):
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


def use_boomerang(entity, entities=None, fov_map=None, game_map=None, damage=120, maximum_range=8, noise_map=None):
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


def use_dads_thong(entity, entities=None, fov_map=None, game_map=None,
                   damage=140, maximum_range=8, noise_map=None):
    """Dad's thong: a thrown single-plugger that always returns. One in
    five throws lands a double-plugger critical."""
    results = []
    target = None
    closest_distance = maximum_range + 1
    for e in entities or []:
        if e.fighter and e is not entity and _in_fov(fov_map, game_map, e.x, e.y):
            distance = entity.distance_to(e)
            if distance < closest_distance:
                target = e
                closest_distance = distance
    if target:
        crit = randint(1, 5) == 1
        dmg = damage * 2 if crit else damage
        results.append({'consumed': True, 'target': target,
                        'message': Message(
                            'You deploy the single-plugger. It claps the {0} '
                            'across the ear for {1} damage, then flies back '
                            'to your hand!'.format(target.name, dmg),
                            C.LIGHT_ORANGE)})
        if crit:
            results.append({'message': Message(
                'DOUBLE-PLUGGER CRITICAL!', C.YELLOW)})
        results.extend(target.fighter.take_damage(dmg))
    else:
        results.append({'consumed': False, 'target': None,
                        'message': Message('No enemy is within range for the thong.', C.RED)})
    return results


def use_meat_pie(entity, entities=None, fov_map=None, game_map=None, noise_map=None):
    """The roadhouse meat pie: 50 scald damage, then +400 HP. Worth it."""
    results = []
    results.append({'message': Message(
        'You bite into the meat pie. It scalds the roof of your mouth for 50 damage.',
        C.ORANGE)})
    results.extend(entity.fighter.take_damage(50))
    entity.fighter.heal(400)
    results.append({'message': Message('...Worth it. (+400 HP)', C.LIGHT_GREEN)})
    results.append({'consumed': True})
    return results


def use_esky(entity, entities=None, fov_map=None, game_map=None, noise_map=None):
    """Esky of Holding: permanently +2 inventory capacity. The tinnies
    staying cold forever is flavour only -- the +2 is the joke's price."""
    inv = entity.inventory
    # getattr guard: pre-esky saves may lack the attribute entirely.
    inv.bonus_capacity = getattr(inv, 'bonus_capacity', 0) + 2
    return [{'consumed': True, 'message': Message(
        'You stash the Esky of Holding in your pack. (inventory capacity +2 '
        '-- and your tinnies are always cold.)', C.CYAN)}]


def use_ned_kelly_chest(entity, entities=None, fov_map=None, game_map=None, noise_map=None):
    """The memorial chest: pry it open for Ned Kelly's breastplate."""
    results = []
    level = getattr(game_map, 'dungeon_level', 1) if game_map else 1
    from loader_functions.items import create_item  # deferred: breaks import cycle
    breastplate = create_item('ned_kelly_breastplate', level, entity.x, entity.y)
    added = entity.inventory.add_item(breastplate)
    if not any(r.get('item_added') for r in added):
        return [{'consumed': False, 'message': Message(
            'You cannot carry the breastplate.', C.YELLOW)}]
    results.append({'consumed': True, 'message': Message(
        "You pry open the rusted chest. Ned Kelly's breastplate gleams inside.",
        C.GOLD)})
    results.append({'message': Message(
        "You heft it. 'Too heavy to run from the law.'", C.LIGHT_GRAY)})
    return results


def use_didgeridoo(entity, entities=None, fov_map=None, game_map=None, turns=6, noise_map=None):
    results = []
    if noise_map:
        noise_map.emit(entity.x, entity.y, 8, 'didgeridoo')
    # Play it inside a roadhouse and the Swaggie hums along, then hands
    # over a free eucalyptus tea.
    if entities:
        swaggie = next((e for e in entities
                        if getattr(e, 'npc_id', None) == 'swaggie'
                        and entity.distance_to(e) <= 8), None)
        # The tea is a one-per-roadhouse-visit favour (the didgeridoo is not
        # consumed when nothing is stunned, so without this it would farm
        # unlimited free heals).
        if swaggie is not None and not getattr(swaggie, '_tea_given', False):
            from loader_functions.items import create_item  # deferred: import cycle
            tea = create_item('eucalyptus_tea', 1, entity.x, entity.y)
            if any(r.get('item_added') for r in entity.inventory.add_item(tea)):
                swaggie._tea_given = True
                results.append({'message': Message(
                    "The Swaggie hums along and hands you a free Eucalyptus "
                    "Tea. ('Good drone. Reminds me of '04.')", C.LIGHT_GREEN)})
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


def use_plasma_grenade(entity, entities=None, fov_map=None, game_map=None, damage=250, radius=3, target_x=None, target_y=None, noise_map=None):
    results = []

    if not _in_fov(fov_map, game_map, target_x, target_y):
        results.append({'consumed': False,
                        'message': Message('You cannot target a tile outside of your field of view!', C.YELLOW)})
        return results

    if noise_map:
        noise_map.emit(target_x, target_y, 10, 'explosion')

    results.append({'consumed': True,
                    'message': Message('The plasma grenade explodes, burning everything within {0} tiles!'.format(radius), C.ORANGE)})

    for e in entities:
        if e.distance(target_x, target_y) <= radius and e.fighter:
            results.append({'message': Message('The {0} gets burned for {1} hit points!'.format(e.name, damage), C.ORANGE)})
            results.extend(e.fighter.take_damage(damage))
    return results


def use_stun_grenade(entity, entities=None, fov_map=None, game_map=None, target_x=None, target_y=None, noise_map=None):
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


def use_ray_gun(entity, entities=None, fov_map=None, game_map=None, damage=80, maximum_range=11, noise_map=None):
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


def eat_emu_egg(entity, amount=550, entities=None, fov_map=None, game_map=None, noise_map=None):
    """Emu egg: food + heal + a temporary speed boost."""
    results = []
    entity.fighter.heal(amount)
    _feed(entity, 250)
    entity.fighter.add_status('speed', 10)
    results.append({'consumed': True,
                    'message': Message('You eat the emu egg. (speed +10 turns)', C.GREEN)})
    return results


def eat_taipan_meat(entity, amount=300, entities=None, fov_map=None, game_map=None, noise_map=None):
    """Taipan meat: food + heal + temporary poison resistance."""
    results = []
    entity.fighter.heal(amount)
    _feed(entity, 180)
    entity.fighter.add_status('poison_resist', 20)
    results.append({'consumed': True,
                    'message': Message('You eat the taipan meat. (poison resistance +20 turns)', C.GREEN)})
    return results


def eat_dropbear_meat(entity, amount=400, entities=None, fov_map=None, game_map=None, noise_map=None):
    """Dropbear meat: food + heal + brief invisibility, but it draws
    attention. The scent is a REAL noise event: dropbears (HEARING 12)
    path toward the player, fulfilling the flavour text mechanically."""
    results = []
    entity.fighter.heal(amount)
    _feed(entity, 220)
    entity.fighter.add_status('invisible', 15)
    if noise_map:
        noise_map.emit(entity.x, entity.y, 12, 'dropbear_scent')
    results.append({'consumed': True,
                    'message': Message('You eat the dropbear meat. You feel invisible... but something stirs.', C.GREEN)})
    results.append({'message': Message('A hungry Dropbear has caught your scent!', C.DARK_RED)})
    return results


def use_neuralyzer(entity, entities=None, fov_map=None, game_map=None, noise_map=None):
    """MIB flash: wipe the memory of visible dingoes and scatter them.

    Easter eggs: flashing the Agent J cameo is blocked (he's seen this bit
    before), and flashing nothing flashes YOURSELF -- which resets the
    rest timer (you forget why you were resting)."""
    results = []
    entities = entities or []
    cameo = any(e.sprite_id == 'agent_j_cameo'
                and _in_fov(fov_map, game_map, e.x, e.y) for e in entities)
    if cameo:
        results.append({'consumed': False, 'message': Message(
            "He shields his eyes. 'I've seen this bit before, mate.'",
            C.LIGHT_VIOLET)})
        return results

    dingo_found = False
    for e in entities:
        if e.ai and isinstance(e.ai, DingoAI) and _in_fov(fov_map, game_map, e.x, e.y):
            e.ai.last_seen = None
            e.ai.state = FLEE
            e.ai.state_turns = 0
            dingo_found = True

    if dingo_found:
        results.append({'consumed': True,
                        'message': Message(
                            'FLASH! Their eyes go blank. The dingoes forget you exist and scatter!',
                            C.CYAN)})
    else:
        results.append({'consumed': False, 'message': Message(
            'FLASH! High-frequency red light reflects uselessly. Turns out '
            'canine brains are uniquely susceptible to MIB tech. Or maybe '
            'they just hate bright lights.', C.LIGHT_RED)})
        results.append({'wait_timer_reset': True, 'message': Message(
            'You flash yourself by accident. You forget why you were resting.',
            C.LIGHT_VIOLET)})
    return results


def read_datalog(entity, text='', entities=None, fov_map=None, game_map=None, noise_map=None):
    """Read a log entry without consuming the item."""
    return [{'consumed': False, 'message': Message(text, C.LIGHT_CYAN)}]


def eat_vegemite(entity, amount=150, entities=None, fov_map=None, game_map=None, noise_map=None):
    """Vegemite: heal + a one-time permanent +1 defense. The first tin
    rides in with a disclaimer (the creator's views are not the game's;
    Marmite is objectively superior); the sixth tin walks it back. Eating
    three rations grants the Acquired Taste: dropbears refuse to ambush
    you (they respect the smell now) and the rest-timer dropbear never
    triggers."""
    results = []
    entity.fighter.heal(amount)
    _feed(entity, 150)

    # Track total lifetime vegemite consumption for the escalating bit below.
    entity.vegemite_count = getattr(entity, 'vegemite_count', 0) + 1

    if entity.fighter.base_defense_bonus == 0:
        entity.fighter.base_defense_bonus = 1
        results.append({
            'consumed': True,
            'message': Message('You eat the vegemite. (+1 permanent defense)', C.GREEN)
        })

        # --- EASTER EGG: the disclaimer rides in with the first tin. ---
        results.append({
            'message': Message(
                "Disclaimer: The views expressed in this game do not reflect "
                "those of the creator. Vegemite is included purely for "
                "cultural authenticity; however, Marmite is objectively "
                "superior.",
                C.LIGHT_VIOLET)
        })

    else:
        results.append({
            'consumed': True,
            'message': Message('You eat the vegemite. (your defense is already hardened)', C.YELLOW)
        })

    # --- EASTER EGG: walk it back on the 6th tin. ---
    if entity.vegemite_count == 6:
        results.append({
            'message': Message(
                "Disclaimer #2: Guys, chill. I'm American and I think both "
                "Vegemite and Marmite on toast are lovely. I only slightly "
                "intended to start an international incident with my "
                "previous claim that Marmite is superior. Really I was just "
                "curious to find out if Australia lied about having a "
                "nuclear arsenal.",
                C.LIGHT_VIOLET)
        })

    # Eating three rations grants the Acquired Taste: dropbears refuse to
    # ambush you (they respect the smell now).
    if entity.vegemite_count >= 3 and not getattr(entity.fighter, 'acquired_taste', False):
        entity.fighter.acquired_taste = True
        results.append({'message': Message(
            'You have acquired a taste for Vegemite. Dropbears will respect '
            'the smell now.', C.LIGHT_GREEN)})

    return results
