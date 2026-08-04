#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Item and equipment templates + factory."""

from components.entity import Entity
from components.equipment_slots import EquipmentSlots
from components.equippable import Equippable
from components.item import Item
from components.game_messages import Message
from functions.render_order import RenderOrder
from functions.item_functions import (heal, morphine_pack, gain_xp,
                                      use_shock_charge, use_boomerang,
                                      use_didgeridoo, use_plasma_grenade,
                                      use_stun_grenade, use_ray_gun,
                                      eat_emu_egg, eat_taipan_meat,
                                      eat_dropbear_meat, eat_vegemite,
                                      use_neuralyzer, read_datalog,
                                      use_dads_thong, use_meat_pie, use_esky,
                                      use_ned_kelly_chest)
from renderer import palette as C

# spawn tables: [chance, min_dungeon_level] pairs
ITEM_TABLES = {
    # consumables
    'lesser_med_kit':      [[30, 1], [20, 4], [10, 7], [1, 10]],
    'med_kit':             [[5, 5], [20, 8], [30, 11], [20, 14], [10, 18]],
    'morphine_pack':       [[5, 4], [15, 6], [10, 9], [5, 12]],
    'golden_wattle_salve': [[0, 8], [8, 10], [12, 13], [10, 16]],
    'vegemite_ration':     [[10, 1], [10, 3], [8, 6], [5, 9]],
    'bush_tucker':         [[0, 3], [8, 5], [10, 8], [12, 11], [10, 15]],
    'eucalyptus_tea':      [[8, 1], [10, 4], [8, 7]],
    'funnel_web_antivenom': [[0, 6], [10, 9], [10, 12]],
    'emu_egg':             [[0, 8], [8, 10], [8, 14]],
    'taipan_meat':         [[0, 6], [15, 9], [25, 12], [20, 15], [15, 19]],
    'dropbear_meat':       [[0, 8], [15, 10], [25, 13], [30, 16]],
    # weapons / tools
    'plasma_grenade':      [[8, 3], [12, 5], [10, 8], [6, 12]],
    'stun_grenade':        [[10, 2], [12, 4], [8, 7]],
    'shock_charge':        [[8, 1], [10, 3], [8, 6], [5, 10]],
    'ray_gun':             [[4, 5], [6, 7], [5, 10]],
    'boomerang':           [[0, 4], [10, 6], [8, 9], [5, 13]],
    'dads_thong':          [[0, 6], [8, 10], [6, 14]],
    'didgeridoo':          [[0, 6], [8, 8], [10, 11]],
    'meat_pie':            [[0, 8], [6, 12]],
    'tinny':               [[5, 1], [4, 3], [3, 6]],
    'esky_of_holding':     [[0, 12], [6, 15]],
    'neuralyzer':          [[0, 11]],  # quest item: only placed by the AECD camp
    'mib_datalog':         [[0, 6], [5, 10]],
    # equipment
    'tentacruels':               [[5, 4], [6, 7]],
    'energy_shield':             [[10, 5], [8, 9]],
    'whippy_willow_twig':        [[15, 1], [10, 3], [5, 6]],
    'taipan_fang_knife':         [[0, 8], [8, 10], [6, 14]],
    'dropbear_claw_gauntlet':    [[0, 10], [8, 12], [8, 16]],
    'quokka_bone_club':          [[0, 12], [6, 14], [5, 18]],
    'spare_sunglasses':          [[0, 4], [8, 7], [6, 11]],
    'goanna_skin_hat':           [[8, 1], [12, 3], [8, 6]],
    'emu_feather_cap':           [[0, 6], [10, 8], [8, 12]],
    'cassowary_crest_crown':     [[0, 12], [6, 14], [6, 18]],
    'aluminite_neck_brace':      [[8, 2], [10, 4], [6, 8]],
    'reinforced_aluminite_brace': [[0, 8], [6, 10], [6, 14]],
    'dropbear_fur_vest':         [[6, 3], [8, 6], [6, 10]],
    'wombat_hide_cuirass':       [[0, 7], [6, 9], [6, 13]],
    'croc_hide_cuirass':         [[0, 14], [5, 16], [5, 19]],
}

