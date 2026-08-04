#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explicit game systems extracted from the main loop:
passive regen, the wait/dropbear ambush mechanic, and player turn-result
processing. Keeping them as pure functions makes the loop readable and the
rules testable.
"""

from random import randint

from components.fighter import HUNGER_MAX, hunger_tier
from components.game_messages import Message
from components.game_states import GameStates
from functions.death_functions import kill_monster, kill_player
from renderer import palette as C


def _wearing(player, choice):
    """True if the player is wearing an equipped item with this choice."""
    eq = getattr(player, 'equipment', None)
    return bool(eq) and eq.wearing_item(choice)


def passive_regen(player, message_log):
    """Small chance to slowly regenerate a bit of HP while moving. Ned
    Kelly's breastplate is too heavy to move-and-heal in, and hunger
    stops regeneration entirely (Qwen balance pass: slower rate too --
    1/40 proc, max_hp/300 step)."""
    if _wearing(player, 'ned_kelly_breastplate'):
        return
    if hunger_tier(player.fighter) != 'well-fed':
        return
    if randint(0, 39) != 39:
        return
    if player.fighter.hp >= player.fighter.max_hp:
        return
    step = max(1, round(player.fighter.max_hp / 300))
    if player.fighter.hp >= player.fighter.max_hp - step:
        player.fighter.hp = player.fighter.max_hp
        message_log.add_message(Message('Your wounds are completely healed!', C.GREEN))
    else:
        player.fighter.hp += step


def speed_free_action(player):
    """While the speed boost is active, every second player action is a
    FREE action: the enemy turn (and all timers) are skipped, mirroring
    the monsters' SLOW parity pattern. Returns True when the turn should
    skip the enemy phase."""
    if not player.fighter.has_status('speed'):
        return False
    player._speed_tick = getattr(player, '_speed_tick', 0) + 1
    return player._speed_tick % 2 == 0


def tick_hunger(player, message_log):
    """Advance the hunger clock one completed player action. Hungry stops
    regeneration (see passive_regen/wait_action); starving drains a little
    HP every tick through the normal death path. Returns True if the
    player starved to death this tick (the caller should go PLAYER_DEAD)."""
    hunger = getattr(player.fighter, 'hunger', HUNGER_MAX)
    prev_tier = hunger_tier(player.fighter)
    player.fighter.hunger = max(0, hunger - 1)
    tier = hunger_tier(player.fighter)
    if tier != prev_tier:
        if tier == 'hungry':
            message_log.add_message(Message(
                'You are getting hungry. Regeneration falters.', C.YELLOW))
        elif tier == 'starving':
            message_log.add_message(Message(
                'You are starving! Find food, Wrpgnyth.', C.RED))
    if tier == 'starving':
        player.fighter.hp -= max(1, player.fighter.max_hp // 300)
        if player.fighter.hp <= 0:
            message, state = kill_player(player)
            message_log.add_message(message)
            return True
    return False


def wait_action(player, message_log, wait_timer):
    """Rest: heal a chunk of HP, but over-resting summons the Dropbear.
    With the Acquired Taste the rest-timer dropbear never triggers; Ned
    Kelly's breastplate halves the healing (too heavy to rest properly).

    Returns ``(new_wait_timer, game_state)``.
    """
    acquired = getattr(player.fighter, 'acquired_taste', False)
    if acquired:
        wait_timer = min(wait_timer, 55)
    if wait_timer <= 55:
        wait_timer += 5
        # Hungry players can still rest (the dropbear ambush stays priced)
        # but recover nothing -- hunger gates out-of-combat healing.
        if hunger_tier(player.fighter) != 'well-fed':
            message_log.add_message(Message(
                'You are too hungry to rest and recover.', C.YELLOW))
            return wait_timer, GameStates.ENEMY_TURN
        if player.fighter.hp < player.fighter.max_hp:
            divisor = 100 if _wearing(player, 'ned_kelly_breastplate') else 50
            step = max(1, round(player.fighter.max_hp / divisor))
            if player.fighter.hp >= player.fighter.max_hp - step:
                player.fighter.hp = player.fighter.max_hp
                message_log.add_message(Message(
                    'You rest for a moment. Your wounds are completely healed!', C.GREEN))
            else:
                player.fighter.hp += step
                message_log.add_message(Message(
                    'You rest for a moment. Your wounds are beginning to feel slightly better.', C.GREEN))
            return wait_timer, GameStates.ENEMY_TURN
        message_log.add_message(Message('You rest for a moment.', C.YELLOW))
        return wait_timer, GameStates.ENEMY_TURN

    # Over-rested: the Dropbear strikes.
    if player.fighter.hp >= 501:
        player.fighter.hp -= 500
        message_log.add_message(Message(
            'You begin to rest, but the Dropbear drops down on your back and begins feasting on your flesh!',
            C.DARK_RED))
        return wait_timer, GameStates.ENEMY_TURN

    player.fighter.hp -= 500
    message_log.add_message(Message(
        'You begin to rest, but the Dropbear drops down on your back and feasts on your flesh!',
        C.DARK_RED))
    return wait_timer, GameStates.PLAYER_DEAD


def process_player_turn_results(results, player, entities, game_map, message_log,
                                game_state, previous_game_state=None, wait_timer=0):
    """Apply every player-turn result. Returns ``(game_state,
    targeting_item, wait_timer)`` (the timer can be reset by the
    neuralyzer self-flash)."""
    targeting_item = None
    cancelled = False

    for result in results:
        message = result.get('message')
        dead_entity = result.get('dead')
        item_added = result.get('item_added')
        item_consumed = result.get('consumed')
        item_dropped = result.get('item_dropped')
        equip = result.get('equip')
        targeting = result.get('targeting')
        targeting_cancelled = result.get('targeting_cancelled')
        xp = result.get('xp')
        wait_timer_reset = result.get('wait_timer_reset')

        if wait_timer_reset:
            wait_timer = 0

        if message:
            message_log.add_message(message)

        if dead_entity:
            species = getattr(dead_entity, 'species', None)
            if dead_entity == player:
                message, game_state = kill_player(dead_entity)
            else:
                message, dropped_items = kill_monster(dead_entity,
                                                      game_map.dungeon_level)
                # Escaped ADF bioweapons: culling them dents ADF standing.
                if species in ('cassowary', 'feral_camel') and player.reputation:
                    player.reputation.update('adf', -5)
                    message_log.add_message(Message(
                        'The ADF will remember this.', C.LIGHT_RED))
                for dropped_item in dropped_items:
                    entities.append(dropped_item)
                    message_log.add_message(Message(
                        'The {0} dropped a {1}!'.format(dead_entity.name,
                                                        dropped_item.name),
                        C.LIGHT_GREEN))
            message_log.add_message(message)

        if item_added:
            entities.remove(item_added)
            game_state = GameStates.ENEMY_TURN

        if item_consumed:
            game_state = GameStates.ENEMY_TURN

        if item_dropped:
            entities.append(item_dropped)
            game_state = GameStates.ENEMY_TURN

        if equip:
            equip_results = player.equipment.toggle_equip(equip)
            for equip_result in equip_results:
                equipped = equip_result.get('equipped')
                dequipped = equip_result.get('dequipped')
                if equipped:
                    message_log.add_message(Message('You equipped the {0}'.format(equipped.name)))
                if dequipped:
                    message_log.add_message(Message('You unequipped the {0}'.format(dequipped.name)))
            game_state = GameStates.ENEMY_TURN

        if targeting:
            targeting_item = targeting
            message_log.add_message(targeting_item.item.targeting_message)

        if targeting_cancelled:
            cancelled = True
            message_log.add_message(Message('Targeting cancelled.'))

        if xp:
            leveled_up = player.level.add_xp(xp)
            message_log.add_message(Message('You gain {0} experience points.'.format(xp)))
            if leveled_up:
                message_log.add_message(Message(
                    'Your battle skills grow stronger! Welcome to level {0}'.format(player.level.current_level) + '!',
                    C.YELLOW))
                game_state = GameStates.LEVEL_UP

    if cancelled and previous_game_state is not None:
        game_state = previous_game_state
        targeting_item = None

    return game_state, targeting_item, wait_timer
