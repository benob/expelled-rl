import builtins
import math
import rl

import ui

import const
import scenes
import util
import monsters
import controllers
import actors
import graphics
import environments

class Power:
    def __init__(self, name=None, cost=0, range=0, effect=None, *args, **kwargs):
        self.name = name
        self.effect = effect
        self.cost = cost
        self.extra_args = args
        self.range = range

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        return 'Power(%s, %d, %d)' % (self.name, self.cost, self.range)
    
    def __repr__(self):
        return str(self)

    def perform(self, performer, *args, **kwargs):
        args = args + tuple(self.extra_args)
        if performer.mana >= self.cost or self.cost == 0:
            if self.effect(performer, *args, **kwargs) != 'cancelled':
                performer.mana -= self.cost
                return
        elif performer is player:
            ui.message('Not enough mana', rl.BLUE)
        return 'cancelled'

def cast_summon(caster, name=None, hostile=False):
    def summon_monster(name):
        print(name)
        x, y = 0, 0
        i = 0
        while i < 100:
            angle = rl.random_int(0, 359)
            distance = rl.random_int(2, 4)
            x = int(caster.x + .5 + math.cos(math.pi * angle / 180) * distance)
            y = int(caster.y + .5 + math.sin(math.pi * angle / 180) * distance)
            print(x, y)
            if not level.is_blocked(x, y) and caster.can_see_tile(x, y):
                break
            i += 1
        if i == 100:
            if caster is player:
                ui.message('You fail to cast the summon spell.', rl.BLUE)
        monster = monsters.make_monster(name, x, y)
        if not hostile:
            monster.master = caster
        level.objects.append(monster)
        if caster is player or player.can_see(caster) or player.can_see(monster):
            ui.message(util.capitalize(caster.get_name('summon{s}')) + ' ' + monster.get_name(determiner='a') + '.', rl.BLUE)
    if name is None:
        if caster is player:
            options = ['rat', 'bat', 'orc', 'troll', 'ghost', 'eye', 'fire_elemental', 'octopus', 'necromancer', 'wizard']
            def callback(index):
                game.pop_scene()
                summon_monster(options[index])
            game.push_scene(scenes.Menu('What monster do you want to summon?', options, callback))
            return
        else:
            name = monsters.random_choice(monsters.get_monster_chances())
    summon_monster(name)


def cast_lightning(caster, target=None):
    # find closest enemy (inside a maximum range) and damage it
    monster = util.closest_hostile(caster, const.LIGHTNING_RANGE)
    if monster is None:  # no enemy found within maximum range
        if caster is player:
            ui.message('No enemy is close enough to strike.', rl.RED)
        return 'cancelled'
    if target is not None and target is not monster:
        return 'cancelled'
 
    # zap it!
    ui.message('A lighting bolt strikes ' + monster.get_name() + ' with a loud thunder! The damage is '
            + str(const.LIGHTNING_DAMAGE) + ' hit points.', rl.BLUE)
    monster.take_damage(const.LIGHTNING_DAMAGE, player)
 
def cast_fear(caster):
    # find closest enemy (inside a maximum range) and damage it
    monster = util.closest_hostile(caster, const.FEAR_RANGE)
    if monster is None:  # no enemy found within maximum range
        if caster is player:
            ui.message('No enemy is close enough to strike.', rl.RED)
        return 'cancelled'
 
    # zap it!
    if caster is player or monster is player:
        ui.message(util.capitalize(caster.get_name('frighten{s}')) + ' ' + monster.get_name() + '. ' + util.capitalize(monster.get_name('flee{s}')) + '.', rl.BLUE)
    if type(monster.controller) is controllers.FrightenedMonster:
            monster.pop_controller()
    monster.push_controller(controllers.FrightenedMonster(caster, const.FEAR_DURATION))
 
