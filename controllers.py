import rl

import debug
import util
import const
import scenes
import actions
import powers
import ui

def get_movement_from_key(key):
    if key == rl.UP or key == rl.KP_8 or key == rl.K:
        return 0, -1
    elif key == rl.DOWN or key == rl.KP_2 or key == rl.J:
        return 0, 1
    elif key == rl.LEFT or key == rl.KP_4 or key == rl.H:
        return -1, 0
    elif key == rl.RIGHT or key == rl.KP_6 or key == rl.L:
        return 1, 0
    elif key == rl.HOME or key == rl.KP_7 or key == rl.Y:
        return -1, -1
    elif key == rl.PAGEUP or key == rl.KP_9 or key == rl.U:
        return 1, -1
    elif key == rl.END or key == rl.KP_1 or key == rl.B:
        return -1, 1
    elif key == rl.PAGEDOWN or key == rl.KP_3 or key == rl.N:
        return 1, 1
    return 0, 0

class Controller:
    def control(self):
        raise NotImplemented

    def __repr__(self):
        return ujson.dumps(self.__dict__)

    #TODO: update
    @classmethod
    def from_json(_, data):
        cls = {
                'controller': Controller, 
                'do nothing': DoNothing, 
                'monster ai': MonsterAI,
                'player': Player,
                }
        return cls[data['type']](*[data[x] for x in ['x', 'y', 'tile', 'name', 'color']], **data)


class Player(Controller):
    keys = []

    def __init__(self, *args, **kwargs):
        self.type = 'player'

    @classmethod
    def add_key(cls, key):
        cls.keys.append(key)

    @classmethod
    def get_key(cls):
        if len(cls.keys) > 0:
            return cls.keys.pop(0)

    def control(self, actor):
        key = Player.get_key()
        dx, dy = get_movement_from_key(key)
        if key == rl.T:
            game.push_scene(scenes.Help())
        elif key == rl.A:
            game.push_scene(scenes.ActionMenu())
        elif key == rl.C:
            game.push_scene(scenes.MessageBox('Character Information',
                   'Your soul currently inhabits a ' + player.name + '.\n\n'
                   'Maximum HP: ' + str(player.max_hp) +
                   '\nAttack: ' + str(player.power) + '\nDefense: ' + str(player.defense)))
        elif key == rl.P:
            actor.set_action(actions.Cast(actor, 10, powers.cast_possess, player))
        elif key == rl.GREATER:
            if level.stairs.x == player.x and level.stairs.y == player.y:
                game.next_level()
        if key == rl.O:
            actor.set_action(actions.AutoExplore(actor))
        elif not(dx == 0 and dy == 0):
            if rl.shift_pressed():
                actor.set_action(actions.Repeat(actions.Move(actor, dx, dy)))
            else:
                actor.move(dx, dy)


class Wanderer(Controller):
    def control(self, actor):
        dx, dy = rl.random_int(-1, 1), rl.random_int(-1, 1)
        actor.set_action(actions.Move(actor, dx, dy))


class DoNothing(Controller):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'do nothing'

    def control(self, monster):
        monster.wait()