# choice -> (sprite_id, color, kind, data)
# kind: 'consume' (Item), 'equip' (Equippable)
ITEM_DEFS = {
    # consumables ------------------------------------------------------------
    'lesser_med_kit':      ('icon_cross', C.VIOLET, 'consume', {'use_function': heal, 'amount': 200}),
    'med_kit':             ('icon_cross', C.MEDKIT_RED, 'consume', {'use_function': morphine_pack, 'amount': 500}),
    'morphine_pack':       ('icon_bottle', C.MORPHINE_BROWN, 'consume', {'use_function': morphine_pack, 'amount': 350, 'is_morphine': True}),
    'golden_wattle_salve': ('icon_bottle', C.GOLD, 'consume', {'use_function': heal, 'amount': 800}),
    'vegemite_ration':     ('icon_ration', C.DARK_YELLOW, 'consume', {'use_function': eat_vegemite, 'amount': 150}),
    'bush_tucker':         ('icon_star', C.LIGHT_GREEN, 'consume', {'use_function': gain_xp, 'amount': 400}),
    'eucalyptus_tea':      ('icon_tea', (60, 120, 60), 'consume', {'use_function': heal, 'amount': 250}),
    'funnel_web_antivenom': ('icon_bottle', (60, 120, 60), 'consume', {'use_function': heal, 'amount': 400}),
    'emu_egg':             ('icon_ration', (245, 245, 235), 'consume', {'use_function': eat_emu_egg, 'amount': 550}),
    'taipan_meat':         ('icon_ration', (139, 125, 60), 'consume', {'use_function': eat_taipan_meat, 'amount': 300}),
    'dropbear_meat':       ('icon_ration', C.DROPBEAR_GREY, 'consume', {'use_function': eat_dropbear_meat, 'amount': 400}),
    'plasma_grenade':      ('icon_grenade', C.CYAN, 'consume', {
        'use_function': use_plasma_grenade, 'targeting': True,
        'targeting_message': Message('Left-click an enemy to lob the Plasma Grenade at it, or right-click to cancel.', C.LIGHT_CYAN),
        'damage': 250, 'radius': 3}),
    'stun_grenade':        ('icon_grenade', C.STUN_GREEN, 'consume', {
        'use_function': use_stun_grenade, 'targeting': True,
        'targeting_message': Message('Left-click an enemy to lob the Stun Grenade at it, or right-click to cancel.', C.LIGHT_CYAN)}),
    'shock_charge':        ('icon_bolt', C.YELLOW, 'consume', {'use_function': use_shock_charge, 'damage': 350, 'maximum_range': 5}),
    'ray_gun':             ('icon_gun', C.RAYGUN_SILVER, 'consume', {'use_function': use_ray_gun, 'damage': 80, 'maximum_range': 11}),
    'boomerang':           ('icon_boomerang', (160, 120, 40), 'consume', {'use_function': use_boomerang, 'damage': 120, 'maximum_range': 8}),
    'dads_thong':          ('icon_boomerang', (150, 90, 70), 'consume', {'use_function': use_dads_thong, 'damage': 140, 'maximum_range': 8}),
    'didgeridoo':          ('icon_tube', (120, 80, 40), 'consume', {'use_function': use_didgeridoo, 'turns': 6}),
    'neuralyzer':          ('icon_neuralyzer', C.SILVER, 'consume', {'use_function': use_neuralyzer}),
    'mib_datalog':         ('icon_datalog', (60, 60, 70), 'consume', {
        'use_function': read_datalog,
        'text': 'MIB LOG: Unidentified crash at floor 1. All witnesses to be neuralyzed.'}),
    'meat_pie':            ('icon_ration', (160, 100, 50), 'consume', {'use_function': use_meat_pie}),
    'tinny':               ('icon_bottle', (200, 150, 60), 'consume', {'use_function': heal, 'amount': 150}),
    'esky_of_holding':     ('icon_bottle', (60, 100, 160), 'consume', {'use_function': use_esky}),
    'black_box':           ('icon_datalog', (40, 40, 50), 'consume', {
        'use_function': read_datalog,
        'text': '...if anyone finds this, the documentary is cancelled. Tell no one. Especially the agent.'}),
    'dev_mug':             ('icon_ration', (230, 230, 235), 'consume', {
        'use_function': read_datalog,
        'text': 'Still warm. Somehow. Copyright 2019-2026.'}),
    'emu_war_plaque':      ('icon_datalog', (120, 110, 90), 'consume', {
        'use_function': read_datalog,
        'text': 'The Australian Army lost. The emus have never forgotten.'}),
    'ned_kelly_chest':     ('icon_cross', (120, 90, 50), 'consume', {'use_function': use_ned_kelly_chest}),
    # equipment --------------------------------------------------------------
    'tentacruels':                ('icon_tentacle', C.PURPLE, 'equip', {'slot': EquipmentSlots.TENTACLE, 'power_bonus': 40}),
    'energy_shield':              ('icon_shield', C.CYAN, 'equip', {'slot': EquipmentSlots.TENTACLE, 'defense_bonus': 50, 'max_hp_bonus': 250}),
    'whippy_willow_twig':         ('icon_twig', C.TWIG_BROWN, 'equip', {'slot': EquipmentSlots.TENTACLE, 'power_bonus': 15}),
    'taipan_fang_knife':          ('icon_tentacle', (139, 125, 60), 'equip', {'slot': EquipmentSlots.TENTACLE, 'power_bonus': 35, 'defense_bonus': 5}),
    'dropbear_claw_gauntlet':     ('icon_tentacle', C.DROPBEAR_GREY, 'equip', {'slot': EquipmentSlots.TENTACLE, 'power_bonus': 25, 'defense_bonus': 10}),
    'quokka_bone_club':           ('icon_twig', (150, 120, 70), 'equip', {'slot': EquipmentSlots.TENTACLE, 'power_bonus': 45, 'defense_bonus': 5}),
    'spare_sunglasses':           ('icon_hat', (30, 30, 30), 'equip', {'slot': EquipmentSlots.HELMET}),
    'goanna_skin_hat':            ('icon_hat', C.HAT_GREEN, 'equip', {'slot': EquipmentSlots.HELMET, 'power_bonus': 5, 'defense_bonus': 10}),
    'emu_feather_cap':            ('icon_hat', (110, 90, 60), 'equip', {'slot': EquipmentSlots.HELMET, 'power_bonus': 8, 'defense_bonus': 6}),
    'cassowary_crest_crown':      ('icon_hat', (40, 60, 120), 'equip', {'slot': EquipmentSlots.HELMET, 'power_bonus': 15, 'defense_bonus': 4}),
    'aluminite_neck_brace':       ('icon_neck', C.SILVER, 'equip', {'slot': EquipmentSlots.NECK, 'defense_bonus': 5}),
    'reinforced_aluminite_brace': ('icon_neck', C.GOLD, 'equip', {'slot': EquipmentSlots.NECK, 'defense_bonus': 12, 'power_bonus': 8}),
    'dropbear_fur_vest':          ('icon_vest', C.VEST_GREY, 'equip', {'slot': EquipmentSlots.CHEST_PLATE, 'max_hp_bonus': 100, 'defense_bonus': 25}),
    'wombat_hide_cuirass':        ('icon_vest', (90, 90, 90), 'equip', {'slot': EquipmentSlots.CHEST_PLATE, 'max_hp_bonus': 200, 'defense_bonus': 40}),
    'croc_hide_cuirass':          ('icon_vest', (30, 80, 40), 'equip', {'slot': EquipmentSlots.CHEST_PLATE, 'max_hp_bonus': 300, 'defense_bonus': 55}),
    'ned_kelly_breastplate':       ('icon_vest', (140, 130, 120), 'equip', {
        'slot': EquipmentSlots.CHEST_PLATE, 'defense_bonus': 90, 'max_hp_bonus': 200}),
}


