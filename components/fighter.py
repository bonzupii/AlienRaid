# -*- coding: utf-8 -*-
"""Fighter component: hp/defense/power/attack, no libtcod."""

from components.game_messages import Message
from renderer import palette as C

# Hunger clock (Qwen's roguelike-balance pass): the counter ticks down one
# per player action. Generous thresholds; food feeds, medicine never does.
HUNGER_MAX = 600       # starts full; a ration restores a chunk of this
HUNGRY_AT = 300        # at/below: rest-healing stops (passive regen gates
                       # separately at 80% satiety -- see systems.py)
STARVING_AT = 120      # at/below: small HP drain each turn, can kill
HUNGER_LABELS = {'well-fed': 'well fed', 'hungry': 'hungry',
                 'starving': 'STARVING'}


def hunger_tier(fighter):
    """'well-fed' / 'hungry' / 'starving' from a fighter's hunger counter."""
    h = getattr(fighter, 'hunger', HUNGER_MAX)
    if h <= STARVING_AT:
        return 'starving'
    if h <= HUNGRY_AT:
        return 'hungry'
    return 'well-fed'


class Fighter:
    def __init__(self, hp, defense, power, xp=0, thorns=0, base_defense_bonus=0):
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.xp = xp
        self.thorns = thorns  # damage dealt back to whoever hits this fighter
        self.base_defense_bonus = base_defense_bonus  # permanent bonus (vegemite)
        self.status = {}  # 'webbed': n, 'speed': n, 'invisible': n, ...
        # Easter-egg bookkeeping (getattr-guarded at use sites for old saves).
        self.acquired_taste = False   # 3 vegemite rations: dropbears respect you
        # Hunger clock (getattr-guarded at read sites for old saves).
        self.hunger = HUNGER_MAX

    @property
    def max_hp(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.max_hp_bonus
        else:
            bonus = 0
        return self.base_max_hp + bonus

    @property
    def power(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.power_bonus
        else:
            bonus = 0
        return self.base_power + bonus

    @property
    def defense(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.defense_bonus
        else:
            bonus = 0
        return self.base_defense + self.base_defense_bonus + bonus

    def take_damage(self, amount, attacker=None):
        results = []
        self.hp -= amount
        if self.hp <= 0:
            results.append({'dead': self.owner, 'xp': self.xp})
        # Let the world know who hurt us (pack morale reacts to this).
        if attacker is not None and attacker is not self.owner:
            results.append({'hurt': self.owner, 'attacker': attacker})
        # Quills / thorns: the attacker gets pricked back. Note the intent:
        # if the killing blow and the quill-prick both land, the results carry
        # two 'dead' entries (kill_monster + kill_player) — death-quills on a
        # mutual kill, handled fine by process_player_turn_results.
        if self.thorns and attacker is not None and attacker is not self.owner:
            if attacker.fighter and attacker.fighter.hp > 0:
                attacker.fighter.hp -= self.thorns
                results.append({'message': Message(
                    '{0} is pricked by {1}\'s quills!'.format(
                        attacker.name, self.owner.name), C.WHITE)})
                if attacker.fighter.hp <= 0:
                    results.append({'dead': attacker, 'xp': attacker.fighter.xp})
        return results

    def heal(self, amount):
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def add_status(self, status_type, turns):
        """Add or extend a timed status effect."""
        if status_type in self.status:
            self.status[status_type] += turns
        else:
            self.status[status_type] = turns

    def has_status(self, status_type):
        return status_type in self.status and self.status[status_type] > 0

    def tick_statuses(self):
        """Decrement all status timers; returns the list of expired ones."""
        expired = []
        for status_type in list(self.status.keys()):
            self.status[status_type] -= 1
            if self.status[status_type] <= 0:
                expired.append(status_type)
                del self.status[status_type]
        return expired

    def attack(self, target):
        results = []
        damage = self.power - target.fighter.defense

        if damage > 0:
            results.append({'message': Message('{0} attacks {1} for {2} hit points.'.format(
                self.owner.name.capitalize(), target.name, str(damage)), C.WHITE)})
            results.extend(target.fighter.take_damage(damage, attacker=self.owner))
        else:
            results.append({'message': Message('{0} attacks {1} but does no damage.'.format(
                self.owner.name.capitalize(), target.name), C.WHITE)})

        return results
