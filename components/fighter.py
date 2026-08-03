# -*- coding: utf-8 -*-
"""Fighter component: hp/defense/power/attack, no libtcod."""

from components.game_messages import Message
from renderer import palette as C


class Fighter:
    def __init__(self, hp, defense, power, xp=0, thorns=0):
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.xp = xp
        self.thorns = thorns  # damage dealt back to whoever hits this fighter

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
        return self.base_defense + bonus

    def take_damage(self, amount, attacker=None):
        results = []
        self.hp -= amount
        if self.hp <= 0:
            results.append({'dead': self.owner, 'xp': self.xp})
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
