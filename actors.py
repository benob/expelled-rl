import math
import rl

import controllers
import actions
import ui
import util
import graphics
import scenes

class Actor:
    def __init__(self, x=0, y=0, tile=0, name=None, color=0, **kwargs):
        self.type = 'actor'
        self.x = x
        self.y = y
        self.tile = tile
        self.name = name
        self.color = color
        self.z = 0
        self.sight_radius = 10
        self.blocks = False
        self.always_visible = False
        #self.known = False
        self.speed = 10
        self.action = None
        self.energy = 0
        self.fg = 0
        self.bg = 0
        for name, value in kwargs.items():
            setattr(self, name, value)

    def __repr__(self):
        return ujson.dumps(self.__dict__)

    @property
    def alive(self):
        return hasattr(self, 'hp') and self.hp > 0

    def can_see(self, other):
        distance = self.distance_to(other)
        if distance > self.sight_radius:
            return False
        if isinstance(other, Monster) and 'invisible' in other.skills and isinstance(self, Monster) and 'see_invisible' not in self.skills:
            return distance < 2
        if self is player:
            return level.fov[other.x, other.y]
        if other is player:
            return level.fov[self.x, self.y]
        # symetrize line-of-sight
        start_x, start_y = self.x, self.y
        end_x, end_y = other.x, other.y
        #if other is player:
        #    start_x, start_y = player.x, player.y
        #    end_x, end_y = self.x, self.y
        if level.blocked.can_see(start_x, start_y, end_x, end_y):
            return True
        return False

    def can_see_tile(self, x, y):
        distance = math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
        if distance > self.sight_radius:
            return False
        # TODO: use rl.can_see
        for i, j in util.line_iter(self.x, self.y, x, y):
            if i == self.x and j == self.y:
                continue
            if level.blocked[i, j]:
                return False
        return True

    def wait(self):
        self.action = actions.Wait(self)

    def move(self, dx, dy):
        self.action = actions.Move(self, dx, dy)
 
    def move_towards(self, target_x, target_y):
        path = level.blocked.shortest_path(self.x, self.y, target_x, target_y)
        if len(path) > 0:
            self.move(path[0][0] - self.x, path[0][1] - self.y) 

    def move_away_from(self, target_x, target_y):
        # TODO: use better approach
        max_distance = 0
        argmax = None
        for x in range(self.x - self.sight_radius, self.x + self.sight_radius + 1):
            for y in range(self.y - self.sight_radius, self.y + self.sight_radius + 1):
                if not level.is_blocked(x, y):
                    distance = (x - target_x) ** 2 + (y - target_y) ** 2
                    if distance > max_distance:
                        max_distance = distance
                        argmax = (x, y)
        if argmax is not None and self.distance(target_x, target_y) < max_distance:
            return self.move_towards(*argmax)
        # fallback, try local escape
        dx = dy = 0
        if target_x < self.x:
            dx = 1
        elif target_x > self.x:
            dx = -1
        if target_y < self.y:
            dy = 1
        elif target_y > self.y:
            dy = -1
        return self.move(dx, dy)
 
    def distance_to(self, other):
        # return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)
 
    def distance(self, x, y):
        # return the distance to some coordinates
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
 
    def draw(self, x_offset, y_offset):
        # only show if it's visible to the player; or it's set to "always visible" and on an explored tile
        if (level.tile_in_fov(self.x, self.y) or
                (self.always_visible and level.visited[self.x, self.y] > 0)):
            if game.state == 'dead' or (isinstance(self, Monster) and not self.is_hostile(player)) or not (isinstance(self, Monster) and 'invisible' in self.skills) or ('see_invisible' in player.skills) or self.distance_to(player) <= 1:
                if self.alive and player.alive and (self is player or (isinstance(self, Monster) and not self.is_hostile(player))):
                    rl.draw_tile(tileset, (self.x + x_offset) * 8, (self.y + y_offset) * 8, self.tile + 16, self.fg, self.bg)
                else:
                    rl.draw_tile(tileset, (self.x + x_offset) * 8, (self.y + y_offset) * 8, self.tile, self.fg, self.bg)
            if not level.tile_in_fov(self.x, self.y):
                rl.fill_rect((self.x + x_offset) * 8, (self.y + y_offset) * 8, 8, 8, rl.color(0, 0, 0, 128))

    #def enters_player_focus(self):
    #    if player.can_see(self.x, self.y) and (game.state == 'dead' or (isinstance(self, Monster) and not self.is_hostile(player)) or not (isinstance(self, Monster) and 'invisible' in self.skills) or ('see_invisible' in player.skills) or self.distance_to(player) <= 1):
    #        if not self.known:
    #            self.known = True
    #            print('cancel action')
    #            player.action = None

    def info(self):
        return str(self)

    def __str__(self):
        return self.get_name(determiner=None)

    def get_pronoun(self, verb=None):
        if self is player:
            if verb is None:
                return 'you'
            else:
                return 'you ' + verb.format(**{'is': 'are', 'has': 'have', 's': ''})
        pronoun = 'it'
        if self.name in ['wizard', 'nuphrindas']:
            pronoun = 'he'
        return pronoun + ' ' + verb.format(**{'is': 'is', 'has': 'has', 's': 's'})

    def get_name(self, verb=None, determiner='the'):
        if self is player:
            if verb is None:
                return 'you'
            else:
                return 'you ' + verb.format(**{'is': 'are', 'has': 'have', 's': ''})
        subject = determiner + ' ' + self.name if determiner else self.name
        if verb:
            return subject + ' ' + verb.format(**{'is': 'is', 'has': 'has', 's': 's'})
        return subject



