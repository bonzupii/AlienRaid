#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explicit game systems extracted from the main loop:
passive regen, the wait/dropbear ambush mechanic, and player turn-result
processing. Keeping them as pure functions makes the loop readable and the
rules testable.
"""

from random import randint

from components.game_messages import Message
from components.game_states import GameStates
from functions.death_functions import kill_monster, kill_player
from renderer import palette as C


def passive_regen(player, message_log):
    """Small chance to slowly regenerate a bit of HP while moving."""
    if randint(0, 20) != 20:
        return
    if player.fighter.hp >= player.fighter.max_hp:
        return
    step = max(1, round(player.fighter.max_hp / 150))
    if player.fighter.hp >= player.fighter.max_hp - step:
        player.fighter.hp = player.fighter.max_hp
        message_log.add_message(Message('Your wounds are completely healed!', C.GREEN))
    else:
        player.fighter.hp += step


def wait_action(player, message_log, wait_timer):
    """Rest: heal a chunk of HP, but over-resting summons the Dropbear.

    Returns ``(new_wait_timer, game_state)``.
    """
    if wait_timer <= 55:
        wait_timer += 5
        if player.fighter.hp < player.fighter.max_hp:
            step = max(1, round(player.fighter.max_hp / 50))
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
                                game_state, previous_game_state=None):
    """Apply every player-turn result. Returns ``(game_state, targeting_item)``."""
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

        if message:
            message_log.add_message(message)

        if dead_entity:
            if dead_entity == player:
                message, game_state = kill_player(dead_entity)
            else:
                message, dropped_item = kill_monster(dead_entity,
                                                     game_map.dungeon_level)
                if dropped_item:
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

    return game_state, targeting_item