class SpellEffect(Controller):
    def __init__(self, duration, effect=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'spell effect'
        self.effect = effect
        self.duration = duration

    def control(self, monster):
        if self.duration > 0:
            self.duration -= 1
            for obj in level.objects:
                if obj.alive and obj is not monster and obj.x == monster.x and obj.y == monster.y:
                    self.effect(obj)
            monster.set_action(actions.Wait(monster))
        else:
            level.objects.remove(monster)


class MonsterAI(Controller):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'monster ai'

    def control(self, monster):
        old_target = monster.target
        old_flee = monster.flee
        def info(*args, **kwargs):
            pass
            #if debug.active:
            #    if (player.can_see(monster) or old_flee is player or old_target is player):
            #        print('AI', monster.name, *args, **kwargs)

        info(monster.info())
        target = monster.target
        # dangling target after it becomes friendly
        # no dead target
        # 25% chance to forget target if monster can't see it
        if target \
            and (not target.is_hostile(monster) \
                or target.hp <= 0 \
                or (not monster.can_see(target) and rl.random() < .25)):
            target = monster.target = None
            info('  forget target')

        # save target last seen location to be able to follow it when it leaves fov
        if target:
            monster.target_location = (target.x, target.y)
            info('  save target location %d,%d' % (target.x, target.y))
        else:
            monster.target_location = None

        flee = monster.flee
        # dangling flee after it becomes friendly
        # no dead flee
        # 25% chance to forget flee if monster can't see it
        if flee \
            and (not flee.is_hostile(monster) \
                or flee.hp <= 0 \
                or (not monster.can_see(flee) and rl.random() < .25)):
            flee = monster.flee = None
            info('  forget flee')

        # compute flee based on friends and foes
        friends, foes = util.friends_and_foes(monster)
        friends += [monster]
        if len(foes) > 0:
            #foes_hp = sum([m.hp for m in foes])
            friends_hp = sum([m.hp for m in friends])
            foes_power = sum([m.power for m in foes])
            #friends_power = sum([m.power for m in friends])
            #foes_defense = sum([m.defense for m in foes])
            friends_defense = sum([m.defense for m in friends])
            if foes_power - friends_defense >= friends_hp:
                flee = monster.flee = util.closest_hostile(monster, monster.sight_radius)
                info('  outnumbered, flee', str(flee))

        # highest priority is to flee
        if flee and monster.can_see(flee):
            monster.move_away_from(flee.x, flee.y)
            info('  flee: move away from', str(flee))
        elif not target:
            # if no target, move towards master or select new target
            if monster.master and monster.distance_to(monster.master) > 3:
                monster.move_towards(monster.master.x, monster.master.y)
                info('  no target: move towards master')
            else:
                target = monster.target = util.closest_hostile(monster, monster.sight_radius)
                info('  new target: ', str(target))
        else:
            if monster.can_see(target):
                if monster.distance_to(target) >= 2:
                    potential_actions = [action for action in monster.actions if monster.mana >= action.cost]
                    info('potential-actions', monster.mana, potential_actions)
                    value = rl.random()
                    info(value, value < .5, value > .5)
                    if len(potential_actions) > 0 and value < .5:
                        selected = rl.random_int(0, len(monster.actions) - 1)
                        action = monster.actions[selected]
                        info('selected', action)
                        if monster.distance_to(target) <= action.range:
                            if action in [powers.LIGHTNING, powers.FEAR, powers.SUMMON, powers.SUMMON_BAT, powers.SUMMON_EYE, powers.SUMMON_RAT, powers.SUMMON_SKELETON, powers.SUMMON]:
                                action.perform(monster)
                            elif action in [powers.CONFUSE, powers.FREEZE, powers.TELEPORT]:
                                action.perform(monster, target)
                            elif action in [powers.FIREBALL, powers.DIG]:
                                action.perform(monster, target.x, target.y)
                            else:
                                raise ValueError('monster cannot handle action ' + str(action))
                            info('  perform action: ', str(action))
                        else:
                            monster.move_towards(target.x, target.y)
                            info('  move towards target: ', str(target))
                    else:
                        monster.move_towards(target.x, target.y)
                        info('  move towards target: ', str(target))
                else:
                    monster.attack(target)
                    info('  move towards target: ', str(target))
            elif monster.target_location is not None and not (monster.x == monster.target_location[0] and monster.y == monster.target_location[1]):
                monster.move_towards(monster.target_location[0], monster.target_location[1])
                info('  move towards old target location %d,%d' % monster.target_location)
            elif target is not None:
                if powers.DIG in monster.actions:
                    powers.DIG.perform(monster, x=target.x, y=target.y)
                    info('  dig to reach target at %d,%d' % (target.x, target.y))
                else:
                    info('  wait, no dig')
            else:
                info('  wait')

        info('  <<', monster.info())
        if monster.action is None:
            monster.wait()
 
 
class ConfusedMonster(Controller):
    def __init__(self, num_turns=const.CONFUSE_NUM_TURNS, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'confused monster'
        self.num_turns = num_turns
 
    def control(self, monster):
        if self.num_turns > 0:  # still confused...
            # move in a random direction, and decrease the number of turns confused
            self.num_turns -= 1
            monster.move(rl.random_int(-1, 1), rl.random_int(-1, 1))
 
        else:  # restore the previous AI (this one will be deleted because it's not referenced anymore)
            monster.pop_controller()
            ui.message(util.capitalize(monster.get_name('{is}')) + ' no longer confused!', rl.RED)
            monster.controller.control(monster)
 

class ParalyzedMonster(Controller):
    def __init__(self, num_turns=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'paralized monster'
        self.num_turns = num_turns
    
    def control(self, monster):
        if self.num_turns > 0:
            self.num_turns -= 1
            monster.wait()
        else:
            monster.pop_controller()
            if player.can_see(monster) or player is monster:
                ui.message(util.capitalize(monster.get_name('start{s}')) + ' moving again', rl.ORANGE)
            monster.controller.control(monster)


class FrightenedMonster(Controller):
    def __init__(self, flee=None, num_turns=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'frightened monster'
        self.num_turns = num_turns
        self.flee = flee
    
    def control(self, monster):
        if self.num_turns > 0:
            self.num_turns -= 1
            monster.move_away_from(self.flee.x, self.flee.y)
        else:
            monster.pop_controller()
            if player.can_see(monster) or player is monster:
                ui.message(util.capitalize(monster.get_name('{is}')) + ' not frightened anymore.', rl.ORANGE)
            monster.controller.control(monster)