DISPLAY_NAMES = {
    'lesser_med_kit': 'Lesser Med Kit', 'med_kit': 'Med Kit',
    'morphine_pack': 'Morphine Pack', 'golden_wattle_salve': 'Golden Wattle Salve',
    'vegemite_ration': 'Vegemite Ration', 'bush_tucker': 'Bush Tucker',
    'eucalyptus_tea': 'Eucalyptus Tea', 'funnel_web_antivenom': 'Funnel-web Antivenom',
    'emu_egg': 'Emu Egg', 'taipan_meat': 'Taipan Meat',
    'dropbear_meat': 'Dropbear Meat', 'plasma_grenade': 'Plasma Grenade',
    'stun_grenade': 'Stun Grenade', 'shock_charge': 'Shock Charge',
    'ray_gun': 'Ray Gun', 'boomerang': 'Boomerang', 'dads_thong': "Dad's Thong",
    'didgeridoo': 'Didgeridoo', 'meat_pie': 'Meat Pie', 'tinny': 'Warm Tinny',
    'esky_of_holding': 'Esky of Holding', 'black_box': 'Black Box',
    'dev_mug': "Developer's Mug", 'emu_war_plaque': 'Emu War Plaque',
    'ned_kelly_chest': 'Rusted Chest', 'ned_kelly_breastplate': "Ned Kelly's Breastplate",
    'spare_sunglasses': 'Spare Sunglasses',
    'neuralyzer': 'Neuralyzer', 'mib_datalog': 'MIB Datalog',
    'tentacruels': 'Tentacruel', 'energy_shield': 'Energy Shield',
    'whippy_willow_twig': 'Whippy Willow Twig', 'taipan_fang_knife': "Taipan Fang Knife",
    'dropbear_claw_gauntlet': 'Dropbear Claw Gauntlet', 'quokka_bone_club': 'Quokka Bone Club',
    'goanna_skin_hat': 'Goanna Skin Hat',
    'emu_feather_cap': 'Emu Feather Cap', 'cassowary_crest_crown': 'Cassowary Crest Crown',
    'aluminite_neck_brace': 'Aluminite Neck Brace', 'reinforced_aluminite_brace': 'Reinforced Aluminite Brace',
    'dropbear_fur_vest': 'Dropbear Fur Vest', 'wombat_hide_cuirass': 'Wombat Hide Cuirass',
    'croc_hide_cuirass': 'Croc Hide Cuirass',
}


def create_item(choice, dungeon_level, x, y):
    """Build an item/equipment Entity of the given choice at (x, y)."""
    sprite_id, color, kind, data = ITEM_DEFS[choice]
    name = DISPLAY_NAMES[choice]

    if kind == 'equip':
        equippable = Equippable(**data)
        item = Entity(x, y, sprite_id, color, name,
                      render_order=RenderOrder.ITEM, equippable=equippable)
    else:
        item_component = Item(**data)
        item = Entity(x, y, sprite_id, color, name,
                      render_order=RenderOrder.ITEM, item=item_component)
    item.item_choice = choice
    return item
