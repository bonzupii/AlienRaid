#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monster AI — Turochamp-inspired heuristics.

Turochamp (Turing) won games by evaluating a small set of candidate moves
with a hand-tuned scoring function (material + mobility + king safety)
instead of searching deep. We do the same: every turn each monster scores a
tiny action space — wait, the 8 neighbouring tiles, and (for some species) a
special ability — with a species-tuned evaluation, then executes the best
cheap action. Pathfinding is at most one A* per monster per turn.

Species differ only in their weight table and optional special abilities, so
the behaviour is data-driven and cheap to tune.
"""

import math
from random import randint

from components.game_messages import Message
from renderer import palette as C

# 8-neighbour offsets used for cover/escape-route counting.
_NEIGHBOURS = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))

# State-machine labels (graze / alert / hunt / flee).
GRAZE = 'graze'
ALERT = 'alert'
HUNT = 'hunt'
FLEE = 'flee'


class _PhantomFighter:
    """Inert fighter for _PhantomTarget: the AI's scoring/attack code can
    run against a remembered position without crashing or dealing damage."""

    hp = 1
    max_hp = 1
    power = 0
    defense = 0

    def take_damage(self, amount, attacker=None):
        return []

    def attack(self, target):
        return []


class _PhantomTarget:
    """Stand-in for a position a monster is chasing (a remembered spot or
    a noise source) so the normal distance / pathfinding logic can be
    reused without a real target entity."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.name = 'the last place'
        self.fighter = _PhantomFighter()


def _in_fov(fov_map, game_map, x, y):
    if not (0 <= x < game_map.width and 0 <= y < game_map.height):
        return False
    return fov_map[y * game_map.width + x] != 0


def _line_of_sight(game_map, start, end):
    """Bresenham line between two entities; True if no wall blocks it."""
    x0, y0 = start.x, start.y
    x1, y1 = end.x, end.y
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        if (x0, y0) == (x1, y1):
            return True
        if (x0, y0) != (start.x, start.y) and game_map.is_wall(x0, y0):
            return False
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


