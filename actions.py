import rl

import actors
import ui

class Action:
    def __init__(self, actor, cost, repeat=False):
        self.actor = actor
        self.cost = cost
        self.repeat = repeat

    def can_perform(self):
        return self.actor.energy >= self.cost

    def perform(self):
        return self.actor.consume_energy(self.cost)

    def replace(self, other):
        self.actor.energy += self.cost
        return other

class Wait(Action):
    def __init__(self, actor):
        super().__init__(actor, actor.speed)

    def perform(self):
        if super().perform():
            return True
        return False


class Move(Action):
    def __init__(self, actor, dx, dy):
        super().__init__(actor, 10)
        self.dx = dx
        self.dy = dy

    def perform(self):
        if super().perform():
            x, y = self.actor.x + self.dx, self.actor.y + self.dy
            if x < 0 or x >= level.width or y < 0 or y >= level.height:
                return False
            # TODO: refrain from walking in lava
            if not level.is_blocked(x, y):
                self.actor.x = x
                self.actor.y = y
                if self.actor is player:
                    level.compute_fov()
                return True
            elif not level.blocked[x, y]: # not blocked by a wall
                for obj in level.objects:
                    if obj.x == x and obj.y == y and isinstance(obj, actors.Monster):
                        if obj.is_hostile(self.actor):
                            return self.replace(Attack(self.actor, obj))
                        else:
                            if obj is player:
                                return False
                            # swap places
                            self.actor.x, obj.x = obj.x, self.actor.x
                            self.actor.y, obj.y = obj.y, self.actor.y
                            if self.actor is player:
                                ui.message(self.actor.get_name('swap{s} places with') + ' ' + obj.get_name() + '.', rl.LIGHTGRAY)
                                level.compute_fov()
                            return True
        return False


class Repeat(Action):
    def __init__(self, action):
        super().__init__(action.actor, 0, True)
        self.action = action

    def can_perform(self):
        return self.action.can_perform()

    def perform(self):
        result = self.action.perform()
        if not result:
            self.repeat = False
            self.actor.action = None
        else:
            self.action.actor.energy += self.action.cost
        return result


class Attack(Action):
    def __init__(self, actor, target):
        super().__init__(actor, 10)
        self.target = target
    
    def perform(self):
        if super().perform():
            self.actor.attack(self.target)
            return True
        return False


class AutoExplore(Action):
    def __init__(self, actor):
        super().__init__(actor, actor.speed, True)
        self.dx = self.dy = 0

    def can_perform(self):
        level.compute_autoexplore()
        moves = level.to_visit.view(player.x - 1, player.y - 1, 3, 3)
        x, y = moves.argmin(-1)
        self.dx, self.dy = x - 1, y - 1
        return moves[1, 1] > 0

    def perform(self):
        action = Move(self.actor, self.dx, self.dy)
        return action.perform()


class MoveTowards(Action):
    def __init__(self, actor, x, y):
        super().__init__(actor, actor.speed, True)
        self.target_x = x
        self.target_y = y

    def can_perform(self):
        path = level.blocked.shortest_path(self.actor.x, self.actor.y, self.target_x, self.target_y)
        if len(path) > 0:
            self.x, self.y = path[0]
            return True
        self.repeat = False
        return False

    def perform(self):
        action = Move(self.actor, self.x - self.actor.x, self.y - self.actor.y)
        return action.perform()


class Cast(Action):
    def __init__(self, actor, cost, spell_function, *args):
        super().__init__(actor, cost)
        self.spell_function = spell_function
        self.args = args

    def perform(self):
        if super().perform():
            self.spell_function(*self.args)