def cast_at_location(text, caster, spell_range, effect, x=None, y=None, any_tile=False):
    def apply_effect_to_tile(x, y):
        if not any_tile and not caster.can_see_tile(x, y):
            if caster is player:
                ui.message('Invalid target', rl.BLUE)
            return 'cancelled'
        if player.can_see_tile(x, y):
            ui.message(text['result'].format(caster=caster.name), rl.ORANGE)
        effect(caster, x, y)
    if caster is player and x is None:
        util.target_tile('Select where to cast {name}'.format(**text), apply_effect_to_tile, spell_range)
    else:
        apply_effect_to_tile(x, y)
 
def cast_fireball(caster, x=None, y=None):
    def effect(caster, x, y):
        for i in range(x - const.FIREBALL_RADIUS, x + const.FIREBALL_RADIUS + 1):
            for j in range(y - const.FIREBALL_RADIUS, y + const.FIREBALL_RADIUS + 1):
                distance = math.sqrt((x - i) ** 2 + (y - j) ** 2)
                if distance < const.FIREBALL_RADIUS and level.blocked[i, j] == 0:
                    level.objects.append(actors.Monster(i, j, graphics.FIREBALL, 'fireball', rl.RED, z=3, blocks=False, max_hp=5, controllers=[controllers.SpellEffect(3, environments.fireball_effect)]))
    return cast_at_location({
        'name': 'fireball',
        'result': util.capitalize(caster.get_name('cast{s}')) + 'a fireball spell. The fireball explodes, burning everything within ' + str(const.FIREBALL_RADIUS) + ' tiles!',
        }, caster, const.FIREBALL_RANGE, effect, x, y)
 
def cast_dig(caster, x=None, y=None):
    def effect(caster, x, y):
        dx = x - caster.x
        dy = y - caster.y
        num = 0
        for i, j in util.line_iter(caster.x, caster.y, caster.x + dx * const.DIG_RANGE, caster.y + dy * const.DIG_RANGE):
            if i >= 0 and i < level.width and j >= 0 and j < level.height:
                if level[i, j].type == 'rock':
                    level[i, j] = graphics.Tile.mapping[graphics.Tile.FLOOR]
            if num > const.DIG_RANGE:
                break
            num += 1
        level.compute_fov()
    return cast_at_location({
        'name': 'dig',
        'result': 'Good diggning makes nice corridors.',
        }, caster, const.DIG_RANGE, effect, x, y, any_tile=True)