class HeuristicMonster:
    """Base class. Subclasses tune the weights / add specials."""

    # --- Species tuning knobs -------------------------------------------------
    AGGRESSION = 1.0   # desire to close in / attack
    CAUTION = 0.0      # self-preservation (avoid losing fights, flee when hurt)
    PACK = 0.0         # value of staying near allies / fighting with numbers
    AMBUSH = 0.0       # prefer waiting unseen and striking from cover
    ERRATIC = 0.0      # randomness in chosen step
    FLEE_HP = 0.0      # hp fraction below which the monster retreats
    ENGAGE = 1         # preferred engagement distance (tiles)
    FAST = 1           # tiles moved per turn (emu = 2)
    SLOW = 1           # acts once every SLOW turns (wombat / croc = 2)
    HEARING = 0        # radius at which the monster hears noise events
    SMELL = 0          # radius at which the monster smells the target
    STATE = GRAZE      # starting state-machine state

    def __init__(self):
        self.slow_tick = 0   # incremented each turn; act when % SLOW == 0
        self.retreat = 0     # bee: retreat turns after attacking
        self.last_seen = None  # (x, y) of the last known target position
        self.state = self.STATE
        self.state_turns = 0

    # ------------------------------------------------------------------ public
    def take_turn(self, target, fov_map, game_map, entities, noise_map=None):
        results = []
        monster = self.owner

        if not (target.fighter and target.fighter.hp > 0):
            return results

        in_fov = _in_fov(fov_map, game_map, monster.x, monster.y)
        if in_fov:
            self.last_seen = (target.x, target.y)
        elif self.SMELL and monster.distance_to(target) <= self.SMELL:
            # Scent-trackers (dingoes) shadow the player without sight.
            self.last_seen = (target.x, target.y)
            in_fov = True

        # Dormant until seen / smelled / heard (classic roguelike behaviour).
        if not in_fov and self.last_seen is None:
            if noise_map and self.HEARING > 0:
                noise = noise_map.get_noise_at(monster.x, monster.y)
                if noise > 0:
                    strongest = noise_map.find_strongest_noise()
                    if strongest:
                        noise_x, noise_y, _ = strongest
                        phantom = _PhantomTarget(noise_x, noise_y)
                        if monster.distance_to(phantom) > 1:
                            monster.move_astar(phantom, entities, game_map)
            return results

        # Hit-and-run species count down their retreat turns.
        self.retreat = max(0, self.retreat - 1)
        # Slow species act only every SLOW turns.
        self.slow_tick += 1
        if self.slow_tick % self.SLOW != 0:
            return results

        dist = monster.distance_to(target)

        # State machine (graze / alert / hunt / flee).
        self._update_state(target, fov_map, game_map, dist)
        self.state_turns += 1

        # Out of sight: chase the last known position instead of the player.
        effective_target = target
        if not in_fov and self.last_seen:
            effective_target = _PhantomTarget(self.last_seen[0], self.last_seen[1])
            if monster.distance_to(effective_target) < 2:
                self.last_seen = None
        dist = monster.distance_to(effective_target)

        # 1) Special ability phase (pounce / spit / swoop / howl...).
        results.extend(self._special_turn(effective_target, fov_map, game_map, entities, dist))
        if target.fighter.hp <= 0:
            return results
        dist = monster.distance_to(effective_target)

        # 2) Melee when adjacent (and the heuristic wants to fight). Only
        # ever strike the real target — a phantom is just a spot to search.
        if dist < 2:
            if effective_target is target and self._should_attack(effective_target, game_map, entities):
                results.extend(self._attack(effective_target))
                self._after_attack()
            return results

        # 3) Ambush: hold still while unseen and far away.
        if self.AMBUSH and not _in_fov(fov_map, game_map, monster.x, monster.y) and dist > self.ENGAGE + 1:
            return results

        # 4) Pick the best step (or wait) by scoring candidate tiles.
        dx, dy = self._pick_step(effective_target, game_map, entities, dist)
        if dx == 0 and dy == 0:
            return results
        for _ in range(max(1, self.FAST)):
            nx, ny = monster.x + dx, monster.y + dy
            if game_map.is_blocked(nx, ny) or self._blocked_by(entities, nx, ny):
                break
            monster.move(dx, dy)
            if monster.distance_to(effective_target) < 2:
                break
        return results

    # ------------------------------------------------------------ to override
    def _special_turn(self, target, fov_map, game_map, entities, dist):
        return []

    def _update_state(self, target, fov_map, game_map, dist):
        """State-machine hook; species override this to define their own
        graze/alert/hunt/flee transitions."""
        pass

    def _attack(self, target):
        return self.owner.fighter.attack(target)

    def _after_attack(self):
        pass

    # ------------------------------------------------------------ heuristics
    def _blocked_by(self, entities, x, y):
        for e in entities:
            if e.blocks and e.x == x and e.y == y:
                return True
        return False

    def _damage_vs(self, target):
        return self.owner.fighter.power - target.fighter.defense

    def _threat_from(self, target):
        return target.fighter.power - self.owner.fighter.defense

    def _hp_ratio(self):
        fighter = self.owner.fighter
        return fighter.hp / max(1, fighter.max_hp)

    def _allies_near(self, entities, x, y):
        allies = 0
        for e in entities:
            if e is self.owner or not e.ai or not e.fighter:
                continue
            if type(e.ai) is type(self) and math.hypot(e.x - x, e.y - y) <= 6:
                allies += 1
        return allies

    def _should_attack(self, target, game_map, entities):
        monster = self.owner
        if self.state == FLEE:
            return False
        if self._hp_ratio() <= self.FLEE_HP:
            return False
        if self.PACK:
            allies = self._allies_near(entities, monster.x, monster.y)
            target_hp_ratio = target.fighter.hp / max(1, target.fighter.max_hp)
            if allies < 1 and target_hp_ratio > 0.35:
                return False
        if self.CAUTION > 0.5 and self._damage_vs(target) <= 0:
            return False
        return True

    def _pick_step(self, target, game_map, entities, dist):
        monster = self.owner
        best = (0, 0)
        best_score = -1e9

        candidates = [(0, 0)]
        candidates += [(x, y) for x in (-1, 0, 1) for y in (-1, 0, 1) if (x, y) != (0, 0)]

        for dx, dy in candidates:
            nx, ny = monster.x + dx, monster.y + dy
            if not game_map.in_bounds(nx, ny) or game_map.is_blocked(nx, ny):
                continue
            if self._blocked_by(entities, nx, ny):
                continue
            if self.state == FLEE:
                # Run away: score tiles by distance from the target.
                score = math.hypot(target.x - nx, target.y - ny)
            else:
                score = self._score_tile(target, game_map, nx, ny, dist, entities)
            if score > best_score:
                best_score = score
                best = (dx, dy)
        return best

    def _score_tile(self, target, game_map, nx, ny, dist, entities):
        monster = self.owner
        new_dist = math.hypot(target.x - nx, target.y - ny)
        score = 0.0

        # Closing in vs backing off.
        score += self.AGGRESSION * (dist - new_dist)
        score += self.CAUTION * (new_dist - dist)

        # Prefer sitting at the species' engagement distance.
        if 1 < new_dist <= self.ENGAGE:
            score += self.AGGRESSION * 2.0

        # Threat: don't march into a fight we would lose (if cautious).
        threat = self._threat_from(target)
        damage = self._damage_vs(target)
        if threat > damage and new_dist < 3:
            score -= (3 - new_dist) * self.CAUTION * 3.0

        # Cover (ambush species like wall/floor adjacency).
        if self.AMBUSH:
            cover = 0
            for (ox, oy) in _NEIGHBOURS:
                cx, cy = nx + ox, ny + oy
                if not game_map.in_bounds(cx, cy) or game_map.is_wall(cx, cy):
                    cover += 1
            score += self.AMBUSH * cover

        # Pack cohesion.
        if self.PACK:
            score += self.PACK * self._allies_near(entities, nx, ny)

        # Erratic movement.
        if self.ERRATIC:
            score += self.ERRATIC * randint(-2, 2)

        return score