class Monster(Actor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'monster'
        self.z = 1
        self.blocks = True

        self.hp = self.max_hp = 0
        self.mana = self.max_mana = 0
        self.possession_cooldown = 0
        self.current_possession_cooldown = 0
        self.defense = 0
        self.power = 0
        self.target = None
        self.target_location = None
        self.flee = None
        self.owner = None
        self.skills = []
        self.actions = []
        self.master = None
        self.controllers = [controllers.MonsterAI()]

        for name, value in kwargs.items():
            setattr(self, name, value)

        for name in ['hp', 'mana']:
            if name not in kwargs:
                setattr(self, name, getattr(self, 'max_' + name))

    def info(self):
        return ' '.join(['(%d,%d)' % (self.x, self.y), 'HP: %d/%d' % (self.hp, self.max_hp), 'MANA: %d/%d' % (self.mana, self.max_mana), 'target:', str(self.target) + ', flee:', str(self.flee)])

    def draw_hp_bar(self, x_offset, y_offset):
        if level.tile_in_fov(self.x, self.y) \
                or (self.always_visible and level.visited[self.x, self.y] > 0):
            #if (not 'invisible' in self.skills) or ('see_invisible' in player.skills) or self.distance_to(player) <= 1:
            if game.state == 'dead' or (isinstance(self, Monster) and not self.is_hostile(player)) or not (isinstance(self, Monster) and 'invisible' in self.skills) or ('see_invisible' in player.skills) or self.distance_to(player) <= 1:
                if self.alive and self.hp < self.max_hp:
                    width = 8 * self.hp // self.max_hp
                    if width < 1:
                        width = 1
                    rl.fill_rect((self.x + x_offset) * 8, (self.y + y_offset + 1) * 8, 8, 1, rl.BLACK)
                    rl.fill_rect((self.x + x_offset) * 8, (self.y + y_offset + 1) * 8, width, 1, rl.RED)

    def push_controller(self, controller):
        self.controllers.append(controller)

    def pop_controller(self):
        if len(self.controllers) > 0:
            return self.controllers.pop()

    @property
    def controller(self):
        if len(self.controllers) > 0:
            return self.controllers[-1]
        return None

    def set_action(self, action):
        self.action = action

    def get_action(self):
        if self.action is None and self.controller:
            self.controller.control(self)
        action = self.action
        if action is not None:
            if not action.repeat:
                self.action = None
            if self.current_possession_cooldown > 0:
                self.current_possession_cooldown -= 1
            if self.mana < self.max_mana:
                self.mana += 1
            if level[self.x, self.y].effect:
                level[self.x, self.y].effect(self)
        return action

    def add_energy(self, amount):
        self.energy += amount

    def consume_energy(self, amount):
        if self.energy < amount:
            return False
        self.energy -= amount
        return True

    #def take_turn(self):
    #    if len(self.controllers) > 0:
    #        result = self.controllers[-1].take_turn(self)
    #        if result != 'didnt-take-turn':
    #            if self.current_possession_cooldown > 0:
    #                self.current_possession_cooldown -= 1
    #            if self.mana < self.max_mana:
    #                self.mana += 1
    #            if level[self.x, self.y].effect:
    #                level[self.x, self.y].effect(self)
    #        return result

    def die(self):
        if self is player:
            ui.message('You died! Press ESCAPE to continue.', rl.RED)
            game.state = 'dead'
            self.tile = graphics.TOMB2
            #save_game()
        else:
            if player.can_see(self):
                ui.message(util.capitalize(self.get_name('{is}')) + ' dead!', rl.ORANGE) 
            self.tile = graphics.CORPSE
        self.color = rl.RED
        self.blocks = False
        self.controllers = []
        self.name = 'remains of ' + self.name
        self.skills = [x for x in self.skills if x != 'invisible']
        self.master = self.target = self.flee = None
        self.z = -1

        if 'boss' in self.skills:
            # show dead boss and trigger ending
            game.push_scene(scenes.Ending())

    def attack(self, target):
        if not self.is_hostile(target):
            print('warning, %s trying to attack friend %s' % (self.owner.name, target.name))
            return
        # a simple formula for attack damage
        damage = rl.random_int(0, self.power) - rl.random_int(0, target.defense)
        print('attack:', self, target, self.power, target.defense, damage)
 
        if damage > 0:
            #damage = rl.random_int(1, damage)
            # make the target take some damage
            if player in [self, target] or player.can_see(self):
                ui.message(util.capitalize(self.get_name('attack{s}')) + ' ' + target.get_name() + ' for ' + str(damage) + ' hit points.')
            else:
                ui.message('You hear combat in the distance', rl.LIGHTGRAY)
            target.take_damage(damage, self)
        else:
            if player in [self, target] or player.can_see(self):
                ui.message(util.capitalize(self.get_name('attack{s}')) + ' ' + target.get_name() + ' but it has no effect!')
 
    def take_damage(self, damage, perpetrator=None):
        if self.hp <= 0:
            return
        if damage > 0:
            self.hp -= damage
            if self.hp <= 0:
                self.die()
            if self is player:
                self.action = None
        if perpetrator is not None:
            self.target = perpetrator
 
    def is_hostile(self, other):
        if not self.alive or not other.alive:
            return False
        if self is other:
            return False
        if self.target == other or other.target == self:
            return True
        if self.master is other or other.master is self: # friendly with master
            return False
        if self.master is not None and self.master is other.master: # friendly with monsters who have the same master
            return False
        if self.master:
            return self.master.is_hostile(other)
        if self.name == other.name and not(self is player or other is player or self.master is player or other.master is player):
            return False
        return True
 
 
class Cloud(Actor):
    def __init__(self, ticks=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticks = ticks

    def apply_effect(self):
        print(self.ticks)
        if self.ticks > 0:
            self.ticks -= 1
            self.wait()
        else:
            level.objects.remove(self)
 