def cast_possess(caster):
    if caster.current_possession_cooldown > 0:
        if caster is player:
            ui.message('You need to wait for your possess spell to cool down', rl.BLUE)
        return 'cancelled'
    # ask the player for a target to confuse
    in_fov = util.visible_monsters(caster)

    if len(in_fov) == 0:
        #if caster is player:
        ui.message('No monster in sight to possess.', rl.BLUE)
        return 'cancelled'
    elif len(in_fov) == 1:
        monster = in_fov[0]
        if monster.name == 'nuphrindas':
            if caster is player:
                ui.message('Nuphrindas is too powerfull to be possessed.', rl.YELLOW)
            return 'cancelled'
        monster.push_controller(caster.pop_controller())
        monster.target = None
        monster.flee = None
        monster.master = None
        caster.push_controller(controllers.ParalyzedMonster(3))
        if caster is player:
            if monster.name == 'original body':
                ui.message('You possess your original body. It feels like home.', rl.GREEN)
            else:
                ui.message('You possess ' + monster.get_name(), rl.GREEN)
            builtins.player, old_monster = monster, player
            value = rl.random()
            if value < .2:
                old_monster.hp = 0
                old_monster.die()
            elif value < .4:
                old_monster.take_damage(old_monster.hp // 3)
                if caster is old_monster or player.can_see(old_monster):
                    ui.message(util.capitalize(old_monster.get_name('get{s} hurt and turn{s}')) + ' against ' + monster.get_name() + '.', rl.ORANGE)
            else:
                old_monster.master = player
                if caster is old_monster or player.can_see(old_monster):
                    ui.message(util.capitalize(old_monster.get_name('{is} subdued and start{s} helping')) + ' ' + monster.get_name() + '.', rl.ORANGE)

            level.compute_fov()
        monster.current_possession_cooldown = monster.possession_cooldown
    elif caster is player:
        ui.message('You need to be alone with a monster to possess it.', rl.BLUE)
    return 'cancelled'

def cast_at_monster(text, spell_range, immune, effect, caster, target):
    def apply_effect_to_monster(target):
        if target is None:
            return
        if player is caster or player.can_see(caster):
            ui.message(util.capitalize(caster.get_name('cast{s}')) + ' a {spell}'.format(**text))
     
        if len(set(immune) & set(target.skills)) == 0:
            effect(caster, target)
        else:
            if player.can_see(caster) or caster is player:
                ui.message(util.capitalize(target.get_name('resist{s}')) + '.')

    if target is None:
        #if caster is player:
        #    ui.message('Select a monster to {verb} it (ARROWS+RETURN to select; ESCAPE to cancel).'.format(**text), rl.BLUE)
        util.target_monster('Select a monster to {verb}'.format(**text), apply_effect_to_monster, spell_range)
 
def cast_confuse(caster, target=None):
    def effect(caster, target):
        if type(target.controller) is controllers.ConfusedMonster:
            target.pop_controller()
        target.push_controller(controllers.ConfusedMonster())
        if target is player or player.can_see(target): 
            ui.message(util.capitalize(target.get_name()) + ' is confused. ' + util.capitalize(target.get_pronoun('start{s}')) + ' to stumble around!', rl.BLUE)
    return cast_at_monster({
        'verb': 'confuse', 
        'spell': 'spell of confusion', 
        }, const.CONFUSE_RANGE, ['immune_mind'], effect, caster, target)

def cast_freeze(caster, target=None):
    def effect(caster, target):
        if type(target.controller) is controllers.ParalyzedMonster:
            target.pop_controller()
        target.push_controller(controllers.ParalyzedMonster(const.FREEZE_DURATION))
        if target is player or player.can_see(target):
            ui.message(target.get_name('freeze{s}') + '!', rl.BLUE)
    return cast_at_monster({
        'verb': 'feeze', 
        'spell': 'spell of freezing', 
        }, const.FREEZE_RANGE, ['immune_cold'], effect, caster, target)

def cast_teleport(caster, target=None):
    def effect(caster, target):
        target.x, caster.x = caster.x, target.x
        target.y, caster.y = caster.y, target.y
        if target is player or caster is player or player.can_see(target) or player.can_see(caster):
            ui.message('Teleportation: ' + caster.get_name('exchange{s}') + ' location with ' + target.get_name() + '!', rl.BLUE)
    return cast_at_monster({
        'verb': 'teleport', 
        'spell': 'spell of teleporation', 
        }, const.TELEPORT_RANGE, ['immune_teleport'], effect, caster, target)


LIGHTNING = Power('Create lightning', 7, const.LIGHTNING_RANGE, cast_lightning)
FEAR = Power('Induce fear', 3, const.FEAR_RANGE, cast_fear)
FIREBALL = Power('Launch fireball', 12, const.FIREBALL_RANGE, cast_fireball)
CONFUSE = Power('Confuse other', 2, const.CONFUSE_RANGE, cast_confuse)
FREEZE = Power('Freeze other', 6, const.FREEZE_RANGE, cast_freeze)
TELEPORT = Power('Teleport', 2, const.TELEPORT_RANGE, cast_teleport)
#POSSESS = Power('Cast possess', 0, cast_possess)
DIG = Power('Dig', 4, const.NO_RANGE, cast_dig)
SUMMON = Power('Summon monster', 30, const.NO_RANGE, cast_summon)
SUMMON_BAT = Power('Summon bat', 10, const.NO_RANGE, cast_summon, 'bat')
SUMMON_EYE = Power('Summon eye', 10, const.NO_RANGE, cast_summon, 'eye')
SUMMON_RAT = Power('Summon rat', 10, const.NO_RANGE, cast_summon, 'rat')
SUMMON_SKELETON = Power('Summon skeleton', 30, const.NO_RANGE, cast_summon, 'skeleton')