# ---------------------------------------------------------------------------
# Species
# ---------------------------------------------------------------------------

class KangaAI(HeuristicMonster):
    """Territorial bruiser: grazes until provoked, charges in, never
    retreats, winds up telegraphed kicks."""
    AGGRESSION = 1.4
    CAUTION = 0.1
    ERRATIC = 0.3
    FLEE_HP = 0.0
    ENGAGE = 1
    STATE = GRAZE

    def __init__(self):
        super().__init__()
        self.charge = 0

    def _update_state(self, target, fov_map, game_map, dist):
        # Grazing until the player comes close, then it commits.
        if self.state == GRAZE and dist <= 3:
            self.state = HUNT
            self.state_turns = 0

    def _should_attack(self, target, game_map, entities):
        if self.state != HUNT:
            return False
        return super()._should_attack(target, game_map, entities)

    def _attack(self, target):
        results = []
        if self.charge == 1:
            # Second contact after the wind-up: the real kick lands.
            self.charge = 0
            self.owner.sprite_id = 'kanga'
            bonus = int(self.owner.fighter.power * 0.5)
            results.append({'message': Message('The Kanga winds up a mighty kick!', C.LIGHT_ORANGE)})
            damage = self.owner.fighter.power + bonus - target.fighter.defense
            if damage > 0:
                results.append({'message': Message('The Kanga kicks {0} for {1} hit points!'.format(target.name, damage), C.WHITE)})
                results.extend(target.fighter.take_damage(damage, attacker=self.owner))
            return results
        # First contact: rear up and telegraph the kick for the next hit.
        self.charge = 1
        self.owner.sprite_id = 'kanga_rear'
        results.extend(self.owner.fighter.attack(target))
        results.append({'message': Message('The Kanga rears up, telegraphing a kick!', C.LIGHT_ORANGE)})
        return results


class WallarooAI(KangaAI):
    """A stockier, meaner kangaroo: same charge, weaker kick."""
    AGGRESSION = 1.1
    CAUTION = 0.2
    ERRATIC = 0.4
    FLEE_HP = 0.0

    def _attack(self, target):
        results = []
        self.charge += 1
        if self.charge >= 2:
            bonus = int(self.owner.fighter.power * 0.3)
            results.append({'message': Message('The Wallaroo slams into you with a heavy body-check!', C.LIGHT_ORANGE)})
            damage = self.owner.fighter.power + bonus - target.fighter.defense
            if damage > 0:
                results.append({'message': Message('The Wallaroo body-checks {0} for {1} hit points!'.format(target.name, damage), C.WHITE)})
                results.extend(target.fighter.take_damage(damage, attacker=self.owner))
            self.charge = 0
        else:
            results.extend(self.owner.fighter.attack(target))
        return results


