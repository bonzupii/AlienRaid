# -*- coding: utf-8 -*-
"""Scripted NPC dialogue trees and choices (Phase F).

``get_dialogue(npc, player)`` returns ``(header, [(option_text, key), ...])``
and ``process_dialogue_choice`` applies the chosen option. Dialogue state
lives on the player's ``Reputation``.
"""

from loader_functions.items import create_item
from components.game_messages import Message
from renderer import palette as C


def _has_choice(player, choice):
    return any(getattr(item, 'item_choice', None) == choice
               for item in player.inventory.items)


def get_dialogue(npc, player):
    """Return (header, [(option_text, choice_key), ...]) for an NPC."""
    rep = player.reputation
    npc_id = getattr(npc, 'npc_id', None)

    if npc_id == 'mib':
        if rep.mib_quest_state == 'not_started':
            return ("Agent J adjusts his sunglasses. 'Civilian, you are in an "
                    "active exclusion zone conducting UNLICENSED DOCUMENTARY "
                    "activity. Explain yourself.'", [
                        ("Prove you're lost and just surviving.", 'mib_lost'),
                        ("Show him a salvaged alien ship part.", 'mib_part'),
                        ("Play completely dumb.", 'mib_dumb'),
                        ("Threaten him with your tentaclaws.", 'mib_threat'),
                    ])
        if rep.mib_quest_state == 'given':
            if _has_choice(player, 'neuralyzer'):
                return ("'My Neuralyzer! You actually got it back from the "
                        "AECD checkpoint. Hand it over and I'll make it worth "
                        "your while.'", [
                            ("Hand over the Neuralyzer.", 'mib_complete'),
                        ])
            return ("'Did you retrieve my Neuralyzer from the AECD checkpoint "
                    "on floor 11 yet?'", [
                        ("Working on it.", 'mib_busy'),
                    ])
        return ("'Good luck out there. Remember: you saw nothing.'", [
            ("Leave", 'exit'),
        ])

    if npc_id == 'aecd':
        return ("AECD Officer: 'Halt! State your clearance level before "
                "entering the deep caverns.'", [
                    ("Claim an outback research permit.", 'aecd_permit'),
                    ("Bribe with a Vegemite Ration.", 'aecd_bribe'),
                    ("Snarl and shove past.", 'aecd_attack'),
                ])

    if npc_id == 'swaggie':
        return ("Swaggie: 'G'day mate! Cold tea and rumour's on the house. "
                "What d'ya wanna know?'", [
                    ("Ask where the ship parts land.", 'swaggie_parts'),
                    ("Ask about the black suits.", 'swaggie_mib'),
                    ("Buy a tin of Eucalyptus Tea.", 'swaggie_tea'),
                ])

    return ("The survivor nods quietly.", [("Leave", 'exit')])


def process_dialogue_choice(npc, choice, player, dungeon_level, message_log):
    """Apply the chosen dialogue option. Messages go to the log."""
    rep = player.reputation
    npc_id = getattr(npc, 'npc_id', None)

    if npc_id == 'mib':
        if choice == 'mib_lost':
            rep.update('mib', 10)
            rep.mib_quest_state = 'given'
            message_log.add_message(Message(
                "Agent J: 'Fine. My Neuralyzer was confiscated at floor 11. "
                "Fetch it and we'll talk.'", C.CYAN))
        elif choice == 'mib_part':
            rep.update('mib', 20)
            rep.mib_quest_state = 'given'
            message_log.add_message(Message(
                "Agent J's jaw drops. 'That's alien tech! Find my Neuralyzer "
                "at floor 11 and I'll authorize your exit.'", C.CYAN))
        elif choice == 'mib_dumb':
            rep.update('mib', -5)
            rep.mib_quest_state = 'given'
            message_log.add_message(Message(
                "Agent J sighs. 'Clueless. Just recover my Neuralyzer from "
                "floor 11.'", C.CYAN))
        elif choice == 'mib_threat':
            rep.update('mib', -20)
            message_log.add_message(Message(
                "Agent J draws a noisy cricket. You back off quickly!", C.LIGHT_RED))
        elif choice == 'mib_busy':
            message_log.add_message(Message(
                "Agent J taps his watch impatiently.", C.LIGHT_GRAY))
        elif choice == 'mib_complete':
            rep.update('mib', 30)
            rep.mib_quest_state = 'completed'
            for item in list(player.inventory.items):
                if getattr(item, 'item_choice', None) == 'neuralyzer':
                    player.inventory.remove_item(item)
                    break
            grenade = create_item('plasma_grenade', dungeon_level,
                                  player.x, player.y)
            player.inventory.add_item(grenade)
            message_log.add_message(Message(
                "Agent J hands you a Plasma Grenade and a knowing nod.",
                C.LIGHT_GREEN))

    elif npc_id == 'aecd':
        if choice == 'aecd_permit':
            rep.update('aecd', 10)
            message_log.add_message(Message(
                "AECD Officer: 'Permit checks out. Pass through.'", C.LIGHT_GREEN))
        elif choice == 'aecd_bribe':
            for item in list(player.inventory.items):
                if getattr(item, 'item_choice', None) == 'vegemite_ration':
                    player.inventory.remove_item(item)
                    rep.update('aecd', 15)
                    message_log.add_message(Message(
                        "AECD Officer pockets the Vegemite and waves you "
                        "through.", C.LIGHT_GREEN))
                    return
            message_log.add_message(Message(
                "AECD Officer: 'Bribery is a federal offence. Move along.'",
                C.LIGHT_RED))
        elif choice == 'aecd_attack':
            rep.update('aecd', -10)
            message_log.add_message(Message(
                "You shove past. The Officer scribbles your description into "
                "a very large binder.", C.LIGHT_ORANGE))

    elif npc_id == 'swaggie':
        if choice == 'swaggie_parts':
            message_log.add_message(Message(
                "Swaggie: 'Shiny wreckage always falls at floors 5, 10, 15 "
                "and 20!'", C.YELLOW))
        elif choice == 'swaggie_mib':
            message_log.add_message(Message(
                "Swaggie: 'Them men in black suits came from above, just "
                "like your ship!'", C.YELLOW))
        elif choice == 'swaggie_tea':
            tea = create_item('eucalyptus_tea', dungeon_level,
                              player.x, player.y)
            player.inventory.add_item(tea)
            message_log.add_message(Message(
                "Swaggie hands you a hot tin of Eucalyptus Tea.", C.LIGHT_GREEN))
