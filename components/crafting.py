# -*- coding: utf-8 -*-
"""Crafting system and recipes (Phase D).

Recipes combine carried items (tracked by their ``item_choice``) into a new
item. The menu layer reads ``RECIPES``, ``craftable``, ``result_name`` and
``needs_text``; the launcher calls ``craft_item``.
"""

from loader_functions.items import create_item, DISPLAY_NAMES
from components.game_messages import Message
from renderer import palette as C

RECIPES = {
    'med_kit': {
        'name': 'Med Kit',
        'ingredients': {'lesser_med_kit': 2, 'eucalyptus_tea': 1},
        'desc': 'Combine 2 Lesser Med Kits and 1 Eucalyptus Tea.',
    },
    'taipan_fang_knife': {
        'name': 'Taipan Fang Knife',
        'ingredients': {'boomerang': 1, 'taipan_meat': 1},
        'desc': 'Craft a venom-laced blade from a Boomerang and Taipan Meat.',
    },
    'dropbear_fur_vest': {
        'name': 'Dropbear Fur Vest',
        'ingredients': {'dropbear_meat': 1, 'whippy_willow_twig': 1},
        'desc': 'Weave a protective vest from Dropbear Meat and a Whippy Willow Twig.',
    },
    'reinforced_aluminite_brace': {
        'name': 'Reinforced Aluminite Brace',
        'ingredients': {'aluminite_neck_brace': 1, 'dropbear_claw_gauntlet': 1},
        'desc': 'Reinforce your neck brace with Dropbear Claws.',
    },
    'plasma_grenade': {
        'name': 'Plasma Grenade',
        'ingredients': {'shock_charge': 1, 'ray_gun': 1},
        'desc': 'Rig a ray gun battery to a shock charge to build a Plasma Grenade.',
    },
    'golden_wattle_salve': {
        'name': 'Golden Wattle Salve',
        'ingredients': {'bush_tucker': 1, 'funnel_web_antivenom': 1},
        'desc': 'Refine Bush Tucker and Antivenom into Golden Wattle Salve.',
    },
}


def _count_ingredients(player):
    """item_choice -> number carried (equipped items stay in the bag)."""
    counts = {}
    for item in player.inventory.items:
        choice = getattr(item, 'item_choice', None)
        if choice:
            counts[choice] = counts.get(choice, 0) + 1
    return counts


def craftable(player):
    """recipe_id -> True if the player currently holds every ingredient."""
    counts = _count_ingredients(player)
    result = {}
    for rid, recipe in RECIPES.items():
        result[rid] = all(
            counts.get(ing, 0) >= need for ing, need in recipe['ingredients'].items())
    return result


def result_name(rid):
    return RECIPES[rid]['name']


def needs_text(rid, player):
    """Human-readable list of the ingredients still missing for ``rid``."""
    counts = _count_ingredients(player)
    recipe = RECIPES[rid]
    missing = []
    for ing, need in recipe['ingredients'].items():
        have = counts.get(ing, 0)
        if have < need:
            name = DISPLAY_NAMES.get(ing, ing)
            missing.append('{0}x {1}'.format(need - have, name))
    return ', '.join(missing) or 'nothing'


def craft_item(player, recipe_key, entities, dungeon_level):
    """Consume the ingredients and add the crafted result to the inventory."""
    results = []
    recipe = RECIPES.get(recipe_key)
    if not recipe or not craftable(player).get(recipe_key, False):
        results.append({'message': Message(
            'You lack the required ingredients!', C.YELLOW)})
        return results

    for ing, need in recipe['ingredients'].items():
        consumed = 0
        for item in list(player.inventory.items):
            if getattr(item, 'item_choice', None) == ing:
                player.inventory.remove_item(item)
                consumed += 1
                if consumed >= need:
                    break

    new_item = create_item(recipe_key, dungeon_level, player.x, player.y)
    player.inventory.add_item(new_item)
    results.append({
        'consumed': True,
        'message': Message('You crafted a {0}!'.format(recipe['name']), C.LIGHT_GREEN),
    })
    return results