class JoeyAI(HeuristicMonster):
    """Timid: keeps distance, flees when threatened, fights only when cornered."""
    AGGRESSION = 0.6
    CAUTION = 0.9
    FLEE_HP = 0.55
    ENGAGE = 1
    ERRATIC = 0.5

    def _should_attack(self, target, game_map, entities):
        if self._hp_ratio() <= self.FLEE_HP:
            return False
        # Only fight if cornered or the target is nearly dead.
        target_hp = target.fighter.hp / max(1, target.fighter.max_hp)
        free = 0
        for (dx, dy) in _NEIGHBOURS:
            if not game_map.is_blocked(self.owner.x + dx, self.owner.y + dy):
                free += 1
        return free <= 2 or target_hp <= 0.25


class WallabyAI(HeuristicMonster):
    """Skittish hopper: circles at range 2, strikes when the target is weak."""
    AGGRESSION = 0.9
    CAUTION = 0.4
    ERRATIC = 1.2
    FLEE_HP = 0.3
    ENGAGE = 2


class TreeKangaAI(HeuristicMonster):
    """Tree-dweller: prefers cover, waits unseen, retreats up walls when hurt."""
    AGGRESSION = 0.8
    CAUTION = 0.5
    AMBUSH = 1.0
    FLEE_HP = 0.35
    ENGAGE = 1


class DingoAI(HeuristicMonster):
    """Pack hunter: circles, only commits with numbers or a wounded target."""
    AGGRESSION = 1.0
    CAUTION = 0.3
    PACK = 1.5
    ENGAGE = 2
    FLEE_HP = 0.25
    ERRATIC = 0.3
    SMELL = 8  # can smell the player from far away

    def _special_turn(self, target, fov_map, game_map, entities, dist):
        results = []
        if dist > 6 and randint(0, 25) == 0:
            results.append({'message': Message('A Dingo howls somewhere nearby...', C.LIGHT_GRAY)})
        return results


class GoannaAI(HeuristicMonster):
    """Ambush lizard: darts to cover, strikes from flank, flees when hurt."""
    AGGRESSION = 0.8
    CAUTION = 0.6
    AMBUSH = 1.2
    FLEE_HP = 0.4
    ENGAGE = 1
    ERRATIC = 0.4


class KillerBeeAI(HeuristicMonster):
    """Swarm hit-and-run: stings, then retreats; erratic zigzag."""
    AGGRESSION = 1.3
    CAUTION = 0.5
    ERRATIC = 1.5
    FLEE_HP = 0.3
    ENGAGE = 1

    def _after_attack(self):
        self.retreat = 2

    def _score_tile(self, target, game_map, nx, ny, dist, entities):
        monster = self.owner
        if self.retreat > 0:
            # Prioritise tiles away from the target.
            return math.hypot(target.x - nx, target.y - ny)
        return super()._score_tile(target, game_map, nx, ny, dist, entities)


class DropbearAI(HeuristicMonster):
    """Ambush pouncer: waits unseen, then leaps onto the target."""
    AGGRESSION = 1.2
    CAUTION = 0.2
    AMBUSH = 1.5
    FLEE_HP = 0.2
    ENGAGE = 1
    HEARING = 12  # hears explosions, grenades and didgeridoos from afar

    def __init__(self):
        super().__init__()
        self.pounce_cooldown = 0

    def _special_turn(self, target, fov_map, game_map, entities, dist):
        results = []
        monster = self.owner
        self.pounce_cooldown = max(0, self.pounce_cooldown - 1)
        if self.pounce_cooldown == 0 and dist <= 5 and dist >= 2:
            # Leapt up to 2 tiles along the approach, then attack with bonus.
            step = 0
            while step < 2 and monster.distance_to(target) > 1.5:
                dx = 1 if target.x > monster.x else (-1 if target.x < monster.x else 0)
                dy = 1 if target.y > monster.y else (-1 if target.y < monster.y else 0)
                if dx == 0 and dy == 0:
                    break
                nx, ny = monster.x + dx, monster.y + dy
                if game_map.is_blocked(nx, ny) or self._blocked_by(entities, nx, ny):
                    break
                monster.move(dx, dy)
                step += 1
            if monster.distance_to(target) < 2:
                self.pounce_cooldown = 4
                results.append({'message': Message('The Dropbear pounces down onto you!', C.LIGHT_ORANGE)})
                damage = self.owner.fighter.power + int(self.owner.fighter.power * 0.4) - target.fighter.defense
                if damage > 0:
                    results.append({'message': Message('The Dropbear rakes {0} for {1} hit points!'.format(target.name, damage), C.WHITE)})
                    results.extend(target.fighter.take_damage(damage, attacker=self.owner))
                self._after_attack()
        return results


class TaipanAI(HeuristicMonster):
    """Venomous striker: keeps distance and spits poison, flees when cornered."""
    AGGRESSION = 0.4
    CAUTION = 0.6
    FLEE_HP = 0.3
    ENGAGE = 3

    def __init__(self):
        super().__init__()
        self.spit_cooldown = 0

    def _special_turn(self, target, fov_map, game_map, entities, dist):
        results = []
        self.spit_cooldown = max(0, self.spit_cooldown - 1)
        if self.spit_cooldown == 0 and 2 <= dist <= 5 and _line_of_sight(game_map, self.owner, target):
            self.spit_cooldown = 3
            damage = int(self.owner.fighter.power * 0.7)
            results.append({'message': Message('The Taipan spits a stream of venom!', C.GREEN)})
            if damage > 0:
                results.append({'message': Message('The venom burns {0} for {1} hit points!'.format(target.name, damage), C.WHITE)})
                results.extend(target.fighter.take_damage(damage, attacker=self.owner))
        return results


class EmuAI(HeuristicMonster):
    """Fast runner: closes quickly, keeps moving."""
    AGGRESSION = 1.0
    CAUTION = 0.2
    FLEE_HP = 0.15
    ENGAGE = 1
    FAST = 2
    ERRATIC = 0.3


class WombatAI(HeuristicMonster):
    """Slow tank: ignores you until hurt once, then hunts forever."""
    AGGRESSION = 0.7
    CAUTION = 0.0
    FLEE_HP = 0.0
    ENGAGE = 1
    SLOW = 2  # acts every other turn

    def _update_state(self, target, fov_map, game_map, dist):
        # Hurt once -> hunting forever (no going back).
        if self.state == GRAZE and self.owner.fighter.hp < self.owner.fighter.max_hp:
            self.state = HUNT
            self.state_turns = 0

    def _should_attack(self, target, game_map, entities):
        if self.state != HUNT:
            return False
        return super()._should_attack(target, game_map, entities)


class MagpieAI(HeuristicMonster):
    """Swooper: closes to range 2 then dive-bombs and strikes."""
    AGGRESSION = 0.9
    CAUTION = 0.5
    ERRATIC = 1.2
    FLEE_HP = 0.3
    ENGAGE = 2

    def __init__(self):
        super().__init__()
        self.swoop_cooldown = 0

    def _special_turn(self, target, fov_map, game_map, entities, dist):
        results = []
        monster = self.owner
        self.swoop_cooldown = max(0, self.swoop_cooldown - 1)
        if self.swoop_cooldown == 0 and dist <= 3 and dist > 1.5:
            self.swoop_cooldown = 4
            # Swoop 2 tiles straight at the target, then strike.
            moved = 0
            while moved < 2 and monster.distance_to(target) > 1.5:
                dx = 1 if target.x > monster.x else (-1 if target.x < monster.x else 0)
                dy = 1 if target.y > monster.y else (-1 if target.y < monster.y else 0)
                if dx == 0 and dy == 0:
                    break
                nx, ny = monster.x + dx, monster.y + dy
                if game_map.is_blocked(nx, ny) or self._blocked_by(entities, nx, ny):
                    break
                monster.move(dx, dy)
                moved += 1
            if monster.distance_to(target) < 2:
                results.append({'message': Message('The Magpie swoops down and pecks at you!', C.LIGHT_GRAY)})
                results.extend(monster.fighter.attack(target))
        return results


class CassowaryAI(HeuristicMonster):
    """Living weapon: never flees, kicks with crushing force."""
    AGGRESSION = 1.3
    CAUTION = 0.0
    FLEE_HP = 0.0
    ENGAGE = 1

    def __init__(self):
        super().__init__()
        self.claw_ready = False

    def _attack(self, target):
        results = []
        if self.claw_ready:
            # The telegraphed dagger-claw strike lands.
            self.claw_ready = False
            self.owner.sprite_id = 'cassowary'
            damage = int(self.owner.fighter.power * 2) - target.fighter.defense
            results.append({'message': Message('The Cassowary lashes out with its dagger claw!', C.LIGHT_ORANGE)})
            if damage > 0:
                results.append({'message': Message('The Cassowary rips {0} for {1} hit points!'.format(target.name, damage), C.WHITE)})
                results.extend(target.fighter.take_damage(damage, attacker=self.owner))
            else:
                results.append({'message': Message('The Cassowary strikes but does no damage.', C.WHITE)})
            return results
        if randint(0, 100) < 30:
            # Rear up: visible telegraph, the big claw lands next contact.
            self.claw_ready = True
            self.owner.sprite_id = 'cassowary_rear'
            results.append({'message': Message('The Cassowary rears back, dagger claw raised!', C.LIGHT_ORANGE)})
            results.extend(self.owner.fighter.attack(target))
        else:
            results.extend(self.owner.fighter.attack(target))
        return results


class CrocodileAI(HeuristicMonster):
    """Ambush hunter: lies in wait near walls, then strikes savagely."""
    AGGRESSION = 1.1
    CAUTION = 0.1
    AMBUSH = 1.3
    FLEE_HP = 0.0
    ENGAGE = 1
    SLOW = 2  # acts every other turn


class EchidnaAI(HeuristicMonster):
    """Living tank: plods forward every other turn and never flees; its
    quills prick anyone foolish enough to hit it."""
    AGGRESSION = 0.6
    CAUTION = 0.0
    FLEE_HP = 0.0
    ENGAGE = 1
    SLOW = 2  # acts every other turn


class FunnelWebAI(HeuristicMonster):
    """Fast venomous ambusher: closes quickly and fang-bites with venom."""
    AGGRESSION = 1.2
    CAUTION = 0.2
    FLEE_HP = 0.2
    ENGAGE = 1
    ERRATIC = 0.6

    def _attack(self, target):
        results = []
        if randint(0, 100) < 40:
            damage = int(self.owner.fighter.power * 1.3) - target.fighter.defense
            results.append({'message': Message(
                'The Funnel-web Spider sinks its fangs into {0}!'.format(target.name), C.GREEN)})
            if damage > 0:
                results.append({'message': Message(
                    'The venom burns {0} for {1} hit points!'.format(target.name, damage), C.WHITE)})
                results.extend(target.fighter.take_damage(damage, attacker=self.owner))
            else:
                results.append({'message': Message('The bite leaves no mark.', C.WHITE)})
        else:
            results.extend(self.owner.fighter.attack(target))
        return results


class QuokkaAI(HeuristicMonster):
    """Friendly marsupial: approaches curiously, never attacks."""
    AGGRESSION = 0.0
    CAUTION = 0.8
    FLEE_HP = 0.5
    ENGAGE = 2
    ERRATIC = 0.5

    def _should_attack(self, target, game_map, entities):
        return False  # never attacks


class ThornyDevilAI(HeuristicMonster):
    """Camouflaged lizard: slow, thorny, ambushes from cover."""
    AGGRESSION = 0.7
    CAUTION = 0.4
    AMBUSH = 1.0
    FLEE_HP = 0.3
    ENGAGE = 1
    SLOW = 2


class BlueTongueAI(HeuristicMonster):
    """Docile lizard: flees when threatened."""
    AGGRESSION = 0.3
    CAUTION = 0.9
    FLEE_HP = 0.6
    ENGAGE = 1
    ERRATIC = 0.6


class WedgeTailedEagleAI(HeuristicMonster):
    """Swooper like the magpie, but faster on the approach."""
    AGGRESSION = 1.1
    CAUTION = 0.4
    ERRATIC = 1.0
    FLEE_HP = 0.25
    ENGAGE = 2

    def __init__(self):
        super().__init__()
        self.swoop_cooldown = 0

    def _special_turn(self, target, fov_map, game_map, entities, dist):
        results = []
        self.swoop_cooldown = max(0, self.swoop_cooldown - 1)
        if self.swoop_cooldown == 0 and dist <= 4 and dist > 1.5:
            self.swoop_cooldown = 5
            moved = 0
            while moved < 2 and self.owner.distance_to(target) > 1.5:
                dx = 1 if target.x > self.owner.x else (-1 if target.x < self.owner.x else 0)
                dy = 1 if target.y > self.owner.y else (-1 if target.y < self.owner.y else 0)
                if dx == 0 and dy == 0:
                    break
                nx, ny = self.owner.x + dx, self.owner.y + dy
                if game_map.is_blocked(nx, ny) or self._blocked_by(entities, nx, ny):
                    break
                self.owner.move(dx, dy)
                moved += 1
            if self.owner.distance_to(target) < 2:
                results.append({'message': Message('The Wedge-tailed Eagle swoops down and strikes!', C.LIGHT_GRAY)})
                results.extend(self.owner.fighter.attack(target))
        return results


class FeralCamelAI(HeuristicMonster):
    """Neutral tank: only fights once it has been hurt."""
    AGGRESSION = 0.5
    CAUTION = 0.2
    FLEE_HP = 0.0
    ENGAGE = 1
    STATE = GRAZE

    def _update_state(self, target, fov_map, game_map, dist):
        if self.state == GRAZE and self.owner.fighter.hp < self.owner.fighter.max_hp:
            self.state = HUNT
            self.state_turns = 0

    def _should_attack(self, target, game_map, entities):
        if self.state != HUNT:
            return False
        return super()._should_attack(target, game_map, entities)


class PythonAI(HeuristicMonster):
    """Constrictor: wraps its coils around the target for several turns."""
    AGGRESSION = 1.2
    CAUTION = 0.3
    FLEE_HP = 0.2
    ENGAGE = 1

    def __init__(self):
        super().__init__()
        self.constricting = False
        self.constrict_turns = 0

    def _attack(self, target):
        results = []
        if not self.constricting and randint(0, 100) < 40:
            self.constricting = True
            self.constrict_turns = 3
            results.append({'message': Message('The Python wraps around {0}!'.format(target.name), C.LIGHT_ORANGE)})
            damage = int(self.owner.fighter.power * 1.5) - target.fighter.defense
            if damage > 0:
                results.append({'message': Message('The Python constricts {0} for {1} hit points!'.format(target.name, damage), C.WHITE)})
                results.extend(target.fighter.take_damage(damage, attacker=self.owner))
        elif self.constricting:
            self.constrict_turns -= 1
            damage = int(self.owner.fighter.power * 1.2) - target.fighter.defense
            if damage > 0:
                results.append({'message': Message('The Python squeezes {0} for {1} hit points!'.format(target.name, damage), C.WHITE)})
                results.extend(target.fighter.take_damage(damage, attacker=self.owner))
            if self.constrict_turns <= 0:
                self.constricting = False
                results.append({'message': Message('The Python releases {0}.'.format(target.name), C.LIGHT_GRAY)})
        else:
            results.extend(self.owner.fighter.attack(target))
        return results


class RedbackAI(HeuristicMonster):
    """Venomous spider: webs its target on a successful bite."""
    AGGRESSION = 1.3
    CAUTION = 0.3
    FLEE_HP = 0.25
    ENGAGE = 1
    ERRATIC = 0.7

    def _attack(self, target):
        results = []
        if randint(0, 100) < 50:
            damage = int(self.owner.fighter.power * 1.4) - target.fighter.defense
            results.append({'message': Message(
                'The Redback Spider bites {0} and injects venom!'.format(target.name), C.GREEN)})
            if damage > 0:
                results.append({'message': Message(
                    'The venom burns {0} for {1} hit points!'.format(target.name, damage), C.WHITE)})
                results.extend(target.fighter.take_damage(damage, attacker=self.owner))
            # Web the target: it loses its next move.
            if hasattr(target, 'fighter') and target.fighter:
                results.append({'webbed': target, 'turns': 1})
        else:
            results.append({'message': Message('The bite leaves no mark.', C.WHITE)})
            results.extend(self.owner.fighter.attack(target))
        return results


class StunnedMonster:
    """Wraps another AI for a few turns of confused wandering (stun grenade)."""

    def __init__(self, previous_ai, number_of_turns=10):
        self.previous_ai = previous_ai
        self.number_of_turns = number_of_turns

    def take_turn(self, target, fov_map, game_map, entities, noise_map=None):
        results = []
        if self.number_of_turns > 0:
            random_x = self.owner.x + randint(0, 2) - 1
            random_y = self.owner.y + randint(0, 2) - 1
            if random_x != self.owner.x and random_y != self.owner.y:
                self.owner.move_towards(random_x, random_y, game_map, entities)
            self.number_of_turns -= 1
        else:
            self.owner.ai = self.previous_ai
            results.append({'message': Message('The {0} is no longer stunned!'.format(self.owner.name), C.VIOLET)})
        return results
